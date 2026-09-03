"""F07-035 — JSON review pack for one decision (HITL, no LLM)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from analysis.abstention import DiagnosisAbstention, assess_diagnosis_abstention
from analysis.comparison import PlayedVsCandidates
from analysis.criticality import PlyCriticality
from analysis.engine_eval import EngineScore, EvaluationLoss, PlayerScore
from analysis.game_models import NormalizedGame, PlayerSelection, PlyRecord

SCHEMA_VERSION = "chessinsight.review_pack.v1"
FEATURE_ID = "F07-035"


def _player_score_json(score: PlayerScore) -> dict[str, Any]:
    return {
        "player_color": score.player_color,
        "kind": score.kind,
        "cp": score.cp,
        "mate": score.mate,
        "as_cp_units": score.as_cp_units(),
    }


def _engine_score_json(score: EngineScore) -> dict[str, Any]:
    return {
        "kind": score.kind,
        "white_cp": score.white_cp,
        "white_mate": score.white_mate,
    }


def _safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())[:48]
    return cleaned or "game"


def default_review_pack_name(game_id: str, ply: int, san: str) -> str:
    move = _safe_stem(san)
    return f"review_pack_{_safe_stem(game_id)}_ply{ply}_{move}.json"


def build_review_pack(
    game: NormalizedGame,
    ply: PlyRecord,
    player: PlayerSelection,
    comparison: PlayedVsCandidates,
    abstention: DiagnosisAbstention | None = None,
    *,
    pgn_source: str = "",
    criticality: PlyCriticality | None = None,
    eval_loss: EvaluationLoss | None = None,
    case_id: str | None = None,
) -> dict[str, Any]:
    """Assemble a JSON-serializable pack for one ply (F07-035)."""
    gate = abstention or assess_diagnosis_abstention(comparison)
    played = comparison.played
    status = "PENDING_REVIEW" if gate.status == "NONE" else gate.status
    pack: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "feature_id": FEATURE_ID,
        "case_id": case_id or f"{game.game_id}-ply{ply.ply}-{ply.san}",
        "game_id": game.game_id,
        "pgn_source": pgn_source,
        "pgn": game.pgn,
        "player": player.username,
        "player_color": player.color.upper(),
        "move_number": ply.move_number,
        "ply": ply.ply,
        "fen_before": ply.fen_before,
        "fen_after": ply.fen_after,
        "played_move": {
            "san": ply.san,
            "uci": ply.uci,
            "in_multipv": played.in_multipv,
            "multipv_rank": played.multipv_rank,
            "source": played.source,
            "score": _engine_score_json(played.score),
            "player_score": _player_score_json(played.player_score),
            "pv_san": list(played.pv_san),
            "purpose": comparison.played_purpose.value,
            "consequence": {
                "tags": list(comparison.played_consequence.tags),
                "gives_check": comparison.played_consequence.gives_check,
                "is_capture": comparison.played_consequence.is_capture,
                "is_mate": comparison.played_consequence.is_mate,
                "material_delta_cp": comparison.played_consequence.material_delta_cp,
                "opponent_pv_san": comparison.played_consequence.opponent_pv_san,
            },
        },
        "candidates": [
            {
                "rank": row.candidate.multipv_rank,
                "san": row.candidate.move_san,
                "uci": row.candidate.move_uci,
                "pv_san": list(row.pv_san),
                "player_score": _player_score_json(row.candidate.player_score),
                "eval_gap_cp": row.eval_gap_cp,
                "same_move": row.same_move,
                "purpose": row.purpose.value,
                "purpose_differs": row.purpose_differs,
                "consequence_tags": list(row.consequence.tags),
            }
            for row in comparison.diffs
        ],
        "actual_result": {
            "eval_gap_vs_best_cp": comparison.eval_gap_vs_best_cp,
            "played_is_best": comparison.played_is_best,
            "best_san": comparison.best.move_san if comparison.best else None,
            "abstention": {
                "status": gate.status,
                "reasons": list(gate.reasons),
                "may_diagnose": gate.may_diagnose,
                "message": gate.message,
            },
            "primary_error": None,
        },
        "expected_result": {},
        "human_label": {"confirmed": None, "comment": ""},
        "evidence": {
            "engine": "Stockfish",
            "multipv": len(comparison.diffs),
            "layer": "evidence",
            "inference_as_fact": False,
        },
        "status": status,
        "notes": "",
    }
    if criticality is not None:
        pack["criticality"] = {
            "score": criticality.score,
            "level": criticality.level,
            "critical": criticality.critical,
        }
    if eval_loss is not None:
        pack["eval_loss"] = {
            "eval_delta": eval_loss.eval_delta,
            "eval_loss": eval_loss.eval_loss,
            "cp_loss": eval_loss.cp_loss,
        }
    return pack


def write_review_pack(pack: dict[str, Any], path: str | Path) -> Path:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest
