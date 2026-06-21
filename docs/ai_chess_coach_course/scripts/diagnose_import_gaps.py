#!/usr/bin/env python3
"""Compare PG ELO-band availability vs SQLite balanced import."""
from __future__ import annotations

import os
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = COURSE_ROOT.parents[1]
sys.path.insert(0, str(COURSE_ROOT))

from dotenv import load_dotenv

from data_access.features_repository import CourseFeaturesRepository
from dataset.skill_groups import COURSE_SKILL_GROUP_GAME_QUOTAS, COURSE_SKILL_GROUPS

load_dotenv(REPO_ROOT / ".env")

BANDS = [(group.name, group.min_elo, group.max_elo) for group in COURSE_SKILL_GROUPS]


def _print_band_table(title: str, repo: CourseFeaturesRepository, *, exclusive: bool) -> None:
    print(title)
    print(f"{'Band':<20} {'PG avail':>10} {'Quota':>8} {'Can fill?':>10}")
    print("-" * 52)
    for name, min_elo, max_elo in BANDS:
        quota = COURSE_SKILL_GROUP_GAME_QUOTAS[name]
        available = repo.count_games(
            player_elo_min=min_elo,
            player_elo_max=max_elo,
            exclusive_elo_band=exclusive,
        )
        fill = "yes" if available >= quota else f"NO ({available:,})"
        print(f"{name:<20} {available:>10,} {quota:>8,} {fill:>10}")
    print()


def main() -> int:
    pg_url = os.environ.get("CHESS_TRAINER_DB_URL")
    if not pg_url:
        print("CHESS_TRAINER_DB_URL not set")
        return 1

    repo = CourseFeaturesRepository(pg_url)
    total = repo.count_games()
    print(f"PostgreSQL games (excl. stockfish): {total:,}\n")
    _print_band_table("Either-side ELO (legacy OR filter):", repo, exclusive=False)
    _print_band_table("Exclusive ELO (avg white/black, disjoint bands):", repo, exclusive=True)

    sqlite_path = COURSE_ROOT / "course_data.sqlite"
    if sqlite_path.exists():
        sqlite_repo = CourseFeaturesRepository(sqlite_path)
        games = sqlite_repo.load_games(columns=["game_id", "skill_group"])
        print(f"SQLite {sqlite_path.name}: {len(games):,} games")
        counts = games["skill_group"].value_counts()
        for name, _min, _max in BANDS:
            quota = COURSE_SKILL_GROUP_GAME_QUOTAS[name]
            got = int(counts.get(name, 0))
            print(f"  {name:<18} {got:>5,} / {quota:,}  ({got/quota:.0%})")
        print(f"  {'TOTAL':<18} {len(games):>5,} / {sum(COURSE_SKILL_GROUP_GAME_QUOTAS.values()):,}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
