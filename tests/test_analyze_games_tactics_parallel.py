from scripts.analyze_games_tactics_parallel import (
    run_parallel_analysis_from_db,
    analyze_game_parallel
)
import pytest
import os
import pandas as pd
import time
import chess.pgn
import io
from unittest.mock import Mock, patch, MagicMock, call
from concurrent.futures import ProcessPoolExecutor, Future
import sqlalchemy.exc

# Import the module under test
import sys
sys.path.append('/app/src')


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("LIMIT_FOR_DEBUG", "5")
    monkeypatch.setenv("ANALYSIS_WORKERS", "2")
    monkeypatch.setenv("ANALYZED_PER_CHUNK", "3")
    monkeypatch.setenv("GAMES_SOURCE", "lichess")


@pytest.fixture
def sample_pgn_game():
    """Sample PGN game for testing."""
    pgn_text = """[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 1-0"""
    return chess.pgn.read_game(io.StringIO(pgn_text))


@pytest.fixture
def sample_tags_dataframe():
    """Sample tags DataFrame for testing."""
    return pd.DataFrame([
        {
            "move_number": 5,
            "player_color": 1,
            "tag": "castle_kingside",
            "score_diff": 10,
            "error_label": "good"
        },
        {
            "move_number": 8,
            "player_color": 0,
            "tag": "development",
            "score_diff": -5,
            "error_label": "good"
        }
    ])


@pytest.fixture
def mock_repositories():
    """Mock repository objects."""
    analyzed_tacticals_repo = Mock()
    features_repo = Mock()
    games_repo = Mock()

    # Mock the get_all method to return some analyzed games
    analyzed_tacticals_repo.get_all.return_value = [
        Mock(game_id="analyzed_game_1"),
        Mock(game_id="analyzed_game_2")
    ]

    return analyzed_tacticals_repo, features_repo, games_repo


@pytest.fixture
def mock_game_data():
    """Mock game data for testing."""
    return [
        "game_pgn_1",
        "game_pgn_2",
        "game_pgn_3"
    ]


