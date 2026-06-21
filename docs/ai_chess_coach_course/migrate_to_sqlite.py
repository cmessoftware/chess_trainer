#!/usr/bin/env python3
"""
migrate_to_sqlite.py
====================
Portable course export utility.

This script uses the course SQLAlchemy data layer to copy the `games` and
`features` tables from PostgreSQL into a local SQLite file.

Default behaviour:
  export games matching the requested filters (no player filter unless --player is set).

Extended filters:
  --skill-group / --player-elo-min / --player-elo-max  ELO-band balanced export
  --source     optional legacy filter by games.source
  --player     optional filter by username
  --max-games  cap the export after filters (most recent games first)
  --merge      append/update into existing SQLite without wiping other exports
  --list-sources  print available source values and exit
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = COURSE_ROOT.parents[1]
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from dotenv import load_dotenv  # noqa: E402

from data_access.features_repository import (  # noqa: E402
    DEFAULT_SQLITE_PATH,
    CourseFeaturesRepository,
    export_course_slice,
)
from dataset.skill_groups import SKILL_GROUP_BY_NAME  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Export chess games and features from PostgreSQL to SQLite.",
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
        default=None,
        help=(
            "Player username to export. "
            "If omitted, all games matching the other filters are exported."
        ),
    )
    parser.add_argument(
        "--source",
        default=None,
        help='Filter games by source (e.g. "personal", "lichess", "chess.com", "elite").',
    )
    parser.add_argument(
        "--max-games",
        type=int,
        default=None,
        help="Maximum number of games to export after filters (most recent first).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_SQLITE_PATH),
        help=f"Path to the output SQLite file (default: {DEFAULT_SQLITE_PATH}).",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help=(
            "Merge into the existing SQLite file instead of replacing all rows. "
            "Use this to accumulate exports from multiple sources or runs."
        ),
    )
    parser.add_argument(
        "--skill-group",
        default=None,
        choices=sorted(SKILL_GROUP_BY_NAME),
        help=(
            "Course skill group label stamped on exported games (metadata). "
            "Use together with --player-elo-min/--player-elo-max."
        ),
    )
    parser.add_argument(
        "--player-elo-min",
        type=int,
        default=None,
        help="Minimum white/black ELO for game selection (inclusive).",
    )
    parser.add_argument(
        "--player-elo-max",
        type=int,
        default=None,
        help="Maximum white/black ELO for game selection (inclusive).",
    )
    parser.add_argument(
        "--either-side-elo",
        action="store_true",
        help=(
            "Legacy filter: include a game when either white_elo OR black_elo is in range. "
            "Default for --skill-group is exclusive band assignment via average ELO."
        ),
    )
    parser.add_argument(
        "--exclusive-elo-band",
        action="store_true",
        help="Assign each game to one band using average valid white/black ELO.",
    )
    parser.add_argument(
        "--export-chunk-size",
        type=int,
        default=400,
        help="Export games/features in batches to limit memory use (default: 400).",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help=(
            "Path to a .env file with CHESS_TRAINER_DB_URL. "
            f"Defaults to {REPO_ROOT / '.env'} when present."
        ),
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List distinct games.source values in PostgreSQL and exit.",
    )
    return parser.parse_args(argv)


def resolve_player_filter(
    player: str | None,
    *,
    source: str | None = None,
    skill_group: str | None = None,
    player_elo_min: int | None = None,
    player_elo_max: int | None = None,
) -> str | None:
    if player:
        return player
    if source is not None or skill_group is not None:
        return None
    if player_elo_min is not None or player_elo_max is not None:
        return None
    return None


def load_course_env(env_file: str | None = None) -> Path | None:
    candidates = []
    if env_file:
        candidates.append(Path(env_file))
    candidates.extend([REPO_ROOT / ".env", COURSE_ROOT / ".env"])

    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate.resolve()
    return None


def main(argv=None) -> int:
    args = parse_args(argv)
    loaded_env = load_course_env(args.env_file)
    source_db_url = args.pg_url or os.environ.get("CHESS_TRAINER_DB_URL")
    if not source_db_url:
        env_hint = f" ({loaded_env})" if loaded_env else f" (looked for {REPO_ROOT / '.env'})"
        print(
            "[ERROR] No PostgreSQL URL found.\n"
            "    Set CHESS_TRAINER_DB_URL in your .env, pass --pg-url, or use --env-file."
            f"\n    Env file checked{env_hint}.",
            file=sys.stderr,
        )
        return 1

    if args.list_sources:
        try:
            sources = CourseFeaturesRepository(source_db_url).list_sources()
        except Exception as exc:
            print(f"[ERROR] Could not list sources: {exc}", file=sys.stderr)
            return 1

        if not sources:
            print("No sources found in games.source.")
            return 0

        print("Available sources:")
        for value in sources:
            print(f"  - {value}")
        return 0

    skill_group = args.skill_group
    player_elo_min = args.player_elo_min
    player_elo_max = args.player_elo_max
    if skill_group:
        group = SKILL_GROUP_BY_NAME[skill_group]
        player_elo_min = group.min_elo if player_elo_min is None else player_elo_min
        player_elo_max = group.max_elo if player_elo_max is None else player_elo_max

    player = resolve_player_filter(
        args.player,
        source=args.source,
        skill_group=skill_group,
        player_elo_min=player_elo_min,
        player_elo_max=player_elo_max,
    )

    if args.either_side_elo:
        exclusive_elo_band = False
    elif args.exclusive_elo_band:
        exclusive_elo_band = True
    else:
        exclusive_elo_band = skill_group is not None

    try:
        result = export_course_slice(
            source_db_url=source_db_url,
            output_db_url=args.output,
            player=player,
            source=args.source,
            max_games=args.max_games,
            player_elo_min=player_elo_min,
            player_elo_max=player_elo_max,
            skill_group=skill_group,
            exclusive_elo_band=exclusive_elo_band,
            merge=args.merge,
            export_chunk_size=args.export_chunk_size,
        )
    except Exception as exc:
        print(f"[ERROR] Migration failed: {exc}", file=sys.stderr)
        return 1

    filters = []
    if player:
        filters.append(f"player={player!r}")
    if args.source:
        filters.append(f"source={args.source!r}")
    if args.max_games is not None:
        filters.append(f"max_games={args.max_games}")
    if skill_group:
        filters.append(f"skill_group={skill_group!r}")
    if exclusive_elo_band:
        filters.append("exclusive_elo_band=True")
    elif skill_group:
        filters.append("either_side_elo=True")
    if player_elo_min is not None or player_elo_max is not None:
        filters.append(f"elo_range={player_elo_min}-{player_elo_max}")
    if args.merge:
        filters.append("merge=True")
    filter_summary = ", ".join(filters) if filters else "no filters"
    mode_label = "merged into" if args.merge else "replaced in"

    print(
        "\n[OK] Migration complete!\n"
        f"    mode     : {mode_label} {Path(result['sqlite_path'] or args.output).resolve()}\n"
        f"    filters  : {filter_summary}\n"
        f"    exported : {result['games_exported']} games, {result['features_exported']} features\n"
        f"    totals   : {result['games_total']} games, {result['features_total']} features"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
