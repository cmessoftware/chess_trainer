#!/usr/bin/env python3
"""
🎯 RETRAIN ML MODELS WITH CURRENT FEATURES
==========================================

Entrena modelos ML con las 11,658 features actuales en PostgreSQL:
- Carga features directamente desde DB (sin reimportar)
- Balanceo estratificado por source
- Múltiples modelos: XGBoost, RandomForest, CatBoost, LightGBM
- Tracking completo con MLflow
- Comparación automática de métricas

Dataset actual:
- Elite: 3,999 partidas
- Personal: 4,039 partidas  
- Stockfish: 1,000 partidas
- Fide: 1,434 partidas
- Novice: 994 partidas
- Validation: 192 partidas
TOTAL: 11,658 partidas

Usage:
    python retrain_with_current_features.py
    python retrain_with_current_features.py --quick  # Solo 1 modelo para test
"""

import pandas as pd
import numpy as np
import os
import sys
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text

# MLflow y modelos
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    print("⚠️ SMOTE no disponible. Instalar con: pip install imbalanced-learn")

# Modelos
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    
try:
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Configuración
DB_URL = os.getenv("DATABASE_URL", "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT_NAME = "chess_model_SMOTE_PARTIAL_v1"

# SMOTE para balancear clases (mejora detección de blunders)
USE_SMOTE = True and SMOTE_AVAILABLE

# Features que causan DATA LEAKAGE (excluir del training)
LEAKAGE_FEATURES = ['score_diff', 'score_before', 'score_after']

# Features numéricas a usar (SIN score_diff - causa overfitting)
NUMERIC_FEATURES = [
    'material_balance', 'material_total', 'num_pieces',
    'branching_factor', 'self_mobility', 'opponent_mobility',
    'move_number_global', 'has_castling_rights',
    'is_repetition', 'is_low_mobility', 'is_center_controlled',
    'is_pawn_endgame', 'num_moves'
]

# Categóricas
CATEGORICAL_FEATURES = ['phase', 'player_color']

# Target
TARGET = 'error_label'

def load_features_from_db():
    """Carga features desde PostgreSQL."""
    logger.info("📊 Cargando features desde PostgreSQL...")
    start_time = time.time()
    
    engine = create_engine(DB_URL)
    
    # Query optimizada: JOIN con games para obtener source
    query = """
        SELECT 
            f.*,
            g.source
        FROM features f
        INNER JOIN games g ON f.game_id = g.game_id
        WHERE f.error_label IS NOT NULL
        ORDER BY f.created_at DESC
    """
    
    df = pd.read_sql(query, engine)
    
    elapsed = time.time() - start_time
    logger.info(f"✅ Cargadas {len(df):,} features en {elapsed:.1f}s")
    logger.info(f"   Partidas únicas: {df['game_id'].nunique():,}")
    logger.info(f"   Sources: {df['source'].value_counts().to_dict()}")
    
    return df

def prepare_dataset(df):
    """Prepara dataset para entrenamiento."""
    logger.info("🔧 Preparando dataset...")
    
    # Info inicial
    logger.info(f"   Shape original: {df.shape}")
    logger.info(f"   Clases target: {df[TARGET].value_counts().to_dict()}")
    
    # Handle missing values
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    
    # Encode categoricas
    le_phase = LabelEncoder()
    if 'phase' in df.columns:
        df['phase_encoded'] = le_phase.fit_transform(df['phase'].fillna('unknown'))
    
    # Encode target
    le_target = LabelEncoder()
    df['target_encoded'] = le_target.fit_transform(df[TARGET])
    
    logger.info(f"   Clases encoded: {sorted(le_target.classes_)}")
    logger.info(f"   Distribución target: {df['target_encoded'].value_counts().to_dict()}")
    
    # Seleccionar features finales
    feature_cols = [col for col in NUMERIC_FEATURES if col in df.columns]
    if 'phase_encoded' in df.columns:
        feature_cols.append('phase_encoded')
    
    X = df[feature_cols].copy()
    y = df['target_encoded'].copy()
    sources = df['source'].copy()
    
    logger.info(f"✅ Dataset preparado: X={X.shape}, y={y.shape}")
    
    return X, y, sources, le_target, feature_cols

def create_train_test_split(X, y, sources, test_size=0.2, random_state=42):
    """Split estratificado por source y target."""
    logger.info(f"✂️ Creando train/test split (test_size={test_size})...")
    
    # Crear stratify combinando source + target
    stratify_col = sources.astype(str) + "_" + y.astype(str)
    
    X_train, X_test, y_train, y_test, src_train, src_test = train_test_split(
        X, y, sources, 
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_col
    )
    
    logger.info(f"   Train: {X_train.shape[0]:,} samples")
    logger.info(f"   Test:  {X_test.shape[0]:,} samples")
    logger.info(f"   Sources train: {src_train.value_counts().to_dict()}")
    logger.info(f"   Sources test: {src_test.value_counts().to_dict()}")
    
    return X_train, X_test, y_train, y_test

def apply_smote(X_train, y_train):
    """Aplica SMOTE PARCIAL para balancear clases minoritarias de forma inteligente.
    
    Estrategia:
    - blunder (1.4%): Oversample a ~30k (8x) - crítico detectar
    - inaccuracy (7.6%): Oversample a ~50k (2.5x)
    - mistake (6.2%): Oversample a ~40k (2.4x)
    - good (84.7%): Mantener original (mayoría)
    
    Balance parcial mejora detección de errores sin generar exceso de falsos positivos.
    """
    if not USE_SMOTE:
        logger.info("⏭️ SMOTE deshabilitado, usando dataset original")
        return X_train, y_train
    
    logger.info("⚖️ Aplicando SMOTE PARCIAL (balance inteligente)...")
    logger.info(f"   Distribución ANTES: {pd.Series(y_train).value_counts().to_dict()}")
    
    # Calcular distribución actual
    class_counts = pd.Series(y_train).value_counts().to_dict()
    
    # Estrategia de sampling parcial (no balance total)
    # Asumiendo: 0=blunder, 1=good, 2=inaccuracy, 3=mistake
    sampling_strategy = {}
    
    # Identificar la clase mayoritaria (good)
    majority_class = max(class_counts, key=class_counts.get)
    majority_count = class_counts[majority_class]
    
    for class_label, count in class_counts.items():
        if class_label == majority_class:
            # Mantener mayoría sin cambios
            continue
        else:
            # Oversample minoritarias de forma controlada
            if count < 5000:  # blunder (~3.7k)
                target = min(30000, int(majority_count * 0.13))  # 13% de mayoría
            elif count < 18000:  # inaccuracy (~20k)
                target = min(50000, int(majority_count * 0.23))  # 23% de mayoría
            elif count < 20000:  # mistake (~16k)
                target = min(40000, int(majority_count * 0.18))  # 18% de mayoría
            else:
                target = count  # No modificar
            
            sampling_strategy[class_label] = target
    
    logger.info(f"   Estrategia SMOTE: {sampling_strategy}")
    
    smote = SMOTE(random_state=42, k_neighbors=5, sampling_strategy=sampling_strategy)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    logger.info(f"   Distribución DESPUÉS: {pd.Series(y_train_balanced).value_counts().to_dict()}")
    logger.info(f"   Samples: {len(X_train):,} → {len(X_train_balanced):,} (+{len(X_train_balanced)-len(X_train):,})")
    
    return X_train_balanced, y_train_balanced

def analyze_predictions(y_true, y_pred, label_encoder):
    """Análisis detallado de predicciones con confusion matrix."""
    class_names = label_encoder.classes_
    cm = confusion_matrix(y_true, y_pred)
    
    logger.info("\n📊 CONFUSION MATRIX:")
    logger.info(f"   Classes: {class_names}")
    
    # Mostrar matriz
    cm_df = pd.DataFrame(cm, index=class_names, columns=class_names)
    logger.info(f"\n{cm_df.to_string()}")
    
    # Métricas por clase
    logger.info("\n📈 MÉTRICAS POR CLASE:")
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    
    for class_name in class_names:
        if class_name in report:
            metrics = report[class_name]
            logger.info(f"   {class_name}:")
            logger.info(f"      Precision: {metrics['precision']:.3f}")
            logger.info(f"      Recall:    {metrics['recall']:.3f}")
            logger.info(f"      F1-Score:  {metrics['f1-score']:.3f}")
            logger.info(f"      Support:   {metrics['support']}")
    
    # Accuracy por clase
    correct_per_class = cm.diagonal()
    total_per_class = cm.sum(axis=1)
    acc_per_class = correct_per_class / total_per_class
    
    logger.info("\n🎯 ACCURACY POR CLASE:")
    for i, class_name in enumerate(class_names):
        logger.info(f"   {class_name}: {acc_per_class[i]:.3f} ({correct_per_class[i]}/{total_per_class[i]})")
    
    return cm, report

def train_xgboost(X_train, y_train, X_test, y_test, feature_names, label_encoder=None):
    """Entrena XGBoost con tracking MLflow."""
    logger.info("🚀 Entrenando XGBoost...")
    
    with mlflow.start_run(run_name="XGBoost_optimized") as run:
        # Hyperparameters
        params = {
            'n_estimators': 300,
            'max_depth': 8,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'eval_metric': 'mlogloss',
            'early_stopping_rounds': 20
        }
        
        mlflow.log_params(params)
        mlflow.log_param("model_type", "XGBoost")
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("train_samples", len(X_train))
        
        # Train
        start = time.time()
        model = XGBClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        train_time = time.time() - start
        
        # Predictions on TEST
        y_pred_test = model.predict(X_test)
        y_proba_test = model.predict_proba(X_test)
        
        # Predictions on TRAIN (detectar overfitting)
        y_pred_train = model.predict(X_train)
        
        # Metrics TEST
        metrics = calculate_metrics(y_test, y_pred_test, y_proba_test)
        metrics['train_time'] = train_time
        
        # Metrics TRAIN
        metrics['train_accuracy'] = accuracy_score(y_train, y_pred_train)
        metrics['train_f1_weighted'] = f1_score(y_train, y_pred_train, average='weighted')
        
        # Overfitting gap
        metrics['overfitting_gap'] = metrics['train_accuracy'] - metrics['accuracy']
        
        # Log metrics
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        # Log model
        mlflow.xgboost.log_model(model, "model")
        
        # Análisis detallado de predicciones
        if label_encoder:
            logger.info("\n" + "="*80)
            cm, report = analyze_predictions(y_test, y_pred_test, label_encoder)
            logger.info("="*80)
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"   Test Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   Train Accuracy: {metrics['train_accuracy']:.4f}")
        logger.info(f"   Overfitting Gap: {metrics['overfitting_gap']:.4f}")
        logger.info(f"   F1 (test): {metrics['f1_weighted']:.4f}")
        logger.info(f"   Train time: {train_time:.1f}s")
        logger.info(f"   Top 5 features:\n{importance.head().to_string(index=False)}")
        
        return model, metrics, importance

