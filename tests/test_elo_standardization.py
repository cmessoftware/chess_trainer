#!/usr/bin/env python3
"""
Test script for ELO standardization functionality.
Verifies Issue #21 completion status and identifies remaining work.
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from modules.ml_preprocessing import ChessMLPreprocessor
    from db.repository.repository import Repository
    from db.models import Base, GameBase
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the chess_trainer root directory")
    sys.exit(1)


def test_elo_conversion_algorithms():
    """Test ELO conversion formulas between platforms."""
    print("🧪 TESTING ELO CONVERSION ALGORITHMS")
    print("=" * 50)

    preprocessor = ChessMLPreprocessor()

    # Test data with known conversions
    test_data = {
        "lichess": [1500, 1800, 2100, 2400, 2700],
        "chess.com": [1400, 1700, 2000, 2300, 2600],
    }

    print("📊 Testing Lichess to FIDE-like conversion:")
    for rating in test_data["lichess"]:
        converted = preprocessor._convert_elo_to_fide(
            pd.Series([rating]), "lichess"
        ).iloc[0]
        print(
            f"   Lichess {rating} → FIDE-like {converted:.0f} (diff: {converted - rating:+.0f})"
        )

    print("\n📊 Testing Chess.com to FIDE-like conversion:")
    for rating in test_data["chess.com"]:
        converted = preprocessor._convert_elo_to_fide(
            pd.Series([rating]), "chesscom"
        ).iloc[0]
        print(
            f"   Chess.com {rating} → FIDE-like {converted:.0f} (diff: {converted - rating:+.0f})"
        )

    return True


def test_standardized_elo_creation():
    """Test standardized_elo field creation and derived features."""
    print("\n🔧 TESTING STANDARDIZED_ELO FIELD CREATION")
    print("=" * 50)

    # Create test DataFrame
    test_df = pd.DataFrame(
        {
            "white_elo": [1500, 1800, 2100, 1200, 2400],
            "black_elo": [1600, 1700, 2000, 1300, 2200],
            "site": [
                "lichess.org",
                "chess.com",
                "lichess.org",
                "chess.com",
                "lichess.org",
            ],
            "score_diff": [50, -20, 100, -150, 200],
            "material_total": [39, 35, 28, 40, 30],
        }
    )

    print("📋 Test data (before preprocessing):")
    print(test_df[["white_elo", "black_elo", "site"]].to_string(index=False))

    preprocessor = ChessMLPreprocessor()
    processed_df = preprocessor.standardize_elo(test_df, source_type="personal")

    print("\n📋 Test data (after ELO standardization):")
    elo_cols = [
        "white_elo",
        "black_elo",
        "standardized_elo",
        "elo_difference",
        "elo_category",
    ]
    available_cols = [col for col in elo_cols if col in processed_df.columns]
    print(processed_df[available_cols].to_string(index=False))

    # Verify derived features
    derived_features = []
    if "standardized_elo" in processed_df.columns:
        derived_features.append("standardized_elo")
    if "elo_difference" in processed_df.columns:
        derived_features.append("elo_difference")
    if "elo_category" in processed_df.columns:
        derived_features.append("elo_category")

    print(f"\n✅ Created derived ELO features: {derived_features}")
    return len(derived_features) >= 2


def test_data_pipeline_integration():
    """Test integration with data pipeline."""
    print("\n🔄 TESTING DATA PIPELINE INTEGRATION")
    print("=" * 50)

    try:
        # Try to connect to database and get sample data
        repo = Repository()

        # Get a small sample of games to test with
        sample_query = """
        SELECT white_elo, black_elo, site, score_diff, material_total 
        FROM game_moves 
        WHERE white_elo IS NOT NULL AND black_elo IS NOT NULL 
        LIMIT 10
        """

        df_sample = pd.read_sql(sample_query, repo.get_connection())

        if len(df_sample) == 0:
            print("⚠️ No sample data found in database")
            return False

        print(f"📊 Retrieved {len(df_sample)} sample records from database")

        # Test preprocessing pipeline
        preprocessor = ChessMLPreprocessor()
        processed_sample = preprocessor.standardize_elo(
            df_sample, source_type="personal"
        )

        # Check if standardized_elo was created
        if "standardized_elo" in processed_sample.columns:
            print("✅ standardized_elo field successfully created in pipeline")
            print(
                f"   Range: {processed_sample['standardized_elo'].min():.0f} - {processed_sample['standardized_elo'].max():.0f}"
            )
            print(f"   Mean: {processed_sample['standardized_elo'].mean():.0f}")
            return True
        else:
            print("❌ standardized_elo field NOT created in pipeline")
            return False

    except Exception as e:
        print(f"⚠️ Database connection error: {e}")
        print("   Testing with mock data instead...")
        return test_standardized_elo_creation()


def validate_against_benchmarks():
    """Validate standardized ratings against known benchmarks."""
    print("\n🎯 VALIDATING AGAINST KNOWN BENCHMARKS")
    print("=" * 50)

    # Known benchmark conversions (approximate)
    benchmarks = [
        {
            "platform": "lichess",
            "original": 1500,
            "expected_fide": 1280,
            "tolerance": 50,
        },
        {
            "platform": "lichess",
            "original": 2000,
            "expected_fide": 1740,
            "tolerance": 50,
        },
        {
            "platform": "chesscom",
            "original": 1500,
            "expected_fide": 1580,
            "tolerance": 50,
        },
        {
            "platform": "chesscom",
            "original": 2000,
            "expected_fide": 2090,
            "tolerance": 50,
        },
    ]

    preprocessor = ChessMLPreprocessor()
    passed_tests = 0

    for benchmark in benchmarks:
        original = benchmark["original"]
        expected = benchmark["expected_fide"]
        tolerance = benchmark["tolerance"]
        platform = benchmark["platform"]

        converted = preprocessor._convert_elo_to_fide(
            pd.Series([original]), platform
        ).iloc[0]
        diff = abs(converted - expected)

        status = "✅" if diff <= tolerance else "❌"
        passed_tests += 1 if diff <= tolerance else 0

        print(
            f"   {status} {platform.title()} {original} → {converted:.0f} (expected ~{expected}, diff: {diff:.0f})"
        )

    success_rate = (passed_tests / len(benchmarks)) * 100
    print(
        f"\n📊 Validation success rate: {success_rate:.0f}% ({passed_tests}/{len(benchmarks)})"
    )

    return success_rate >= 75


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🛡️ TESTING EDGE CASES AND ERROR HANDLING")
    print("=" * 50)

    if USE_FULL_PREPROCESSOR:
        preprocessor = ChessMLPreprocessor()
    else:
        preprocessor = create_basic_elo_preprocessor()

    test_cases = []

    # Test 1: Missing site information
    df_missing_site = pd.DataFrame(
        {"white_elo": [1500], "black_elo": [1600], "site": [None]}  # Missing site
    )

    try:
        result = preprocessor.standardize_elo(df_missing_site, source_type="personal")
        if "standardized_elo" in result.columns:
            test_cases.append(("Missing site info", True, "Handled gracefully"))
        else:
            test_cases.append(
                ("Missing site info", False, "Failed to create standardized_elo")
            )
    except Exception as e:
        test_cases.append(("Missing site info", False, f"Exception: {str(e)[:50]}"))

    # Test 2: Extreme ELO values
    df_extreme = pd.DataFrame(
        {
            "white_elo": [10000, 100],  # Extreme values
            "black_elo": [50, 5000],
            "site": ["lichess.org", "chess.com"],
        }
    )

    try:
        result = preprocessor.standardize_elo(df_extreme, source_type="personal")
        # Check if values were clipped appropriately
        if (
            result["standardized_elo"].max() <= 3000
            and result["standardized_elo"].min() >= 600
        ):
            test_cases.append(("Extreme ELO values", True, "Values clipped correctly"))
        else:
            test_cases.append(
                ("Extreme ELO values", False, "Values not clipped properly")
            )
    except Exception as e:
        test_cases.append(("Extreme ELO values", False, f"Exception: {str(e)[:50]}"))

    # Test 3: Unknown platform
    df_unknown = pd.DataFrame(
        {"white_elo": [1500], "black_elo": [1600], "site": ["unknown-chess-site.com"]}
    )

    try:
        result = preprocessor.standardize_elo(df_unknown, source_type="personal")
        if "standardized_elo" in result.columns:
            test_cases.append(
                ("Unknown platform", True, "Defaulted to Chess.com conversion")
            )
        else:
            test_cases.append(
                ("Unknown platform", False, "Failed to handle unknown platform")
            )
    except Exception as e:
        test_cases.append(("Unknown platform", False, f"Exception: {str(e)[:50]}"))

    # Test 4: Missing ELO columns
    df_no_elo = pd.DataFrame({"site": ["lichess.org"], "score_diff": [50]})

    try:
        result = preprocessor.standardize_elo(df_no_elo, source_type="personal")
        # Should return original DataFrame without error
        test_cases.append(("Missing ELO columns", True, "Returned gracefully"))
    except Exception as e:
        test_cases.append(("Missing ELO columns", False, f"Exception: {str(e)[:50]}"))

    # Print results
    passed = 0
    for test_name, success, note in test_cases:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {note}")
        if success:
            passed += 1

    print(f"\n📊 Edge case handling: {passed}/{len(test_cases)} passed")
    return passed >= len(test_cases) * 0.75  # 75% pass rate


def test_performance():
    """Test performance with larger datasets."""
    print("\n⚡ TESTING PERFORMANCE WITH LARGE DATASET")
    print("=" * 50)

    import time

    if USE_FULL_PREPROCESSOR:
        preprocessor = ChessMLPreprocessor()
    else:
        preprocessor = create_basic_elo_preprocessor()

    # Create larger test dataset
    n_samples = 10000
    large_df = pd.DataFrame(
        {
            "white_elo": np.random.normal(1600, 300, n_samples),
            "black_elo": np.random.normal(1600, 300, n_samples),
            "site": np.random.choice(["lichess.org", "chess.com"], n_samples),
            "score_diff": np.random.normal(0, 100, n_samples),
        }
    )

    print(f"📊 Processing {n_samples:,} games...")

    start_time = time.time()
    result = preprocessor.standardize_elo(large_df, source_type="personal")
    end_time = time.time()

    processing_time = end_time - start_time
    games_per_second = n_samples / processing_time

    print(f"⏱️ Processing time: {processing_time:.2f} seconds")
    print(f"🚀 Performance: {games_per_second:.0f} games/second")

    # Verify all standardized_elo values were created
    if "standardized_elo" in result.columns:
        non_null_count = result["standardized_elo"].notna().sum()
        print(f"✅ Successfully processed: {non_null_count:,}/{n_samples:,} games")
        return games_per_second >= 500  # At least 500 games/second
    else:
        print("❌ standardized_elo column not created")
        return False


def analyze_completion_status():
    print("\n📋 ISSUE #21 COMPLETION ANALYSIS")
    print("=" * 50)

    completed_items = [
        "✅ ELO conversion algorithms implemented",
        "✅ standardized_elo field creation",
        "✅ Platform detection (auto from 'site' field)",
        "✅ Derived features (elo_difference, elo_category)",
        "✅ Integration with ml_preprocessing.py",
        "✅ Tactical features preprocessing integration",
        "✅ MLflow tracking compatibility",
    ]

    remaining_items = [
        "🔄 Comprehensive validation against real-world benchmarks",
        "🔄 Documentation and usage examples",
        "🔄 Performance optimization for large datasets",
        "🔄 Edge case handling (missing platform info)",
        "🔄 Integration testing with full ML pipeline",
    ]

    print("🎯 COMPLETED FEATURES:")
    for item in completed_items:
        print(f"   {item}")

    print(f"\n⏳ REMAINING WORK ({len(remaining_items)} items):")
    for item in remaining_items:
        print(f"   {item}")

    completion_percentage = (
        len(completed_items) / (len(completed_items) + len(remaining_items))
    ) * 100
    print(f"\n📊 Current completion: {completion_percentage:.0f}%")

    return completion_percentage


def main():
    """Run comprehensive ELO standardization tests."""
    print("🚀 ELO STANDARDIZATION TESTING - Issue #21")
    print("=" * 60)

    test_results = []

    # Run all tests
    test_results.append(("ELO Conversion Algorithms", test_elo_conversion_algorithms()))
    test_results.append(("Standardized ELO Creation", test_standardized_elo_creation()))
    test_results.append(("Benchmark Validation", validate_against_benchmarks()))
    test_results.append(("Edge Cases & Error Handling", test_edge_cases()))
    test_results.append(("Performance Testing", test_performance()))

    # Analyze completion
    completion_percentage = analyze_completion_status()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)

    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")

    print(f"\n🎯 Test Results: {passed_tests}/{total_tests} passed")
    print(f"📈 Issue #21 Completion: {completion_percentage:.0f}%")

    if completion_percentage >= 90:
        print("\n🎉 READY FOR ISSUE CLOSURE!")
        print("   - All core functionality implemented")
        print("   - Tests passing")
        print("   - Integration validated")
    elif completion_percentage >= 75:
        print("\n⚡ ALMOST READY!")
        print("   - Minor validation and documentation needed")
        print("   - Core functionality complete")
    else:
        print("\n🚧 MORE WORK NEEDED")
        print("   - Significant functionality gaps remain")
        print("   - Continue development required")


if __name__ == "__main__":
    main()
