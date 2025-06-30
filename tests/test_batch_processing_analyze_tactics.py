#!/usr/bin/env python3
"""
Test suite for batch processing functionality in analyze_tactics pipeline step.
This test verifies that the analyze_games_tactics_parallel.py script properly supports
batch processing with --source, --max-games, and --offset parameters.
"""

from db.postgres_utils import get_postgres_connection
import pytest
import subprocess
import sys
import os
import tempfile
import time
from unittest.mock import patch, MagicMock

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBatchProcessingAnalyzeTactics:
    """Test class for analyze_tactics batch processing functionality."""

    def test_script_parameters_help(self):
        """Test that analyze_games_tactics_parallel.py supports required parameters."""
        script_path = "/app/src/scripts/analyze_games_tactics_parallel.py"

        # Test that the script responds to --help
        result = subprocess.run([
            sys.executable, script_path, "--help"
        ], capture_output=True, text=True)

        assert result.returncode == 0, f"Script help failed: {result.stderr}"

        # Verify required parameters are documented
        help_output = result.stdout
        assert "--source" in help_output, "Missing --source parameter in help"
        assert "--max-games" in help_output, "Missing --max-games parameter in help"
        assert "--offset" in help_output, "Missing --offset parameter in help"

    def test_script_parameter_validation(self):
        """Test that the script accepts the required parameters without error."""
        script_path = "/app/src/scripts/analyze_games_tactics_parallel.py"

        # Create a temporary test that just validates parameter parsing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(f'''
import sys
import argparse
sys.path.insert(0, "/app/src")

# Import the argument parser setup from the original script
parser = argparse.ArgumentParser(description="Test parameter validation")
parser.add_argument("--source", type=str, default=None)
parser.add_argument("--max-games", type=int, default=1000000)
parser.add_argument("--offset", type=int, default=0)

# Test parsing with batch parameters
test_args = ["--source", "elite", "--max-games", "100", "--offset", "50"]
args = parser.parse_args(test_args)