def train_random_forest(X_train, y_train, X_test, y_test, feature_names, label_encoder=None):
    """Entrena RandomForest con tracking MLflow."""
    logger.info("🌲 Entrenando Random Forest...")
    
    with mlflow.start_run(run_name="RandomForest_optimized") as run:
        params = {
            'n_estimators': 200,
            'max_depth': 15,
            'min_samples_split': 10,
            'min_samples_leaf': 5,
            'random_state': 42,
            'n_jobs': -1
        }
        
        mlflow.log_params(params)
        mlflow.log_param("model_type", "RandomForest")
        mlflow.log_param("n_features", len(feature_names))
        
        start = time.time()
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)
        train_time = time.time() - start
        
        # Predictions TEST and TRAIN
        y_pred_test = model.predict(X_test)
        y_proba_test = model.predict_proba(X_test)
        y_pred_train = model.predict(X_train)
        
        # Metrics TEST
        metrics = calculate_metrics(y_test, y_pred_test, y_proba_test)
        metrics['train_time'] = train_time
        
        # Metrics TRAIN (overfitting detection)
        metrics['train_accuracy'] = accuracy_score(y_train, y_pred_train)
        metrics['train_f1_weighted'] = f1_score(y_train, y_pred_train, average='weighted')
        metrics['overfitting_gap'] = metrics['train_accuracy'] - metrics['accuracy']
        
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        mlflow.sklearn.log_model(model, "model")
        
        # Análisis RandomForest
        if label_encoder:
            logger.info("\n" + "="*80)
            cm, report = analyze_predictions(y_test, y_pred_test, label_encoder)
            logger.info("="*80)
        
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"   Test Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   Train Accuracy: {metrics['train_accuracy']:.4f}")
        logger.info(f"   Overfitting Gap: {metrics['overfitting_gap']:.4f}")
        logger.info(f"   F1 (test): {metrics['f1_weighted']:.4f}")
        logger.info(f"   Train time: {train_time:.1f}s")
        
        return model, metrics, importance

