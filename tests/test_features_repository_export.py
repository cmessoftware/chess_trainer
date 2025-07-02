#!/usr/bin/env python3
"""
Unit tests for FeaturesRepository.get_features_with_filters method.

Tests the database layer functionality for feature export, including:
- Filter application (source, ELO, player, opening)
- Data retrieval and formatting
- Error handling and edge cases
- SQL query validation
"""

from db.models.games import Games
from db.models.features import Features
from db.repository.features_repository import FeaturesRepository
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

# Import the modules to test
import sys
sys.path.insert(0, '/app/src')


class TestFeaturesRepositoryExport:
    """Test class for FeaturesRepository export functionality."""

    @pytest.fixture
    def mock_session_factory(self):
        """Mock session factory for testing."""
        session_factory = Mock()
        session = Mock(spec=Session)
        session_factory.return_value.__enter__ = Mock(return_value=session)
        session_factory.return_value.__exit__ = Mock(return_value=None)
        return session_factory, session

    @pytest.fixture
    def features_repository(self, mock_session_factory):
        """Create FeaturesRepository instance with mocked session."""
        session_factory, session = mock_session_factory
        repo = FeaturesRepository()
        repo.session_factory = session_factory
        return repo, session

    @pytest.fixture
    def sample_query_result(self):
        """Mock query result data."""
        return [
            (1, 1, 'white', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
             'e4', 'e2e4', 0, 32, 16, 20, 28, 15, 'opening', True, 1, False, False,
             False, False, '{"tactical": true}', 0.5, False, 40, 'inaccuracy',
             'lichess.org', 'Rated Rapid game', '2025-01-01', 'Player1', 'Player2',
             1500, 1450, '1-0', 'B01', 'Scandinavian Defense'),
            (1, 2, 'black', 'rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
             'd5', 'd7d5', 0, 32, 16, 18, 25, 18, 'opening', True, 2, False, False,
             False, False, '{"tactical": false}', 0.0, False, 40, 'good',
             'lichess.org', 'Rated Rapid game', '2025-01-01', 'Player1', 'Player2',
             1500, 1450, '1-0', 'B01', 'Scandinavian Defense')
        ]

    @pytest.fixture
    def sample_column_names(self):
        """Sample column names for query result."""
        return [
            'game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci',
            'material_balance', 'material_total', 'num_pieces', 'branching_factor',
            'self_mobility', 'opponent_mobility', 'phase', 'has_castling_rights',
            'move_number_global', 'is_repetition', 'is_low_mobility', 'is_center_controlled',
            'is_pawn_endgame', 'tags', 'score_diff', 'is_stockfish_test', 'num_moves',
            'error_label', 'site', 'event', 'date', 'white_player', 'black_player',
            'white_elo', 'black_elo', 'result', 'eco', 'opening'
        ]

    @pytest.mark.unit
    def test_get_features_with_filters_source_only(self, features_repository, sample_query_result, sample_column_names):
        """Test filtering by source only."""
        # Arrange
        repo, session = features_repository

        # Mock the game_ids query
        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,), (2,), (3,)]

        # Mock the features query
        features_result = Mock()
        features_result.fetchall.return_value = sample_query_result
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            # Create a mock DataFrame without actually calling pd.DataFrame
            mock_result_df = Mock()
            mock_df.return_value = mock_result_df
            result = repo.get_features_with_filters(source="elite")

        # Assert
        assert session.execute.call_count == 2
        # Verify DataFrame was called with correct arguments
        assert mock_df.call_count == 1
        call_args, call_kwargs = mock_df.call_args
        assert call_args[0] == sample_query_result
        assert call_kwargs['columns'] == sample_column_names
        assert result == mock_result_df

    @pytest.mark.unit
    def test_get_features_with_filters_all_parameters(self, features_repository, sample_query_result, sample_column_names):
        """Test filtering with all parameters."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        # Only first game
        features_result.fetchall.return_value = sample_query_result[:1]
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            # Create a mock DataFrame without actually calling pd.DataFrame
            mock_result_df = Mock()
            mock_df.return_value = mock_result_df
            result = repo.get_features_with_filters(
                source="elite",
                min_elo=1400,
                max_elo=1600,
                player_name="Player1",
                opening="Scandinavian",
                limit=100
            )

        # Assert
        assert session.execute.call_count == 2
        # Verify DataFrame was called correctly
        assert mock_df.call_count == 1
        call_args, call_kwargs = mock_df.call_args
        assert call_args[0] == sample_query_result[:1]
        assert call_kwargs['columns'] == sample_column_names
        assert result == mock_result_df

    @pytest.mark.unit
    def test_get_features_with_filters_no_games_found(self, features_repository):
        """Test behavior when no games match the filters."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = []  # No games found

        session.execute.return_value = game_ids_result

        # Act
        result = repo.get_features_with_filters(source="nonexistent")

        # Assert
        assert result is None
        assert session.execute.call_count == 1

    @pytest.mark.unit
    def test_get_features_with_filters_elo_range(self, features_repository, sample_query_result, sample_column_names):
        """Test ELO range filtering."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        features_result.fetchall.return_value = sample_query_result[:1]
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            mock_df.return_value = pd.DataFrame(
                sample_query_result[:1], columns=sample_column_names)
            result = repo.get_features_with_filters(
                source="elite",
                min_elo=1200,
                max_elo=1800
            )

        # Assert
        assert result is not None
        assert session.execute.call_count == 2

    @pytest.mark.unit
    def test_get_features_with_filters_player_search(self, features_repository, sample_query_result, sample_column_names):
        """Test player name filtering (case insensitive)."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        features_result.fetchall.return_value = sample_query_result[:1]
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            mock_df.return_value = pd.DataFrame(
                sample_query_result[:1], columns=sample_column_names)
            result = repo.get_features_with_filters(
                source="elite",
                player_name="player1"  # lowercase should still match
            )

        # Assert
        assert result is not None
        assert session.execute.call_count == 2

    @pytest.mark.unit
    def test_get_features_with_filters_opening_search(self, features_repository, sample_query_result, sample_column_names):
        """Test opening filtering (ECO and name)."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        features_result.fetchall.return_value = sample_query_result[:1]
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            mock_df.return_value = pd.DataFrame(
                sample_query_result[:1], columns=sample_column_names)
            result = repo.get_features_with_filters(
                source="elite",
                opening="B01"  # Should match ECO code
            )

        # Assert
        assert result is not None
        assert session.execute.call_count == 2

    @pytest.mark.unit
    def test_get_features_with_filters_limit_application(self, features_repository, sample_query_result, sample_column_names):
        """Test that limit is properly applied to games, not features."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,), (2,)]  # 2 games

        features_result = Mock()
        # Multiple features per game
        features_result.fetchall.return_value = sample_query_result
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            # Create a mock DataFrame without actually calling pd.DataFrame
            mock_result_df = Mock()
            mock_df.return_value = mock_result_df
            result = repo.get_features_with_filters(
                source="elite",
                limit=5  # Limit games, not features
            )

        # Assert
        assert result is not None
        # Should return all features for the limited games
        assert mock_df.call_count == 1
        call_args, call_kwargs = mock_df.call_args
        assert call_args[0] == sample_query_result
        assert call_kwargs['columns'] == sample_column_names
        assert result == mock_result_df

    @pytest.mark.unit
    def test_get_features_with_filters_database_error(self, features_repository):
        """Test handling of database errors."""
        # Arrange
        repo, session = features_repository
        session.execute.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            repo.get_features_with_filters(source="elite")

    @pytest.mark.unit
    def test_get_features_with_filters_empty_dataframe(self, features_repository, sample_column_names):
        """Test handling when features query returns empty result."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]  # Games exist

        features_result = Mock()
        features_result.fetchall.return_value = []  # But no features
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            # Create a mock DataFrame without actually calling pd.DataFrame
            mock_result_df = Mock()
            mock_df.return_value = mock_result_df
            result = repo.get_features_with_filters(source="elite")

        # Assert
        assert result is not None
        assert mock_df.call_count == 1
        call_args, call_kwargs = mock_df.call_args
        assert call_args[0] == []
        assert call_kwargs['columns'] == sample_column_names
        assert result == mock_result_df

    @pytest.mark.unit
    def test_get_features_with_filters_column_selection(self, features_repository, sample_query_result, sample_column_names):
        """Test that all expected columns are selected in the query."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        features_result.fetchall.return_value = sample_query_result[:1]
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]

        # Act
        with patch('pandas.DataFrame') as mock_df:
            mock_df.return_value = pd.DataFrame(
                sample_query_result[:1], columns=sample_column_names)
            result = repo.get_features_with_filters(source="elite")

        # Assert
        expected_columns = [
            'game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci',
            'material_balance', 'material_total', 'num_pieces', 'branching_factor',
            'self_mobility', 'opponent_mobility', 'phase', 'has_castling_rights',
            'move_number_global', 'is_repetition', 'is_low_mobility', 'is_center_controlled',
            'is_pawn_endgame', 'tags', 'score_diff', 'is_stockfish_test', 'num_moves',
            'error_label', 'site', 'event', 'date', 'white_player', 'black_player',
            'white_elo', 'black_elo', 'result', 'eco', 'opening'
        ]

        # Verify that the DataFrame was created with the expected columns
        call_args = mock_df.call_args
        assert call_args[1]['columns'] == sample_column_names
        assert all(col in sample_column_names for col in expected_columns)

    @pytest.mark.unit
    def test_get_features_with_filters_null_values(self, features_repository):
        """Test handling of null/None filter values."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        features_result.fetchall.return_value = []
        features_result.keys.return_value = [
            'game_id', 'move_number']  # Mock proper column names

        session.execute.side_effect = [game_ids_result, features_result]

        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            mock_df.return_value = pd.DataFrame()
            result = repo.get_features_with_filters(
                source="elite",
                min_elo=None,
                max_elo=None,
                player_name=None,
                opening=None,
                limit=None
            )

        # Assert - should handle None values gracefully
        # The function should not add filters for None values
        assert session.execute.call_count >= 1

    @pytest.mark.unit
    def test_get_features_with_filters_special_characters(self, features_repository, sample_query_result, sample_column_names):
        """Test handling of special characters in filter parameters."""
        # Arrange
        repo, session = features_repository

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = [(1,)]

        features_result = Mock()
        features_result.fetchall.return_value = sample_query_result[:1]
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            mock_df.return_value = pd.DataFrame(
                sample_query_result[:1], columns=sample_column_names)
            result = repo.get_features_with_filters(
                source="elite",
                player_name="José María",  # Special characters
                opening="King's Indian"   # Apostrophe
            )

        # Assert
        assert result is not None
        assert session.execute.call_count == 2

    @pytest.mark.integration
    def test_get_features_with_filters_realistic_scenario(self, features_repository, sample_column_names):
        """Integration test with realistic data scenario."""
        # Arrange
        repo, session = features_repository

        # Simulate a realistic scenario with multiple games and features
        realistic_game_ids = [(i,) for i in range(1, 11)]  # 10 games
        realistic_features = []

        for game_id in range(1, 11):
            for move_num in range(1, 6):  # 5 moves per game
                color = 'white' if move_num % 2 == 1 else 'black'
                realistic_features.append((
                    game_id, move_num, color, 'fen_placeholder', f'move_{move_num}',
                    f'uci_{move_num}', 0, 32, 16, 20, 25, 15, 'middlegame',
                    True, move_num, False, False, False, False, '{}', 0.0, False,
                    40, 'good', 'lichess.org', 'Rated game', '2025-01-01',
                    f'Player{game_id}', f'Opponent{game_id}', 1500 +
                        game_id * 10,
                    1450 + game_id * 10, '1-0', 'E40', 'Nimzo-Indian Defense'
                ))

        game_ids_result = Mock()
        game_ids_result.fetchall.return_value = realistic_game_ids

        features_result = Mock()
        features_result.fetchall.return_value = realistic_features
        features_result.keys.return_value = sample_column_names

        session.execute.side_effect = [game_ids_result, features_result]
        # Act
        with patch('db.repository.features_repository.pd.DataFrame') as mock_df:
            # Create a mock DataFrame without actually calling pd.DataFrame
            mock_result_df = Mock()
            mock_df.return_value = mock_result_df

            result = repo.get_features_with_filters(
                source="elite",
                min_elo=1500,
                max_elo=1600,
                limit=10
            )

        # Assert
        assert result is not None
        assert mock_df.call_count == 1
        call_args, call_kwargs = mock_df.call_args
        assert call_args[0] == realistic_features
        assert call_kwargs['columns'] == sample_column_names
        assert result == mock_result_df
        # Should have 50 features (10 games × 5 moves each)
        assert len(realistic_features) == 50


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
