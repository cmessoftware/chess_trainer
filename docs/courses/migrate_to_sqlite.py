#!/usr/bin/env python3
"""
migrate_to_sqlite.py
====================
Portable course export utility.

This script uses the course SQLAlchemy data layer to copy the `games` and
`features` tables for a single player from PostgreSQL into a local SQLite file.
The resulting SQLite database is the default runtime for the course notebooks.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import (  # noqa: E402
    DEFAULT_PLAYER,
    DEFAULT_SQLITE_PATH,
    export_course_slice,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Export chess games and features for a player from PostgreSQL to SQLite.",
    )
    parser.add_argument(
        "--pg-url",
        default=None,
        help=(
            "Full PostgreSQL connection URL. "
            "Defaults to the CHESS_TRAINER_DB_URL environment variable."
        ),
    )
    parser.add_argument(
        "--player",
        default=DEFAULT_PLAYER,
        help=f"Player username to export (default: {DEFAULT_PLAYER}).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_SQLITE_PATH),
        help=f"Path to the output SQLite file (default: {DEFAULT_SQLITE_PATH}).",
    )
    return parser.parse_args(argv)



def main(argv=None) -> int:
    args = parse_args(argv)
    source_db_url = args.pg_url or os.environ.get("CHESS_TRAINER_DB_URL")
    if not source_db_url:
        print(
            "❌  No PostgreSQL URL found.\n"
            "    Set the CHESS_TRAINER_DB_URL environment variable or pass --pg-url.",
            file=sys.stderr,
        )
        return 1

    try:
        result = export_course_slice(
            source_db_url=source_db_url,
            output_db_url=args.output,
            player=args.player,
        )
    except Exception as exc:
        print(f"❌  Migration failed: {exc}", file=sys.stderr)
        return 1

    print(
        "\n✅  Migration complete!\n"
        f"    games    : {result['games']} rows\n"
        f"    features : {result['features']} rows\n"
        f"    Output   : {Path(result['sqlite_path'] or args.output).resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