def train_catboost(X_train, y_train, X_test, y_test, feature_names, label_encoder=None):
    """Entrena CatBoost con tracking MLflow."""
    if not CATBOOST_AVAILABLE:
        logger.warning("⚠️ CatBoost no disponible, saltando...")
        return None, None, None
    
    logger.info("🐱 Entrenando CatBoost...")
    
    with mlflow.start_run(run_name="CatBoost_optimized") as run:
        params = {
            'iterations': 500,
            'depth': 8,
            'learning_rate': 0.05,
            'random_state': 42,
            'verbose': False,
            'early_stopping_rounds': 30
        }
        
        mlflow.log_params(params)
        mlflow.log_param("model_type", "CatBoost")
        
        start = time.time()
        model = CatBoostClassifier(**params)
        model.fit(X_train, y_train, eval_set=(X_test, y_test), verbose=False)
        train_time = time.time() - start
        
        # Predictions TEST and TRAIN
        y_pred_test = model.predict(X_test)
        y_proba_test = model.predict_proba(X_test)
        y_pred_train = model.predict(X_train)
        
        # Metrics TEST
        metrics = calculate_metrics(y_test, y_pred_test, y_proba_test)
        metrics['train_time'] = train_time
        
        # Metrics TRAIN (overfitting detection)
        metrics['train_accuracy'] = accuracy_score(y_train, y_pred_train)
        metrics['train_f1_weighted'] = f1_score(y_train, y_pred_train, average='weighted')
        metrics['overfitting_gap'] = metrics['train_accuracy'] - metrics['accuracy']
        
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        mlflow.sklearn.log_model(model, "model")
        
        # Análisis CatBoost
        if label_encoder:
            logger.info("\n" + "="*80)
            cm, report = analyze_predictions(y_test, y_pred_test, label_encoder)
            logger.info("="*80)
        
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"   Test Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   Train Accuracy: {metrics['train_accuracy']:.4f}")
        logger.info(f"   Overfitting Gap: {metrics['overfitting_gap']:.4f}")
        logger.info(f"   F1 (test): {metrics['f1_weighted']:.4f}")
        
        return model, metrics, importance

