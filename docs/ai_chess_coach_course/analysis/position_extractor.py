"""F07-001 — Load normalized games from PGN or the course database."""

from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import chess
import chess.pgn

from analysis.game_models import NormalizedGame, PlyRecord

if TYPE_CHECKING:
    from data_access.features_repository import CourseFeaturesRepository

PLAYER_COLOR_WHITE = 1
PLAYER_COLOR_BLACK = 0
_GAME_LOOKUP_COLUMNS = [
    "game_id",
    "pgn",
    "white_player",
    "black_player",
    "result",
    "source",
]


def _normalize_game_id(game_id: str) -> str:
    return str(game_id).strip().strip("\"'")


def _load_repo_dotenv() -> None:
    start = Path(__file__).resolve()
    try:
        from mm_lab_imports import load_repo_dotenv

        load_repo_dotenv(start, override=False)
        return
    except ImportError:
        pass
    for folder in [start.parent, *start.parents]:
        env_path = folder / ".env"
        if env_path.is_file() and (folder / "src" / "db" / "database.py").is_file():
            from dotenv import load_dotenv

            load_dotenv(env_path, override=False)
            return


def _redact_db_url(db_url: str) -> str:
    try:
        from sqlalchemy.engine import make_url

        parsed = make_url(db_url)
        host = parsed.host or ""
        db = parsed.database or ""
        return f"{parsed.get_backend_name()}://{host}/{db}"
    except Exception:
        return db_url.split("@")[-1] if "@" in db_url else db_url


def _iter_game_lookup_repos(
    repo: CourseFeaturesRepository | None,
    db_url: str | None,
):
    from data_access.features_repository import CourseFeaturesRepository, resolve_course_db_url

    if repo is not None:
        yield repo
        return

    _load_repo_dotenv()
    seen: set[str] = set()
    urls: list[str] = []
    if db_url:
        urls.append(str(db_url))
    else:
        urls.append(resolve_course_db_url())
        trainer = os.environ.get("CHESS_TRAINER_DB_URL")
        if trainer:
            urls.append(trainer)

    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        yield CourseFeaturesRepository(url)


def _compute_game_id(game: chess.pgn.Game) -> str:
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    pgn_str = game.accept(exporter)
    return hashlib.sha256(pgn_str.encode("utf-8")).hexdigest()


def _initial_board(game: chess.pgn.Game) -> chess.Board:
    setup = game.headers.get("SetUp", "0")
    fen = game.headers.get("FEN")
    if setup == "1" and fen:
        return chess.Board(fen)
    return chess.Board()


def _side_label(color: chess.Color) -> str:
    return "white" if color == chess.WHITE else "black"


def _build_plies_from_board_walk(game: chess.pgn.Game) -> tuple[list[PlyRecord], str]:
    board = _initial_board(game)
    initial_fen = board.fen()
    plies: list[PlyRecord] = []

    for ply_index, move in enumerate(game.mainline_moves()):
        if not board.is_legal(move):
            raise ValueError(f"Illegal move {move.uci()} at ply {ply_index} ({board.fen()})")

        fen_before = board.fen()
        side = _side_label(board.turn)
        move_number = board.fullmove_number
        san = board.san(move)
        uci = move.uci()
        board.push(move)

        plies.append(
            PlyRecord(
                ply=ply_index,
                move_number=move_number,
                san=san,
                uci=uci,
                fen_before=fen_before,
                fen_after=board.fen(),
                side_to_move=side,
            )
        )

    return plies, initial_fen


def import_game_from_pgn(
    pgn_text: str,
    *,
    game_id: str | None = None,
) -> NormalizedGame:
    """Parse PGN text into a normalized mainline game (AC-01)."""
    text = (pgn_text or "").strip()
    if not text:
        raise ValueError("PGN text is empty")

    game = chess.pgn.read_game(io.StringIO(text))
    if game is None:
        raise ValueError("Could not parse PGN")

    plies, initial_fen = _build_plies_from_board_walk(game)
    headers = dict(game.headers)
    resolved_id = game_id or _compute_game_id(game)

    return NormalizedGame(
        game_id=resolved_id,
        headers=headers,
        plies=plies,
        result=headers.get("Result", "*"),
        pgn=text,
        source="pgn",
        metadata={"initial_fen": initial_fen},
    )


