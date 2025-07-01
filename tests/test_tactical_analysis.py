import chess.pgn
from modules.analyze_games_tactics import detect_tactics_from_game
import pytest
import chess
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '/app/src')


# Minimal config mocks for required globals
class DummySettings(dict):
    def get(self, key, default=None):
        return super().get(key, default)


@pytest.fixture(autouse=True)
def patch_globals(monkeypatch):
    # Patch TACTICAL_ANALYSIS_SETTINGS and PHASE_DEPTHS
    monkeypatch.setattr("modules.analyze_games_tactics.TACTICAL_ANALYSIS_SETTINGS", DummySettings({
        "opening_move_threshold": 2,
        "min_branching_for_analysis": 0,
    }))
    monkeypatch.setattr("modules.analyze_games_tactics.PHASE_DEPTHS", {
                        "opening": 4, "middlegame": 6, "endgame": 8})

    # Patch classify_simple_pattern to return None (no pre_tag)
    monkeypatch.setattr(
        "modules.analyze_games_tactics.classify_simple_pattern", lambda board, move: None)
    # Patch get_game_phase to always return 'middlegame'
    monkeypatch.setattr(
        "modules.analyze_games_tactics.get_game_phase", lambda board: "middlegame")
    # Patch classify_tactical_pattern to return a dummy tag
    monkeypatch.setattr("modules.analyze_games_tactics.classify_tactical_pattern",
                        lambda score_diff, board, move: "dummy_tag")
    # Patch classify_error_label to return a dummy error label
    monkeypatch.setattr(
        "modules.analyze_games_tactics.classify_error_label", lambda score_diff: "dummy_error")
    # Patch compare_to_best to return a dummy alternative tag
    monkeypatch.setattr("modules.analyze_games_tactics.compare_to_best",
                        lambda best, alternatives, threshold_cp=100: "alt_tag")

    # Patch get_evaluation to return a dummy evaluation dict
    def dummy_get_evaluation(fen, depth, multipv=1):
        return {"best": {"value": 50}, "alternatives": []}
    monkeypatch.setattr(
        "modules.analyze_games_tactics.get_evaluation", dummy_get_evaluation)


def make_pgn_game(moves):
    """Helper to create a chess.pgn.Game from a list of SAN moves."""
    game = chess.pgn.Game()
    node = game
    board = chess.Board()
    for move in moves:
        m = board.parse_san(move)
        node = node.add_variation(m)
        board.push(m)
    return game


def test_detect_tactics_from_game_returns_tags_for_simple_game():
    # A simple game with a few moves
    moves = ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]
    game = make_pgn_game(moves)
    tags = detect_tactics_from_game(game)
    # Should return a list of dicts, one for each move after opening threshold (2)
    assert isinstance(tags, list)
    # There should be len(moves) - opening_move_threshold tags
    assert len(tags) == len(moves) - 2
    for tag in tags:
        assert isinstance(tag, dict)
        assert "fen" in tag
        assert "move" in tag
        assert "tag" in tag
        assert "error_label" in tag
        assert "score_diff" in tag
        assert "player_color" in tag
        assert "move_number" in tag


def test_detect_tactics_from_game_handles_no_moves():
    # Empty game
    game = make_pgn_game([])
    tags = detect_tactics_from_game(game)
    assert tags == []


def test_detect_tactics_from_game_handles_exception(monkeypatch):
    # Patch get_evaluation to raise an exception
    monkeypatch.setattr("modules.tactical_analysis.get_evaluation",
                        lambda fen, depth, multipv=1: 1/0)
    moves = ["e4", "e5", "Nf3", "Nc6"]
    game = make_pgn_game(moves)
    tags = detect_tactics_from_game(game)
    # Should return None due to exception before any tags processed
    assert tags is None


def test_detect_tactics_from_game_skips_opening_moves():
    moves = ["e4", "e5", "Nf3", "Nc6"]
    game = make_pgn_game(moves)
    tags = detect_tactics_from_game(game)
    # With opening_move_threshold=2, only 2 moves should be analyzed
    assert len(tags) == 2
    # The move_numbers should be 3 and 4
    assert [tag["move_number"] for tag in tags] == [3, 4]
