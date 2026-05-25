#!/usr/bin/env python3
"""
Diagnóstico de Overfitting - Análisis del modelo ELITE con F1 99.9%

Este script investiga las posibles causas del overfitting extremo:
1. Data leakage en features
2. Feature importance analysis
3. Validación temporal
4. Distribución de errores
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.inspection import permutation_importance
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

def load_elite_data_with_metadata():
    """Load ELITE data with all metadata for leakage detection."""
    print("📊 Loading ELITE data with metadata...")
    
    engine = create_engine(DB_URL)
    
    query = """
    SELECT f.*, g.source, g.date_played, g.white_elo, g.black_elo, g.result
    FROM features f
    JOIN games g ON f.game_id = g.game_id
    WHERE g.source = 'elite' AND f.error_label IS NOT NULL
    ORDER BY g.date_played
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    
    print(f"✅ Loaded {len(df)} ELITE samples")
    print(f"📅 Date range: {df['date_played'].min()} to {df['date_played'].max()}")
    
    return df

def analyze_feature_importance(df):
    """Analyze feature importance to detect suspicious features."""
    print("\n🔍 FEATURE IMPORTANCE ANALYSIS")
    print("="*50)
    
    # Prepare data
    feature_columns = [col for col in df.columns if col not in [
        'game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci', 
        'error_label', 'source', 'date_played', 'white_elo', 'black_elo', 'result'
    ]]
    
    X = df[feature_columns].select_dtypes(include=[np.number]).fillna(0)
    y = df['error_label']
    
    print(f"Features analyzed: {len(feature_columns)}")
    
    # Train simple RF model
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    rf.fit(X_train, y_train)
    
    # Get feature importance
    importances = pd.DataFrame({
        'feature': X.columns,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🏆 TOP 20 MOST IMPORTANT FEATURES:")
    print(importances.head(20).to_string(index=False))
    
    # Check for extremely high importance (potential leakage)
    suspicious_features = importances[importances['importance'] > 0.1]
    if len(suspicious_features) > 0:
        print(f"\n⚠️ SUSPICIOUS FEATURES (importance > 0.1):")
        print(suspicious_features.to_string(index=False))
    
    # Permutation importance for validation
    print("\n🔄 Calculating permutation importance...")
    perm_importance = permutation_importance(rf, X_test, y_test, n_repeats=5, random_state=42)
    
    perm_df = pd.DataFrame({
        'feature': X.columns,
        'perm_importance_mean': perm_importance.importances_mean,
        'perm_importance_std': perm_importance.importances_std
    }).sort_values('perm_importance_mean', ascending=False)
    
    print("\n🏆 TOP 20 PERMUTATION IMPORTANCE:")
    print(perm_df.head(20).to_string(index=False))
    
    return importances, perm_df

def temporal_validation(df):
    """Test model with temporal validation to detect overfitting."""
    print("\n⏰ TEMPORAL VALIDATION ANALYSIS")
    print("="*50)
    
    # Sort by date
    df_sorted = df.sort_values('date_played').copy()
    
    # Prepare features
    feature_columns = [col for col in df.columns if col not in [
        'game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci', 
        'error_label', 'source', 'date_played', 'white_elo', 'black_elo', 'result'
    ]]
    
    X = df_sorted[feature_columns].select_dtypes(include=[np.number]).fillna(0)
    y = df_sorted['error_label']
    
    # Temporal split: 80% early data for training, 20% recent data for testing
    split_point = int(len(df_sorted) * 0.8)
    
    X_train_temporal = X.iloc[:split_point]
    X_test_temporal = X.iloc[split_point:]
    y_train_temporal = y.iloc[:split_point]
    y_test_temporal = y.iloc[split_point:]
    
    train_date_max = df_sorted.iloc[split_point-1]['date_played']
    test_date_min = df_sorted.iloc[split_point]['date_played']
    
    print(f"📅 Training data: up to {train_date_max} ({len(X_train_temporal)} samples)")
    print(f"📅 Testing data: from {test_date_min} ({len(X_test_temporal)} samples)")
    
    # Train with same parameters as original
    rf_temporal = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    
    rf_temporal.fit(X_train_temporal, y_train_temporal)
    y_pred_temporal = rf_temporal.predict(X_test_temporal)
    
    f1_temporal = f1_score(y_test_temporal, y_pred_temporal, average='weighted')
    
    print(f"\n📊 TEMPORAL VALIDATION RESULTS:")
    print(f"F1 Score (temporal): {f1_temporal:.3f}")
    print(f"Difference from random split: {0.999 - f1_temporal:.3f}")
    
    if f1_temporal < 0.8:
        print("⚠️ SIGNIFICANT DROP! Strong indication of overfitting")
    elif f1_temporal < 0.9:
        print("⚠️ Moderate drop. Some overfitting detected")
    else:
        print("✅ Minor drop. Model seems robust")
    
    print("\n📋 Detailed Classification Report (Temporal):")
    print(classification_report(y_test_temporal, y_pred_temporal))
    
    return f1_temporal

def analyze_label_distribution(df):
    """Analyze error label distribution for patterns."""
    print("\n📊 ERROR LABEL DISTRIBUTION ANALYSIS")
    print("="*50)
    
    # Overall distribution
    label_dist = df['error_label'].value_counts()
    print("Overall distribution:")
    print(label_dist)
    print(f"Percentage: {label_dist / len(df) * 100}")
    
    # Distribution by ELO ranges
    if 'white_elo' in df.columns and 'black_elo' in df.columns:
        df['avg_elo'] = (df['white_elo'] + df['black_elo']) / 2
        df['elo_range'] = pd.cut(df['avg_elo'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        
        print("\n🎯 Error distribution by ELO ranges:")
        elo_dist = pd.crosstab(df['elo_range'], df['error_label'], normalize='index')
        print(elo_dist.round(3))
        
        # Check if distribution is too imbalanced
        max_class_prop = label_dist.max() / len(df)
        print(f"\n⚖️ Largest class proportion: {max_class_prop:.3f}")
        
        if max_class_prop > 0.95:
            print("⚠️ SEVERE CLASS IMBALANCE! This could cause overfitting")
        elif max_class_prop > 0.9:
            print("⚠️ High class imbalance detected")
    
    return label_dist

def suggest_improvements():
    """Suggest improvements to reduce overfitting."""
    print("\n💡 RECOMMENDATIONS TO REDUCE OVERFITTING")
    print("="*60)
    
    suggestions = [
        "1. 🌳 RANDOM FOREST REGULARIZATION:",
        "   - Reduce n_estimators: 200 → 100",
        "   - Reduce max_depth: 15 → 8-10", 
        "   - Increase min_samples_split: 10 → 20-50",
        "   - Increase min_samples_leaf: 5 → 10-20",
        "   - Add max_features: 'sqrt' or 0.3",
        "",
        "2. 🔍 FEATURE ENGINEERING:",
        "   - Remove high-importance suspicious features",
        "   - Add feature selection (SelectKBest, RFE)",
        "   - Check for data leakage in features",
        "",
        "3. ✅ VALIDATION STRATEGY:",
        "   - Use temporal validation instead of random split",
        "   - Implement nested cross-validation",
        "   - Use stratified folds for imbalanced data",
        "",
        "4. 📊 DATA QUALITY:",
        "   - Balance classes with SMOTE/undersampling",
        "   - Remove duplicate or near-duplicate samples",
        "   - Add more diverse data if possible",
        "",
        "5. 🎯 MODEL COMPLEXITY:",
        "   - Try simpler models (Logistic Regression)",
        "   - Add L1/L2 regularization",
        "   - Use ensemble with diversity"
    ]
    
    for suggestion in suggestions:
        print(suggestion)

def main():
    print("🚨 OVERFITTING DIAGNOSIS - ELITE MODEL")
    print("="*60)
    
    # Load data
    df = load_elite_data_with_metadata()
    
    # Run analyses
    print("\n" + "="*60)
    importances, perm_importance = analyze_feature_importance(df)
    
    print("\n" + "="*60)
    f1_temporal = temporal_validation(df)
    
    print("\n" + "="*60)
    label_dist = analyze_label_distribution(df)
    
    print("\n" + "="*60)
    suggest_improvements()
    
    # Summary
    print(f"\n🏁 DIAGNOSIS SUMMARY")
    print("="*30)
    print(f"Original F1 (random split): 0.999")
    print(f"Temporal F1 (time-based):   {f1_temporal:.3f}")
    print(f"Performance drop:           {0.999 - f1_temporal:.3f}")
    
    if f1_temporal < 0.8:
        verdict = "🚨 SEVERE OVERFITTING"
    elif f1_temporal < 0.9:
        verdict = "⚠️ MODERATE OVERFITTING" 
    else:
        verdict = "✅ MINOR OVERFITTING"
    
    print(f"Verdict: {verdict}")

if __name__ == "__main__":
    main()