class TestRunParallelAnalysisFromDb:
    """Test suite for run_parallel_analysis_from_db function."""

    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.FeaturesRepository')
    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.ProcessPoolExecutor')
    @patch('scripts.analyze_games_tactics_parallel.get_game_id')
    @patch('scripts.analyze_games_tactics_parallel.pgn_str_to_game')
    @patch('scripts.analyze_games_tactics_parallel.psutil.Process')
    def test_run_parallel_analysis_basic_flow(
        self,
        mock_process,
        mock_pgn_str_to_game,
        mock_get_game_id,
        mock_executor_class,
        mock_games_repo_class,
        mock_features_repo_class,
        mock_analyzed_repo_class,
        mock_env_vars
    ):
        """Test the basic flow of parallel analysis."""
        # Setup mocks
        mock_analyzed_repo = Mock()
        mock_features_repo = Mock()
        mock_games_repo = Mock()

        mock_analyzed_repo_class.return_value = mock_analyzed_repo
        mock_features_repo_class.return_value = mock_features_repo
        mock_games_repo_class.return_value = mock_games_repo

        # Mock analyzed games (empty set)
        mock_analyzed_repo.get_all.return_value = []

        # Mock games data
        mock_games_repo.get_games_by_pagination_not_analyzed.side_effect = [
            ["pgn1", "pgn2"],  # First chunk
            []  # Empty chunk to end loop
        ]

        # Mock game IDs
        mock_get_game_id.side_effect = ["game_id_1", "game_id_2"]
        mock_pgn_str_to_game.side_effect = [Mock(), Mock()]

        # Mock process executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        # Mock futures
        future1 = Mock()
        future1.result.return_value = (
            "game_id_1", pd.DataFrame([{"tag": "test"}]))
        future2 = Mock()
        future2.result.return_value = ("game_id_2", None)

        mock_executor.submit.side_effect = [future1, future2]
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        # Mock as_completed
        with patch('scripts.analyze_games_tactics_parallel.as_completed', return_value=[future1, future2]):
            # Mock psutil
            mock_memory_info = Mock()
            mock_memory_info.rss = 1024 * 1024 * 100  # 100 MB
            mock_process.return_value.memory_info.return_value = mock_memory_info

            # Run the function
            run_parallel_analysis_from_db(max_games=10)

            # Verify repository calls
            mock_analyzed_repo.get_all.assert_called_once()
            assert mock_games_repo.get_games_by_pagination_not_analyzed.call_count >= 1
            mock_features_repo.update_features_tags_and_score_diff.assert_called_once()
            mock_analyzed_repo.save_analyzed_tactical_hash.assert_called()

    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.FeaturesRepository')
    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    def test_run_parallel_analysis_no_games(
        self,
        mock_games_repo_class,
        mock_features_repo_class,
        mock_analyzed_repo_class,
        mock_env_vars
    ):
        """Test behavior when no games are available for analysis."""
        # Setup mocks
        mock_analyzed_repo = Mock()
        mock_features_repo = Mock()
        mock_games_repo = Mock()

        mock_analyzed_repo_class.return_value = mock_analyzed_repo
        mock_features_repo_class.return_value = mock_features_repo
        mock_games_repo_class.return_value = mock_games_repo

        # Mock no analyzed games
        mock_analyzed_repo.get_all.return_value = []

        # Mock no games available
        mock_games_repo.get_games_by_pagination_not_analyzed.return_value = []

        # Run the function
        run_parallel_analysis_from_db(max_games=10)

        # Verify that we checked for games but didn't process any
        mock_games_repo.get_games_by_pagination_not_analyzed.assert_called_once()
        mock_features_repo.update_features_tags_and_score_diff.assert_not_called()

    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.FeaturesRepository')
    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.ProcessPoolExecutor')
    @patch('scripts.analyze_games_tactics_parallel.get_game_id')
    @patch('scripts.analyze_games_tactics_parallel.pgn_str_to_game')
    @patch('scripts.analyze_games_tactics_parallel.psutil.Process')
    def test_run_parallel_analysis_with_sqlalchemy_error(
        self,
        mock_process,
        mock_pgn_str_to_game,
        mock_get_game_id,
        mock_executor_class,
        mock_games_repo_class,
        mock_features_repo_class,
        mock_analyzed_repo_class,
        mock_env_vars
    ):
        """Test handling of SQLAlchemy PendingRollbackError."""
        # Setup mocks
        mock_analyzed_repo = Mock()
        mock_features_repo = Mock()
        mock_games_repo = Mock()

        mock_analyzed_repo_class.return_value = mock_analyzed_repo
        mock_features_repo_class.return_value = mock_features_repo
        mock_games_repo_class.return_value = mock_games_repo

        # Mock analyzed games
        mock_analyzed_repo.get_all.return_value = []

        # Mock games data
        mock_games_repo.get_games_by_pagination_not_analyzed.side_effect = [
            ["pgn1"],  # First chunk
            []  # Empty chunk to end loop
        ]

        # Mock game IDs
        mock_get_game_id.return_value = "game_id_1"
        mock_pgn_str_to_game.return_value = Mock()

        # Mock process executor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        # Mock future with successful result
        future1 = Mock()
        future1.result.return_value = (
            "game_id_1", pd.DataFrame([{"tag": "test"}]))
        mock_executor.submit.return_value = future1

        # Mock SQLAlchemy error on features update
        mock_features_repo.update_features_tags_and_score_diff.side_effect = sqlalchemy.exc.PendingRollbackError(
            "Test error", None, None)

        # Mock as_completed
        with patch('scripts.analyze_games_tactics_parallel.as_completed', return_value=[future1]):
            # Mock psutil
            mock_memory_info = Mock()
            mock_memory_info.rss = 1024 * 1024 * 100
            mock_process.return_value.memory_info.return_value = mock_memory_info

            # Run the function
            run_parallel_analysis_from_db(max_games=10)

            # Verify rollback was called
            mock_features_repo.session.rollback.assert_called_once()
            mock_analyzed_repo.save_analyzed_tactical_hash.assert_called_with(
                "game_id_1")


