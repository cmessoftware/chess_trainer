"""
Integration tests for V7 pipeline.

Tests end-to-end flow:
1. Repository adapter loads data
2. Validator cross-checks ML vs Stockfish
3. Pattern engine detects patterns (stub)
4. Explanation pack builds JSON
5. LLM explainer generates text
6. Pipeline orchestrates all steps
"""

import pytest
from unittest.mock import MagicMock, patch
from src.api.services.analysis_pipeline import (
    generate_validated_feedback,
    create_v7_repos,
)
from src.api.services.analysis_pipeline.repository_adapters import V7RepositoryAdapter
from src.api.services.analysis_pipeline.integration_example import LLMClientWrapper


class TestV7RepositoryAdapter:
    """Tests for V7 repository adapter."""

    def test_adapter_interface(self):
        """Test that adapter has required methods."""
        mock_db = MagicMock()
        mock_models = MagicMock()

        adapter = V7RepositoryAdapter(mock_db, mock_models)

        # Check that all required methods exist
        assert hasattr(adapter, "get_game")
        assert hasattr(adapter, "get_stockfish_rows")
        assert hasattr(adapter, "get_predictions")
        assert hasattr(adapter, "get_temporal_context")

    def test_create_v7_repos_factory(self):
        """Test factory function creates adapter."""
        mock_db = MagicMock()
        mock_models = MagicMock()

        repos = create_v7_repos(mock_db, mock_models)

        assert isinstance(repos, V7RepositoryAdapter)


class TestLLMClientWrapper:
    """Tests for LLM client wrapper."""

    def test_wrapper_interface(self):
        """Test that wrapper has complete method."""
        mock_llm = MagicMock()
        wrapper = LLMClientWrapper(mock_llm)

        assert hasattr(wrapper, "complete")

    def test_wrapper_returns_string(self):
        """Test that wrapper returns string output."""
        mock_llm = MagicMock()
        wrapper = LLMClientWrapper(mock_llm)

        result = wrapper.complete("test prompt")

        assert isinstance(result, str)
        assert "Diagnosis:" in result
        assert "Better move:" in result
        assert "Training rule:" in result


