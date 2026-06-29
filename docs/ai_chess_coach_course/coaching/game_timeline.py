"""Build ordered game timelines for root-cause analysis (any game)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from coaching.pgn_context import player_ply_index

PLAYER_COLOR_WHITE = 1
PLAYER_COLOR_BLACK = 0


def resolve_player_is_white(
    rows: pd.DataFrame,
    player_name: str,
) -> bool:
    if rows.empty:
        return True
    row = rows.iloc[0]
    if row.get("white_player") == player_name:
        return True
    if row.get("black_player") == player_name:
        return False
    return True


def resolve_player_color_value(rows: pd.DataFrame, player_name: str) -> int:
    return PLAYER_COLOR_WHITE if resolve_player_is_white(rows, player_name) else PLAYER_COLOR_BLACK


def ply_to_player_move_number(ply: int, *, is_white: bool) -> int | None:
    """Map 0-based mainline ply index to the coached player's move_number."""
    if ply < 0:
        return None
    if is_white and ply % 2 == 0:
        return ply // 2 + 1
    if not is_white and ply % 2 == 1:
        return (ply + 1) // 2
    return None


def fetch_game_feature_rows(
    repo: Any,
    game_id: str,
    *,
    fallback_rows: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Load all feature rows for one game (both colors when available)."""
    columns = [
        "game_id",
        "move_number",
        "move_number_global",
        "player_color",
        "error_label",
        "score_diff",
        "move_san",
        "phase",
        "white_player",
        "black_player",
        "king_safety",
        "self_mobility",
        "opponent_mobility",
        "center_control",
        "branching_factor",
        "has_castling_rights",
        "is_pawn_endgame",
        "is_low_mobility",
        "is_center_controlled",
        "material_total",
        "material_balance",
        "tags",
    ]
    if repo is not None:
        loaded = repo.load_features(columns=columns, game_ids=[game_id])
        if not loaded.empty:
            return loaded.copy()

    if fallback_rows is not None and not fallback_rows.empty:
        if game_id and "game_id" in fallback_rows.columns:
            scoped = fallback_rows[fallback_rows["game_id"] == game_id].copy()
        else:
            scoped = fallback_rows.copy()
        available = [column for column in columns if column in scoped.columns]
        return scoped[available].copy() if available else scoped

    return pd.DataFrame(columns=columns)


def _sort_timeline_rows(rows: pd.DataFrame, *, is_white: bool) -> pd.DataFrame:
    if rows.empty:
        return rows.copy()

    frame = rows.copy()
    if "player_color" not in frame.columns:
        return frame

    target_color = PLAYER_COLOR_WHITE if is_white else PLAYER_COLOR_BLACK
    frame["_ply"] = frame.apply(
        lambda row: player_ply_index(int(row["move_number"]), is_white=row["player_color"] == PLAYER_COLOR_WHITE)
        if pd.notna(row.get("move_number"))
        else -1,
        axis=1,
    )
    frame = frame.sort_values(["_ply", "player_color"], ascending=[True, False]).reset_index(drop=True)
    return frame.drop(columns=["_ply"], errors="ignore")


def player_move_lookup(
    game_rows: pd.DataFrame,
    *,
    player_name: str,
) -> dict[int, pd.Series]:
    """Map coached-player move_number → feature row."""
    if game_rows.empty:
        return {}

    is_white = resolve_player_is_white(game_rows, player_name)
    target_color = PLAYER_COLOR_WHITE if is_white else PLAYER_COLOR_BLACK
    if "player_color" not in game_rows.columns:
        return {}

    scoped = game_rows[game_rows["player_color"] == target_color].copy()
    lookup: dict[int, pd.Series] = {}
    for _, row in scoped.iterrows():
        if pd.isna(row.get("move_number")):
            continue
        move_number = int(row["move_number"])
        existing = lookup.get(move_number)
        if existing is None:
            lookup[move_number] = row
            continue
        existing_label = str(existing.get("error_label") or "")
        new_label = str(row.get("error_label") or "")
        if new_label in {"blunder", "mistake"} and existing_label not in {"blunder", "mistake"}:
            lookup[move_number] = row
    return lookup


def build_game_timeline(
    game_rows: pd.DataFrame,
    *,
    player_name: str,
) -> tuple[pd.DataFrame, bool]:
    """Return feature rows sorted by ply order and whether the coached player is White."""
    is_white = resolve_player_is_white(game_rows, player_name)
    return _sort_timeline_rows(game_rows, is_white=is_white), is_white