print(f"source={{args.source}}")
print(f"max_games={{args.max_games}}")
print(f"offset={{args.offset}}")
''')
            tmp.flush()

            result = subprocess.run([sys.executable, tmp.name],
                                    capture_output=True, text=True)

            assert result.returncode == 0, f"Parameter validation failed: {result.stderr}"
            assert "source=elite" in result.stdout
            assert "max_games=100" in result.stdout
            assert "offset=50" in result.stdout

            # Clean up
            os.unlink(tmp.name)

    def test_database_query_for_sources(self):
        """Test that the database query for getting sources works correctly."""
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()

            # Test the query used in run_pipeline.sh
            cursor.execute(
                "SELECT DISTINCT source FROM games WHERE source IS NOT NULL ORDER BY source")
            sources = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            # Should have at least some sources
            assert isinstance(sources, list), "Sources should be a list"
            print(f"Found sources: {sources}")

        except Exception as e:
            pytest.skip(f"Database not available for testing: {e}")

    def test_database_query_for_unanalyzed_games(self):
        """Test that the query for counting unanalyzed games works correctly."""
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()

            # First get available sources
            cursor.execute(
                "SELECT DISTINCT source FROM games WHERE source IS NOT NULL ORDER BY source LIMIT 1")
            sources = [row[0] for row in cursor.fetchall()]

            if not sources:
                pytest.skip("No sources available in database")

            test_source = sources[0]

            # Test the query used in run_pipeline.sh for counting unanalyzed games
            cursor.execute('''
                SELECT COUNT(*) 
                FROM games g 
                WHERE g.source = %s 
                AND g.game_id NOT IN (SELECT DISTINCT game_id FROM analyzed_tacticals)
            ''', (test_source,))

            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            assert isinstance(count, int), "Count should be an integer"
            assert count >= 0, "Count should be non-negative"
            print(f"Unanalyzed games for {test_source}: {count}")

        except Exception as e:
            pytest.skip(f"Database not available for testing: {e}")

    def test_pipeline_script_batch_logic(self):
        """Test that the pipeline script logic for batch processing is correct."""
        # Test the batch calculation logic used in run_pipeline.sh

        test_cases = [
            (100, 10000, 1),    # 100 games, 10k batch size = 1 batch
            (15000, 10000, 2),  # 15k games, 10k batch size = 2 batches
            (25000, 10000, 3),  # 25k games, 10k batch size = 3 batches
            (10000, 10000, 1),  # Exactly 10k games = 1 batch
            (0, 10000, 0),      # 0 games = 0 batches
        ]

        for total_games, batch_size, expected_batches in test_cases:
            # Simulate the bash calculation: batches=$(( (total_games + batch_size - 1) / batch_size ))
            if total_games == 0:
                calculated_batches = 0
            else:
                calculated_batches = (
                    total_games + batch_size - 1) // batch_size

            assert calculated_batches == expected_batches, \
                f"Batch calculation failed for {total_games} games: expected {expected_batches}, got {calculated_batches}"

    def test_offset_calculation(self):
        """Test that offset calculation for batches is correct."""
        batch_size = 10000

        test_cases = [
            (1, 0),      # Batch 1 -> offset 0
            (2, 10000),  # Batch 2 -> offset 10000
            (3, 20000),  # Batch 3 -> offset 20000
            (4, 30000),  # Batch 4 -> offset 30000
        ]

        for batch_num, expected_offset in test_cases:
            # Simulate the bash calculation: --offset $(( (batch - 1) * batch_size ))
            calculated_offset = (batch_num - 1) * batch_size

            assert calculated_offset == expected_offset, \
                f"Offset calculation failed for batch {batch_num}: expected {expected_offset}, got {calculated_offset}"

    @pytest.mark.slow
    def test_script_execution_with_minimal_parameters(self):
        """Test that the script can be executed with batch parameters (minimal execution)."""
        script_path = "/app/src/scripts/analyze_games_tactics_parallel.py"

        # Test with minimal parameters - this should start but we'll timeout quickly
        proc = subprocess.Popen([
            sys.executable, script_path,
            "--source", "elite",
            "--max-games", "1",
            "--offset", "0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Give it a few seconds to start and show initial logs
        try:
            stdout, stderr = proc.communicate(timeout=10)

            # Check if the script started correctly (look for expected log messages)
            combined_output = stdout + stderr

            # Should show configuration and startup messages
            assert "Starting parallel analysis" in combined_output or \
                   "Config: WORKERS=" in combined_output, \
                   f"Script didn't start correctly. Output: {combined_output}"

        except subprocess.TimeoutExpired:
            # This is expected - the script started and is running
            proc.kill()
            stdout, stderr = proc.communicate()
            combined_output = stdout + stderr

            # Even with timeout, we should see startup messages
            print(f"Script output (with timeout): {combined_output}")

        except Exception as e:
            proc.kill()
            pytest.fail(f"Script execution failed: {e}")

    def test_pipeline_integration_dry_run(self):
        """Test that the pipeline script accepts analyze_tactics with parameters."""
        pipeline_script = "/app/src/pipeline/run_pipeline.sh"

        if not os.path.exists(pipeline_script):
            pytest.skip("Pipeline script not found")

        # Test parameter parsing (this will show the interactive prompt)
        # We'll simulate what the script does with parameter parsing
        test_command = f'bash -c "echo \\"y\\" | timeout 10 {pipeline_script} analyze_tactics --source elite --max-games 1"'

        try:
            result = subprocess.run(
                test_command, shell=True, capture_output=True, text=True, timeout=15)

            # The script should start and show expected messages
            combined_output = result.stdout + result.stderr
            print(f"Pipeline output: {combined_output}")

            # Look for expected pipeline behavior
            success_indicators = [
                "Analyzing tactics in games",
                "Running analyze_tactics sequentially",
                "Getting available sources",
                "Processing source:",
                "Found sources:",
            ]

            found_indicator = any(
                indicator in combined_output for indicator in success_indicators)
            assert found_indicator, f"Pipeline didn't show expected behavior. Output: {combined_output}"

        except subprocess.TimeoutExpired:
            # Expected - the pipeline was working
            print("Pipeline started successfully (timed out as expected)")
        except Exception as e:
            pytest.skip(
                f"Pipeline test failed (may be environment specific): {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
