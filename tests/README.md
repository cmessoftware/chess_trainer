# Tests Directory

This directory contains all test scripts and utilities for the chess_trainer project. All tests have been centralized here for better organization and management.

## Test Runner

The comprehensive test runner script is located at `/app/tests/run_tests.sh` and can be used to execute any tests in the project.

### Usage

#### From the tests directory:
```bash
cd /app/tests
./run_tests.sh [OPTIONS] [TEST_PATTERN]
```

#### From the project root:
```bash
./tests/run_tests.sh [OPTIONS] [TEST_PATTERN]
```

### Available Options

**General Options:**
- `--coverage` - Run with code coverage reporting
- `--parallel` - Run tests in parallel (requires pytest-xdist)
- `--slow` - Run only tests marked as slow
- `--unit` - Run only unit tests
- `--integration` - Run only integration tests
- `--verbose` - Enable verbose output (-vvv)
- `--quiet` - Enable quiet output
- `--no-syntax-check` - Skip syntax checking

**Test Categories:**
- `--parallel-analysis` - Run parallel game analysis tests
- `--simple` - Run simple parallel analysis tests (recommended for quick testing)
- `--tactics` - Run tactical analysis tests
- `--batch-processing` - Run batch processing functionality tests
- `--features` - Run feature generation pipeline tests
- `--db` - Run database tests
- `--downloads` - Run download functionality tests
- `--exercises` - Run exercise generation tests
- `--all` - Run all tests

**Utility Options:**
- `--list` - List all available tests
- `--help` - Show help message

### Examples

```bash
# Run default tests (simple parallel analysis)
./tests/run_tests.sh

# Run only simple/fast tests
./tests/run_tests.sh --simple

# Run all parallel analysis tests
./tests/run_tests.sh --parallel-analysis

# Run specific test file
./tests/run_tests.sh test_classify_error_label.py

# Run all tests with coverage
./tests/run_tests.sh --all --coverage

# Run tactical tests with verbose output
./tests/run_tests.sh --tactics --verbose

# Run batch processing tests
./tests/run_tests.sh --batch-processing

# Run feature generation tests
./tests/run_tests.sh --features

# Run tests in parallel (faster execution)
./tests/run_tests.sh --all --parallel

# List all available tests
./tests/run_tests.sh --list
```

### Test Files Overview

**Parallel Analysis Tests:**
- `test_analyze_games_tactics_parallel_simple.py` - Comprehensive, well-maintained test suite ✅
- `test_analyze_games_tactics_parallel.py` - Original test suite (may have some failing tests)

**Core Functionality Tests:**
- `test_tactical_analysis.py` - Tactical pattern detection tests
- `test_classify_error_label.py` - Error classification tests ✅
- `test_tag_games.py` - Game tagging tests ✅
- `test_batch_processing_analyze_tactics.py` - Batch processing functionality tests ✅

**Pipeline Tests:**
- `test_generate_features_pipeline.py` - Feature generation pipeline tests ✅

**Database Tests:**
- `test_db_integrity.py` - Database structure and integrity tests
- `test_save_tacticals_tags.py` - Tactical data saving tests

**Download Tests:**
- `test_chesscom_download.py` - Chess.com download functionality
- `test_lichess_download.py` - Lichess download functionality

**Exercise Generation Tests:**
- `test_exercise_generation.py` - Exercise creation tests
- `test_generate_exercises.py` - Exercise generation pipeline tests
- `test_generate_training_dataset.py` - Training dataset generation tests

**Other Tests:**
- `test_elite_pipeline.py` - Elite player analysis pipeline tests
- `test_stockfish_eval.py` - Stockfish engine evaluation tests
- `test_tactics.py` - General tactical tests
- `test_analyze_errors.py` - Error analysis tests

### Environment Variables

The script automatically sets up the following environment variables:
- `PYTHONPATH="/app/src:$PYTHONPATH"`
- `CHESS_TRAINER_DB_URL="postgresql://chess:chess_pass@postgres:5432/chess_trainer_db"`
- `STOCKFISH_PATH="/usr/games/stockfish"`

### Requirements

The script will automatically install test requirements from `requirements_test.txt` if pytest is not found.

### Features

✅ **Centralized Testing** - All tests in one directory  
✅ **Path Independence** - Works from any directory  
✅ **Automatic Setup** - Sets up environment variables and paths  
✅ **Syntax Checking** - Validates module syntax  
✅ **Flexible Categories** - Run specific test types  
✅ **Individual Test Support** - Run specific test files  
✅ **Coverage Reporting** - Built-in coverage support  
✅ **Parallel Execution** - Fast parallel test execution  
✅ **Color Output** - Beautiful colored terminal output  
✅ **Error Handling** - Graceful error handling and reporting  

### Test Categories Explained

- **`--simple`**: Quick, reliable tests for core parallel analysis functionality
- **`--parallel-analysis`**: All tests related to parallel game analysis
- **`--tactics`**: Tests for tactical pattern recognition and analysis
- **`--batch-processing`**: Tests for batch processing functionality in pipeline steps
- **`--features`**: Tests for feature generation pipeline and related functionality
- **`--db`**: Database-related tests (integrity, saving, retrieval)
- **`--downloads`**: Tests for downloading games from chess platforms
- **`--exercises`**: Tests for exercise and training data generation
- **`--all`**: Complete test suite (may take longer to run)

---

*Last updated: June 30, 2025*
