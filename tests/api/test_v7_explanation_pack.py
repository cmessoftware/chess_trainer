"""
Unit tests for V7 pipeline explanation_pack module.

Tests:
- phase_from_ply() game phase detection
- build_explanation_pack() JSON structure
- ExplanationPack dataclass integrity
"""

import pytest
from src.api.services.analysis_pipeline.explanation_pack import (
    ExplanationPack,
    build_explanation_pack,
    phase_from_ply,
)


class TestPhaseFromPly:
    """Tests for phase_from_ply function."""

    def test_opening_phase_fixed(self):
        """Test opening phase detection with fixed thresholds."""
        assert phase_from_ply(1) == "opening"
        assert phase_from_ply(10) == "opening"
        assert phase_from_ply(20) == "opening"

    def test_middlegame_phase_fixed(self):
        """Test middlegame phase detection with fixed thresholds."""
        assert phase_from_ply(21) == "middlegame"
        assert phase_from_ply(40) == "middlegame"
        assert phase_from_ply(60) == "middlegame"

    def test_endgame_phase_fixed(self):
        """Test endgame phase detection with fixed thresholds."""
        assert phase_from_ply(61) == "endgame"
        assert phase_from_ply(80) == "endgame"
        assert phase_from_ply(120) == "endgame"

    def test_opening_phase_proportional(self):
        """Test opening phase with total_plies (proportional)."""
        # First 25% of 100 plies = 0-24 (ply < 25)
        assert phase_from_ply(1, total_plies=100) == "opening"
        assert phase_from_ply(24, total_plies=100) == "opening"

    def test_middlegame_phase_proportional(self):
        """Test middlegame phase with total_plies (proportional)."""
        # Middle 50% of 100 plies = 25-74 (0.25 <= proportion < 0.75)
        assert phase_from_ply(25, total_plies=100) == "middlegame"
        assert phase_from_ply(50, total_plies=100) == "middlegame"
        assert phase_from_ply(74, total_plies=100) == "middlegame"

    def test_endgame_phase_proportional(self):
        """Test endgame phase with total_plies (proportional)."""
        # Last 25% of 100 plies = 75-100 (proportion >= 0.75)
        assert phase_from_ply(75, total_plies=100) == "endgame"
        assert phase_from_ply(100, total_plies=100) == "endgame"

    def test_boundary_values(self):
        """Test exact boundary values."""
        # Fixed thresholds
        assert phase_from_ply(20) == "opening"
        assert phase_from_ply(21) == "middlegame"
        assert phase_from_ply(60) == "middlegame"
        assert phase_from_ply(61) == "endgame"