def import_game_from_file(path: str | Path) -> NormalizedGame:
    """Load the first game from a PGN file."""
    pgn_path = Path(path)
    if not pgn_path.is_file():
        raise FileNotFoundError(f"PGN file not found: {pgn_path}")
    return import_game_from_pgn(pgn_path.read_text(encoding="utf-8", errors="replace"))



def _parse_score_diff(value: Any) -> float | None:
    if value is None:
        return None
    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except ImportError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_game_from_db(
    game_id: str,
    repo: CourseFeaturesRepository | None = None,
    *,
    db_url: str | None = None,
) -> NormalizedGame:
    """Build a normalized game from ``games`` + ``features``.

    Looks up by primary key (not a full table scan). If ``repo`` is omitted,
    tries the course DB (SQLite / ``CHESS_COURSE_DB_URL``) and then
    ``CHESS_TRAINER_DB_URL`` (PostgreSQL ingest).
    """
    gid = _normalize_game_id(game_id)
    if not gid:
        raise ValueError("game_id is required")

    tried: list[str] = []
    last_repo = None
    game_row = None
    for candidate in _iter_game_lookup_repos(repo, db_url):
        last_repo = candidate
        tried.append(_redact_db_url(candidate.db_url))
        game_row = candidate.get_game(gid, columns=_GAME_LOOKUP_COLUMNS)
        if game_row is not None:
            break

    if game_row is None or last_repo is None:
        raise LookupError(
            f"Game not found: {gid}. Looked in: {tried or ['(no database)']}. "
            "IDs copied from PostgreSQL are not in course_data.sqlite unless you "
            "export them. load_game_from_db now also checks CHESS_TRAINER_DB_URL "
            "from the repo .env — restart the kernel and retry."
        )

    pgn_text = str(game_row.get("pgn") or "").strip()
    if not pgn_text:
        raise ValueError(f"Game {gid} has no PGN stored")

    features = last_repo.load_features(
        game_ids=[gid],
        columns=[
            "game_id",
            "move_number",
            "player_color",
            "fen",
            "move_san",
            "move_uci",
            "score_diff",
            "move_number_global",
        ],
    )

    move_rows = features[
        (features["move_number"] > 0)
        & features["fen"].notna()
        & features["move_uci"].notna()
    ].copy()

    if move_rows.empty:
        normalized = import_game_from_pgn(pgn_text, game_id=gid)
        normalized.source = "database"
        normalized.metadata["db_fallback"] = True
        normalized.metadata["db_url"] = _redact_db_url(last_repo.db_url)
        return normalized

    move_rows = move_rows.sort_values(
        by=["move_number", "player_color"],
        ascending=[True, False],
    ).reset_index(drop=True)

    plies: list[PlyRecord] = []
    board = chess.Board()
    for _, row in move_rows.iterrows():
        ply_index = len(plies)
        fen_before = str(row["fen"])
        if board.fen() != fen_before:
            board.set_fen(fen_before)

        move = chess.Move.from_uci(str(row["move_uci"]))
        if not board.is_legal(move):
            raise ValueError(
                f"Illegal stored move {row['move_uci']} at ply {ply_index} for game {gid}"
            )

        board.push(move)
        plies.append(
            PlyRecord(
                ply=ply_index,
                move_number=int(row["move_number"]),
                san=str(row["move_san"]),
                uci=str(row["move_uci"]),
                fen_before=fen_before,
                fen_after=board.fen(),
                side_to_move=_side_label(chess.WHITE if int(row["player_color"]) == PLAYER_COLOR_WHITE else chess.BLACK),
                score_diff=_parse_score_diff(row.get("score_diff")),
            )
        )

    parsed = chess.pgn.read_game(io.StringIO(pgn_text))
    headers = dict(parsed.headers) if parsed is not None else {}
    if not headers.get("White") and game_row.get("white_player"):
        headers["White"] = str(game_row["white_player"])
    if not headers.get("Black") and game_row.get("black_player"):
        headers["Black"] = str(game_row["black_player"])
    if not headers.get("Result") and game_row.get("result"):
        headers["Result"] = str(game_row["result"])

    return NormalizedGame(
        game_id=gid,
        headers=headers,
        plies=plies,
        result=str(headers.get("Result") or game_row.get("result") or "*"),
        pgn=pgn_text,
        source="database",
        metadata={
            "db_source": game_row.get("source"),
            "feature_rows": len(plies),
            "db_url": _redact_db_url(last_repo.db_url),
        },
    )
