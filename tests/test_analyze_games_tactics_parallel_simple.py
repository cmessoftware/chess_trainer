import pytest
import os
import pandas as pd
import chess.pgn
import io
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the src directory to the Python path
sys.path.insert(0, '/app/src')

# Test the core functions from analyze_games_tactics_parallel


@pytest.fixture
def sample_pgn_text():
    """Sample PGN text for testing."""
    return """[Event "Test Tournament"]
[Site "Test Location"]
[Date "2024.01.01"]
[Round "1"]
[White "Test Player 1"]
[Black "Test Player 2"]
[Result "1-0"]

 1. Nf3 b6 2. g3 d5 3. Bg2 Bb7 4. d4 e6 5. O-O Nf6 6. Ne5 Qc8 7. c4 dxc4 8. Qa4+ Nfd7 9. Nxd7 Nxd7 10. Bc6 Rb8 11. Qxc4 Bxc6 12. Qxc6 Qb7 13. Qxb7 Rxb7 14. Nc3 b5 15. Be3 Nb6 16. Rfc1 Kd7 17. Ne4 Nc4 18. b3 Nxe3 19. fxe3 Rb6 20. Nc5+ Bxc5 21. Rxc5 Rhb8 22. Rac1 R8b7 23. e4 Ra6 24. R1c2 Ra3 25. e5 a5 26. R5c3 b4 27. Rf3 Ke8 28. g4 a4 29. g5 c6 30. Kf2 Rd7 31. Rd3 Kd8 32. Rxc6 Rxa2 33. Rb6 a3 34. Rxb4 Rb2 35. Ra4 a2 36. Rc3 Rc7 37. Rcc4 Kc8 38. Ra7 Rxc4 39. bxc4 Kb8 40. Ra4 Kc7 41. Kf3 Kc6 42. h4 h5 43. gxh6 gxh6 44. e4 Rc2 45. Ke3 Rh2 46. h5 Rh3+ 47. Kf4 Rh4+ 48. Kf3 Rh2 49. d5+ Kc5 50. d6 Kc6 51. Ke3 Kc5 52. d7 Rh3+ 53. Kd2 Rh2+ 54. Kc3 Rh3+ 55. Kb2 Rh2+ 56. Ka1 Rd2 57. Ra5+ Kb4 58. Rd5 exd5 59. d8=Q d4 60. c5 d3 61. c6 1-0"""


@pytest.fixture
def sample_game_object(sample_pgn_text):
    """Sample chess.pgn.Game object for testing."""
    return chess.pgn.read_game(io.StringIO(sample_pgn_text))


@pytest.fixture
def mock_tactical_analysis_settings():
    """Mock TACTICAL_ANALYSIS_SETTINGS for testing."""
    return {"depth": 8, "min_moves": 3}


@pytest.fixture
def sample_tactics_data():
    """Sample tactics data that would be returned from detect_tactics_from_game."""
    return [
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
            "tag": "castle_kingside",
            "score_diff": 5,
            "error_label": "good"
        },
        {
            "move_number": 15,
            "player_color": 1,
            "tag": "sacrifice_piece",
            "score_diff": 150,
            "error_label": "mistake"
        }
    ]