def train_lightgbm(X_train, y_train, X_test, y_test, feature_names):
    """Entrena LightGBM con tracking MLflow."""
    if not LIGHTGBM_AVAILABLE:
        logger.warning("⚠️ LightGBM no disponible, saltando...")
        return None, None, None
    
    logger.info("💡 Entrenando LightGBM...")
    
    with mlflow.start_run(run_name="LightGBM_optimized") as run:
        params = {
            'n_estimators': 300,
            'max_depth': 8,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'random_state': 42,
            'verbose': -1
        }
        
        mlflow.log_params(params)
        mlflow.log_param("model_type", "LightGBM")
        
        start = time.time()
        model = LGBMClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], callbacks=[])
        train_time = time.time() - start
        
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)
        
        metrics = calculate_metrics(y_test, y_pred, y_proba)
        metrics['train_time'] = train_time
        
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        mlflow.sklearn.log_model(model, "model")
        
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info(f"   Test Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   Train Accuracy: {metrics['train_accuracy']:.4f}")
        logger.info(f"   Overfitting Gap: {metrics['overfitting_gap']:.4f}")
        logger.info(f"   F1 (test): {metrics['f1_weighted']:.4f}")
        
        return model, metrics, importance

def calculate_metrics(y_true, y_pred, y_proba):
    """Calcula métricas comprehensivas."""
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision_weighted': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall_weighted': recall_score(y_true, y_pred, average='weighted', zero_division=0),
        'f1_weighted': f1_score(y_true, y_pred, average='weighted', zero_division=0),
        'precision_macro': precision_score(y_true, y_pred, average='macro', zero_division=0),
        'recall_macro': recall_score(y_true, y_pred, average='macro', zero_division=0),
        'f1_macro': f1_score(y_true, y_pred, average='macro', zero_division=0)
    }
    
    # AUC solo si es multiclass
    try:
        if len(np.unique(y_true)) > 2:
            metrics['roc_auc_ovr'] = roc_auc_score(y_true, y_proba, multi_class='ovr', average='weighted')
    except:
        pass
    
    return metrics

