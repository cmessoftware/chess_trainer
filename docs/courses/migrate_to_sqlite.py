#!/usr/bin/env python3
"""
migrate_to_sqlite.py
====================
ONE-TIME migration utility — not part of the regular ChessTrainer workflow.
The main application continues to use PostgreSQL.  This script is only needed
to create a portable copy of the course data so that the course notebooks can
run without a running Docker/PostgreSQL service.

Exports the games and features of player *cmess1315*
from the ChessTrainer PostgreSQL database into a portable SQLite file.

The resulting SQLite database is stored alongside this script as
``course_data.sqlite`` (configurable via --output).

Usage
-----
    # Minimal (uses CHESS_TRAINER_DB_URL environment variable)
    python migrate_to_sqlite.py

    # Explicit PostgreSQL URL
    python migrate_to_sqlite.py --pg-url "postgresql://user:pass@host:5432/chess_trainer_db"

    # Custom output path
    python migrate_to_sqlite.py --output /tmp/my_course.sqlite

    # Different player
    python migrate_to_sqlite.py --player myusername

Required environment variable (if --pg-url is not supplied)
-------------------------------------------------------------
    CHESS_TRAINER_DB_URL   Full PostgreSQL connection URL, e.g.
                           postgresql://chess:chess_pass@localhost:5432/chess_trainer_db

The script is **idempotent**: running it again replaces the data without
leaving stale rows (it drops and recreates both tables).
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_PLAYER = "cmess1315"
DEFAULT_OUTPUT = Path(__file__).parent / "course_data.sqlite"


# ---------------------------------------------------------------------------
# PostgreSQL helpers
# ---------------------------------------------------------------------------

def _pg_connect(pg_url: str):
    """Return a psycopg2 connection.  Raises ImportError if psycopg2 is absent."""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError as exc:
        raise ImportError(
            "psycopg2 is required to run this migration.  "
            "Install it with:  pip install psycopg2-binary"
        ) from exc
    return psycopg2.connect(pg_url)


def fetch_games(pg_conn, player: str) -> list[dict]:
    """Return all rows from `games` where the player appears as white or black."""
    import psycopg2.extras
    query = """
        SELECT
            game_id, pgn, source,
            white_player, black_player,
            white_elo, black_elo,
            result, time_control, opening, eco,
            date_played, created_at,
            import_batch_id, source_filename, imported_by
        FROM games
        WHERE white_player = %s
           OR black_player = %s
    """
    with pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, (player, player))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_features(pg_conn, game_ids: list[str]) -> list[dict]:
    """Return all features rows for the given list of game IDs."""
    if not game_ids:
        return []
    import psycopg2.extras
    placeholders = ",".join(["%s"] * len(game_ids))
    query = f"""
        SELECT
            game_id, move_number, fen, elo, opening,
            material_total, num_pieces, king_safety, center_control,
            has_castling_rights, is_pawn_endgame,
            score_cp, mate_in, depth_score_diff,
            error_label, tags
        FROM features
        WHERE game_id IN ({placeholders})
    """
    with pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, game_ids)
        rows = cur.fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------

def _create_schema(sqlite_conn: sqlite3.Connection) -> None:
    """Create (or recreate) the games and features tables."""
    cur = sqlite_conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS features;
        DROP TABLE IF EXISTS games;

        CREATE TABLE games (
            game_id          TEXT PRIMARY KEY,
            pgn              TEXT,
            source           TEXT,
            white_player     TEXT,
            black_player     TEXT,
            white_elo        TEXT,
            black_elo        TEXT,
            result           TEXT,
            time_control     TEXT,
            opening          TEXT,
            eco              TEXT,
            date_played      TEXT,
            created_at       TEXT,
            import_batch_id  TEXT,
            source_filename  TEXT,
            imported_by      TEXT
        );

        CREATE TABLE features (
            game_id              TEXT,
            move_number          INTEGER,
            fen                  TEXT,
            elo                  INTEGER,
            opening              TEXT,
            material_total       REAL,
            num_pieces           INTEGER,
            king_safety          REAL,
            center_control       REAL,
            has_castling_rights  INTEGER,
            is_pawn_endgame      INTEGER,
            score_cp             INTEGER,
            mate_in              INTEGER,
            depth_score_diff     REAL,
            error_label          TEXT,
            tags                 TEXT,
            PRIMARY KEY (game_id, move_number)
        );
    """)
    sqlite_conn.commit()