class TestAnalyzeGameParallelFunction:
    """Test the analyze_game_parallel function specifically."""

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.detect_tactics_from_game')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    @patch('scripts.analyze_games_tactics_parallel.TACTICAL_ANALYSIS_SETTINGS')
    def test_analyze_game_parallel_successful_analysis(
        self,
        mock_settings,
        mock_read_game,
        mock_detect_tactics,
        mock_analyzed_repo_class,
        mock_games_repo_class,
        sample_game_object,
        sample_pgn_text,
        sample_tactics_data,
        mock_tactical_analysis_settings
    ):
        """Test successful game analysis returns proper results."""
        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup mock settings
        mock_settings.get.return_value = 8
        mock_settings.__getitem__ = lambda self, key: mock_tactical_analysis_settings[key]

        # Setup repository mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Setup game data
        game_id = "test_game_123"
        mock_games_repo.get_pgn_text_by_id.return_value = sample_pgn_text
        mock_read_game.return_value = sample_game_object
        mock_detect_tactics.return_value = sample_tactics_data

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(sample_tactics_data)
        assert "tag" in result_df.columns
        assert "score_diff" in result_df.columns

        # Verify function calls
        mock_games_repo.get_pgn_text_by_id.assert_called_once_with(game_id)
        mock_read_game.assert_called_once()
        mock_detect_tactics.assert_called_once()

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    def test_analyze_game_parallel_empty_pgn(
        self,
        mock_analyzed_repo_class,
        mock_games_repo_class
    ):
        """Test handling of empty PGN returns None result."""
        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup repository mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Setup empty PGN
        game_id = "empty_game_123"
        mock_games_repo.get_pgn_text_by_id.return_value = ""

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None

        # Verify that the game was marked as analyzed
        mock_analyzed_repo.save_analyzed_tactical_hash.assert_called_once_with(
            game_id)

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    def test_analyze_game_parallel_invalid_pgn(
        self,
        mock_read_game,
        mock_analyzed_repo_class,
        mock_games_repo_class,
        sample_pgn_text
    ):
        """Test handling of PGN that fails to parse."""
        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup repository mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Setup invalid PGN parsing
        game_id = "invalid_game_123"
        mock_games_repo.get_pgn_text_by_id.return_value = sample_pgn_text
        mock_read_game.return_value = None  # Simulates failed parsing

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None

        # Verify that the game was marked as analyzed
        mock_analyzed_repo.save_analyzed_tactical_hash.assert_called_once_with(
            game_id)

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.detect_tactics_from_game')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    @patch('scripts.analyze_games_tactics_parallel.TACTICAL_ANALYSIS_SETTINGS')
    def test_analyze_game_parallel_no_tactics_detected(
        self,
        mock_settings,
        mock_read_game,
        mock_detect_tactics,
        mock_analyzed_repo_class,
        mock_games_repo_class,
        sample_game_object,
        sample_pgn_text,
        mock_tactical_analysis_settings
    ):
        """Test when no tactics are detected in a game."""
        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup mock settings
        mock_settings.get.return_value = 8

        # Setup repository mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Setup game data with no tactics
        game_id = "no_tactics_game_123"
        mock_games_repo.get_pgn_text_by_id.return_value = sample_pgn_text
        mock_read_game.return_value = sample_game_object
        mock_detect_tactics.return_value = []  # No tactics detected

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df is None  # Should return None when no tactics


class TestRunParallelAnalysisFromDbFunction:
    """Test the run_parallel_analysis_from_db function."""

    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.FeaturesRepository')
    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.get_game_id')
    @patch('scripts.analyze_games_tactics_parallel.pgn_str_to_game')
    def test_run_parallel_analysis_no_games_available(
        self,
        mock_pgn_str_to_game,
        mock_get_game_id,
        mock_games_repo_class,
        mock_features_repo_class,
        mock_analyzed_repo_class
    ):
        """Test behavior when no games are available for analysis."""
        from scripts.analyze_games_tactics_parallel import run_parallel_analysis_from_db

        # Setup repository mocks
        mock_analyzed_repo = Mock()
        mock_features_repo = Mock()
        mock_games_repo = Mock()

        mock_analyzed_repo_class.return_value = mock_analyzed_repo
        mock_features_repo_class.return_value = mock_features_repo
        mock_games_repo_class.return_value = mock_games_repo

        # Setup no analyzed games initially
        mock_analyzed_repo.get_all.return_value = []

        # Setup no games to analyze
        mock_games_repo.get_games_by_pagination_not_analyzed.return_value = []

        # Run the function
        run_parallel_analysis_from_db(max_games=10)

        # Verify that we checked for games but didn't process any
        mock_games_repo.get_games_by_pagination_not_analyzed.assert_called_once()
        mock_features_repo.update_features_tags_and_score_diff.assert_not_called()

    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    @patch('scripts.analyze_games_tactics_parallel.FeaturesRepository')
    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    def test_run_parallel_analysis_with_analyzed_games(
        self,
        mock_games_repo_class,
        mock_features_repo_class,
        mock_analyzed_repo_class
    ):
        """Test that already analyzed games are properly excluded."""
        from scripts.analyze_games_tactics_parallel import run_parallel_analysis_from_db

        # Setup repository mocks
        mock_analyzed_repo = Mock()
        mock_features_repo = Mock()
        mock_games_repo = Mock()

        mock_analyzed_repo_class.return_value = mock_analyzed_repo
        mock_features_repo_class.return_value = mock_features_repo
        mock_games_repo_class.return_value = mock_games_repo

        # Setup some already analyzed games
        analyzed_game_1 = Mock()
        analyzed_game_1.game_id = "already_analyzed_1"
        analyzed_game_2 = Mock()
        analyzed_game_2.game_id = "already_analyzed_2"
        mock_analyzed_repo.get_all.return_value = [
            analyzed_game_1, analyzed_game_2]

        # Setup no new games to analyze
        mock_games_repo.get_games_by_pagination_not_analyzed.return_value = []

        # Run the function
        run_parallel_analysis_from_db(max_games=10)

        # Verify that analyzed games were properly excluded
        mock_analyzed_repo.get_all.assert_called_once()
        call_args = mock_games_repo.get_games_by_pagination_not_analyzed.call_args
        # First positional argument should be the analyzed set
        analyzed_set = call_args[0][0]
        assert "already_analyzed_1" in analyzed_set
        assert "already_analyzed_2" in analyzed_set