def compare_models(results):
    """Compara resultados de todos los modelos."""
    logger.info("\n" + "="*80)
    logger.info("📊 COMPARACIÓN DE MODELOS")
    logger.info("="*80)
    
    comparison = []
    for name, (model, metrics, importance) in results.items():
        if model is not None:
            comparison.append({
                'model': name,
                'accuracy': metrics['accuracy'],
                'f1_weighted': metrics['f1_weighted'],
                'precision': metrics['precision_weighted'],
                'recall': metrics['recall_weighted'],
                'train_time': metrics['train_time']
            })
    
    df_comp = pd.DataFrame(comparison).sort_values('f1_weighted', ascending=False)
    
    logger.info("\n" + df_comp.to_string(index=False))
    logger.info("\n🏆 MEJOR MODELO: " + df_comp.iloc[0]['model'])
    logger.info("="*80 + "\n")
    
    return df_comp

def main():
    parser = argparse.ArgumentParser(description="Retrain ML models with current features")
    parser.add_argument('--quick', action='store_true', help='Solo entrenar XGBoost (más rápido)')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("🎯 REENTRENAMIENTO ML CON 11,658 FEATURES ACTUALES")
    logger.info("="*80)
    
    # Setup MLflow
    logger.info(f"🔧 Configurando MLflow: {MLFLOW_URI}")
    mlflow.set_tracking_uri(MLFLOW_URI)
    
    try:
        experiment_id = mlflow.create_experiment(EXPERIMENT_NAME)
        logger.info(f"✅ Experimento creado: {EXPERIMENT_NAME}")
    except:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        experiment_id = experiment.experiment_id
        logger.info(f"📋 Usando experimento existente: {EXPERIMENT_NAME}")
    
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # 1. Load data
    df = load_features_from_db()
    
    # 2. Prepare dataset
    X, y, sources, le_target, feature_names = prepare_dataset(df)
    
    # 3. Train/Test split
    X_train, X_test, y_train, y_test = create_train_test_split(X, y, sources)
    
    # 4. Aplicar SMOTE para balancear clases
    X_train_balanced, y_train_balanced = apply_smote(X_train, y_train)
    
    # 5. Train models
    results = {}
    
    # Siempre entrenar XGBoost
    xgb_model, xgb_metrics, xgb_importance = train_xgboost(
        X_train_balanced, y_train_balanced, X_test, y_test, feature_names, le_target
    )
    results['XGBoost'] = (xgb_model, xgb_metrics, xgb_importance)
    
    if not args.quick:
        # RandomForest
        rf_model, rf_metrics, rf_importance = train_random_forest(
            X_train_balanced, y_train_balanced, X_test, y_test, feature_names, le_target
        )
        results['RandomForest'] = (rf_model, rf_metrics, rf_importance)
        
        # CatBoost
        cb_model, cb_metrics, cb_importance = train_catboost(
            X_train_balanced, y_train_balanced, X_test, y_test, feature_names, le_target
        )
        if cb_model is not None:
            results['CatBoost'] = (cb_model, cb_metrics, cb_importance)
        
        # LightGBM
        lgbm_model, lgbm_metrics, lgbm_importance = train_lightgbm(
            X_train, y_train, X_test, y_test, feature_names
        )
        if lgbm_model is not None:
            results['LightGBM'] = (lgbm_model, lgbm_metrics, lgbm_importance)
    
    # 5. Compare
    comparison = compare_models(results)
    
    logger.info("✅ Reentrenamiento completado!")
    logger.info(f"🌐 Ver resultados en MLflow: {MLFLOW_URI}")
    logger.info("="*80)

if __name__ == "__main__":
    main()