def _insert_games(sqlite_conn: sqlite3.Connection, rows: list[dict]) -> None:
    cur = sqlite_conn.cursor()
    cur.executemany(
        """
        INSERT OR REPLACE INTO games
            (game_id, pgn, source, white_player, black_player,
             white_elo, black_elo, result, time_control, opening, eco,
             date_played, created_at, import_batch_id, source_filename, imported_by)
        VALUES
            (:game_id, :pgn, :source, :white_player, :black_player,
             :white_elo, :black_elo, :result, :time_control, :opening, :eco,
             :date_played, :created_at, :import_batch_id, :source_filename, :imported_by)
        """,
        rows,
    )
    sqlite_conn.commit()


def _insert_features(sqlite_conn: sqlite3.Connection, rows: list[dict]) -> None:
    import json
    cur = sqlite_conn.cursor()
    normalised = []
    for r in rows:
        row = dict(r)
        # Serialise JSONB / dict tags to text
        if isinstance(row.get("tags"), dict):
            row["tags"] = json.dumps(row["tags"])
        # Coerce booleans to int for SQLite
        for col in ("has_castling_rights", "is_pawn_endgame"):
            if isinstance(row.get(col), bool):
                row[col] = int(row[col])
        normalised.append(row)

    cur.executemany(
        """
        INSERT OR REPLACE INTO features
            (game_id, move_number, fen, elo, opening,
             material_total, num_pieces, king_safety, center_control,
             has_castling_rights, is_pawn_endgame,
             score_cp, mate_in, depth_score_diff,
             error_label, tags)
        VALUES
            (:game_id, :move_number, :fen, :elo, :opening,
             :material_total, :num_pieces, :king_safety, :center_control,
             :has_castling_rights, :is_pawn_endgame,
             :score_cp, :mate_in, :depth_score_diff,
             :error_label, :tags)
        """,
        normalised,
    )
    sqlite_conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Export chess games and features for a player from PostgreSQL to SQLite.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--pg-url",
        default=None,
        help=(
            "Full PostgreSQL connection URL.  "
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
        default=str(DEFAULT_OUTPUT),
        help=f"Path to the output SQLite file (default: {DEFAULT_OUTPUT}).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    # Resolve PostgreSQL URL
    pg_url = args.pg_url or os.environ.get("CHESS_TRAINER_DB_URL")
    if not pg_url:
        print(
            "❌  No PostgreSQL URL found.\n"
            "    Set the CHESS_TRAINER_DB_URL environment variable or pass --pg-url.",
            file=sys.stderr,
        )
        return 1

    output_path = Path(args.output)
    player = args.player

    print(f"🔌  Connecting to PostgreSQL …")
    try:
        pg_conn = _pg_connect(pg_url)
    except Exception as exc:
        print(f"❌  Could not connect to PostgreSQL: {exc}", file=sys.stderr)
        return 1

    print(f"📤  Fetching games for player '{player}' …")
    games = fetch_games(pg_conn, player)
    print(f"    Found {len(games)} game(s).")

    game_ids = [g["game_id"] for g in games]
    print(f"📤  Fetching features for {len(game_ids)} game(s) …")
    features = fetch_features(pg_conn, game_ids)
    print(f"    Found {len(features)} feature row(s).")

    pg_conn.close()

    print(f"💾  Writing SQLite database → {output_path} …")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_conn = sqlite3.connect(str(output_path))

    _create_schema(sqlite_conn)
    _insert_games(sqlite_conn, games)
    _insert_features(sqlite_conn, features)

    # Quick verification
    cur = sqlite_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM games")
    n_games = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM features")
    n_features = cur.fetchone()[0]
    sqlite_conn.close()

    print(
        f"\n✅  Migration complete!\n"
        f"    games    : {n_games} rows\n"
        f"    features : {n_features} rows\n"
        f"    Output   : {output_path.resolve()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