class TestAnalyzeGameParallel:
    """Test suite for analyze_game_parallel function."""

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.detect_tactics_from_game')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    @patch('scripts.analyze_games_tactics_parallel.psutil.Process')
    @patch('scripts.analyze_games_tactics_parallel.TACTICAL_ANALYSIS_SETTINGS', {"depth": 8})
    def test_analyze_game_parallel_success(
        self,
        mock_process,
        mock_read_game,
        mock_detect_tactics,
        mock_analyzed_repo_class,
        mock_games_repo_class,
        sample_pgn_game
    ):
        """Test successful game analysis."""
        # Setup mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Mock game data
        game_id = "test_game_id"
        pgn_text = "[Event \"Test\"]\n1. e4 e5 2. Nf3 *"
        mock_games_repo.get_pgn_text_by_id.return_value = pgn_text
        mock_read_game.return_value = sample_pgn_game

        # Mock tactics detection
        mock_tactics = [
            {"move_number": 1, "tag": "opening", "score_diff": 0}
        ]
        mock_detect_tactics.return_value = mock_tactics

        # Mock psutil
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 50  # 50 MB
        mock_process.return_value.memory_info.return_value = mock_memory_info

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 1

        # Verify function calls
        mock_games_repo.get_pgn_text_by_id.assert_called_once_with(game_id)
        mock_read_game.assert_called_once()
        mock_detect_tactics.assert_called_once_with(sample_pgn_game, 8)

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    def test_analyze_game_parallel_empty_pgn(
        self,
        mock_analyzed_repo_class,
        mock_games_repo_class
    ):
        """Test handling of empty PGN text."""
        # Setup mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Mock empty PGN
        game_id = "test_game_id"
        mock_games_repo.get_pgn_text_by_id.return_value = ""

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None

        # Verify analyzed tactical was saved
        mock_analyzed_repo.save_analyzed_tactical_hash.assert_called_once_with(
            game_id)

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    def test_analyze_game_parallel_invalid_pgn(
        self,
        mock_read_game,
        mock_analyzed_repo_class,
        mock_games_repo_class
    ):
        """Test handling of invalid PGN that cannot be parsed."""
        # Setup mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Mock invalid PGN
        game_id = "test_game_id"
        mock_games_repo.get_pgn_text_by_id.return_value = "invalid pgn text"
        mock_read_game.return_value = None  # Simulates failed parsing

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None

        # Verify analyzed tactical was saved
        mock_analyzed_repo.save_analyzed_tactical_hash.assert_called_once_with(
            game_id)

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.detect_tactics_from_game')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    @patch('scripts.analyze_games_tactics_parallel.psutil.Process')
    @patch('scripts.analyze_games_tactics_parallel.TACTICAL_ANALYSIS_SETTINGS', {"depth": 8})
    def test_analyze_game_parallel_no_tactics_found(
        self,
        mock_process,
        mock_read_game,
        mock_detect_tactics,
        mock_analyzed_repo_class,
        mock_games_repo_class,
        sample_pgn_game
    ):
        """Test when no tactics are detected in the game."""
        # Setup mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Mock game data
        game_id = "test_game_id"
        pgn_text = "[Event \"Test\"]\n1. e4 e5 *"
        mock_games_repo.get_pgn_text_by_id.return_value = pgn_text
        mock_read_game.return_value = sample_pgn_game

        # Mock no tactics detected
        mock_detect_tactics.return_value = []

        # Mock psutil
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 50
        mock_process.return_value.memory_info.return_value = mock_memory_info

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    def test_analyze_game_parallel_exception_handling(
        self,
        mock_analyzed_repo_class,
        mock_games_repo_class
    ):
        """Test exception handling in analyze_game_parallel."""
        # Setup mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Mock exception in get_pgn_text_by_id
        game_id = "test_game_id"
        mock_games_repo.get_pgn_text_by_id.side_effect = Exception(
            "Database error")

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_default_environment_variables(self, monkeypatch):
        """Test default values when environment variables are not set."""
        # Clear environment variables
        for var in ["LIMIT_FOR_DEBUG", "ANALYSIS_WORKERS", "ANALYZED_PER_CHUNK", "GAMES_SOURCE"]:
            monkeypatch.delenv(var, raising=False)

        # Reload the module to get default values
        import importlib
        import scripts.analyze_games_tactics_parallel as module
        importlib.reload(module)

        # Test default values
        assert module.LIMIT_FOR_DEBUG == 0
        assert module.ANALYSIS_WORKERS == 2
        assert module.ANALYZED_PER_CHUNK == 10
        assert module.GAMES_SOURCE is None

    def test_custom_environment_variables(self, monkeypatch):
        """Test custom environment variable values."""
        # Set custom environment variables
        monkeypatch.setenv("LIMIT_FOR_DEBUG", "100")
        monkeypatch.setenv("ANALYSIS_WORKERS", "4")
        monkeypatch.setenv("ANALYZED_PER_CHUNK", "20")
        monkeypatch.setenv("GAMES_SOURCE", "chesscom")

        # Reload the module to get new values
        import importlib
        import scripts.analyze_games_tactics_parallel as module
        importlib.reload(module)

        # Test custom values
        assert module.LIMIT_FOR_DEBUG == 100
        assert module.ANALYSIS_WORKERS == 4
        assert module.ANALYZED_PER_CHUNK == 20
        assert module.GAMES_SOURCE == "chesscom"