class TestV7PipelineIntegration:
    """Integration tests for complete V7 pipeline."""

    def test_pipeline_with_mock_data(self):
        """Test pipeline with complete mock data."""
        # Mock repository
        mock_repos = MagicMock()
        mock_repos.get_game.return_value = {
            "game_id": "test_game_123",
            "pgn": "[Event 'Test']",
            "white_player": "TestWhite",
            "black_player": "TestBlack",
            "result": "1-0",
        }
        mock_repos.get_stockfish_rows.return_value = [
            {
                "ply": 23,
                "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "played_move_uci": "e2e4",
                "played_move_san": "e4",
                "cp_loss": 150,
                "eval_before_cp": 45,
                "eval_after_cp": -105,
                "best_moves": ["d2d4", "g1f3"],
                "multipv": [
                    {"rank": 1, "pv": ["d2d4"], "eval_cp": 45},
                    {"rank": 2, "pv": ["g1f3"], "eval_cp": 40},
                ],
            },
            {
                "ply": 25,
                "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "played_move_uci": "d2d4",
                "played_move_san": "d4",
                "cp_loss": 30,
                "eval_before_cp": 20,
                "eval_after_cp": -10,
                "best_moves": ["d2d4"],
                "multipv": [],
            },
        ]
        mock_repos.get_predictions.return_value = {
            23: {"predicted_label": "good", "predicted_proba": 0.85},
            25: {"predicted_label": "good", "predicted_proba": 0.90},
        }
        mock_repos.get_temporal_context.return_value = {
            23: {
                "previous_inaccuracies": 2,
                "mistake_streak": 1,
                "cascade_score": 0.0,
            },
            25: {
                "previous_inaccuracies": 2,
                "mistake_streak": 0,
                "cascade_score": 0.0,
            },
        }

        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.complete.return_value = (
            "Diagnosis: Error detectado en esta jugada\n"
            "Better move: Se recomienda alternativa más precisa\n"
            "Training rule: Analizar consecuencias antes de mover"
        )
        llm_client = LLMClientWrapper(mock_llm)

        # Execute pipeline
        result = generate_validated_feedback(
            "test_game_123",
            repos=mock_repos,
            llm_client=llm_client,
            cp_loss_threshold=90,
            max_items=10,
        )

        # Verify result structure
        assert "game_id" in result
        assert "stats" in result
        assert "critical_feedback" in result

        # Verify game_id
        assert result["game_id"] == "test_game_123"

        # Verify stats
        assert result["stats"]["num_moves_analyzed"] == 2
        assert result["stats"]["num_critical"] >= 1  # ply 23 has cp_loss=150

        # Verify critical feedback structure
        assert len(result["critical_feedback"]) >= 1
        feedback = result["critical_feedback"][0]

        assert "ply" in feedback
        assert "final_label" in feedback
        assert "model_disagreement" in feedback
        assert "explanation" in feedback
        assert "pack" in feedback

        # Verify explanation structure
        explanation = feedback["explanation"]
        assert "diagnosis" in explanation
        assert "better_move" in explanation
        assert "training_rule" in explanation

    def test_pipeline_with_no_critical_moves(self):
        """Test pipeline when no moves exceed threshold."""
        # Mock repository with all good moves
        mock_repos = MagicMock()
        mock_repos.get_game.return_value = {
            "game_id": "test_game_456",
            "pgn": "[Event 'Test']",
        }
        mock_repos.get_stockfish_rows.return_value = [
            {
                "ply": 1,
                "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "played_move_uci": "e2e4",
                "cp_loss": 10,
                "eval_before_cp": 25,
                "eval_after_cp": 15,
                "best_moves": ["e2e4"],
                "multipv": [],
            },
        ]
        mock_repos.get_predictions.return_value = {
            1: {"predicted_label": "good", "predicted_proba": 0.95}
        }
        mock_repos.get_temporal_context.return_value = {
            1: {"previous_inaccuracies": 0, "mistake_streak": 0, "cascade_score": 0.0}
        }

        # Mock LLM client
        mock_llm = MagicMock()
        llm_client = LLMClientWrapper(mock_llm)

        # Execute pipeline
        result = generate_validated_feedback(
            "test_game_456",
            repos=mock_repos,
            llm_client=llm_client,
            cp_loss_threshold=90,
            max_items=10,
        )

        # Verify no critical moves
        assert result["stats"]["num_critical"] == 0
        assert len(result["critical_feedback"]) == 0

    def test_pipeline_detects_ml_stockfish_disagreement(self):
        """Test that pipeline detects when ML and Stockfish disagree."""
        # Mock repository with disagreement
        mock_repos = MagicMock()
        mock_repos.get_game.return_value = {"game_id": "test_game_789", "pgn": "[Event 'Test']"}
        mock_repos.get_stockfish_rows.return_value = [
            {
                "ply": 10,
                "fen_before": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "played_move_uci": "e2e4",
                "cp_loss": 150,  # Stockfish says mistake
                "eval_before_cp": 50,
                "eval_after_cp": -100,
                "best_moves": ["d2d4"],
                "multipv": [],
            },
        ]
        mock_repos.get_predictions.return_value = {
            10: {"predicted_label": "good", "predicted_proba": 0.80}  # ML says good
        }
        mock_repos.get_temporal_context.return_value = {
            10: {"previous_inaccuracies": 0, "mistake_streak": 0, "cascade_score": 0.0}
        }

        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.complete.return_value = (
            "Diagnosis: Desacuerdo detectado entre ML y Stockfish\n"
            "Better move: d2d4 era mejor alternativa\n"
            "Training rule: Confiar en análisis del motor"
        )
        llm_client = LLMClientWrapper(mock_llm)

        # Execute pipeline
        result = generate_validated_feedback(
            "test_game_789",
            repos=mock_repos,
            llm_client=llm_client,
            cp_loss_threshold=90,
            max_items=10,
        )

        # Verify disagreement detected
        assert result["stats"]["num_disagreements"] == 1

        # Verify feedback reflects disagreement
        feedback = result["critical_feedback"][0]
        assert feedback["model_disagreement"] is True
        assert feedback["final_label"] == "mistake"  # Stockfish wins


class TestV7PipelineErrorHandling:
    """Tests for error handling in V7 pipeline."""

    def test_pipeline_handles_missing_game(self):
        """Test pipeline handles missing game gracefully."""
        mock_repos = MagicMock()
        mock_repos.get_game.side_effect = ValueError("Game test_missing not found")

        mock_llm = MagicMock()
        llm_client = LLMClientWrapper(mock_llm)

        with pytest.raises(ValueError, match="Game test_missing not found"):
            generate_validated_feedback(
                "test_missing",
                repos=mock_repos,
                llm_client=llm_client,
            )

    def test_pipeline_handles_empty_stockfish_data(self):
        """Test pipeline handles empty Stockfish data."""
        mock_repos = MagicMock()
        mock_repos.get_game.return_value = {"game_id": "test_empty", "pgn": "[Event 'Test']"}
        mock_repos.get_stockfish_rows.return_value = []  # No Stockfish data
        mock_repos.get_predictions.return_value = {}
        mock_repos.get_temporal_context.return_value = {}

        mock_llm = MagicMock()
        llm_client = LLMClientWrapper(mock_llm)

        # Execute pipeline
        result = generate_validated_feedback(
            "test_empty",
            repos=mock_repos,
            llm_client=llm_client,
        )

        # Should return empty feedback
        assert result["stats"]["num_moves_analyzed"] == 0
        assert result["stats"]["num_critical"] == 0
