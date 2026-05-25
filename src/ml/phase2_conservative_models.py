#!/usr/bin/env python3
"""
Phase 2 FIXED: Segmented ML Models WITHOUT Data Leakage

Esta versión corregida elimina features con data leakage y usa parámetros más conservadores
para evitar overfitting.

FEATURES ELIMINADAS (Data Leakage):
- score_diff: Contiene información del resultado futuro
- material_balance: Podría contener info post-juego

MEJORAS IMPLEMENTADAS:
- Parámetros más conservadores en Random Forest
- Mejor regularización en Logistic Regression  
- Feature selection automática
- Validación más robusta
"""

import argparse
import os
import sys
import time
import warnings
from datetime import datetime
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif, RFE
import psycopg2
from sqlalchemy import create_engine

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment
from dotenv import load_dotenv
load_dotenv()

warnings.filterwarnings('ignore')

# Configuration
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "./mlruns")

# Features to exclude (data leakage)
EXCLUDED_FEATURES = [
    'score_diff',         # Main data leakage source
    'material_balance',   # Potentially derived from outcome
]

# MLflow setup
try:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    if MLFLOW_TRACKING_URI.startswith("http"):
        mlflow.list_experiments()
except Exception as e:
    print(f"⚠️ MLflow server not available ({e}), using local tracking")
    mlflow.set_tracking_uri("./mlruns")

