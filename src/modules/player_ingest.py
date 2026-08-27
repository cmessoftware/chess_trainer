"""Shared ingest: download PGN → save games → generate features.

Used by import_chesscom_player.py and import_lichess_player.py.
"""

from __future__ import annotations

import importlib.util
import sys
import argparse
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import chess.pgn
import requests
from dotenv import load_dotenv

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv()

from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository
from modules.features_generator import generate_features_from_game
from modules.fetch_games import HEADERS as LICHESS_HEADERS
from modules.pgn_batch_loader import extract_features_from_game
from modules.pgn_utils import pgn_str_to_game

DATE_FORMAT = "%Y-%m-%d"
DATE_HELP = "Format YYYY-MM-DD (example: 2026-01-15). Same format on Chess.com and Lichess."


def parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT)
    except ValueError as exc:
        raise ValueError(
            f"Invalid date {value!r}. Use {DATE_FORMAT} (example: 2026-01-15)"
        ) from exc


def resolve_date_range(since: str | None, until: str | None) -> tuple[datetime | None, datetime]:
    until_dt = parse_iso_date(until) or datetime.combine(date.today(), datetime.min.time())
    since_dt = parse_iso_date(since)
    if since_dt and since_dt.date() > until_dt.date():
        raise ValueError(
            f"--since ({since}) cannot be after --until ({until_dt.date().isoformat()})"
        )
    return since_dt, until_dt


def add_date_range_arguments(
    parser: argparse.ArgumentParser, *, since_default: str | None = None
) -> None:
    parser.add_argument(
        "--since",
        default=since_default,
        metavar="YYYY-MM-DD",
        help=f"Import games from this date inclusive. {DATE_HELP}",
    )
    parser.add_argument(
        "--until",
        default=None,
        metavar="YYYY-MM-DD",
        help=f"Import games until this date inclusive (default: today). {DATE_HELP}",
    )
    parser.add_argument(
        "--after-date",
        dest="after_date",
        metavar="YYYY-MM-DD",
        help="Deprecated alias of --since. Same YYYY-MM-DD format.",
    )


def _end_of_day(day: datetime) -> datetime:
    return day.replace(hour=23, minute=59, second=59)


def _unix_in_range(end_time: int, since_dt: datetime | None, until_dt: datetime) -> bool:
    played = datetime.fromtimestamp(end_time)
    if since_dt and played < since_dt.replace(hour=0, minute=0, second=0):
        return False
    return played <= _end_of_day(until_dt)


def _archive_overlaps(year: int, month: int, since_dt: datetime | None, until_dt: datetime) -> bool:
    month_start = datetime(year, month, 1)
    month_end = datetime(year, month, monthrange(year, month)[1], 23, 59, 59)
    if month_start > _end_of_day(until_dt):
        return False
    if since_dt and month_end < since_dt.replace(hour=0, minute=0, second=0):
        return False
    return True


def _load_chess_com_downloader():
    path = SRC_DIR / "scripts" / "chess_com_downloader.py"
    spec = importlib.util.spec_from_file_location("chess_com_downloader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def download_chesscom_pgn(
    username: str,
    output_path: Path,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    months: int = 12,
) -> tuple[Path, int]:
    until_dt = until or datetime.combine(date.today(), datetime.min.time())
    downloader = _load_chess_com_downloader()
    api = downloader.ChessComAPI()
    profile = api.get_user_profile(username)
    if not profile:
        raise RuntimeError(f"Chess.com user not found: {username}")

    archives = api.get_user_archives(username)
    if not archives:
        raise RuntimeError(f"No Chess.com archives for {username}")

    selected: list[str] = []
    for archive_url in sorted(archives):
        parts = archive_url.split("/")
        year, month = int(parts[-2]), int(parts[-1])
        if _archive_overlaps(year, month, since, until_dt):
            selected.append(archive_url)
    if since is None:
        selected = selected[-months:]

    print(
        f"Date window: {(since.date().isoformat() if since else 'archive start')} "
        f"→ {until_dt.date().isoformat()} inclusive"
    )
    all_games: list[dict[str, Any]] = []
    for archive_url in selected:
        parts = archive_url.split("/")
        year, month = int(parts[-2]), int(parts[-1])
        month_games = api.download_monthly_games(username, year, month, None)
        all_games.extend(
            g
            for g in month_games
            if _unix_in_range(int(g.get("end_time") or 0), since, until_dt)
        )

    pgn_content = downloader.convert_chess_com_to_pgn(all_games, username)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pgn_content, encoding="utf-8")
    return output_path, len(all_games)


