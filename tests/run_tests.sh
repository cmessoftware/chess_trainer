#!/bin/bash

# Comprehensive Test Runner Script for chess_trainer project
# Usage: ./run_tests.sh [OPTIONS] [TEST_PATTERN]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
TEST_OPTIONS="-v --tb=short --color=yes"
TEST_FILES=""
SPECIFIC_TEST=""
RUN_SYNTAX_CHECK=true

echo -e "${BLUE}🧪 Chess Trainer - Comprehensive Test Runner${NC}"
echo "=============================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest is not installed. Installing test requirements...${NC}"
    pip install -r ../requirements_test.txt
fi

# Set environment variables for testing
export PYTHONPATH="/app/src:$PYTHONPATH"
export CHESS_TRAINER_DB_URL="postgresql://chess:chess_pass@postgres:5432/chess_trainer_db"
export STOCKFISH_PATH="/usr/games/stockfish"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            TEST_OPTIONS="$TEST_OPTIONS --cov=src --cov-report=html --cov-report=term"
            shift
            ;;
        --html-report)
            TEST_OPTIONS="$TEST_OPTIONS --html=test_reports/test_report_$(date +%Y%m%d_%H%M%S).html --self-contained-html"
            mkdir -p test_reports
            shift
            ;;
        --parallel)
            TEST_OPTIONS="$TEST_OPTIONS -n auto"
            shift
            ;;
        --slow)
            TEST_OPTIONS="$TEST_OPTIONS -m slow"
            shift
            ;;
        --unit)
            TEST_OPTIONS="$TEST_OPTIONS -m unit"
            shift
            ;;
        --integration)
            TEST_OPTIONS="$TEST_OPTIONS -m integration"
            shift
            ;;
        --verbose)
            TEST_OPTIONS="$TEST_OPTIONS -vvv"
            shift
            ;;
        --quiet)
            TEST_OPTIONS="$TEST_OPTIONS -q"
            shift
            ;;
        --no-syntax-check)
            RUN_SYNTAX_CHECK=false
            shift
            ;;
        # Specific test categories
        --parallel-analysis)
            TEST_FILES="tests/test_analyze_games_tactics_parallel*.py"
            shift
            ;;
        --simple)
            TEST_FILES="tests/test_analyze_games_tactics_parallel_simple.py"
            shift
            ;;
        --tactics)
            TEST_FILES="tests/test_tactical*.py tests/test_tactics.py"
            shift
            ;;
        --batch-processing)
            TEST_FILES="tests/test_batch_processing_analyze_tactics.py"
            shift
            ;;
        --db)
            TEST_FILES="tests/test_db*.py"
            shift
            ;;
        --downloads)
            TEST_FILES="tests/test_*download*.py"
            shift
            ;;
        --exercises)
            TEST_FILES="tests/test_*exercise*.py tests/test_generate*.py"
            shift
            ;;
        --export-dataset)
            TEST_FILES="tests/test_export_features_dataset.py tests/test_features_repository_export.py"
            shift
            ;;
        --features)
            TEST_FILES="tests/test_generate_features_pipeline.py"
            shift
            ;;
        --all)
            TEST_FILES="tests/test_*.py"
            shift
            ;;
        --list)
            echo -e "${CYAN}📋 Available test files:${NC}"
            cd /app
            find tests/ -name "test_*.py" -type f | sort
            echo ""
            echo -e "${CYAN}📊 Test categories:${NC}"
            echo "  --parallel-analysis  : Parallel game analysis tests"
            echo "  --simple            : Simple parallel analysis tests"
            echo "  --tactics           : Tactical analysis tests"
            echo "  --batch-processing  : Batch processing functionality tests"
            echo "  --features          : Feature generation pipeline tests"
            echo "  --db                : Database tests"
            echo "  --downloads         : Download functionality tests"
            echo "  --exercises         : Exercise generation tests"
            echo "  --export-dataset    : Dataset export functionality tests"
            echo "  --all               : All tests"
            exit 0
            ;;
        --help)
            echo "Usage: $0 [OPTIONS] [TEST_PATTERN]"
            echo ""
            echo "Options:"
            echo "  --coverage          Run with code coverage"
            echo "  --html-report       Generate HTML test report"
            echo "  --parallel          Run tests in parallel"
            echo "  --slow              Run only slow tests"
            echo "  --unit              Run only unit tests"
            echo "  --integration       Run only integration tests"
            echo "  --verbose           Verbose output"
            echo "  --quiet             Quiet output"
            echo "  --no-syntax-check   Skip syntax checking"
            echo ""
            echo "Test Categories:"
            echo "  --parallel-analysis Run parallel analysis tests"
            echo "  --simple            Run simple parallel analysis tests"
            echo "  --tactics           Run tactical analysis tests"
            echo "  --batch-processing  Run batch processing functionality tests"
            echo "  --features          Run feature generation pipeline tests"
            echo "  --db                Run database tests"
            echo "  --downloads         Run download tests"
            echo "  --exercises         Run exercise generation tests"
            echo "  --export-dataset    Run dataset export functionality tests"
            echo "  --all               Run all tests"
            echo ""
            echo "Utility:"
            echo "  --list              List all available tests"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --simple                    # Run simple tests only"
            echo "  $0 --all --coverage            # Run all tests with coverage"
            echo "  $0 --parallel-analysis --verbose  # Run parallel tests with verbose output"
            echo "  $0 --tactics --html-report     # Run tactical tests and generate HTML report"
            echo "  $0 --export-dataset --unit     # Run export dataset unit tests"
            echo "  $0 test_specific.py            # Run specific test file"
            echo "  $0 --tactics --parallel        # Run tactical tests in parallel"
            echo "  $0 --batch-processing          # Run batch processing tests"
            exit 0
            ;;
        test_*.py|*/test_*.py)
            # Direct test file specification
            SPECIFIC_TEST="$1"
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Determine what tests to run
if [[ -n "$SPECIFIC_TEST" ]]; then
    TEST_FILES="tests/$SPECIFIC_TEST"
    echo -e "${CYAN}🎯 Running specific test: $SPECIFIC_TEST${NC}"
