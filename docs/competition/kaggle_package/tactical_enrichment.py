"""Enrich competition game feature rows with tactical tags in course SQLite."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from kaggle_package.config import DEFAULT_SQLITE_PATH, RANDOM_STATE
from kaggle_package.game_inventory import load_human_games
from kaggle_package.game_selection import select_games_by_elo_band
from kaggle_package.tactical_patterns import detect_pattern_from_row

DEFAULT_CHECKPOINT_PATH = Path(__file__).resolve().parents[1] / "output" / "tactical_enrichment_checkpoint.json"
DEFAULT_GAME_IDS_PATH = Path(__file__).resolve().parents[1] / "output" / "competition_game_ids.json"
FEATURE_BATCH_SIZE = 5000


@dataclass
class TacticalEnrichmentResult:
    game_ids: list[str]
    rows_updated: int
    tag_distribution: dict[str, int]
    checkpoint_path: Path


def resolve_competition_game_ids(
    db_url: str | Path,
    *,
    random_state: int = RANDOM_STATE,
) -> list[str]:
    games = load_human_games(db_url)
    selected = select_games_by_elo_band(games, random_state=random_state)
    return selected["game_id"].astype(str).tolist()


def _load_checkpoint(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(payload.get("completed_game_ids", []))


def _save_checkpoint(path: Path, completed_game_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"completed_game_ids": sorted(completed_game_ids)}, indent=2),
        encoding="utf-8",
    )


def _sqlite_path(db_url: str | Path) -> Path:
    text = str(db_url)
    if text.startswith("sqlite:///"):
        return Path(text.removeprefix("sqlite:///"))
    return Path(text)


def enrich_tactical_tags(
    db_url: str | Path | None = None,
    game_ids: Sequence[str] | None = None,
    *,
    checkpoint_path: Path | None = None,
    game_ids_path: Path | None = None,
    resume: bool = True,
) -> TacticalEnrichmentResult:
    sqlite_path = _sqlite_path(db_url or DEFAULT_SQLITE_PATH)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite not found: {sqlite_path}")

    resolved_game_ids = list(game_ids or resolve_competition_game_ids(sqlite_path))
    if not resolved_game_ids:
        raise ValueError("No competition game IDs to enrich.")

    ids_out = game_ids_path or DEFAULT_GAME_IDS_PATH
    ids_out.parent.mkdir(parents=True, exist_ok=True)
    ids_out.write_text(json.dumps(resolved_game_ids, indent=2), encoding="utf-8")

    checkpoint = checkpoint_path or DEFAULT_CHECKPOINT_PATH
    completed = _load_checkpoint(checkpoint) if resume else set()
    pending = [game_id for game_id in resolved_game_ids if game_id not in completed]

    tag_counts: dict[str, int] = {}
    rows_updated = 0

    conn = sqlite3.connect(sqlite_path)
    try:
        for game_id in pending:
            cur = conn.execute(
                """
                SELECT move_number, player_color, fen, move_uci, move_san
                FROM features
                WHERE game_id = ?
                ORDER BY move_number, player_color
                """,
                (game_id,),
            )
            updates: list[tuple[str, str, int, int]] = []
            for move_number, player_color, fen, move_uci, move_san in cur.fetchall():
                tag = detect_pattern_from_row(
                    fen=fen,
                    move_uci=move_uci,
                    move_san=move_san,
                )
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                updates.append((json.dumps([tag]), game_id, move_number, player_color))

            if updates:
                conn.executemany(
                    """
                    UPDATE features
                    SET tags = ?
                    WHERE game_id = ? AND move_number = ? AND player_color = ?
                    """,
                    updates,
                )
                rows_updated += len(updates)

            conn.commit()
            completed.add(game_id)
            _save_checkpoint(checkpoint, completed)

        conn.commit()
    finally:
        conn.close()

    return TacticalEnrichmentResult(
        game_ids=resolved_game_ids,
        rows_updated=rows_updated,
        tag_distribution=dict(sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))),
        checkpoint_path=checkpoint,
    )
