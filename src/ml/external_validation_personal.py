#!/usr/bin/env python3
"""
Validación Externa con Nuevas Partidas Personales

Este script permite validar el modelo PERSONAL con partidas nuevas que NO están
en el dataset de entrenamiento, para evaluar la capacidad de generalización real.

Flujo:
1. Importar nuevas partidas PGN (sin contaminar dataset de entrenamiento)
2. Generar features usando el mismo pipeline
3. Aplicar modelo PERSONAL ya entrenado
4. Comparar predicciones con análisis manual/motor
5. Generar reporte de validación externa

Uso:
    python src/ml/external_validation_personal.py --pgn-file "mis_nuevas_partidas.pgn"
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

# Import existing scripts for feature generation
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def import_new_games_temporarily(pgn_file: str, temp_db_url: str = None):
    """
    Import new games to a TEMPORARY table to avoid contaminating training data.
    
    Args:
        pgn_file: Path to PGN file with new games
        temp_db_url: Optional separate DB for validation
    
    Returns:
        List of game_ids for the imported games
    """
    print(f"📥 Importing NEW games from {pgn_file} (temporary, no contamination)")
    
    # TODO: Implement temporary import
    # For now, we'll create a strategy that marks these games as "validation_external"
    
    print("⚠️ IMPORTANT: New games will be marked as 'validation_external'")
    print("   This prevents contamination of training data")
    
    # Strategy: Import to games table with source='validation_external'
    import_command = f"""
    python src/scripts/import_pgns_parallel.py \\
        --source validation_external \\
        --pgn-files "{pgn_file}" \\
        --max-games 100 \\
        --workers 1
    """
    
    print(f"🔧 Run this command first:")
    print(import_command)
    
    return []

def generate_validation_features(source="validation_external"):
    """Generate features for validation games."""
    print(f"🔧 Generating features for {source} games...")
    
    feature_command = f"""
    python src/scripts/generate_features_with_tactics.py \\
        --source {source} \\
        --max-games 100 \\
        --workers 2
    """
    
    print(f"🔧 Run this command:")
    print(feature_command)
    
    return True

def load_trained_personal_model():
    """Load the trained PERSONAL model from MLflow."""
    print("🤖 Loading trained PERSONAL model...")
    
    try:
        # Try to load latest version of personal model
        model_name = "personal_conservative_specialist"
        model_version = "latest"
        
        model_uri = f"models:/{model_name}/{model_version}"
        model = mlflow.sklearn.load_model(model_uri)
        
        print(f"✅ Loaded {model_name} version {model_version}")
        return model
    
    except Exception as e:
        print(f"❌ Could not load model from MLflow: {e}")
        print("💡 Alternative: Load from local mlruns folder")
        
        # Alternative: Load from local file system
        # You would need to navigate mlruns folder to find the model
        print("🔧 Check ./mlruns folder for personal_conservative_specialist model")
        return None

def load_validation_features():
    """Load features for validation games."""
    print("📊 Loading validation features...")
    
    from sqlalchemy import create_engine
    
    DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
    engine = create_engine(DB_URL)
    
    query = """
    SELECT f.*, g.game_id, g.white_player, g.black_player, g.result, g.date_played
    FROM features f
    JOIN games g ON f.game_id = g.game_id
    WHERE g.source = 'validation_holdout' AND f.error_label IS NOT NULL
    ORDER BY g.game_id, f.move_number
    """
    
    try:
        df = pd.read_sql(query, engine)
        engine.dispose()
        
        print(f"✅ Loaded {len(df)} moves from validation games")
        return df
    
    except Exception as e:
        print(f"❌ Error loading validation features: {e}")
        engine.dispose()
        return pd.DataFrame()

def prepare_features_for_prediction(df):
    """Prepare features in same format as training (remove excluded features)."""
    print("🔧 Preparing features for prediction...")
    
    # Same excluded features as in training
    EXCLUDED_FEATURES = [
        'score_diff',         # Data leakage
        'material_balance',   # Potential leakage
    ]
    
    # Same exclude columns as training
    exclude_columns = [
        'game_id', 'move_number', 'player_color', 'fen', 'move_san', 'move_uci', 
        'error_label', 'white_player', 'black_player', 'result', 'date_played'
    ] + EXCLUDED_FEATURES
    
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].copy()
    X = X.select_dtypes(include=[np.number])  # Only numeric features
    X = X.fillna(0)  # Fill NaN with 0
    
    # Remove excluded features if they exist
    remaining_excluded = [col for col in EXCLUDED_FEATURES if col in X.columns]
    if remaining_excluded:
        print(f"🚫 Excluding features with potential leakage: {remaining_excluded}")
        X = X.drop(columns=remaining_excluded)
    
    print(f"✅ Prepared {X.shape[1]} features for {len(X)} moves")
    return X

def make_predictions(model, X):
    """Make predictions using the trained model."""
    print("🎯 Making predictions...")
    
    try:
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        print(f"✅ Made predictions for {len(predictions)} moves")
        
        # Get class names (error types)
        classes = model.classes_ if hasattr(model, 'classes_') else ['blunder', 'mistake', 'inaccuracy', 'good']
        
        return predictions, probabilities, classes
    
    except Exception as e:
        print(f"❌ Error making predictions: {e}")
        return None, None, None

def create_validation_report(df, predictions, probabilities, classes):
    """Create detailed validation report."""
    print("📋 Creating validation report...")
    
    # Add predictions to dataframe
    df_report = df.copy()
    df_report['predicted_error'] = predictions
    
    # Add actual vs predicted comparison
    df_report['actual_error'] = df_report['error_label']
    df_report['prediction_correct'] = (df_report['actual_error'] == df_report['predicted_error'])
    
    # Add probability columns
    for i, class_name in enumerate(classes):
        df_report[f'prob_{class_name}'] = probabilities[:, i]
    
    # Calculate accuracy metrics
    total_moves = len(df_report)
    correct_predictions = df_report['prediction_correct'].sum()
    accuracy = correct_predictions / total_moves
    
    print(f"\n🎯 VALIDATION ACCURACY: {accuracy:.3f} ({correct_predictions}/{total_moves})")
    
    # Group by game for summary - fix column selection
    game_cols = ['game_id', 'white_player', 'black_player', 'date_played']
    # Ensure we're using scalar values for grouping
    df_for_grouping = df_report.copy()
    
    game_summary = df_for_grouping.groupby(game_cols).agg({
        'predicted_error': ['count', lambda x: list(x)],
        'actual_error': [lambda x: list(x)], 
        'prediction_correct': ['sum', 'count'],
        'prob_blunder': 'mean',
        'prob_mistake': 'mean', 
        'prob_inaccuracy': 'mean',
        'prob_good': 'mean'
    }).round(3)
    
    # Flatten column names
    game_summary.columns = ['total_moves', 'predicted_errors', 'actual_errors', 
                           'correct_predictions', 'total_predictions',
                           'avg_prob_blunder', 'avg_prob_mistake', 
                           'avg_prob_inaccuracy', 'avg_prob_good']
    
    # Calculate per-game accuracy
    game_summary['game_accuracy'] = (game_summary['correct_predictions'] / 
                                   game_summary['total_predictions']).round(3)
    
    # Count predictions per game
    for error_type in classes:
        game_summary[f'predicted_{error_type}'] = game_summary['predicted_errors'].apply(
            lambda x: sum(1 for pred in x if pred == error_type)
        )
        game_summary[f'actual_{error_type}'] = game_summary['actual_errors'].apply(
            lambda x: sum(1 for actual in x if actual == error_type)
        )
    
    print("\n📊 VALIDATION RESULTS BY GAME:")
    print("="*80)
    display_cols = ['total_moves', 'game_accuracy', 'predicted_good', 'actual_good', 
                   'predicted_mistake', 'actual_mistake']
    print(game_summary[display_cols].head(10).to_string())
    
    # Overall statistics comparison
    print(f"\n📈 ACTUAL vs PREDICTED DISTRIBUTION:")
    actual_counts = pd.Series(df_report['actual_error']).value_counts()
    pred_counts = pd.Series(predictions).value_counts()
    
    comparison_df = pd.DataFrame({
        'Actual_Count': actual_counts,
        'Predicted_Count': pred_counts,
        'Actual_Pct': (actual_counts / len(df_report) * 100).round(1),
        'Predicted_Pct': (pred_counts / len(df_report) * 100).round(1)
    }).fillna(0)
    
    print(comparison_df)
    
    # Confusion Matrix-like summary
    print(f"\n🔍 PREDICTION ACCURACY BY ERROR TYPE:")
    for error_type in classes:
        mask = df_report['actual_error'] == error_type
        if mask.sum() > 0:
            type_accuracy = df_report[mask]['prediction_correct'].mean()
            print(f"  {error_type:>12}: {type_accuracy:.3f} ({df_report[mask]['prediction_correct'].sum()}/{mask.sum()})")
    
    return df_report, game_summary

def main():
    parser = argparse.ArgumentParser(description="External Validation with New Personal Games")
    parser.add_argument('--pgn-file', type=str, required=True,
                       help='Path to PGN file with NEW games for validation')
    parser.add_argument('--skip-import', action='store_true',
                       help='Skip import step (games already imported)')
    parser.add_argument('--skip-features', action='store_true',
                       help='Skip feature generation (features already generated)')
    parser.add_argument('--output-dir', type=str, default='./validation_results',
                       help='Directory to save validation results')
    
    args = parser.parse_args()
    
    print("🚀 EXTERNAL VALIDATION: PERSONAL LEVEL MODEL")
    print("="*60)
    print(f"📁 PGN File: {args.pgn_file}")
    print(f"📁 Output: {args.output_dir}")
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Import games (if needed)
    if not args.skip_import:
        if not os.path.exists(args.pgn_file):
            print(f"❌ PGN file not found: {args.pgn_file}")
            return
        
        import_new_games_temporarily(args.pgn_file)
        print(f"⏭️ Please run the import command above, then re-run with --skip-import")
        return
    
    # Step 2: Generate features (if needed)  
    if not args.skip_features:
        generate_validation_features()
        print(f"⏭️ Please run the feature command above, then re-run with --skip-features")
        return
    
    # Step 3: Load trained model
    model = load_trained_personal_model()
    if model is None:
        print("❌ Cannot proceed without trained model")
        return
    
    # Step 4: Load validation features
    df = load_validation_features()
    if df.empty:
        print("❌ No validation features found")
        return
    
    # Step 5: Prepare features
    X = prepare_features_for_prediction(df)
    if X.empty:
        print("❌ No valid features for prediction")
        return
    
    # Step 6: Make predictions
    predictions, probabilities, classes = make_predictions(model, X)
    if predictions is None:
        print("❌ Prediction failed")
        return
    
    # Step 7: Create report
    df_report, game_summary = create_validation_report(df, predictions, probabilities, classes)
    
    # Step 8: Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save detailed results
    detail_file = os.path.join(args.output_dir, f'validation_details_{timestamp}.csv')
    df_report.to_csv(detail_file, index=False)
    print(f"💾 Detailed results saved: {detail_file}")
    
    # Save game summary
    summary_file = os.path.join(args.output_dir, f'validation_summary_{timestamp}.csv')
    game_summary.to_csv(summary_file)
    print(f"💾 Game summary saved: {summary_file}")
    
    print("\n🎉 EXTERNAL VALIDATION COMPLETED!")
    print("="*40)
    print(f"✅ Analyzed {len(df)} moves from {len(game_summary)} games")
    print(f"🤖 Used PERSONAL model (F1: 0.468 on training)")
    print(f"📊 Results saved in {args.output_dir}")

if __name__ == "__main__":
    main()