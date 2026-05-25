#!/usr/bin/env python3
"""
Phase 2: Segmented ML Models by Chess Level

This script creates specialized models for each chess level (elite, fide, stockfish, personal, novice)
to capture the unique characteristics of each skill group.

Dataset Status:
- ELITE: 48,831 labeled (ELO ~2455)
- FIDE: 16,137 labeled (ELO ~2354)  
- STOCKFISH: 16,059 labeled (engine)
- PERSONAL: 5,458 labeled (ELO ~1325)
- NOVICE: 3,744 labeled (ELO ~828)
Total: ~90,229 labeled features

Usage:
    python src/ml/phase2_segmented_models.py --all-levels
    python src/ml/phase2_segmented_models.py --level elite --experiment-name "elite_specialist"
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

# MLflow setup - use local file tracking if server not available
try:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    # Test connection for remote URI
    if MLFLOW_TRACKING_URI.startswith("http"):
        mlflow.list_experiments()
except Exception as e:
    print(f"⚠️ MLflow server not available ({e}), using local tracking")
    mlflow.set_tracking_uri("./mlruns")

def load_segmented_data(source: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load features and labels for specific chess level or all levels.
    
    Args:
        source: Chess level (elite, fide, stockfish, personal, novice) or None for all
        
    Returns:
        Tuple of (features_df, labels_df)
    """
    print(f"📊 Loading data for level: {source or 'ALL'}")
    
    engine = create_engine(DB_URL)
    
    if source:
        query = """
        SELECT f.*, g.source
        FROM features f
        JOIN games g ON f.game_id = g.game_id
        WHERE g.source = %(source)s AND f.error_label IS NOT NULL
        ORDER BY RANDOM()
        """
        df = pd.read_sql(query, engine, params={"source": source})
    else:
        query = """
        SELECT f.*, g.source
        FROM features f
        JOIN games g ON f.game_id = g.game_id
        WHERE f.error_label IS NOT NULL
        ORDER BY RANDOM()
        """
        df = pd.read_sql(query, engine)
    
    engine.dispose()
    
    print(f"✅ Loaded {len(df)} samples")
    if 'source' in df.columns:
        print("📈 Distribution by source:")
        print(df.source.value_counts())
    
    # Separate features and labels
    feature_columns = [col for col in df.columns if col not in ['game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci', 'error_label', 'source']]
    
    X = df[feature_columns].copy()
    y = df['error_label'].copy()
    
    # Clean features
    X = X.select_dtypes(include=[np.number])  # Only numeric features
    X = X.fillna(0)  # Fill NaN with 0
    
    print(f"🔢 Features shape: {X.shape}")
    print(f"🏷️ Label distribution:\n{y.value_counts()}")
    
    return X, y