elif [[ -z "$TEST_FILES" ]]; then
    # Default: run parallel analysis tests if no specific option given
    TEST_FILES="tests/test_analyze_games_tactics_parallel_simple.py"
    echo -e "${CYAN}🎯 Running default tests (simple parallel analysis)${NC}"
else
    echo -e "${CYAN}🎯 Running test category${NC}"
fi

echo -e "${YELLOW}🔧 Test configuration:${NC}"
echo "  PYTHONPATH: $PYTHONPATH"
echo "  TEST_OPTIONS: $TEST_OPTIONS"
echo "  TEST_FILES: $TEST_FILES"
echo ""

# Change to project root directory to run tests
cd /app

# Run the tests
HTML_REPORT_FILE=""
if [[ "$TEST_OPTIONS" == *"--html="* ]]; then
    # Extract HTML report filename from TEST_OPTIONS
    HTML_REPORT_FILE=$(echo "$TEST_OPTIONS" | grep -o '--html=[^ ]*' | cut -d'=' -f2)
fi

if [[ "$TEST_FILES" == *"*"* ]]; then
    # Handle wildcard patterns
    echo -e "${YELLOW}🚀 Running tests: $TEST_FILES${NC}"
    if bash -c "pytest $TEST_OPTIONS $TEST_FILES"; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        TEST_SUCCESS=true
    else
        echo -e "${RED}❌ Some tests failed!${NC}"
        TEST_SUCCESS=false
    fi
else
    # Handle specific files
    echo -e "${YELLOW}🚀 Running tests: $TEST_FILES${NC}"
    if pytest $TEST_OPTIONS $TEST_FILES; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        TEST_SUCCESS=true
    else
        echo -e "${RED}❌ Some tests failed!${NC}"
        TEST_SUCCESS=false
    fi
fi

# Run syntax check if enabled
if [[ "$RUN_SYNTAX_CHECK" == true ]]; then
    echo ""
    echo -e "${YELLOW}🔍 Running syntax checks...${NC}"
    
    # Check main modules
    SYNTAX_SUCCESS=true
    
    # Check analyze_games_tactics_parallel.py
    if python -m py_compile src/scripts/analyze_games_tactics_parallel.py 2>/dev/null; then
        echo -e "${GREEN}✅ analyze_games_tactics_parallel.py syntax OK${NC}"
    else
        echo -e "${RED}❌ analyze_games_tactics_parallel.py syntax error${NC}"
        SYNTAX_SUCCESS=false
    fi
    
    # Test batch processing parameter validation
    echo -e "${YELLOW}🔧 Testing batch processing parameter validation...${NC}"
    if python src/scripts/analyze_games_tactics_parallel.py --help >/dev/null 2>&1; then
        echo -e "${GREEN}✅ analyze_games_tactics_parallel.py parameters OK${NC}"
    else
        echo -e "${RED}❌ analyze_games_tactics_parallel.py parameter validation failed${NC}"
        SYNTAX_SUCCESS=false
    fi
    
    # Test pipeline script syntax
    if bash -n src/pipeline/run_pipeline.sh 2>/dev/null; then
        echo -e "${GREEN}✅ run_pipeline.sh syntax OK${NC}"
    else
        echo -e "${RED}❌ run_pipeline.sh syntax error${NC}"
        SYNTAX_SUCCESS=false
    fi
    
    # Test export dataset script syntax
    if [[ -f "src/scripts/export_features_dataset_parallel.py" ]]; then
        if python -m py_compile src/scripts/export_features_dataset_parallel.py 2>/dev/null; then
            echo -e "${GREEN}✅ export_features_dataset_parallel.py syntax OK${NC}"
        else
            echo -e "${RED}❌ export_features_dataset_parallel.py syntax error${NC}"
            SYNTAX_SUCCESS=false
        fi
        
        # Test export script parameter validation
        if python src/scripts/export_features_dataset_parallel.py --help >/dev/null 2>&1; then
            echo -e "${GREEN}✅ export_features_dataset_parallel.py parameters OK${NC}"
        else
            echo -e "${RED}❌ export_features_dataset_parallel.py parameter validation failed${NC}"
            SYNTAX_SUCCESS=false
        fi
    fi
    
    # Check other key modules
    for module in src/modules/tactical_analysis.py src/modules/analyze_games_tactics.py; do
        if [[ -f "$module" ]]; then
            if python -m py_compile "$module" 2>/dev/null; then
                echo -e "${GREEN}✅ $(basename $module) syntax OK${NC}"
            else
                echo -e "${RED}❌ $(basename $module) syntax error${NC}"
                SYNTAX_SUCCESS=false
            fi
        fi
    done
    
    if [[ "$SYNTAX_SUCCESS" == true ]]; then
        echo -e "${GREEN}✅ All syntax checks passed!${NC}"
    else
        echo -e "${RED}❌ Some syntax checks failed!${NC}"
    fi
else
    SYNTAX_SUCCESS=true
fi

# Final result
echo ""
echo "=============================================="
if [[ "$TEST_SUCCESS" == true && "$SYNTAX_SUCCESS" == true ]]; then
    echo -e "${GREEN}🎉 All checks completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some checks failed!${NC}"
    exit 1
fi
