"""F07-001 — Load normalized games from PGN or the course database."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import TYPE_CHECKING, Any

import chess
import chess.pgn

from analysis.game_models import NormalizedGame, PlyRecord

if TYPE_CHECKING:
    from data_access.features_repository import CourseFeaturesRepository

PLAYER_COLOR_WHITE = 1
PLAYER_COLOR_BLACK = 0


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
) -> NormalizedGame:
    """Build a normalized game from ``games`` + ``features`` (F07-001 DB path)."""
    if not game_id or not str(game_id).strip():
        raise ValueError("game_id is required")

    if repo is None:
        from data_access.features_repository import CourseFeaturesRepository

        repo = CourseFeaturesRepository()

    games = repo.load_games(columns=["game_id", "pgn", "white_player", "black_player", "result", "source"])
    game_rows = games[games["game_id"] == game_id]
    if game_rows.empty:
        raise LookupError(f"Game not found: {game_id}")

    game_row = game_rows.iloc[0]
    pgn_text = str(game_row.get("pgn") or "").strip()
    if not pgn_text:
        raise ValueError(f"Game {game_id} has no PGN stored")

    features = repo.load_features(
        game_ids=[game_id],
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
        normalized = import_game_from_pgn(pgn_text, game_id=game_id)
        normalized.source = "database"
        normalized.metadata["db_fallback"] = True
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
                f"Illegal stored move {row['move_uci']} at ply {ply_index} for game {game_id}"
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
        game_id=game_id,
        headers=headers,
        plies=plies,
        result=str(headers.get("Result") or game_row.get("result") or "*"),
        pgn=pgn_text,
        source="database",
        metadata={
            "db_source": game_row.get("source"),
            "feature_rows": len(plies),
        },
    )
