#!/usr/bin/env python3
"""
pytest configuration file for chess trainer tests.

Defines custom markers and fixtures for the test suite.
"""

import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, '/app/src')


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "parallel: marks tests related to parallel processing"
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set environment variables for testing
    test_env = {
        "PYTHONPATH": "/app/src",
        "CHESS_TRAINER_DB_URL": "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db",
        "STOCKFISH_PATH": "/usr/games/stockfish",
        "MAX_WORKERS": "2",
        "FEATURES_PER_CHUNK": "10",
        "PYTEST_CURRENT_TEST": "true"  # Signal that we're in test mode
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # Cleanup is automatic since we're just setting environment variables
