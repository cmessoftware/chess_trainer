"""Tests for complete-game coaching analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.game_analysis import (
    collect_player_game_frames,
    filter_player_moves,
    select_player_game_ids,
    summarize_game,
)


def _toy_game_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "game_id": ["g1"] * 4 + ["g2"] * 4,
            "move_number": [1, 1, 2, 2, 1, 1, 2, 2],
            "player_color": [1, 0, 1, 0, 1, 0, 1, 0],
            "white_player": ["cmess1315"] * 8,
            "black_player": ["rival_a"] * 4 + ["rival_b"] * 4,
            "player_elo": [1500, 1400, 1500, 1400] * 2,
            "error_label": ["good", "good", "mistake", "good"] * 2,
            "result": ["1-0"] * 8,
            "opening_French Defense": [1, 0, 1, 0, 1, 0, 1, 0],
        }
    )


def test_filter_player_moves_keeps_white_moves_only():
    game_rows = _toy_game_df()[_toy_game_df()["game_id"] == "g1"]
    color_index = game_rows[["game_id", "move_number", "player_color"]]
    player_moves = filter_player_moves(
        game_rows,
        player_name="cmess1315",
        player_color_index=color_index,
    )
    assert len(player_moves) == 2
    assert set(player_moves["move_number"]) == {1, 2}
    assert set(player_moves["player_color"]) == {1}


def test_filter_player_moves_does_not_swap_opponent_san():
    game_rows = pd.DataFrame(
        {
            "game_id": ["g1"] * 4,
            "move_number": [21, 21, 29, 29],
            "player_color": [1, 0, 1, 0],
            "move_san": ["c4", "Rxe5", "Rxc5", "Rdd2"],
            "white_player": ["cmess1315"] * 4,
            "black_player": ["rival"] * 4,
            "error_label": ["mistake", "good", "blunder", "good"],
        }
    )
    player_moves = filter_player_moves(
        game_rows,
        player_name="cmess1315",
        player_color_index=game_rows[["game_id", "move_number", "player_color"]],
    )
    lookup = dict(zip(player_moves["move_number"], player_moves["move_san"]))
    assert lookup[21] == "c4"
    assert lookup[29] == "Rxc5"


def test_select_player_game_ids():
    frame = _toy_game_df()
    selected = select_player_game_ids(frame, player_name="cmess1315", n_games=1, random_state=42)
    assert len(selected) == 1
    assert selected[0] in {"g1", "g2"}


def test_summarize_game_includes_identity_fields():
    frame = _toy_game_df()
    summary = summarize_game(
        frame[frame["game_id"] == "g1"],
        player_name="cmess1315",
        player_color_index=frame[["game_id", "move_number", "player_color"]],
    )
    assert summary["game_id"] == "g1"
    assert summary["opponent"] == "rival_a"
    assert summary["player_moves_analyzed"] == 2
    assert "error_breakdown" in summary


def test_collect_player_game_frames_across_games():
    frame = _toy_game_df()
    combined, summaries = collect_player_game_frames(
        frame,
        ["g1", "g2"],
        player_name="cmess1315",
        player_color_index=frame[["game_id", "move_number", "player_color"]],
    )
    assert len(combined) == 4
    assert len(summaries) == 2
