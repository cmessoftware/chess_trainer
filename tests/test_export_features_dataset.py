#!/usr/bin/env python3
"""
Unit tests for export_features_dataset_parallel.py module.

Tests the export functionality for features datasets, including:
- Individual source exports
- Parallel processing
- Filter validation
- File output verification
- Error handling
"""

from db.repository.features_repository import FeaturesRepository
from scripts.export_features_dataset_parallel import (
    export_features_to_dataset,
    export_features_for_source,
    export_all_sources_parallel,
    EXPORT_DIR,
    SOURCES
)
import pytest
import os
import tempfile
import shutil
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ProcessPoolExecutor

# Import the modules to test
import sys
sys.path.insert(0, '/app/src')


class TestExportFeaturesDataset:
    """Test class for export features dataset functionality."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create a temporary directory for export tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_features_repo(self):
        """Mock FeaturesRepository for testing."""
        repo = Mock(spec=FeaturesRepository)
        return repo

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'game_id': [1, 1, 2, 2, 3],
            'move_number': [1, 2, 1, 2, 1],
            'player_color': ['white', 'black', 'white', 'black', 'white'],
            'fen': ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'] * 5,
            'move_san': ['e4', 'e5', 'd4', 'd5', 'Nf3'],
            'material_balance': [0, 0, 0, 0, 0],
            'white_elo': [1500, 1500, 1600, 1600, 1700],
            'black_elo': [1450, 1450, 1550, 1550, 1650],
            'source': ['elite', 'elite', 'personal', 'personal', 'stockfish']
        })

    @pytest.mark.unit
    def test_export_features_to_dataset_success(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test successful export of features to dataset."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_export")
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                file_type="parquet"
            )

        # Assert
        expected_file = output_path + ".parquet"
        assert os.path.exists(expected_file)

        # Verify the exported data
        exported_df = pd.read_parquet(expected_file)
        assert len(exported_df) == len(sample_dataframe)
        assert list(exported_df.columns) == list(sample_dataframe.columns)

        # Verify repository was called with correct parameters
        mock_features_repo.get_features_with_filters.assert_called_once_with(
            "elite",
            player_name=None,
            opening=None,
            min_elo=None,
            max_elo=None,
            limit=None
        )

    @pytest.mark.unit
    def test_export_features_to_dataset_csv_format(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test export in CSV format."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_export_csv")
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="personal",
                output_path=output_path,
                file_type="csv"
            )

        # Assert
        expected_file = output_path + ".csv"
        assert os.path.exists(expected_file)

        # Verify the exported data
        exported_df = pd.read_csv(expected_file)
        assert len(exported_df) == len(sample_dataframe)

    @pytest.mark.unit
    def test_export_features_to_dataset_with_filters(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test export with various filters applied."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_export_filtered")
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                player="Carlsen",
                opening="e4",
                min_elo=1500,
                max_elo=2000,
                limit=100,
                file_type="parquet"
            )

        # Assert
        mock_features_repo.get_features_with_filters.assert_called_once_with(
            "elite",
            player_name="Carlsen",
            opening="e4",
            min_elo=1500,
            max_elo=2000,
            limit=100
        )

    @pytest.mark.unit
    def test_export_features_to_dataset_no_data(self, temp_export_dir, mock_features_repo):
        """Test behavior when no data is found."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_export_empty")
        mock_features_repo.get_features_with_filters.return_value = None

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="nonexistent",
                output_path=output_path,
                file_type="parquet"
            )

        # Assert
        expected_file = output_path + ".parquet"
        assert not os.path.exists(expected_file)

    @pytest.mark.unit
    def test_export_features_to_dataset_empty_dataframe(self, temp_export_dir, mock_features_repo):
        """Test behavior with empty DataFrame."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_export_empty_df")
        empty_df = pd.DataFrame()
        mock_features_repo.get_features_with_filters.return_value = empty_df

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                file_type="parquet"
            )

        # Assert
        expected_file = output_path + ".parquet"
        assert os.path.exists(expected_file)

        # Verify the file is empty
        exported_df = pd.read_parquet(expected_file)
        assert len(exported_df) == 0

    @pytest.mark.unit
    def test_export_features_for_source(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test export for a single source."""
        # Arrange
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo), \
                patch('scripts.export_features_dataset_parallel.EXPORT_DIR', temp_export_dir):

            # Act
            export_features_for_source("elite")

        # Assert
        expected_file = os.path.join(
            temp_export_dir, "elite", "features.parquet")
        assert os.path.exists(expected_file)

    @pytest.mark.unit
    def test_export_features_directory_creation(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test that output directories are created properly."""
        # Arrange
        nested_path = os.path.join(
            temp_export_dir, "deep", "nested", "path", "test_export")
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=nested_path,
                file_type="parquet"
            )

        # Assert
        assert os.path.exists(os.path.dirname(nested_path))
        assert os.path.exists(nested_path + ".parquet")

    @pytest.mark.unit
    def test_export_features_to_dataset_database_error(self, temp_export_dir, mock_features_repo):
        """Test handling of database errors during export."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_export_error")
        mock_features_repo.get_features_with_filters.side_effect = Exception(
            "Database connection failed")

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act & Assert
            with pytest.raises(Exception, match="Database connection failed"):
                export_features_to_dataset(
                    source="elite",
                    output_path=output_path,
                    file_type="parquet"
                )

    @pytest.mark.integration
    @patch('scripts.export_features_dataset_parallel.ProcessPoolExecutor')
    def test_export_all_sources_parallel_execution(self, mock_executor):
        """Test that parallel execution is called with correct sources."""
        # Arrange
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        # Act
        export_all_sources_parallel()

        # Assert
        mock_executor.assert_called_once()
        mock_executor_instance.map.assert_called_once()

        # Verify that map was called with the export function and SOURCES
        args, kwargs = mock_executor_instance.map.call_args
        assert len(args) == 2
        assert args[1] == SOURCES

    @pytest.mark.unit
    def test_constants_configuration(self):
        """Test that module constants are properly configured."""
        # Assert
        assert isinstance(EXPORT_DIR, str)
        assert isinstance(SOURCES, list)
        assert len(SOURCES) > 0
        assert "elite" in SOURCES
        assert "personal" in SOURCES

    @pytest.mark.unit
    def test_export_features_with_special_characters(self, temp_export_dir, mock_features_repo):
        """Test export with special characters in filters."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_special_chars")
        sample_df = pd.DataFrame({
            'game_id': [1],
            'player_color': ['white'],
            'white_player': ['José María']
        })
        mock_features_repo.get_features_with_filters.return_value = sample_df

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                player="José María",
                opening="Sicilian",
                file_type="parquet"
            )

        # Assert
        mock_features_repo.get_features_with_filters.assert_called_once_with(
            "elite",
            player_name="José María",
            opening="Sicilian",
            min_elo=None,
            max_elo=None,
            limit=None
        )

    @pytest.mark.unit
    def test_export_features_large_dataset(self, temp_export_dir, mock_features_repo):
        """Test export with a large dataset."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_large_dataset")
        # Create a larger dataset for testing
        large_df = pd.DataFrame({
            'game_id': range(1000),
            'move_number': [i % 50 for i in range(1000)],
            'player_color': ['white' if i % 2 == 0 else 'black' for i in range(1000)],
            'fen': ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'] * 1000,
            'source': ['elite'] * 1000
        })
        mock_features_repo.get_features_with_filters.return_value = large_df

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                file_type="parquet"
            )

        # Assert
        expected_file = output_path + ".parquet"
        assert os.path.exists(expected_file)

        exported_df = pd.read_parquet(expected_file)
        assert len(exported_df) == 1000

    @pytest.mark.slow
    @pytest.mark.integration
    def test_export_all_sources_integration(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Integration test for exporting all sources."""
        # Arrange
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo), \
                patch('scripts.export_features_dataset_parallel.EXPORT_DIR', temp_export_dir):

            # Act
            export_all_sources_parallel()

        # Assert
        for source in SOURCES:
            expected_file = os.path.join(
                temp_export_dir, source, "features.parquet")
            assert os.path.exists(
                expected_file), f"File not found for source: {source}"

    @pytest.mark.unit
    def test_export_features_invalid_file_type(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test behavior with invalid file type."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_invalid_type")
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                file_type="invalid_format"
            )

        # Assert - should not create any file for invalid format
        assert not os.path.exists(output_path + ".invalid_format")
        assert not os.path.exists(output_path + ".parquet")
        assert not os.path.exists(output_path + ".csv")

    @pytest.mark.unit
    def test_export_features_path_validation(self, mock_features_repo, sample_dataframe):
        """Test that invalid paths are handled gracefully."""
        # Arrange
        invalid_path = "/invalid/non/existent/deeply/nested/path/test_export"
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act & Assert - should create the directory structure
            export_features_to_dataset(
                source="elite",
                output_path=invalid_path,
                file_type="parquet"
            )

            # The function should create the directory and file
            assert os.path.exists(invalid_path + ".parquet")

            # Cleanup
            import shutil
            shutil.rmtree("/invalid", ignore_errors=True)


# Additional test class for edge cases and error conditions
class TestExportFeaturesDatasetEdgeCases:
    """Test edge cases and error conditions for export functionality."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create a temporary directory for export tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_features_repo(self):
        """Mock FeaturesRepository for testing."""
        repo = Mock(spec=FeaturesRepository)
        return repo

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'game_id': [1, 1, 2, 2, 3],
            'move_number': [1, 2, 1, 2, 1],
            'player_color': ['white', 'black', 'white', 'black', 'white'],
            'fen': ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'] * 5,
            'move_san': ['e4', 'e5', 'd4', 'd5', 'Nf3'],
            'material_balance': [0, 0, 0, 0, 0],
            'white_elo': [1500, 1500, 1600, 1600, 1700],
            'black_elo': [1450, 1450, 1550, 1550, 1650],
            'source': ['elite', 'elite', 'personal', 'personal', 'stockfish']
        })

    @pytest.mark.unit
    def test_export_with_none_parameters(self):
        """Test export with None parameters."""
        with patch('scripts.export_features_dataset_parallel.FeaturesRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_features_with_filters.return_value = None
            mock_repo_class.return_value = mock_repo

            # Act
            result = export_features_to_dataset(
                source=None,
                output_path=None,
                file_type="parquet"
            )

            # Assert - function should handle None gracefully
            assert result is None

    @pytest.mark.unit
    def test_export_source_parameter_validation(self):
        """Test validation of source parameter."""
        # Test that function accepts valid sources
        valid_sources = ["personal", "novice", "elite", "stockfish", "fide"]

        for source in valid_sources:
            with patch('scripts.export_features_dataset_parallel.FeaturesRepository') as mock_repo_class:
                mock_repo = Mock()
                mock_repo.get_features_with_filters.return_value = None
                mock_repo_class.return_value = mock_repo

                # Should not raise an exception
                export_features_to_dataset(
                    source=source,
                    output_path="/tmp/test",
                    file_type="parquet"
                )

    @pytest.mark.unit
    def test_export_elo_filter_validation(self, temp_export_dir, mock_features_repo, sample_dataframe):
        """Test ELO filter validation."""
        # Arrange
        output_path = os.path.join(temp_export_dir, "test_elo_validation")
        mock_features_repo.get_features_with_filters.return_value = sample_dataframe

        with patch('scripts.export_features_dataset_parallel.FeaturesRepository', return_value=mock_features_repo):
            # Act - test with min_elo > max_elo (edge case)
            export_features_to_dataset(
                source="elite",
                output_path=output_path,
                min_elo=2000,
                max_elo=1500,  # This is logically inconsistent
                file_type="parquet"
            )

        # Assert - function should still work (validation is in repository layer)
        mock_features_repo.get_features_with_filters.assert_called_once_with(
            "elite",
            player_name=None,
            opening=None,
            min_elo=2000,
            max_elo=1500,
            limit=None
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
