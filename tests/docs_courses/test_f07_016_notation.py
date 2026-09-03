"""Tests for F07-016 — UCI/SAN conversion."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.notation import (
    parse_legal_move,
    pv_uci_to_san,
    roundtrip_uci,
    san_to_uci,
    uci_to_san,
)
from analysis.position_extractor import import_game_from_file


def test_opening_uci_to_san():
    fen = chess.Board().fen()
    assert uci_to_san(fen, "e2e4") == "e4"
    assert san_to_uci(fen, "e4") == "e2e4"
    assert roundtrip_uci(fen, "g1f3") == "g1f3"


def test_rejects_illegal_uci_and_san():
    fen = chess.Board().fen()
    with pytest.raises(ValueError, match="Illegal"):
        uci_to_san(fen, "e2e5")
    with pytest.raises(ValueError, match="Illegal"):
        san_to_uci(fen, "e5")
    with pytest.raises(ValueError, match="Illegal"):
        parse_legal_move(fen, "Qxh8")


def test_pv_conversion_and_illegal_pv():
    fen = chess.Board().fen()
    assert pv_uci_to_san(fen, ["e2e4", "e7e5", "g1f3"]) == ("e4", "e5", "Nf3")
    with pytest.raises(ValueError, match="Illegal PV"):
        pv_uci_to_san(fen, ["e2e4", "e2e4"])


def test_promotion_and_castling():
    promo_fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
    assert uci_to_san(promo_fen, "a7a8q") == "a8=Q+"
    assert san_to_uci(promo_fen, "a8=Q") == "a7a8q"
    castle_fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    assert uci_to_san(castle_fen, "e1g1") == "O-O"
    assert parse_legal_move(castle_fen, "O-O").uci() == "e1g1"


def test_scholar_game_all_plies_roundtrip():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    for ply in game.plies:
        assert uci_to_san(ply.fen_before, ply.uci) == ply.san
        assert san_to_uci(ply.fen_before, ply.san) == ply.uci
        assert roundtrip_uci(ply.fen_before, ply.uci) == ply.uci
        assert parse_legal_move(ply.fen_before, ply.san).uci() == ply.uci
