"""Tests for F07-001 — game import (PGN and course database)."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.position_extractor import (
    import_game_from_file,
    import_game_from_pgn,
    load_game_from_db,
)
from data_access.features_repository import CourseFeaturesRepository, DEFAULT_SQLITE_PATH

SAMPLE_PGN = """[Event "ChessInsight mental model lab"]
[Site "Chess.com rapid"]
[Date "2026.01.01"]
[White "cmess1315"]
[Black "opponent"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0
"""


def test_import_game_from_pgn_reconstructs_all_plies():
    game = import_game_from_pgn(SAMPLE_PGN)
    assert game.white_player == "cmess1315"
    assert game.black_player == "opponent"
    assert game.result == "1-0"
    assert len(game.plies) == 7
    assert game.plies[0].san == "e4"
    assert game.plies[-1].san == "Qxf7#"


def test_import_game_fens_are_legal_and_chained():
    game = import_game_from_pgn(SAMPLE_PGN)
    board = chess.Board(game.metadata["initial_fen"])

    for record in game.plies:
        assert board.fen() == record.fen_before
        move = chess.Move.from_uci(record.uci)
        assert board.is_legal(move)
        board.push(move)
        assert board.fen() == record.fen_after


def test_import_game_from_sample_file():
    sample_path = COURSE_ROOT / "data" / "games" / "sample_game.pgn"
    if not sample_path.is_file():
        pytest.skip("sample_game.pgn not present")
    game = import_game_from_file(sample_path)
    assert len(game.plies) == 7
    assert game.source == "pgn"


def test_empty_pgn_raises():
    with pytest.raises(ValueError, match="empty"):
        import_game_from_pgn("")


@pytest.mark.skipif(not DEFAULT_SQLITE_PATH.is_file(), reason="course_data.sqlite missing")
def test_load_game_from_db_matches_pgn_import():
    repo = CourseFeaturesRepository()
    game_ids = repo.list_game_ids()
    if not game_ids:
        pytest.skip("no games in course database")

    game_id = game_ids[0]
    from_db = load_game_from_db(game_id, repo=repo)
    from_pgn = import_game_from_pgn(from_db.pgn, game_id=game_id)

    assert from_db.source == "database"
    assert from_db.game_id == game_id
    assert len(from_db.plies) == len(from_pgn.plies)
    assert from_db.plies[0].uci == from_pgn.plies[0].uci
    assert from_db.plies[-1].fen_after == from_pgn.plies[-1].fen_after


@pytest.mark.skipif(not DEFAULT_SQLITE_PATH.is_file(), reason="course_data.sqlite missing")
def test_load_game_from_db_has_metadata_and_fens():
    repo = CourseFeaturesRepository()
    games = repo.load_games(limit=1)
    if games.empty:
        pytest.skip("no games in course database")

    game_id = str(games.iloc[0]["game_id"])
    normalized = load_game_from_db(game_id, repo=repo)

    assert normalized.pgn
    assert normalized.plies
    assert all(p.fen_before and p.uci for p in normalized.plies)
