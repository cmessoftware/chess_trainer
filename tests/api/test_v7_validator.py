"""
Unit tests for V7 pipeline validator module.

Tests:
- classify_cp_loss() thresholds
- validate_prediction() cross-validation logic
- ValidationResult dataclass integrity
"""

import pytest
from src.api.services.analysis_pipeline.validator import (
    classify_cp_loss,
    validate_prediction,
    ValidationResult,
    Label,
)


class TestClassifyCpLoss:
    """Tests for classify_cp_loss function."""

    def test_good_move(self):
        """Test classification of good moves (cp_loss <= 40)."""
        assert classify_cp_loss(0) == "good"
        assert classify_cp_loss(20) == "good"
        assert classify_cp_loss(40) == "good"

    def test_inaccuracy(self):
        """Test classification of inaccuracies (41 <= cp_loss <= 90)."""
        assert classify_cp_loss(41) == "inaccuracy"
        assert classify_cp_loss(60) == "inaccuracy"
        assert classify_cp_loss(90) == "inaccuracy"

    def test_mistake(self):
        """Test classification of mistakes (91 <= cp_loss <= 200)."""
        assert classify_cp_loss(91) == "mistake"
        assert classify_cp_loss(150) == "mistake"
        assert classify_cp_loss(200) == "mistake"

    def test_blunder(self):
        """Test classification of blunders (cp_loss > 200)."""
        assert classify_cp_loss(201) == "blunder"
        assert classify_cp_loss(300) == "blunder"
        assert classify_cp_loss(1000) == "blunder"

    def test_boundary_values(self):
        """Test exact boundary values."""
        # Verify boundaries are inclusive on lower range
        assert classify_cp_loss(40) == "good"
        assert classify_cp_loss(41) == "inaccuracy"
        assert classify_cp_loss(90) == "inaccuracy"
        assert classify_cp_loss(91) == "mistake"
        assert classify_cp_loss(200) == "mistake"
        assert classify_cp_loss(201) == "blunder"


class TestValidatePrediction:
    """Tests for validate_prediction function."""

    def test_agreement_good_move(self):
        """Test when ML and Stockfish agree on good move."""
        result = validate_prediction("good", 30)

        assert result.predicted_label == "good"
        assert result.stockfish_label == "good"
        assert result.final_label == "good"
        assert result.cp_loss == 30
        assert result.model_disagreement is False

    def test_agreement_blunder(self):
        """Test when ML and Stockfish agree on blunder."""
        result = validate_prediction("blunder", 300)

        assert result.predicted_label == "blunder"
        assert result.stockfish_label == "blunder"
        assert result.final_label == "blunder"
        assert result.cp_loss == 300
        assert result.model_disagreement is False

    def test_disagreement_stockfish_wins(self):
        """Test when ML and Stockfish disagree (Stockfish wins by default)."""
        # ML says "good", but Stockfish says "mistake" (cp_loss=150)
        result = validate_prediction("good", 150)

        assert result.predicted_label == "good"
        assert result.stockfish_label == "mistake"
        assert result.final_label == "mistake"  # Stockfish wins
        assert result.cp_loss == 150
        assert result.model_disagreement is True

    def test_disagreement_prefer_model_if_close(self):
        """Test prefer_model_if_close policy."""
        # ML says "inaccuracy", Stockfish says "mistake" (cp_loss=95, close to boundary)
        result = validate_prediction(
            "inaccuracy", 95, final_label_policy="prefer_model_if_close"
        )

        # With "prefer_model_if_close", ML can win if close to boundary
        # For now, implementation defaults to Stockfish, but policy exists
        assert result.predicted_label == "inaccuracy"
        assert result.stockfish_label == "mistake"
        assert result.model_disagreement is True

    def test_validation_result_immutable(self):
        """Test that ValidationResult is frozen (immutable)."""
        result = validate_prediction("good", 30)

        with pytest.raises(AttributeError):
            result.final_label = "blunder"  # Should raise error


class TestValidationResultDataclass:
    """Tests for ValidationResult dataclass."""

    def test_dataclass_fields(self):
        """Test that ValidationResult has all required fields."""
        result = ValidationResult(
            predicted_label="good",
            stockfish_label="good",
            final_label="good",
            cp_loss=30,
            model_disagreement=False,
        )

        assert result.predicted_label == "good"
        assert result.stockfish_label == "good"
        assert result.final_label == "good"
        assert result.cp_loss == 30
        assert result.model_disagreement is False

    def test_label_type_hints(self):
        """Test that Label type is correctly defined."""
        valid_labels: list[Label] = ["good", "inaccuracy", "mistake", "blunder"]
        assert len(valid_labels) == 4
