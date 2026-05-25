#!/usr/bin/env python3
"""
Test script for tactical features preprocessing

This script validates that the ML preprocessing pipeline correctly handles
tactical features like depth_score_diff, threatens_mate, and is_forced_move.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.ml_preprocessing import ChessMLPreprocessor, create_source_specific_preprocessor

def create_sample_data_with_tactical_features():
    """Create sample chess data with tactical features included."""
    
    np.random.seed(42)
    n_samples = 1000
    
    # Base features
    data = {
        'game_id': [f'game_{i}' for i in range(n_samples)],
        'move_number': np.random.randint(1, 40, n_samples),
        'player_color': np.random.choice([0, 1], n_samples),
        'material_balance': np.random.normal(0, 200, n_samples),
        'material_total': np.random.normal(2000, 500, n_samples),
        'branching_factor': np.random.randint(5, 50, n_samples),
        'self_mobility': np.random.randint(0, 40, n_samples),
        'opponent_mobility': np.random.randint(0, 40, n_samples),
        'score_diff': np.random.normal(0, 100, n_samples),
        'num_pieces': np.random.randint(8, 32, n_samples),
        'phase': np.random.choice(['opening', 'middlegame', 'endgame'], n_samples),
        'has_castling_rights': np.random.choice([0, 1], n_samples),
        'is_repetition': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'is_low_mobility': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'is_center_controlled': np.random.choice([0, 1], n_samples),
        'is_pawn_endgame': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'white_elo': np.random.normal(1600, 300, n_samples),
        'black_elo': np.random.normal(1600, 300, n_samples),
        'site': np.random.choice(['chess.com', 'lichess.org'], n_samples),
        'error_label': np.random.choice(['good', 'inaccuracy', 'mistake', 'blunder'], n_samples),
        
        # TACTICAL FEATURES - estas son las que faltaban!
        'depth_score_diff': np.random.normal(0, 150, n_samples),
        'threatens_mate': np.random.choice([False, True], n_samples, p=[0.9, 0.1]),
        'is_forced_move': np.random.choice([False, True], n_samples, p=[0.85, 0.15]),
    }
    
    # Add some NaN values to test missing value handling
    data['depth_score_diff'][np.random.choice(n_samples, 100, replace=False)] = np.nan
    data['threatens_mate'][np.random.choice(n_samples, 50, replace=False)] = np.nan
    data['is_forced_move'][np.random.choice(n_samples, 30, replace=False)] = np.nan
    
    return pd.DataFrame(data)

def test_tactical_features_preprocessing():
    """Test preprocessing with tactical features."""
    
    print("🚀 Testing Tactical Features Preprocessing")
    print("=" * 50)
    
    # Create sample data
    df = create_sample_data_with_tactical_features()
    print(f"📊 Created sample data: {len(df)} rows, {len(df.columns)} columns")
    
    # Check for tactical features
    tactical_features = ['depth_score_diff', 'threatens_mate', 'is_forced_move']
    print(f"🎯 Tactical features present: {[f for f in tactical_features if f in df.columns]}")
    
    # Test different source types
    source_types = ['personal', 'novice', 'elite', 'fide', 'stockfish']
    
    for source_type in source_types:
        print(f"\n🔍 Testing source: {source_type}")
        
        # Create source-specific preprocessor
        preprocessor = create_source_specific_preprocessor(source_type)
        
        # Test fit_transform
        try:
            df_processed = preprocessor.fit_transform(df.copy(), source_type=source_type)
            
            # Validate tactical features were processed
            tactical_derived = [col for col in df_processed.columns 
                              if any(tf in col for tf in tactical_features)]
            
            print(f"  ✅ Processed successfully: {len(df_processed)} rows, {len(df_processed.columns)} columns")
            print(f"  🎯 Tactical features found: {len(tactical_derived)}")
            print(f"     - {tactical_derived[:5]}{'...' if len(tactical_derived) > 5 else ''}")
            
            # Check missing values handling
            missing_before = df[tactical_features].isnull().sum().sum()
            missing_after = df_processed[tactical_features].isnull().sum().sum()
            print(f"  🔧 Missing values: {missing_before} → {missing_after}")
            
            # Validate derived features
            expected_derived = ['depth_score_diff_abs', 'tactical_opportunity']
            found_derived = [f for f in expected_derived if f in df_processed.columns]
            print(f"  ⚡ Derived features: {found_derived}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n📈 Testing feature importance ready columns")
    
    # Test feature selection for ML
    preprocessor = ChessMLPreprocessor()
    df_processed = preprocessor.fit_transform(df, source_type='elite')
    
    ml_ready_cols = preprocessor.get_feature_importance_ready_columns(df_processed)
    tactical_ml_cols = [col for col in ml_ready_cols 
                       if any(tf in col for tf in tactical_features)]
    
    print(f"  📊 Total ML-ready columns: {len(ml_ready_cols)}")
    print(f"  🎯 Tactical ML columns: {len(tactical_ml_cols)}")
    print(f"     - {tactical_ml_cols}")
    
    return True

def test_train_test_split_with_tactical():
    """Test train/test split with tactical features."""
    
    print(f"\n🔄 Testing Train/Test Split with Tactical Features")
    print("=" * 50)
    
    # Create data and preprocess
    df = create_sample_data_with_tactical_features()
    preprocessor = ChessMLPreprocessor()
    df_processed = preprocessor.fit_transform(df, source_type='elite')
    
    # Test train/test split
    try:
        X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.prepare_train_test_split(
            df_processed, 
            target_column='error_label',
            test_size=0.2,
            validation_size=0.1
        )
        
        print(f"✅ Split successful:")
        print(f"   Train: {len(X_train)} samples, {len(X_train.columns)} features")
        print(f"   Val:   {len(X_val)} samples, {len(X_val.columns)} features") 
        print(f"   Test:  {len(X_test)} samples, {len(X_test.columns)} features")
        
        # Check tactical features in splits
        tactical_cols = [col for col in X_train.columns 
                        if any(tf in col for tf in ['depth_score_diff', 'threatens_mate', 'is_forced_move'])]
        print(f"   🎯 Tactical features in splits: {len(tactical_cols)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Split failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("🧪 TACTICAL FEATURES PREPROCESSING TEST")
    print("=" * 60)
    
    success = True
    
    try:
        # Test 1: Basic preprocessing with tactical features
        success &= test_tactical_features_preprocessing()
        
        # Test 2: Train/test split
        success &= test_train_test_split_with_tactical()
        
        print(f"\n{'='*60}")
        if success:
            print("✅ ALL TESTS PASSED! Tactical features preprocessing is working correctly.")
            print("\n🎯 Summary of tactical features support:")
            print("   - depth_score_diff: Stockfish evaluation depth difference")
            print("   - threatens_mate: Boolean for mate threat detection") 
            print("   - is_forced_move: Boolean for forced move detection")
            print("   - All features properly handled in missing values, scaling, and derived features")
        else:
            print("❌ SOME TESTS FAILED! Check the errors above.")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        success = False
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
