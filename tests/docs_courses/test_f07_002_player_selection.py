"""Tests for F07-002 — player selection (username or color)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.game_models import parse_player_color, select_analyzed_player
from analysis.position_extractor import import_game_from_file, import_game_from_pgn

WHITE_PGN = """[Event "F07-002 white"]
[White "cmess1315"]
[Black "opponent"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0
"""

BLACK_PGN = """[Event "F07-002 black"]
[White "opponent"]
[Black "cmess1315"]
[Result "0-1"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 0-1
"""

AMBIGUOUS_PGN = """[Event "F07-002 ambiguous"]
[White "Anonymous"]
[Black "Anonymous"]
[Result "*"]

1. e4 e5 *
"""


def test_select_player_from_white_pgn_file():
    path = COURSE_ROOT / "data" / "games" / "f07_002_white.pgn"
    game = import_game_from_file(path)
    selection = select_analyzed_player(game, username="cmess1315")
    assert selection.color == "white"
    assert [p.san for p in selection.plies] == ["e4", "Qh5", "Bc4", "Qxf7#"]


def test_select_player_from_black_pgn_file():
    path = COURSE_ROOT / "data" / "games" / "f07_002_black.pgn"
    game = import_game_from_file(path)
    selection = game.select_player(username="cmess1315")
    assert selection.color == "black"
    assert [p.san for p in selection.plies] == ["e5", "Nc6", "a6"]


def test_select_player_as_white_by_username():
    game = import_game_from_pgn(WHITE_PGN)
    selection = select_analyzed_player(game, username="cmess1315")

    assert selection.color == "white"
    assert selection.is_white
    assert [p.san for p in selection.plies] == ["e4", "Qh5", "Bc4", "Qxf7#"]
    assert all(p.side_to_move == "white" for p in selection.plies)
    assert len(selection.plies) == 4
    assert len(game.plies) == 7


def test_select_player_as_black_by_username():
    game = import_game_from_pgn(BLACK_PGN)
    selection = game.select_player(username="Cmess1315")

    assert selection.color == "black"
    assert not selection.is_white
    assert [p.san for p in selection.plies] == ["e5", "Nc6", "a6"]
    assert all(p.side_to_move == "black" for p in selection.plies)


def test_select_player_by_color_only():
    game = import_game_from_pgn(WHITE_PGN)
    as_black = select_analyzed_player(game, color="black")
    as_white = select_analyzed_player(game, color=1)

    assert as_black.username == "opponent"
    assert [p.san for p in as_black.plies] == ["e5", "Nc6", "Nf6"]
    assert as_white.username == "cmess1315"
    assert parse_player_color("B") == "black"


def test_username_and_color_must_agree():
    game = import_game_from_pgn(WHITE_PGN)
    with pytest.raises(ValueError, match="is White"):
        select_analyzed_player(game, username="cmess1315", color="black")


def test_unknown_username_raises():
    game = import_game_from_pgn(WHITE_PGN)
    with pytest.raises(ValueError, match="not in this game"):
        select_analyzed_player(game, username="nobody")


def test_ambiguous_username_requires_color():
    game = import_game_from_pgn(AMBIGUOUS_PGN)
    with pytest.raises(ValueError, match="both White and Black"):
        select_analyzed_player(game, username="Anonymous")

    as_white = select_analyzed_player(game, username="Anonymous", color="white")
    assert [p.san for p in as_white.plies] == ["e4"]


def test_missing_selector_raises():
    game = import_game_from_pgn(WHITE_PGN)
    with pytest.raises(ValueError, match="username and/or color"):
        select_analyzed_player(game)