def download_lichess_pgn(
    username: str,
    output_path: Path,
    *,
    since: str,
    until: str,
    max_games: int | None = None,
) -> tuple[Path, int]:
    since_dt = parse_iso_date(since) or datetime(2015, 1, 1)
    until_dt = parse_iso_date(until) or datetime.combine(date.today(), datetime.min.time())
    since_ts = int(since_dt.replace(hour=0, minute=0, second=0).timestamp())
    until_ts = int(_end_of_day(until_dt).timestamp())
    url = f"https://lichess.org/api/games/user/{username}"
    params: dict[str, Any] = {
        "since": since_ts * 1000,
        "until": until_ts * 1000,
        "pgnInJson": True,
        "clocks": False,
        "evals": False,
        "opening": True,
    }
    if max_games:
        params["max"] = max_games

    headers = {**LICHESS_HEADERS, "Accept": "application/x-ndjson"}
    print(
        f"Downloading Lichess games for {username} "
        f"({since_dt.date().isoformat()} → {until_dt.date().isoformat()} inclusive)..."
    )
    response = requests.get(url, params=params, headers=headers, stream=True, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(
            f"Lichess HTTP {response.status_code}: {response.text[:200]}"
        )

    pgns: list[str] = []
    for line in response.iter_lines():
        if not line:
            continue
        try:
            payload = __import__("json").loads(line)
        except Exception:
            continue
        pgn = payload.get("pgn")
        if pgn:
            pgns.append(str(pgn).strip())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(pgns) + ("\n" if pgns else ""), encoding="utf-8")
    return output_path, len(pgns)


def import_pgn_file_to_db(
    pgn_path: Path,
    *,
    source: str,
    imported_by: str,
    max_games: int | None = None,
) -> tuple[list[str], int]:
    """Insert games using existing extract_features_from_game + GamesRepository (SHA256 ids)."""
    if not pgn_path.is_file():
        raise FileNotFoundError(pgn_path)

    repo = GamesRepository()
    imported_ids: list[str] = []
    skipped = 0

    with pgn_path.open(encoding="utf-8", errors="replace") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            pgn_string = str(game)
            game_data = extract_features_from_game(pgn_string)
            if not game_data or not game_data.get("game_id"):
                continue
            game_data["source"] = source
            game_data["source_filename"] = pgn_path.name
            game_data["imported_by"] = imported_by

            if repo.game_exists(game_data["game_id"]):
                skipped += 1
                continue

            repo.save_game(game_data)
            imported_ids.append(game_data["game_id"])
            if max_games and len(imported_ids) >= max_games:
                break

    repo.commit()
    return imported_ids, skipped


def generate_features_for_game_ids(
    game_ids: list[str],
    *,
    with_tactics: bool = False,
) -> tuple[int, int]:
    if not game_ids:
        return 0, 0

    games_repo = GamesRepository()
    features_repo = FeaturesRepository()
    processed_repo = ProcessedFeaturesRepository()
    ok = 0
    errors = 0

    for game_id in game_ids:
        try:
            existing = features_repo.get_by_game_id(game_id)
            if existing:
                print(f"Features already exist for {game_id[:12]}..., skip")
                ok += 1
                continue

            pgn_text = games_repo.get_pgn_text_by_id(game_id)
            game = pgn_str_to_game(pgn_text or "")
            if not game:
                print(f"Could not parse PGN for {game_id}")
                errors += 1
                continue

            rows = generate_features_from_game(game, game_id=game_id)
            if not rows:
                print(f"No features generated for {game_id}")
                errors += 1
                continue

            features_repo.save_many_features(rows)

            if with_tactics:
                try:
                    from modules.analyze_games_tactics import detect_tactics_from_game

                    tactics = detect_tactics_from_game(game, game_id)
                    if tactics:
                        features_repo.update_tactical_data(tactics)
                except Exception as tact_exc:
                    print(f"Tactics skipped for {game_id}: {tact_exc}")

            processed_repo.save_processed_hash(game_id)
            features_repo.session.commit()
            processed_repo.session.commit()
            ok += 1
            print(f"Features saved for {game_id[:12]}... ({len(rows)} rows)")
        except Exception as exc:
            errors += 1
            print(f"Feature error for {game_id}: {exc}")
            try:
                features_repo.session.rollback()
            except Exception:
                pass

    return ok, errors


