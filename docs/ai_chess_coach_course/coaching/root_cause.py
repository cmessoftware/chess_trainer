"""Root-cause analysis for critical moves (game-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from coaching.game_timeline import (
    build_game_timeline,
    fetch_game_feature_rows,
    player_move_lookup,
    ply_to_player_move_number,
    resolve_player_is_white,
)
from coaching.instructional_patterns import (
    BLUNDER_CP_THRESHOLD,
    MISTAKE_CP_THRESHOLD,
)
from coaching.diagnosis_builder import DiagnosisBuilder
from coaching.pgn_context import extract_tactical_line, parse_pgn_sans, player_ply_index

CRITICAL_LABELS = ("mistake", "blunder")
LABEL_PRIORITY = {"blunder": 2, "mistake": 1}

DEFAULT_WALKBACK_PLIES = 5
DEFAULT_MAX_MOMENTS = 6
DEFAULT_INCIDENT_GAP_MOVES = 8

_DIAGNOSIS_BUILDER = DiagnosisBuilder()


@dataclass
class CriticalIncident:
    root_move_number: int
    root_label: str
    root_row: pd.Series
    root_index: int
    consequence_move_numbers: list[int] = field(default_factory=list)
    total_cp_loss: float = 0.0

    @property
    def severity_rank(self) -> tuple[int, float, int]:
        return (
            LABEL_PRIORITY.get(self.root_label, 0),
            self.total_cp_loss,
            self.root_move_number,
        )


def _cp_loss(row: pd.Series) -> float:
    value = row.get("score_diff")
    if value is None or pd.isna(value):
        return 0.0
    return max(0.0, float(value))


def _format_move_label(row: pd.Series) -> str:
    move_number = row.get("move_number")
    move_san = row.get("move_san")
    if pd.notna(move_san) and str(move_san).strip():
        prefix = f"{int(move_number)}. " if pd.notna(move_number) else ""
        return f"{prefix}{str(move_san).strip()}"
    if pd.notna(move_number):
        return f"jugada {int(move_number)}"
    return "jugada clave"


def _verbalize_eval_shift(cp_loss: float) -> str:
    if cp_loss >= BLUNDER_CP_THRESHOLD:
        return "La posición pasó de playable a desventaja decisiva."
    if cp_loss >= MISTAKE_CP_THRESHOLD:
        return "La posición cedió iniciativa o material de forma clara."
    if cp_loss >= 50:
        return "La jugada debilitó la coordinación sin recuperar compensación."
    return "Hubo una pérdida leve de calidad posicional."


def find_root_move_number(
    symptom_move_number: int,
    *,
    is_white: bool,
    player_lookup: dict[int, pd.Series],
    walkback_plies: int = DEFAULT_WALKBACK_PLIES,
) -> int:
    """
    Walk back from a symptom move and return the earliest coached-player
    mistake/blunder in the lookback window. Falls back to the symptom itself.
    """
    symptom_ply = player_ply_index(symptom_move_number, is_white=is_white)
    earliest: int | None = None

    for ply in range(max(0, symptom_ply - walkback_plies), symptom_ply + 1):
        candidate_move_number = ply_to_player_move_number(ply, is_white=is_white)
        if candidate_move_number is None:
            continue
        row = player_lookup.get(candidate_move_number)
        if row is None:
            continue
        label = str(row.get("error_label") or "")
        if label not in CRITICAL_LABELS:
            continue
        if earliest is None or candidate_move_number < earliest:
            earliest = candidate_move_number

    return earliest if earliest is not None else symptom_move_number


def _cluster_error_move_numbers(move_numbers: list[int], *, max_gap: int) -> list[list[int]]:
    if not move_numbers:
        return []
    ordered = sorted(set(move_numbers))
    clusters: list[list[int]] = [[ordered[0]]]
    for move_number in ordered[1:]:
        if move_number - clusters[-1][-1] <= max_gap:
            clusters[-1].append(move_number)
        else:
            clusters.append([move_number])
    return clusters


def resolve_incident_root(
    symptom_move_number: int,
    *,
    is_white: bool,
    player_lookup: dict[int, pd.Series],
    walkback_plies: int,
    cluster_root: int,
) -> int:
    """
    Pick the pedagogical root inside an error cluster.

    Uses a short ply walkback for immediate causes, but never later than the
    cluster's earliest error (handles long forcing sequences in any game).
    """
    local_root = find_root_move_number(
        symptom_move_number,
        is_white=is_white,
        player_lookup=player_lookup,
        walkback_plies=walkback_plies,
    )
    return min(local_root, cluster_root)


def build_critical_incidents(
    player_moves: pd.DataFrame,
    labels: pd.Series,
    *,
    game_rows: pd.DataFrame,
    player_name: str,
    walkback_plies: int = DEFAULT_WALKBACK_PLIES,
    incident_gap_moves: int = DEFAULT_INCIDENT_GAP_MOVES,
) -> list[CriticalIncident]:
    """Group mistake/blunder rows into root-cause incidents for any game."""
    if player_moves.empty:
        return []

    _, is_white = build_game_timeline(game_rows, player_name=player_name)
    player_lookup = player_move_lookup(game_rows, player_name=player_name)

    index_by_move_number: dict[int, int] = {}
    error_move_numbers: list[int] = []
    label_by_move: dict[int, str] = {}

    for index, (_, row) in enumerate(player_moves.iterrows()):
        label = str(labels.iloc[index])
        if label not in CRITICAL_LABELS:
            continue
        if pd.isna(row.get("move_number")):
            continue
        move_number = int(row["move_number"])
        index_by_move_number[move_number] = index
        error_move_numbers.append(move_number)
        label_by_move[move_number] = label

    incidents: dict[int, CriticalIncident] = {}
    for cluster in _cluster_error_move_numbers(error_move_numbers, max_gap=incident_gap_moves):
        cluster_root = cluster[0]
        root_move_number = resolve_incident_root(
            cluster[-1],
            is_white=is_white,
            player_lookup=player_lookup,
            walkback_plies=walkback_plies,
            cluster_root=cluster_root,
        )
        root_row = player_lookup.get(root_move_number)
        if root_row is None:
            root_index = index_by_move_number.get(root_move_number, index_by_move_number[cluster[-1]])
            root_row = player_moves.iloc[root_index]
        else:
            root_index = index_by_move_number.get(root_move_number, index_by_move_number[cluster[0]])

        root_label = str(root_row.get("error_label") or label_by_move.get(root_move_number, "mistake"))
        incident = CriticalIncident(
            root_move_number=root_move_number,
            root_label=root_label,
            root_row=root_row,
            root_index=root_index,
        )

        for move_number in cluster:
            label = label_by_move[move_number]
            row = player_lookup.get(move_number)
            cp_loss = _cp_loss(row) if row is not None else 0.0
            incident.total_cp_loss = max(incident.total_cp_loss, cp_loss)
            if move_number != root_move_number and move_number not in incident.consequence_move_numbers:
                incident.consequence_move_numbers.append(move_number)
            if LABEL_PRIORITY.get(label, 0) > LABEL_PRIORITY.get(incident.root_label, 0):
                incident.root_label = label

        incidents[root_move_number] = incident

    ranked = sorted(incidents.values(), key=lambda item: item.severity_rank, reverse=True)
    return ranked


def analyze_critical_moves(
    player_moves: pd.DataFrame,
    labels: pd.Series,
    explanations: list[dict[str, Any]],
    feature_rows: pd.DataFrame,
    *,
    game_rows: pd.DataFrame | None = None,
    repo: Any | None = None,
    game_id: str | None = None,
    player_name: str,
    pgn_text: str | None = None,
    is_white: bool | None = None,
    max_moments: int = DEFAULT_MAX_MOMENTS,
    walkback_plies: int = DEFAULT_WALKBACK_PLIES,
) -> list[dict[str, Any]]:
    """
    Produce root-cause-aware critical moments for coaching (any game).

    Engine numeric values stay in Python; the payload uses verbal eval_shift only.
    """
    if len(player_moves) != len(labels) or len(player_moves) != len(explanations):
        raise ValueError("player_moves, labels, and explanations must align.")

    resolved_game_id = game_id
    if resolved_game_id is None and not player_moves.empty and "game_id" in player_moves.columns:
        resolved_game_id = str(player_moves["game_id"].iloc[0])

    timeline_rows = game_rows
    if timeline_rows is None or timeline_rows.empty:
        timeline_rows = fetch_game_feature_rows(
            repo,
            str(resolved_game_id) if resolved_game_id else "",
            fallback_rows=player_moves,
        )
    if timeline_rows.empty:
        timeline_rows = player_moves.copy()

    if is_white is None:
        is_white = resolve_player_is_white(timeline_rows, player_name)

    incidents = build_critical_incidents(
        player_moves,
        labels,
        game_rows=timeline_rows,
        player_name=player_name,
        walkback_plies=walkback_plies,
    )

    sans = parse_pgn_sans(pgn_text or "")
    moments: list[dict[str, Any]] = []

    for incident in incidents[:max_moments]:
        root_row = incident.root_row
        root_index = incident.root_index
        lookup = player_move_lookup(timeline_rows, player_name=player_name)
        diagnosis_row = lookup.get(incident.root_move_number, root_row)
        root_ply = player_ply_index(incident.root_move_number, is_white=is_white)
        tactical_line = extract_tactical_line(sans, root_ply, plies_ahead=3) if sans else None
        opponent_reply = sans[root_ply + 1] if sans and root_ply + 1 < len(sans) else None

        diagnosis = _DIAGNOSIS_BUILDER.build(
            diagnosis_row,
            explanations[root_index],
            error_label=incident.root_label,
            sans=sans,
            root_ply=root_ply,
            is_white=is_white,
            tactical_line=tactical_line,
            opponent_reply=opponent_reply,
        )

        consequence_labels = []
        for move_number in sorted(incident.consequence_move_numbers):
            row = lookup.get(move_number)
            if row is None:
                continue
            consequence_labels.append(_format_move_label(row))

        moment = {
            "move_number": incident.root_move_number,
            "move": _format_move_label(root_row),
            "error_label": incident.root_label,
            "root_cause": True,
            "eval_shift": _verbalize_eval_shift(max(_cp_loss(root_row), incident.total_cp_loss)),
            "severity": "error grave" if incident.root_label == "blunder" else "error claro",
            "phase": str(root_row.get("phase") or "") or None,
            "tactical_line": tactical_line,
            "consequence_moves": consequence_labels,
            **diagnosis.as_moment_fields(),
        }
        if moment["phase"]:
            phase_map = {"opening": "apertura", "middlegame": "medio juego", "endgame": "final"}
            moment["phase"] = phase_map.get(str(moment["phase"]).lower(), moment["phase"])
        moments.append(moment)

    return moments