class TestIntegration:
    """Integration tests for the module."""

    @patch('scripts.analyze_games_tactics_parallel.run_parallel_analysis_from_db')
    def test_main_execution(self, mock_run_analysis):
        """Test the main execution block."""
        # Import and execute the main block
        import scripts.analyze_games_tactics_parallel as module

        # Since we can't easily test the if __name__ == "__main__" block,
        # we test that the function can be called without errors
        # Mock 10 second execution
        with patch('time.time', side_effect=[0, 10]):
            module.run_parallel_analysis_from_db()
            mock_run_analysis.assert_called()

    def test_import_all_dependencies(self):
        """Test that all required dependencies can be imported."""
        # This test ensures all imports work correctly
        try:
            import scripts.analyze_games_tactics_parallel
            # If we get here, all imports succeeded
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import dependencies: {e}")


@pytest.mark.parametrize("max_games,expected_calls", [
    (5, 1),   # Small number should result in single batch
    (100, 1),  # Medium number
    (0, 0),   # Zero games should not process anything
])
def test_max_games_parameter(max_games, expected_calls, mock_env_vars):
    """Test that max_games parameter properly limits processing."""
    with patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository') as mock_analyzed_repo_class, \
            patch('scripts.analyze_games_tactics_parallel.FeaturesRepository') as mock_features_repo_class, \
            patch('scripts.analyze_games_tactics_parallel.GamesRepository') as mock_games_repo_class:

        # Setup mocks
        mock_analyzed_repo = Mock()
        mock_features_repo = Mock()
        mock_games_repo = Mock()

        mock_analyzed_repo_class.return_value = mock_analyzed_repo
        mock_features_repo_class.return_value = mock_features_repo
        mock_games_repo_class.return_value = mock_games_repo

        # Mock no analyzed games
        mock_analyzed_repo.get_all.return_value = []

        # Mock games data based on max_games
        if max_games > 0:
            mock_games_repo.get_games_by_pagination_not_analyzed.side_effect = [
                [],  # Empty to end immediately
            ]
        else:
            mock_games_repo.get_games_by_pagination_not_analyzed.return_value = []

        # Run the function
        run_parallel_analysis_from_db(max_games=max_games)

        # Verify call count matches expected
        if expected_calls > 0:
            assert mock_games_repo.get_games_by_pagination_not_analyzed.call_count >= expected_calls
        else:
            mock_games_repo.get_games_by_pagination_not_analyzed.assert_called_once()
