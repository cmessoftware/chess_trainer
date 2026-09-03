"""Tests for F07-035 — review pack JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import chess
from chess.engine import Cp, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.abstention import assess_diagnosis_abstention
from analysis.comparison import compare_played_to_candidates
from analysis.game_models import select_analyzed_player
from analysis.position_extractor import import_game_from_file
from analysis.review_pack import (
    FEATURE_ID,
    SCHEMA_VERSION,
    build_review_pack,
    default_review_pack_name,
    write_review_pack,
)


class ScriptedPlayed:
    def __init__(self, lines: list[dict], independent: dict[str, PovScore] | None = None):
        self.lines = lines
        self.independent = independent or {}
        self.id = {"name": "ScriptedPlayed"}

    def analyse(self, board: chess.Board, limit, multipv=1, root_moves=None):
        if root_moves:
            move = root_moves[0]
            return {"score": self.independent[move.uci()], "pv": [move]}
        count = max(1, int(multipv or 1))
        return self.lines[:count]


def _scholar_nf6_pack():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    player = select_analyzed_player(game, color="black")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    board = chess.Board(nf6.fen_before)
    g6 = chess.Move.from_uci("g7g6")
    others = [g6] + [m for m in board.legal_moves if m.uci() not in {nf6.uci, g6.uci()}]
    engine = ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(-20), chess.WHITE), "pv": [others[0]]},
            {"multipv": 2, "score": PovScore(Cp(-200), chess.WHITE), "pv": [others[1]]},
            {"multipv": 3, "score": PovScore(Cp(-220), chess.WHITE), "pv": [others[2]]},
        ],
        {nf6.uci: PovScore(Cp(900), chess.WHITE)},
    )
    vs = compare_played_to_candidates(
        nf6.fen_before, nf6.uci, engine=engine, depth=6, player_color="black"
    )
    pack = build_review_pack(
        game,
        nf6,
        player,
        vs,
        assess_diagnosis_abstention(vs),
        pgn_source="data/games/f07_002_white.pgn",
    )
    return game, nf6, pack


def test_review_pack_has_fen_pgn_candidates_and_evidence():
    game, nf6, pack = _scholar_nf6_pack()
    assert pack["schema_version"] == SCHEMA_VERSION
    assert pack["feature_id"] == FEATURE_ID
    assert pack["fen_before"] == nf6.fen_before
    assert pack["played_move"]["san"] == "Nf6"
    assert "Nf6" in pack["pgn"]
    assert pack["player_color"] == "BLACK"
    assert len(pack["candidates"]) == 3
    assert pack["candidates"][0]["san"] == "g6"
    assert pack["evidence"]["multipv"] == 3
    assert pack["evidence"]["inference_as_fact"] is False
    assert pack["actual_result"]["primary_error"] is None
    assert pack["human_label"]["confirmed"] is None
    assert pack["status"] == "PENDING_REVIEW"
    json.dumps(pack)


def test_write_review_pack_roundtrip(tmp_path: Path):
    _, nf6, pack = _scholar_nf6_pack()
    path = tmp_path / default_review_pack_name("f07_002_white", nf6.ply, nf6.san)
    written = write_review_pack(pack, path)
    loaded = json.loads(written.read_text(encoding="utf-8"))
    assert loaded["played_move"]["uci"] == nf6.uci
    assert loaded["actual_result"]["abstention"]["may_diagnose"] is True


def test_sample_game4_opening_pack_is_json():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "sample_game4.pgn")
    player = select_analyzed_player(game, username="cmess1315")
    ply = next(p for p in game.plies if p.san == "e4")
    engine = ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(40), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]},
            {"multipv": 2, "score": PovScore(Cp(32), chess.WHITE), "pv": [chess.Move.from_uci("d2d4")]},
            {"multipv": 3, "score": PovScore(Cp(28), chess.WHITE), "pv": [chess.Move.from_uci("g1f3")]},
        ]
    )
    vs = compare_played_to_candidates(
        ply.fen_before, ply.uci, engine=engine, depth=6, player_color="white"
    )
    pack = build_review_pack(game, ply, player, vs)
    assert pack["status"] == "UNKNOWN"
    assert pack["pgn"].startswith("[Event")
    json.dumps(pack)