class TestBuildExplanationPack:
    """Tests for build_explanation_pack function."""

    def test_basic_pack_structure(self):
        """Test that pack has all required fields."""
        pack = build_explanation_pack(
            game_id="test_game_123",
            ply=23,
            played_move_uci="e2e4",
            final_label="mistake",
            validator={
                "predicted_label": "good",
                "stockfish_label": "mistake",
                "final_label": "mistake",
                "cp_loss": 150,
                "model_disagreement": True,
            },
            stockfish_row={
                "eval_before_cp": 45,
                "eval_after_cp": -105,
                "cp_loss": 150,
                "best_moves": ["d2d4", "g1f3"],
                "multipv": [],
            },
            patterns={"tactical_tags": [], "positional_tags": []},
            temporal_context={
                "previous_inaccuracies": 2,
                "mistake_streak": 1,
                "cascade_score": 0.0,
            },
        )

        # Check basic fields
        assert pack.game_id == "test_game_123"
        assert pack.ply == 23
        assert pack.played_move == "e2e4"
        assert pack.final_label == "mistake"
        assert pack.phase == "middlegame"  # ply=23 is middlegame

    def test_validator_dict_structure(self):
        """Test that validator dict is correctly constructed."""
        pack = build_explanation_pack(
            game_id="test_game_123",
            ply=23,
            played_move_uci="e2e4",
            final_label="mistake",
            validator={
                "predicted_label": "good",
                "stockfish_label": "mistake",
                "final_label": "mistake",
                "cp_loss": 150,
                "model_disagreement": True,
            },
            stockfish_row={
                "eval_before_cp": 45,
                "eval_after_cp": -105,
                "cp_loss": 150,
                "best_moves": ["d2d4"],
                "multipv": [],
            },
            patterns={"tactical_tags": [], "positional_tags": []},
            temporal_context={},
        )

        assert pack.validator["predicted_label"] == "good"
        assert pack.validator["stockfish_label"] == "mistake"
        assert pack.validator["final_label"] == "mistake"
        assert pack.validator["cp_loss"] == 150
        assert pack.validator["model_disagreement"] is True

    def test_stockfish_dict_structure(self):
        """Test that stockfish dict is correctly constructed."""
        pack = build_explanation_pack(
            game_id="test_game_123",
            ply=23,
            played_move_uci="e2e4",
            final_label="good",
            validator={"predicted_label": "good", "stockfish_label": "good", "final_label": "good", "cp_loss": 30, "model_disagreement": False},
            stockfish_row={
                "eval_before_cp": 45,
                "eval_after_cp": 15,
                "cp_loss": 30,
                "best_moves": ["e2e4", "d2d4"],
                "multipv": [
                    {"rank": 1, "pv": ["e2e4", "e7e5"], "eval_cp": 15},
                    {"rank": 2, "pv": ["d2d4", "d7d5"], "eval_cp": 10},
                ],
            },
            patterns={"tactical_tags": [], "positional_tags": []},
            temporal_context={},
        )

        assert pack.stockfish["eval_before_cp"] == 45
        assert pack.stockfish["eval_after_cp"] == 15
        assert pack.stockfish["cp_loss"] == 30
        assert pack.stockfish["best_moves"] == ["e2e4", "d2d4"]
        assert len(pack.stockfish["multipv"]) == 2

    def test_patterns_dict_structure(self):
        """Test that patterns dict is correctly constructed."""
        pack = build_explanation_pack(
            game_id="test_game_123",
            ply=23,
            played_move_uci="e2e4",
            final_label="blunder",
            validator={"predicted_label": "blunder", "stockfish_label": "blunder", "final_label": "blunder", "cp_loss": 300, "model_disagreement": False},
            stockfish_row={
                "eval_before_cp": 50,
                "eval_after_cp": -250,
                "cp_loss": 300,
                "best_moves": ["g1f3"],
                "multipv": [],
            },
            patterns={
                "tactical_tags": ["hanging_piece", "fork"],
                "positional_tags": ["exposed_king"],
            },
            temporal_context={},
        )

        assert "hanging_piece" in pack.patterns["tactical_tags"]
        assert "fork" in pack.patterns["tactical_tags"]
        assert "exposed_king" in pack.patterns["positional_tags"]

    def test_temporal_context_dict_structure(self):
        """Test that temporal_context dict is correctly constructed."""
        pack = build_explanation_pack(
            game_id="test_game_123",
            ply=23,
            played_move_uci="e2e4",
            final_label="mistake",
            validator={"predicted_label": "mistake", "stockfish_label": "mistake", "final_label": "mistake", "cp_loss": 150, "model_disagreement": False},
            stockfish_row={
                "eval_before_cp": 50,
                "eval_after_cp": -100,
                "cp_loss": 150,
                "best_moves": ["d2d4"],
                "multipv": [],
            },
            patterns={"tactical_tags": [], "positional_tags": []},
            temporal_context={
                "previous_inaccuracies": 3,
                "mistake_streak": 2,
                "cascade_score": 0.75,
            },
        )

        assert pack.temporal_context["previous_inaccuracies"] == 3
        assert pack.temporal_context["mistake_streak"] == 2
        assert pack.temporal_context["cascade_score"] == 0.75

    def test_to_json_method(self):
        """Test that to_json() returns valid JSON-serializable dict."""
        pack = build_explanation_pack(
            game_id="test_game_123",
            ply=23,
            played_move_uci="e2e4",
            final_label="good",
            validator={"predicted_label": "good", "stockfish_label": "good", "final_label": "good", "cp_loss": 30, "model_disagreement": False},
            stockfish_row={
                "eval_before_cp": 50,
                "eval_after_cp": 20,
                "cp_loss": 30,
                "best_moves": ["e2e4"],
                "multipv": [],
            },
            patterns={"tactical_tags": [], "positional_tags": []},
            temporal_context={},
        )

        json_dict = pack.to_json()

        # Check that it's a dict
        assert isinstance(json_dict, dict)

        # Check that all keys are present
        assert "game_id" in json_dict
        assert "ply" in json_dict
        assert "phase" in json_dict
        assert "played_move" in json_dict
        assert "final_label" in json_dict
        assert "validator" in json_dict
        assert "stockfish" in json_dict
        assert "patterns" in json_dict
        assert "temporal_context" in json_dict


class TestExplanationPackDataclass:
    """Tests for ExplanationPack dataclass."""

    def test_dataclass_can_be_created(self):
        """Test that ExplanationPack can be directly instantiated."""
        pack = ExplanationPack(
            game_id="test_game_123",
            ply=23,
            phase="middlegame",
            played_move="e2e4",
            final_label="good",
            validator={},
            stockfish={},
            patterns={},
            temporal_context={},
        )

        assert pack.game_id == "test_game_123"
        assert pack.ply == 23
        assert pack.phase == "middlegame"
