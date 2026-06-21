"""Tests for competition tactical pattern detection."""

from __future__ import annotations

import sys
from pathlib import Path

import chess

COMPETITION_ROOT = Path(__file__).resolve().parents[2] / "docs" / "competition"
if str(COMPETITION_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPETITION_ROOT))

from kaggle_package.tactical_patterns import classify_move_pattern, detect_pattern_from_row


def test_detect_check_from_fen():
    board = chess.Board("4k3/8/8/8/8/3Q4/8/8 w - - 0 1")
    move = chess.Move.from_uci("d3d8")
    assert classify_move_pattern(board, move) == "check"


def test_detect_pattern_from_row_normal():
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert detect_pattern_from_row(fen=fen, move_uci="e2e4", move_san="e4") == "normal"


def test_primary_tag_export_mapping():
    from kaggle_package.feature_export import attach_tactical_export_columns
    import pandas as pd

    frame = pd.DataFrame({"tags": ['["fork"]', None]})
    enriched = attach_tactical_export_columns(frame)
    assert enriched.loc[0, "tactical_tag"] == "fork"
    assert enriched.loc[0, "tag_fork"] == 1
    assert enriched.loc[1, "tactical_tag"] == "normal"