def train_level_model(source: str, experiment_name: str = None) -> Dict[str, Any]:
    """
    Train specialized model for specific chess level.
    
    Args:
        source: Chess level (elite, fide, stockfish, personal, novice)
        experiment_name: MLflow experiment name
        
    Returns:
        Dictionary with model results
    """
    print(f"\n🚀 Training model for {source.upper()} level")
    print("=" * 50)
    
    # Set experiment
    if not experiment_name:
        experiment_name = f"segmented_models_{source}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run(run_name=f"{source}_specialist"):
        start_time = time.time()
        
        # Load data for this level
        X, y = load_segmented_data(source)
        
        if len(X) < 100:
            print(f"❌ Insufficient data for {source}: {len(X)} samples")
            return {"error": f"Insufficient data: {len(X)} samples"}
        
        # Log dataset info
        mlflow.log_param("chess_level", source)
        mlflow.log_param("total_samples", len(X))
        mlflow.log_param("n_features", X.shape[1])
        
        for label in y.unique():
            mlflow.log_param(f"samples_{label}", sum(y == label))
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        models = {}
        results = {}
        
        # 1. Random Forest (specialized for this level)
        print("🌳 Training Random Forest...")
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_f1 = f1_score(y_test, rf_pred, average='weighted')
        
        # Cross-validation
        cv_scores = cross_val_score(rf, X_train, y_train, cv=5, scoring='f1_weighted', n_jobs=-1)
        
        models[f'{source}_random_forest'] = rf
        results['rf'] = {
            'f1_score': rf_f1,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'classification_report': classification_report(y_test, rf_pred, output_dict=True)
        }
        
        print(f"   F1: {rf_f1:.3f}, CV: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # 2. Logistic Regression (L2 regularization)
        print("📈 Training Logistic Regression L2...")
        lr_l2 = LogisticRegression(
            penalty='l2',
            C=1.0,
            max_iter=1000,
            random_state=42,
            n_jobs=-1
        )
        
        lr_l2.fit(X_train_scaled, y_train)
        lr_l2_pred = lr_l2.predict(X_test_scaled)
        lr_l2_f1 = f1_score(y_test, lr_l2_pred, average='weighted')
        
        cv_scores_l2 = cross_val_score(lr_l2, X_train_scaled, y_train, cv=5, scoring='f1_weighted', n_jobs=-1)
        
        models[f'{source}_logistic_l2'] = lr_l2
        results['lr_l2'] = {
            'f1_score': lr_l2_f1,
            'cv_mean': cv_scores_l2.mean(),
            'cv_std': cv_scores_l2.std(),
            'classification_report': classification_report(y_test, lr_l2_pred, output_dict=True)
        }
        
        print(f"   F1: {lr_l2_f1:.3f}, CV: {cv_scores_l2.mean():.3f} ± {cv_scores_l2.std():.3f}")
        
        # 3. Logistic Regression (L1 regularization) 
        print("📉 Training Logistic Regression L1...")
        lr_l1 = LogisticRegression(
            penalty='l1',
            C=0.1,
            solver='liblinear',
            max_iter=1000,
            random_state=42
        )
        
        lr_l1.fit(X_train_scaled, y_train)
        lr_l1_pred = lr_l1.predict(X_test_scaled)
        lr_l1_f1 = f1_score(y_test, lr_l1_pred, average='weighted')
        
        cv_scores_l1 = cross_val_score(lr_l1, X_train_scaled, y_train, cv=5, scoring='f1_weighted', n_jobs=-1)
        
        models[f'{source}_logistic_l1'] = lr_l1
        results['lr_l1'] = {
            'f1_score': lr_l1_f1,
            'cv_mean': cv_scores_l1.mean(),
            'cv_std': cv_scores_l1.std(),
            'classification_report': classification_report(y_test, lr_l1_pred, output_dict=True)
        }
        
        print(f"   F1: {lr_l1_f1:.3f}, CV: {cv_scores_l1.mean():.3f} ± {cv_scores_l1.std():.3f}")
        
        # Log metrics to MLflow
        mlflow.log_metric("rf_f1_score", rf_f1)
        mlflow.log_metric("rf_cv_mean", cv_scores.mean())
        mlflow.log_metric("rf_cv_std", cv_scores.std())
        
        mlflow.log_metric("lr_l2_f1_score", lr_l2_f1)
        mlflow.log_metric("lr_l2_cv_mean", cv_scores_l2.mean())
        mlflow.log_metric("lr_l2_cv_std", cv_scores_l2.std())
        
        mlflow.log_metric("lr_l1_f1_score", lr_l1_f1)
        mlflow.log_metric("lr_l1_cv_mean", cv_scores_l1.mean())
        mlflow.log_metric("lr_l1_cv_std", cv_scores_l1.std())
        
        # Register best model
        best_model_name = max(results.keys(), key=lambda k: results[k]['f1_score'])
        best_f1 = results[best_model_name]['f1_score']
        
        mlflow.log_metric("best_f1_score", best_f1)
        mlflow.log_param("best_model", best_model_name)
        
        # Log and register best model
        model_key = f'{source}_{best_model_name.replace("_", "_")}'
        if best_model_name == 'rf':
            model_key = f'{source}_random_forest'
        elif best_model_name == 'lr_l2':
            model_key = f'{source}_logistic_l2'
        elif best_model_name == 'lr_l1':
            model_key = f'{source}_logistic_l1'
            
        model_to_register = models[model_key]
        mlflow.sklearn.log_model(
            model_to_register,
            f"{source}_best_model",
            registered_model_name=f"{source}_specialist_best"
        )
        
        training_time = time.time() - start_time
        mlflow.log_metric("training_time_seconds", training_time)
        
        print(f"\n🏆 Best model for {source}: {best_model_name} (F1: {best_f1:.3f})")
        print(f"⏱️ Training time: {training_time:.1f}s")
        
        return {
            'source': source,
            'models': models,
            'results': results,
            'best_model': best_model_name,
            'best_f1': best_f1,
            'training_time': training_time
        }

def train_all_levels(experiment_name: str = None):
    """Train models for all chess levels."""
    levels = ['elite', 'fide', 'stockfish', 'personal', 'novice']
    
    print("🚀 PHASE 2: SEGMENTED MODELS BY CHESS LEVEL")
    print("=" * 60)
    
    if not experiment_name:
        experiment_name = f"segmented_models_all_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    all_results = {}
    
    for level in levels:
        print(f"\n{'='*20} {level.upper()} LEVEL {'='*20}")
        result = train_level_model(level, experiment_name)
        
        if 'error' not in result:
            all_results[level] = result
        else:
            print(f"❌ Skipped {level}: {result['error']}")
    
    # Summary
    print("\n🏆 SEGMENTED MODELS SUMMARY")
    print("=" * 50)
    
    for level, result in all_results.items():
        best_f1 = result['best_f1']
        best_model = result['best_model']
        samples = result['results']['rf']['classification_report']['weighted avg']['support'] / 0.8  # Total samples
        
        print(f"{level.upper():>12}: {best_model:>6} | F1: {best_f1:.3f} | Samples: {samples:.0f}")
    
    return all_results

def main():
    parser = argparse.ArgumentParser(description="Phase 2: Segmented ML Models")
    parser.add_argument('--level', choices=['elite', 'fide', 'stockfish', 'personal', 'novice'], 
                       help='Train model for specific level')
    parser.add_argument('--all-levels', action='store_true', 
                       help='Train models for all levels')
    parser.add_argument('--experiment-name', type=str,
                       help='MLflow experiment name')
    
    args = parser.parse_args()
    
    if args.all_levels:
        train_all_levels(args.experiment_name)
    elif args.level:
        train_level_model(args.level, args.experiment_name)
    else:
        print("Please specify --level or --all-levels")
        parser.print_help()

if __name__ == "__main__":
    main()