class TestEnvironmentVariableHandling:
    """Test environment variable handling."""

    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded."""
        # Test that the module can be imported without errors
        try:
            from scripts import analyze_games_tactics_parallel
            # Basic check that the constants exist
            assert hasattr(analyze_games_tactics_parallel, 'ANALYSIS_WORKERS')
            assert hasattr(analyze_games_tactics_parallel,
                           'ANALYZED_PER_CHUNK')
            assert hasattr(analyze_games_tactics_parallel, 'LIMIT_FOR_DEBUG')
        except ImportError as e:
            pytest.fail(f"Failed to import module: {e}")

    @patch.dict(os.environ, {
        "ANALYSIS_WORKERS": "4",
        "ANALYZED_PER_CHUNK": "20",
        "LIMIT_FOR_DEBUG": "100",
        "GAMES_SOURCE": "test_source"
    })
    def test_environment_variables_set(self):
        """Test that environment variables are used when set."""
        # Force reload to pick up new environment variables
        import importlib
        import scripts.analyze_games_tactics_parallel as module
        importlib.reload(module)

        # Verify the values match what we set
        assert module.ANALYSIS_WORKERS == 4
        assert module.ANALYZED_PER_CHUNK == 20
        assert module.LIMIT_FOR_DEBUG == 100
        assert module.GAMES_SOURCE == "test_source"


class TestDataFrameHandling:
    """Test DataFrame creation and handling."""

    def test_empty_tags_dataframe_creation(self):
        """Test that empty tags result in proper None return."""
        # Test DataFrame creation with empty tags
        empty_tags = []
        df = pd.DataFrame(empty_tags)
        assert df.empty

    def test_tags_dataframe_creation_with_data(self, sample_tactics_data):
        """Test DataFrame creation with actual tactics data."""
        df = pd.DataFrame(sample_tactics_data)

        # Verify DataFrame properties
        assert not df.empty
        assert len(df) == len(sample_tactics_data)
        assert "tag" in df.columns
        assert "score_diff" in df.columns
        assert "move_number" in df.columns
        assert "player_color" in df.columns
        assert "error_label" in df.columns

    def test_tags_dataframe_expected_columns(self, sample_tactics_data):
        """Test that the tactics DataFrame has expected columns."""
        df = pd.DataFrame(sample_tactics_data)

        expected_columns = ["move_number", "player_color",
                            "tag", "score_diff", "error_label"]
        for col in expected_columns:
            assert col in df.columns


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    def test_database_connection_error(self, mock_games_repo_class):
        """Test handling of database connection errors."""
        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup mock that raises exception
        mock_games_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_games_repo.get_pgn_text_by_id.side_effect = Exception(
            "Database connection failed")

        # Run the function
        game_id = "test_game"
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify error is handled gracefully
        assert result_game_id == game_id
        assert result_df is None

    @patch('scripts.analyze_games_tactics_parallel.detect_tactics_from_game')
    @patch('scripts.analyze_games_tactics_parallel.chess.pgn.read_game')
    @patch('scripts.analyze_games_tactics_parallel.GamesRepository')
    @patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository')
    def test_tactics_detection_error(
        self,
        mock_analyzed_repo_class,
        mock_games_repo_class,
        mock_read_game,
        mock_detect_tactics,
        sample_game_object,
        sample_pgn_text
    ):
        """Test handling of errors during tactics detection."""
        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup repository mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Setup game data
        game_id = "test_game"
        mock_games_repo.get_pgn_text_by_id.return_value = sample_pgn_text
        mock_read_game.return_value = sample_game_object

        # Setup tactics detection to raise an exception
        mock_detect_tactics.side_effect = Exception("Tactics detection failed")

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify error is handled gracefully
        assert result_game_id == game_id
        assert result_df is None


@pytest.mark.parametrize("pgn_text,expected_result", [
    ("", None),  # Empty PGN
    ("   ", None),  # Whitespace only PGN
    (None, None),  # None PGN
])
def test_invalid_pgn_inputs(pgn_text, expected_result):
    """Test various invalid PGN inputs."""
    with patch('scripts.analyze_games_tactics_parallel.GamesRepository') as mock_games_repo_class, \
            patch('scripts.analyze_games_tactics_parallel.Analyzed_tacticalsRepository') as mock_analyzed_repo_class:

        from scripts.analyze_games_tactics_parallel import analyze_game_parallel

        # Setup repository mocks
        mock_games_repo = Mock()
        mock_analyzed_repo = Mock()
        mock_games_repo_class.return_value = mock_games_repo
        mock_analyzed_repo_class.return_value = mock_analyzed_repo

        # Setup PGN data
        game_id = "test_game"
        mock_games_repo.get_pgn_text_by_id.return_value = pgn_text

        # Run the function
        result_game_id, result_df = analyze_game_parallel(game_id)

        # Verify results
        assert result_game_id == game_id
        assert result_df == expected_result
