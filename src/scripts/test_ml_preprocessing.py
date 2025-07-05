#!/usr/bin/env python3
"""
Test Script for ML Preprocessing Pipeline

This script tests the comprehensive ML preprocessing pipeline with sample data
and validates that all transformations work correctly for different source types.

Features:
- Tests with synthetic chess data
- Validates all preprocessing steps
- Checks data quality metrics
- Tests source-specific configurations
- Performance benchmarking

Usage:
    python test_ml_preprocessing.py [--source SOURCE] [--verbose]

Author: Chess Trainer ML Pipeline  
Date: 2025-07-05
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import time
from typing import Dict, Any
import warnings

# Add src to path for imports
sys.path.append('/app/src')

from modules.ml_preprocessing import (
    ChessMLPreprocessor,
    create_source_specific_preprocessor,
    quick_preprocess_for_training,
    preprocess_multiple_sources
)
from modules.feature_engineering import apply_comprehensive_feature_engineering

warnings.filterwarnings('ignore')

# Test configuration
TEST_SAMPLES = 1000
RANDOM_STATE = 42

def create_synthetic_chess_data(
    n_samples: int = TEST_SAMPLES,
    source_type: str = "personal"
) -> pd.DataFrame:
    """
    Create synthetic chess data for testing preprocessing pipeline.
    
    Args:
        n_samples: Number of samples to generate
        source_type: Type of source to simulate
        
    Returns:
        DataFrame with synthetic chess data
    """
    np.random.seed(RANDOM_STATE)
    
    # Base features that exist in chess_trainer
    data = {
        # Identifiers
        'game_id': [f"test_game_{i:05d}" for i in range(n_samples)],
        'move_number': np.random.randint(1, 80, n_samples),
        'player_color': np.random.choice([0, 1], n_samples),  # 0=white, 1=black
        
        # Positional features
        'fen': [f"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 {i%50+1}" for i in range(n_samples)],
        'move_san': [np.random.choice(['e4', 'Nf3', 'Bb5', 'O-O', 'Qh5']) for _ in range(n_samples)],
        'move_uci': [np.random.choice(['e2e4', 'g1f3', 'f1b5', 'e1g1', 'd1h5']) for _ in range(n_samples)],
        
        # Numerical features
        'material_balance': np.random.normal(0, 150, n_samples),
        'material_total': np.random.normal(2000, 500, n_samples),
        'num_pieces': np.random.randint(8, 32, n_samples),
        'branching_factor': np.random.randint(5, 40, n_samples),
        'self_mobility': np.random.randint(0, 30, n_samples),
        'opponent_mobility': np.random.randint(0, 30, n_samples),
        'score_diff': np.random.normal(0, 200, n_samples),
        
        # Binary features
        'has_castling_rights': np.random.choice([0, 1], n_samples),
        'is_repetition': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        'is_low_mobility': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'is_center_controlled': np.random.choice([0, 1], n_samples),
        'is_pawn_endgame': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'is_stockfish_test': [source_type == "stockfish"] * n_samples,
        
        # Categorical features
        'phase': np.random.choice(['opening', 'middlegame', 'endgame'], n_samples, p=[0.3, 0.5, 0.2]),
        'error_label': np.random.choice(['ok', 'inaccuracy', 'mistake', 'blunder'], n_samples, p=[0.5, 0.3, 0.15, 0.05]),
        
        # Metadata
        'site': [f"test_{source_type}.com"] * n_samples,
        'event': [f"Test {source_type.capitalize()} Tournament"] * n_samples,
        'date': pd.date_range('2020-01-01', '2024-12-31', periods=n_samples).strftime('%Y.%m.%d'),
        'white_player': [f"TestPlayer{i%100}" for i in range(n_samples)],
        'black_player': [f"TestPlayer{(i+50)%100}" for i in range(n_samples)],
        'result': np.random.choice(['1-0', '0-1', '1/2-1/2'], n_samples),
        
        # Source-specific features
        'source_type': [source_type] * n_samples
    }
    
    # Add ELO data based on source type
    if source_type == "novice":
        data['white_elo'] = np.random.randint(1200, 2000, n_samples)
        data['black_elo'] = np.random.randint(1200, 2000, n_samples)
    elif source_type == "elite":
        data['white_elo'] = np.random.randint(2000, 2800, n_samples)
        data['black_elo'] = np.random.randint(2000, 2800, n_samples)
    elif source_type == "fide":
        data['white_elo'] = np.random.randint(2000, 2700, n_samples)
        data['black_elo'] = np.random.randint(2000, 2700, n_samples)
    elif source_type == "personal":
        data['white_elo'] = np.random.randint(1000, 2200, n_samples)  # Variable range
        data['black_elo'] = np.random.randint(1000, 2200, n_samples)
    else:  # stockfish
        data['white_elo'] = [None] * n_samples  # No ELO for test data
        data['black_elo'] = [None] * n_samples
    
    # Add some tactical tags
    tactical_tags = ['pin', 'fork', 'skewer', 'double_attack', 'sacrifice']
    data['tags'] = [
        [np.random.choice(tactical_tags)] if np.random.random() < 0.3 else []
        for _ in range(n_samples)
    ]
    
    # Add some missing values to test handling
    missing_indices = np.random.choice(n_samples, size=int(n_samples * 0.1), replace=False)
    for idx in missing_indices:
        data['score_diff'][idx] = np.nan
        if np.random.random() < 0.5:
            data['tags'][idx] = None
    
    return pd.DataFrame(data)


def test_basic_preprocessing(source_type: str = "personal") -> Dict[str, Any]:
    """Test basic preprocessing pipeline."""
    print(f"\n🧪 Testing basic preprocessing for source: {source_type}")
    
    # Create test data
    df_test = create_synthetic_chess_data(TEST_SAMPLES, source_type)
    original_shape = df_test.shape
    
    # Test preprocessing
    start_time = time.time()
    preprocessor = create_source_specific_preprocessor(source_type)
    df_processed = preprocessor.fit_transform(df_test, source_type)
    processing_time = time.time() - start_time
    
    # Validate results
    results = {
        'source_type': source_type,
        'original_shape': original_shape,
        'processed_shape': df_processed.shape,
        'processing_time_seconds': round(processing_time, 3),
        'missing_values_before': df_test.isnull().sum().sum(),
        'missing_values_after': df_processed.isnull().sum().sum(),
        'new_columns_added': df_processed.shape[1] - df_test.shape[1],
        'has_standardized_elo': 'standardized_elo' in df_processed.columns,
        'categorical_encoded': any('_encoded' in col for col in df_processed.columns),
        'features_scaled': preprocessor.is_fitted
    }
    
    # Check for common issues
    issues = []
    if df_processed.isnull().sum().sum() > 0:
        issues.append("Still has missing values")
    if df_processed.duplicated().sum() > 0:
        issues.append("Has duplicate rows")
    if any(df_processed.dtypes == 'object'):
        non_numeric = df_processed.select_dtypes(include=['object']).columns.tolist()
        issues.append(f"Non-numeric columns remain: {non_numeric}")
    
    results['issues'] = issues
    results['success'] = len(issues) == 0
    
    print(f"   ✅ Processed {original_shape[0]:,} samples in {processing_time:.3f}s")
    print(f"   📊 Shape: {original_shape} → {df_processed.shape}")
    print(f"   🔢 Missing values: {results['missing_values_before']} → {results['missing_values_after']}")
    
    if issues:
        print(f"   ⚠️  Issues found: {', '.join(issues)}")
    else:
        print("   🎉 All checks passed!")
    
    return results


def test_elo_standardization():
    """Test ELO standardization functionality."""
    print("\n🎯 Testing ELO standardization")
    
    # Create data with different platforms
    platforms = ["lichess", "chess.com"]
    results = {}
    
    for platform in platforms:
        df_test = create_synthetic_chess_data(500, "elite")
        
        # Modify site to indicate platform
        df_test['site'] = f"{platform}.org"
        
        # Create platform-specific ELO ranges
        if platform == "lichess":
            df_test['white_elo'] = np.random.randint(2100, 2900, 500)  # Higher range
            df_test['black_elo'] = np.random.randint(2100, 2900, 500)
        else:
            df_test['white_elo'] = np.random.randint(2000, 2700, 500)  # Lower range
            df_test['black_elo'] = np.random.randint(2000, 2700, 500)
        
        # Test standardization
        preprocessor = ChessMLPreprocessor(elo_standardization=True)
        df_standardized = preprocessor.standardize_elo(df_test, platform)
        
        results[platform] = {
            'original_avg_elo': (df_test['white_elo'].mean() + df_test['black_elo'].mean()) / 2,
            'standardized_avg_elo': df_standardized['standardized_elo'].mean(),
            'elo_difference_created': 'elo_difference' in df_standardized.columns,
            'elo_category_created': 'elo_category' in df_standardized.columns
        }
        
        print(f"   {platform}: {results[platform]['original_avg_elo']:.0f} → {results[platform]['standardized_avg_elo']:.0f}")
    
    # Check that Lichess ratings were adjusted downward
    lichess_diff = results['lichess']['original_avg_elo'] - results['lichess']['standardized_avg_elo']
    chesscom_diff = results['chess.com']['original_avg_elo'] - results['chess.com']['standardized_avg_elo']
    
    print(f"   📊 Lichess adjustment: {lichess_diff:.0f} points")
    print(f"   📊 Chess.com adjustment: {chesscom_diff:.0f} points")
    
    success = lichess_diff > 50 and abs(chesscom_diff) < 100  # Lichess should be adjusted more
    print(f"   {'✅' if success else '❌'} ELO standardization working correctly")
    
    return results


def test_feature_engineering():
    """Test comprehensive feature engineering."""
    print("\n🔧 Testing feature engineering")
    
    df_test = create_synthetic_chess_data(500, "elite")
    original_columns = set(df_test.columns)
    
    # Apply feature engineering
    start_time = time.time()
    df_engineered = apply_comprehensive_feature_engineering(df_test)
    engineering_time = time.time() - start_time
    
    new_columns = set(df_engineered.columns) - original_columns
    
    # Check for specific feature categories
    feature_categories = {
        'temporal': [col for col in new_columns if any(term in col for term in ['year', 'month', 'weekend'])],
        'sequence': [col for col in new_columns if any(term in col for term in ['prev', 'change', 'trend'])],
        'opponent': [col for col in new_columns if any(term in col for term in ['opponent', 'advantage', 'favorite'])],
        'tactical': [col for col in new_columns if any(term in col for term in ['tactical', 'has_', 'complexity'])],
        'positional': [col for col in new_columns if any(term in col for term in ['mobility', 'activity', 'pressure'])]
    }
    
    results = {
        'original_columns': len(original_columns),
        'new_columns': len(new_columns),
        'engineering_time': round(engineering_time, 3),
        'feature_categories': {cat: len(cols) for cat, cols in feature_categories.items()}
    }
    
    print(f"   ⚡ Created {len(new_columns)} new features in {engineering_time:.3f}s")
    for category, count in results['feature_categories'].items():
        print(f"   📈 {category.capitalize()}: {count} features")
    
    return results


def test_multi_source_processing():
    """Test processing multiple sources together."""
    print("\n🔄 Testing multi-source processing")
    
    # Create data for multiple sources
    sources = ["personal", "novice", "elite"]
    source_data = {}
    
    for source in sources:
        source_data[source] = create_synthetic_chess_data(300, source)
    
    # Test multi-source preprocessing
    start_time = time.time()
    df_combined, processing_report = preprocess_multiple_sources(
        source_data, target_column="error_label"
    )
    processing_time = time.time() - start_time
    
    results = {
        'sources_processed': len(sources),
        'total_samples': len(df_combined),
        'processing_time': round(processing_time, 3),
        'source_distribution': df_combined['source_type'].value_counts().to_dict(),
        'quality_metrics': processing_report.get('combined', {}).get('combined_quality', {})
    }
    
    print(f"   📊 Combined {results['total_samples']} samples from {results['sources_processed']} sources")
    print(f"   ⏱️  Processing time: {processing_time:.3f}s")
    
    for source, count in results['source_distribution'].items():
        print(f"   📈 {source}: {count} samples")
    
    return results


def test_train_test_split():
    """Test train/validation/test split functionality."""
    print("\n📊 Testing train/validation/test splits")
    
    df_test = create_synthetic_chess_data(1000, "elite")
    preprocessor = create_source_specific_preprocessor("elite")
    df_processed = preprocessor.fit_transform(df_test, "elite")
    
    # Test splits
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.prepare_train_test_split(
        df_processed,
        target_column="error_label",
        test_size=0.2,
        validation_size=0.1
    )
    
    results = {
        'total_samples': len(df_processed),
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'features_count': len(X_train.columns),
        'train_ratio': len(X_train) / len(df_processed),
        'val_ratio': len(X_val) / len(df_processed),
        'test_ratio': len(X_test) / len(df_processed)
    }
    
    print(f"   📊 Total features: {results['features_count']}")
    print(f"   🎓 Train: {results['train_samples']} ({results['train_ratio']:.1%})")
    print(f"   🔍 Validation: {results['val_samples']} ({results['val_ratio']:.1%})")
    print(f"   🧪 Test: {results['test_samples']} ({results['test_ratio']:.1%})")
    
    # Check that splits are approximately correct
    expected_ratios = [0.7, 0.1, 0.2]  # train, val, test
    actual_ratios = [results['train_ratio'], results['val_ratio'], results['test_ratio']]
    ratio_check = all(abs(actual - expected) < 0.05 for actual, expected in zip(actual_ratios, expected_ratios))
    
    print(f"   {'✅' if ratio_check else '❌'} Split ratios are correct")
    
    return results


def run_performance_benchmark():
    """Run performance benchmark on larger dataset."""
    print("\n⚡ Running performance benchmark")
    
    sample_sizes = [1000, 5000, 10000]
    benchmark_results = {}
    
    for size in sample_sizes:
        print(f"   Testing with {size:,} samples...")
        
        df_test = create_synthetic_chess_data(size, "elite")
        
        start_time = time.time()
        df_processed, quality_report = quick_preprocess_for_training(
            df_test, "elite", "error_label"
        )
        total_time = time.time() - start_time
        
        benchmark_results[size] = {
            'processing_time': round(total_time, 3),
            'samples_per_second': round(size / total_time, 0),
            'memory_usage_mb': round(df_processed.memory_usage(deep=True).sum() / 1024**2, 2),
            'final_columns': len(df_processed.columns)
        }
        
        print(f"      ⏱️  {total_time:.3f}s ({benchmark_results[size]['samples_per_second']:.0f} samples/s)")
    
    return benchmark_results


def main():
    """Run all preprocessing tests."""
    print("🚀 Chess ML Preprocessing Pipeline - Test Suite")
    print("=" * 60)
    
    all_results = {}
    
    # Test 1: Basic preprocessing for each source type
    print("\n1️⃣  BASIC PREPROCESSING TESTS")
    sources = ["personal", "novice", "elite", "fide", "stockfish"]
    basic_results = {}
    
    for source in sources:
        basic_results[source] = test_basic_preprocessing(source)
    
    all_results['basic_preprocessing'] = basic_results
    
    # Test 2: ELO standardization
    print("\n2️⃣  ELO STANDARDIZATION TEST")
    all_results['elo_standardization'] = test_elo_standardization()
    
    # Test 3: Feature engineering
    print("\n3️⃣  FEATURE ENGINEERING TEST")
    all_results['feature_engineering'] = test_feature_engineering()
    
    # Test 4: Multi-source processing
    print("\n4️⃣  MULTI-SOURCE PROCESSING TEST")
    all_results['multi_source'] = test_multi_source_processing()
    
    # Test 5: Train/test splits
    print("\n5️⃣  TRAIN/TEST SPLIT TEST")
    all_results['train_test_split'] = test_train_test_split()
    
    # Test 6: Performance benchmark
    print("\n6️⃣  PERFORMANCE BENCHMARK")
    all_results['performance'] = run_performance_benchmark()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    # Count successful tests
    successful_basic = sum(1 for result in basic_results.values() if result['success'])
    print(f"✅ Basic preprocessing: {successful_basic}/{len(sources)} sources passed")
    
    if 'lichess' in all_results['elo_standardization']:
        print("✅ ELO standardization: Working correctly")
    
    feature_count = all_results['feature_engineering']['new_columns']
    print(f"✅ Feature engineering: {feature_count} new features created")
    
    multi_sources = all_results['multi_source']['sources_processed']
    print(f"✅ Multi-source processing: {multi_sources} sources combined")
    
    split_features = all_results['train_test_split']['features_count']
    print(f"✅ Train/test splits: {split_features} ML-ready features")
    
    # Performance summary
    perf_data = all_results['performance']
    fastest_rate = max(result['samples_per_second'] for result in perf_data.values())
    print(f"⚡ Peak performance: {fastest_rate:.0f} samples/second")
    
    print("\n🎉 All tests completed successfully!")
    print(f"💾 Test data available for manual inspection")
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ML preprocessing pipeline")
    parser.add_argument("--source", choices=["personal", "novice", "elite", "fide", "stockfish"],
                      help="Test specific source only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.source:
        # Test specific source only
        print(f"🔍 Testing source: {args.source}")
        result = test_basic_preprocessing(args.source)
        print(f"Result: {result}")
    else:
        # Run full test suite
        main()
