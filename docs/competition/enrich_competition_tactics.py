#!/usr/bin/env python3
"""Add tactical motif tags to competition games in course SQLite (no engine)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COMPETITION_ROOT = Path(__file__).resolve().parent
if str(COMPETITION_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPETITION_ROOT))

from kaggle_package.config import DEFAULT_SQLITE_PATH  # noqa: E402
from kaggle_package.tactical_enrichment import enrich_tactical_tags  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich competition games with board-pattern tactical tags (pin, fork, check, …)."
    )
    parser.add_argument(
        "--db-url",
        default=str(DEFAULT_SQLITE_PATH),
        help=f"Course SQLite path (default: {DEFAULT_SQLITE_PATH})",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Re-process all competition games (ignore checkpoint).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = enrich_tactical_tags(args.db_url, resume=not args.no_resume)

    print(f"Competition games: {len(result.game_ids):,}")
    print(f"Feature rows updated: {result.rows_updated:,}")
    print(f"Checkpoint: {result.checkpoint_path.resolve()}")
    print("\nTag distribution:")
    for tag, count in result.tag_distribution.items():
        print(f"  {tag:20s} {count:>8,}")

    print("\nNext: python docs/competition/export_competition_dataset.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
