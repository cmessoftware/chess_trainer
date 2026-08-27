#!/usr/bin/env python3
"""Download a player's games from Chess.com or Lichess, import to DB, generate features.

Example:
    python src/scripts/player_ingest.py cmess1315 --platform chess.com --since 2026-01-01
    python src/scripts/import_chesscom_player.py cmess1315 --since 2026-01-01
    python src/scripts/import_lichess_player.py cmess1315 --since 2026-01-01
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from modules.player_ingest import add_date_range_arguments, run_player_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a user's games from Chess.com or Lichess into PostgreSQL"
    )
    parser.add_argument("username", help="Platform username (not email)")
    parser.add_argument(
        "--platform",
        choices=["chess.com", "lichess.org", "lichess"],
        default="chess.com",
        help="Source platform (default: chess.com)",
    )
    add_date_range_arguments(parser)
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Chess.com only: if --since is omitted, last N monthly archives",
    )
    parser.add_argument("--max-games", type=int, help="Cap games downloaded/inserted")
    parser.add_argument("--output", type=Path, help="PGN output file")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-features", action="store_true")
    parser.add_argument("--with-tactics", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not os.environ.get("CHESS_TRAINER_DB_URL"):
        print("CHESS_TRAINER_DB_URL is not set")
        return 1

    platform = "lichess.org" if args.platform == "lichess" else args.platform
    try:
        report = run_player_pipeline(
            platform=platform,
            username=args.username,
            since=args.since or args.after_date,
            until=args.until,
            months=args.months,
            max_games=args.max_games,
            output=args.output,
            skip_download=args.skip_download,
            skip_features=args.skip_features,
            with_tactics=args.with_tactics,
        )
    except Exception as exc:
        print(f"Ingest failed: {exc}")
        return 1

    return 0 if (report.imported > 0 or report.skipped_existing > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
