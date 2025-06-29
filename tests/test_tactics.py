import pytest
from ..modules.tactical_analysis import classify_tactical_pattern
import chess


def test_fork_detection():
    board = chess.Board("8/8/8/3n4/2N5/8/8/8 w - - 0 1")
    move = chess.Move.from_uci("c4e3")
    assert classify_tactical_pattern(300, board, move) == "fork"