def load_clean_segmented_data(source: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load features without data leakage for specific chess level.
    
    Args:
        source: Chess level (elite, fide, stockfish, personal, novice) or None for all
        
    Returns:
        Tuple of (features_df, labels_df)
    """
    print(f"📊 Loading CLEAN data for level: {source or 'ALL'}")
    
    engine = create_engine(DB_URL)
    
    if source:
        query = """
        SELECT f.*, g.source, g.date_played
        FROM features f
        JOIN games g ON f.game_id = g.game_id
        WHERE g.source = %(source)s AND f.error_label IS NOT NULL
        ORDER BY RANDOM()
        """
        df = pd.read_sql(query, engine, params={"source": source})
    else:
        query = """
        SELECT f.*, g.source, g.date_played
        FROM features f
        JOIN games g ON f.game_id = g.game_id
        WHERE f.error_label IS NOT NULL
        ORDER BY RANDOM()
        """
        df = pd.read_sql(query, engine)
    
    engine.dispose()
    
    print(f"✅ Loaded {len(df)} samples")
    
    # Separate features and labels
    exclude_columns = [
        'game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci', 
        'error_label', 'source', 'date_played'
    ] + EXCLUDED_FEATURES
    
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].copy()
    y = df['error_label'].copy()
    
    # Clean features
    X = X.select_dtypes(include=[np.number])  # Only numeric features
    X = X.fillna(0)  # Fill NaN with 0
    
    # Remove excluded features
    remaining_excluded = [col for col in EXCLUDED_FEATURES if col in X.columns]
    if remaining_excluded:
        print(f"🚫 Excluding features with data leakage: {remaining_excluded}")
        X = X.drop(columns=remaining_excluded)
    
    print(f"🔢 Final features shape: {X.shape}")
    print(f"🏷️ Label distribution:\n{y.value_counts()}")
    
    return X, y

def select_best_features(X, y, k=15):
    """Select k best features to reduce noise and overfitting."""
    print(f"🎯 Selecting {k} best features...")
    
    # Use SelectKBest with f_classif
    selector = SelectKBest(score_func=f_classif, k=k)
    X_selected = selector.fit_transform(X, y)
    
    selected_features = X.columns[selector.get_support()].tolist()
    print(f"✅ Selected features: {selected_features}")
    
    return X_selected, selected_features, selector

def train_conservative_level_model(source: str, experiment_name: str = None) -> Dict[str, Any]:
    """
    Train CONSERVATIVE model for specific chess level WITHOUT data leakage.
    
    Args:
        source: Chess level (elite, fide, stockfish, personal, novice)
        experiment_name: MLflow experiment name
        
    Returns:
        Dictionary with model results
    """
    print(f"\n🚀 Training CONSERVATIVE model for {source.upper()} level")
    print("=" * 60)
    
    # Set experiment
    if not experiment_name:
        experiment_name = f"conservative_models_{source}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name=f"{source}_conservative"):
        start_time = time.time()
        
        # Load clean data
        X, y = load_clean_segmented_data(source)
        
        if len(X) < 100:
            print(f"❌ Insufficient data for {source}: {len(X)} samples")
            return {"error": f"Insufficient data: {len(X)} samples"}
        
        # Feature selection
        X_selected, selected_features, feature_selector = select_best_features(X, y, k=min(15, X.shape[1]))
        
        # Log dataset info
        mlflow.log_param("chess_level", source)
        mlflow.log_param("total_samples", len(X))
        mlflow.log_param("original_features", X.shape[1])
        mlflow.log_param("selected_features", len(selected_features))
        mlflow.log_param("excluded_features", ', '.join(EXCLUDED_FEATURES))
        
        for label in y.unique():
            mlflow.log_param(f"samples_{label}", sum(y == label))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_selected, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        models = {}
        results = {}
        
        # 1. CONSERVATIVE Random Forest
        print("🌳 Training CONSERVATIVE Random Forest...")
        rf_conservative = RandomForestClassifier(
            n_estimators=100,        # Reducido de 200
            max_depth=8,             # Reducido de 15
            min_samples_split=20,    # Aumentado de 10
            min_samples_leaf=10,     # Aumentado de 5
            max_features='sqrt',     # Añadido para más diversidad
            random_state=42,
            n_jobs=-1
        )
        
        rf_conservative.fit(X_train, y_train)
        rf_pred = rf_conservative.predict(X_test)
        rf_f1 = f1_score(y_test, rf_pred, average='weighted')
        
        # Cross-validation más robusta
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(rf_conservative, X_train, y_train, cv=skf, scoring='f1_weighted', n_jobs=-1)
        
        models[f'{source}_conservative_rf'] = rf_conservative
        results['conservative_rf'] = {
            'f1_score': rf_f1,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'classification_report': classification_report(y_test, rf_pred, output_dict=True)
        }
        
        print(f"   F1: {rf_f1:.3f}, CV: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # 2. REGULARIZED Logistic Regression (L2 - stronger)
        print("📈 Training REGULARIZED Logistic Regression L2...")
        lr_l2_reg = LogisticRegression(
            penalty='l2',
            C=0.1,                   # Más regularización (era 1.0)
            max_iter=1000,
            random_state=42,
            n_jobs=-1
        )
        
        lr_l2_reg.fit(X_train_scaled, y_train)
        lr_l2_pred = lr_l2_reg.predict(X_test_scaled)
        lr_l2_f1 = f1_score(y_test, lr_l2_pred, average='weighted')
        
        cv_scores_l2 = cross_val_score(lr_l2_reg, X_train_scaled, y_train, cv=skf, scoring='f1_weighted', n_jobs=-1)
        
        models[f'{source}_regularized_l2'] = lr_l2_reg
        results['regularized_l2'] = {
            'f1_score': lr_l2_f1,
            'cv_mean': cv_scores_l2.mean(),
            'cv_std': cv_scores_l2.std(),
            'classification_report': classification_report(y_test, lr_l2_pred, output_dict=True)
        }
        
        print(f"   F1: {lr_l2_f1:.3f}, CV: {cv_scores_l2.mean():.3f} ± {cv_scores_l2.std():.3f}")
        
        # 3. SPARSE Logistic Regression (L1 - stronger)
        print("📉 Training SPARSE Logistic Regression L1...")
        lr_l1_sparse = LogisticRegression(
            penalty='l1',
            C=0.01,                  # Mucha más regularización (era 0.1)
            solver='liblinear',
            max_iter=1000,
            random_state=42
        )
        
        lr_l1_sparse.fit(X_train_scaled, y_train)
        lr_l1_pred = lr_l1_sparse.predict(X_test_scaled)
        lr_l1_f1 = f1_score(y_test, lr_l1_pred, average='weighted')
        
        cv_scores_l1 = cross_val_score(lr_l1_sparse, X_train_scaled, y_train, cv=skf, scoring='f1_weighted', n_jobs=-1)
        
        models[f'{source}_sparse_l1'] = lr_l1_sparse
        results['sparse_l1'] = {
            'f1_score': lr_l1_f1,
            'cv_mean': cv_scores_l1.mean(),
            'cv_std': cv_scores_l1.std(),
            'classification_report': classification_report(y_test, lr_l1_pred, output_dict=True)
        }
        
        print(f"   F1: {lr_l1_f1:.3f}, CV: {cv_scores_l1.mean():.3f} ± {cv_scores_l1.std():.3f}")
        
        # Log metrics to MLflow
        mlflow.log_metric("conservative_rf_f1", rf_f1)
        mlflow.log_metric("conservative_rf_cv_mean", cv_scores.mean())
        mlflow.log_metric("conservative_rf_cv_std", cv_scores.std())
        
        mlflow.log_metric("regularized_l2_f1", lr_l2_f1)
        mlflow.log_metric("regularized_l2_cv_mean", cv_scores_l2.mean())
        mlflow.log_metric("regularized_l2_cv_std", cv_scores_l2.std())
        
        mlflow.log_metric("sparse_l1_f1", lr_l1_f1)
        mlflow.log_metric("sparse_l1_cv_mean", cv_scores_l1.mean())
        mlflow.log_metric("sparse_l1_cv_std", cv_scores_l1.std())
        
        # Register best model
        best_model_name = max(results.keys(), key=lambda k: results[k]['f1_score'])
        best_f1 = results[best_model_name]['f1_score']
        
        mlflow.log_metric("best_f1_score", best_f1)
        mlflow.log_param("best_model", best_model_name)
        
        # Determine model key for registration
        if best_model_name == 'conservative_rf':
            model_key = f'{source}_conservative_rf'
        elif best_model_name == 'regularized_l2':
            model_key = f'{source}_regularized_l2'
        else:
            model_key = f'{source}_sparse_l1'
            
        model_to_register = models[model_key]
        mlflow.sklearn.log_model(
            model_to_register,
            f"{source}_conservative_best",
            registered_model_name=f"{source}_conservative_specialist"
        )
        
        training_time = time.time() - start_time
        mlflow.log_metric("training_time_seconds", training_time)
        
        print(f"\n🏆 Best CONSERVATIVE model for {source}: {best_model_name} (F1: {best_f1:.3f})")
        print(f"⏱️ Training time: {training_time:.1f}s")
        print(f"🎯 Features used: {len(selected_features)}")
        
        # Validation check
        if best_f1 > 0.95:
            print("⚠️ WARNING: Still very high F1 score. Check for remaining data leakage.")
        elif best_f1 > 0.85:
            print("✅ Good F1 score. Model seems realistic.")
        else:
            print("📉 Lower F1 score. Model may be too conservative or need more data.")
        
        return {
            'source': source,
            'models': models,
            'results': results,
            'best_model': best_model_name,
            'best_f1': best_f1,
            'selected_features': selected_features,
            'training_time': training_time
        }

def train_all_conservative_levels(experiment_name: str = None):
    """Train conservative models for all chess levels."""
    levels = ['elite', 'fide', 'stockfish', 'personal', 'novice']
    
    print("🚀 PHASE 2 FIXED: CONSERVATIVE MODELS WITHOUT DATA LEAKAGE")
    print("=" * 70)
    
    if not experiment_name:
        experiment_name = f"conservative_models_all_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    all_results = {}
    
    for level in levels:
        print(f"\n{'='*25} {level.upper()} LEVEL {'='*25}")
        result = train_conservative_level_model(level, experiment_name)
        
        if 'error' not in result:
            all_results[level] = result
        else:
            print(f"❌ Skipped {level}: {result['error']}")
    
    # Summary
    print("\n🏆 CONSERVATIVE MODELS SUMMARY")
    print("=" * 60)
    print("Level       | Best Model    | F1 Score | Features | Samples")
    print("-" * 60)
    
    for level, result in all_results.items():
        best_f1 = result['best_f1']
        best_model = result['best_model']
        n_features = len(result['selected_features'])
        
        # Estimate samples from classification report
        sample_count = 0
        if 'conservative_rf' in result['results']:
            sample_count = result['results']['conservative_rf']['classification_report']['weighted avg']['support'] / 0.8
        
        print(f"{level.upper():>11} | {best_model:>12} | {best_f1:>8.3f} | {n_features:>8} | {sample_count:>7.0f}")
    
    # Final validation
    suspicious_models = [level for level, result in all_results.items() if result['best_f1'] > 0.95]
    if suspicious_models:
        print(f"\n⚠️ MODELS STILL SUSPICIOUS (F1 > 0.95): {suspicious_models}")
        print("   Consider investigating remaining features for data leakage.")
    else:
        print(f"\n✅ All models have realistic performance (F1 < 0.95)")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Phase 2 FIXED: Conservative Models without Data Leakage")
    parser.add_argument('--level', choices=['elite', 'fide', 'stockfish', 'personal', 'novice'], 
                       help='Train model for specific level')
    parser.add_argument('--all-levels', action='store_true', 
                       help='Train models for all levels')
    parser.add_argument('--experiment-name', type=str,
                       help='MLflow experiment name')
    
    args = parser.parse_args()
    
    if args.all_levels:
        train_all_conservative_levels(args.experiment_name)
    elif args.level:
        train_conservative_level_model(args.level, args.experiment_name)
    else:
        print("Please specify --level or --all-levels")
        parser.print_help()

if __name__ == "__main__":
    main()