@dataclass
class IngestReport:
    platform: str
    username: str
    pgn_path: str
    downloaded: int | None
    imported: int
    skipped_existing: int
    features_ok: int | None
    features_errors: int | None
    since: str | None
    until: str | None

    def print_report(self) -> None:
        print()
        print("=" * 52)
        print("INGEST REPORT")
        print("=" * 52)
        print(f"  Platform:              {self.platform}")
        print(f"  Username:              {self.username}")
        print(f"  Date window:           {self.since or '(open)'} → {self.until or 'today'} (inclusive)")
        print(f"  PGN file:              {self.pgn_path}")
        print(f"  Games downloaded:      {self.downloaded if self.downloaded is not None else 'n/a (skip-download)'}")
        print(f"  Games imported (new):  {self.imported}")
        print(f"  Games skipped (exist): {self.skipped_existing}")
        if self.features_ok is None:
            print("  Features generated:    skipped")
        else:
            print(f"  Features generated:    {self.features_ok} ok, {self.features_errors} errors")
        print("=" * 52)


def run_player_pipeline(
    *,
    platform: str,
    username: str,
    since: str | None,
    until: str | None,
    months: int = 12,
    max_games: int | None = None,
    output: Path | None = None,
    skip_download: bool = False,
    skip_features: bool = False,
    with_tactics: bool = False,
) -> IngestReport:
    source = "chess.com" if platform == "chess.com" else "lichess.org"
    since_dt, until_dt = resolve_date_range(since, until)
    pgn_path = output or default_output_path(source, username)
    downloaded: int | None = None

    if skip_download:
        if not pgn_path.is_file():
            raise FileNotFoundError(f"PGN not found: {pgn_path}")
        print(f"Using existing PGN: {pgn_path}")
    elif platform == "chess.com":
        pgn_path, downloaded = download_chesscom_pgn(
            username, pgn_path, since=since_dt, until=until_dt, months=months
        )
        print(f"Downloaded {downloaded} Chess.com games → {pgn_path}")
        if downloaded == 0:
            raise RuntimeError("No Chess.com games in the requested date window")
    else:
        pgn_path, downloaded = download_lichess_pgn(
            username,
            pgn_path,
            since=(since_dt.strftime(DATE_FORMAT) if since_dt else "2015-01-01"),
            until=until_dt.strftime(DATE_FORMAT),
            max_games=max_games,
        )
        print(f"Downloaded {downloaded} Lichess games → {pgn_path}")
        if downloaded == 0:
            raise RuntimeError("No Lichess games in the requested date window")

    imported_ids, skipped = import_pgn_file_to_db(
        pgn_path,
        source=source,
        imported_by=username,
        max_games=max_games,
    )

    features_ok: int | None = None
    features_errors: int | None = None
    if skip_features:
        print("Skipped feature generation")
    else:
        features_ok, features_errors = generate_features_for_game_ids(
            imported_ids, with_tactics=with_tactics
        )

    report = IngestReport(
        platform=source,
        username=username,
        pgn_path=str(pgn_path),
        downloaded=downloaded,
        imported=len(imported_ids),
        skipped_existing=skipped,
        features_ok=features_ok,
        features_errors=features_errors,
        since=since_dt.date().isoformat() if since_dt else None,
        until=until_dt.date().isoformat(),
    )
    report.print_report()
    return report


def default_output_path(platform: str, username: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = SRC_DIR.parent / "data" / "games" / platform / username.lower()
    return folder / f"{username.lower()}_{stamp}.pgn"
