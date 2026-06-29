"""Select complete games and isolate coached-player moves (Module 6.5)."""

from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from coaching.pattern_engine import OPENING_PREFIX

DEFAULT_COURSE_PLAYER = "cmess1315"


def player_mask(dataset: pd.DataFrame, player_name: str) -> pd.Series:
    if "white_player" not in dataset.columns or "black_player" not in dataset.columns:
        raise ValueError("Dataset must include white_player and black_player columns.")
    return (dataset["white_player"] == player_name) | (dataset["black_player"] == player_name)


def list_player_game_ids(
    dataset: pd.DataFrame,
    *,
    player_name: str = DEFAULT_COURSE_PLAYER,
) -> list[str]:
    mask = player_mask(dataset, player_name)
    return dataset.loc[mask, "game_id"].drop_duplicates().tolist()


def select_player_game_ids(
    dataset: pd.DataFrame,
    *,
    player_name: str = DEFAULT_COURSE_PLAYER,
    n_games: int = 1,
    random_state: int = 42,
    game_ids: Sequence[str] | None = None,
) -> list[str]:
    if game_ids is not None:
        return list(game_ids)
    candidates = list_player_game_ids(dataset, player_name=player_name)
    if not candidates:
        raise ValueError(f"No games found for player {player_name!r}.")
    frame = pd.DataFrame({"game_id": candidates})
    sampled = frame.sample(n=min(n_games, len(frame)), random_state=random_state)
    return sampled["game_id"].tolist()


def fetch_player_color_index(
    repo: Any,
    game_ids: Sequence[str],
) -> pd.DataFrame:
    """Load (game_id, move_number, player_color) from the course database."""
    lookup = repo.load_features(
        columns=["game_id", "move_number", "player_color"],
        game_ids=list(game_ids),
    )
    if lookup.empty:
        return lookup
    return lookup.drop_duplicates(subset=["game_id", "move_number", "player_color"])


def filter_player_moves(
    game_rows: pd.DataFrame,
    *,
    player_name: str,
    player_color_index: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Keep one row per move played by the coached player."""
    if game_rows.empty:
        return game_rows.copy()

    game_id = game_rows["game_id"].iloc[0]
    scoped = game_rows[game_rows["game_id"] == game_id].copy()
    player_is_white = scoped["white_player"].iloc[0] == player_name
    target_color = 1 if player_is_white else 0

    if "player_color" in scoped.columns:
        filtered = scoped[scoped["player_color"] == target_color]
        return (
            filtered.drop_duplicates(subset=["game_id", "move_number"])
            .reset_index(drop=True)
        )

    if player_color_index is not None and not player_color_index.empty:
        color_lookup = player_color_index[
            (player_color_index["game_id"] == game_id)
            & (player_color_index["player_color"] == target_color)
        ]
        merged = color_lookup.merge(
            scoped,
            on=["game_id", "move_number"],
            how="inner",
        )
        return (
            merged.drop_duplicates(subset=["game_id", "move_number"])
            .reset_index(drop=True)
        )

    # Fallback when player_color is unavailable: dedupe by move_number parity.
    if player_is_white:
        scoped = scoped[scoped["move_number"] % 2 == 1]
    else:
        scoped = scoped[scoped["move_number"] % 2 == 0]
    return scoped.drop_duplicates(subset=["move_number"]).reset_index(drop=True)


def _opening_from_rows(rows: pd.DataFrame) -> str | None:
    opening_columns = [column for column in rows.columns if str(column).startswith(OPENING_PREFIX)]
    if not opening_columns:
        return None
    totals = {column: float(rows[column].sum()) for column in opening_columns}
    best_column = max(totals, key=totals.get)
    if totals[best_column] <= 0:
        return None
    return str(best_column).removeprefix(OPENING_PREFIX)


def _opponent_name(game_rows: pd.DataFrame, player_name: str) -> str | None:
    if game_rows.empty:
        return None
    row = game_rows.iloc[0]
    if row.get("white_player") == player_name:
        return str(row.get("black_player"))
    if row.get("black_player") == player_name:
        return str(row.get("white_player"))
    return None


def summarize_game(
    game_rows: pd.DataFrame,
    *,
    player_name: str,
    player_color_index: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Human-readable summary for one complete game."""
    if game_rows.empty:
        raise ValueError("Cannot summarize an empty game frame.")

    game_id = str(game_rows["game_id"].iloc[0])
    player_moves = filter_player_moves(
        game_rows,
        player_name=player_name,
        player_color_index=player_color_index,
    )
    labels = player_moves["error_label"] if "error_label" in player_moves.columns else pd.Series(dtype=str)
    breakdown = (
        labels.value_counts(normalize=True).round(4).to_dict() if not labels.empty else {}
    )

    return {
        "game_id": game_id,
        "opponent": _opponent_name(game_rows, player_name),
        "result": str(game_rows["result"].iloc[0]) if "result" in game_rows.columns else None,
        "opening": _opening_from_rows(player_moves),
        "player_moves_analyzed": int(len(player_moves)),
        "move_number_range": [
            int(player_moves["move_number"].min()),
            int(player_moves["move_number"].max()),
        ]
        if not player_moves.empty
        else None,
        "error_breakdown": {str(key): float(value) for key, value in breakdown.items()},
    }


def collect_player_game_frames(
    dataset: pd.DataFrame,
    game_ids: Sequence[str],
    *,
    player_name: str = DEFAULT_COURSE_PLAYER,
    player_color_index: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Return all coached-player moves across games plus per-game summaries."""
    move_frames: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []

    for game_id in game_ids:
        game_rows = dataset[dataset["game_id"] == game_id].copy()
        if game_rows.empty:
            continue
        player_moves = filter_player_moves(
            game_rows,
            player_name=player_name,
            player_color_index=player_color_index,
        )
        if player_moves.empty:
            continue
        move_frames.append(player_moves)
        summaries.append(
            summarize_game(
                game_rows,
                player_name=player_name,
                player_color_index=player_color_index,
            )
        )

    if not move_frames:
        raise ValueError(f"No player moves found for {player_name!r} in selected games.")

    combined = pd.concat(move_frames, ignore_index=True)
    return combined, summaries


def attach_move_notation(
    player_moves: pd.DataFrame,
    repo: Any,
    *,
    game_id: str,
    player_name: str,
    player_color_index: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Join move_san from the course database onto coached-player rows."""
    if player_moves.empty or repo is None:
        return player_moves.copy()

    notation = repo.load_features(
        columns=["game_id", "move_number", "player_color", "move_san", "white_player", "black_player"],
        game_ids=[game_id],
    )
    if notation.empty or "move_san" not in notation.columns:
        return player_moves.copy()

    if "white_player" in notation.columns:
        scoped = filter_player_moves(
            notation,
            player_name=player_name,
            player_color_index=player_color_index,
        )
    else:
        first = player_moves.iloc[0]
        is_white = first.get("white_player") == player_name
        target_color = 1 if is_white else 0
        scoped = notation[notation["player_color"] == target_color]

    if scoped.empty:
        return player_moves.copy()

    lookup = scoped[["move_number", "move_san"]].drop_duplicates(subset=["move_number"])
    return player_moves.merge(lookup, on="move_number", how="left")
