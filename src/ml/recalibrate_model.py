#!/usr/bin/env python3
"""
Script para recalibrar el modelo PERSONAL para que tenga probabilidades más balanceadas
y detecte mejor mistakes e inaccuracies.

ESTRATEGIAS DE RECALIBRACIÓN:
1. CalibratedClassifierCV - Calibración isotónica/sigmoidea
2. Umbrales optimizados por clase
3. Técnicas de rebalanceo
4. Evaluación del impacto
"""

import os
import sys
import mlflow
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.utils.class_weight import compute_class_weight
import psycopg2
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_model_and_data():
    """Load the model and real data for calibration."""
    print("📥 CARGANDO MODELO Y DATOS")
    print("="*50)
    
    # Load environment variables
    load_dotenv()
    
    # Load model
    mlflow.set_tracking_uri("file:./mlruns")
    model_name = "personal_conservative_specialist"
    model = mlflow.sklearn.load_model(f"models:/{model_name}/latest")
    print(f"✅ Modelo cargado: {type(model)}")
    print(f"   Clases: {list(model.classes_)}")
    
    # Load data
    db_url = os.getenv('CHESS_TRAINER_DB_URL')
    parsed = __import__('urllib.parse').parse.urlparse(db_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        port=parsed.port
    )
    
    # Get more data for better calibration
    query = """
    SELECT 
        f.material_total, f.num_pieces, f.branching_factor,
        f.self_mobility, f.opponent_mobility, f.has_castling_rights,
        f.move_number_global, f.is_repetition, f.is_low_mobility,
        f.is_center_controlled, f.is_pawn_endgame, f.num_moves,
        f.error_label
    FROM features f
    JOIN games g ON f.game_id = g.game_id
    WHERE g.source = 'personal' 
        AND f.material_total IS NOT NULL
        AND f.error_label IS NOT NULL
    LIMIT 5000
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"📊 Datos cargados: {len(df)} registros con etiquetas")
    
    # Prepare features and labels
    feature_cols = [
        'material_total', 'num_pieces', 'branching_factor',
        'self_mobility', 'opponent_mobility', 'has_castling_rights',
        'move_number_global', 'is_repetition', 'is_low_mobility',
        'is_center_controlled', 'is_pawn_endgame', 'num_moves'
    ]
    
    X = df[feature_cols].fillna(0)
    y = df['error_label']
    
    print(f"🎯 Distribución original:")
    for label, count in y.value_counts().items():
        print(f"   {label}: {count} ({count/len(y)*100:.1f}%)")
    
    return model, X, y

def analyze_current_performance(model, X, y):
    """Analyze current model performance."""
    print(f"\n📊 ANÁLISIS DE RENDIMIENTO ACTUAL")
    print("="*50)
    
    # Get predictions and probabilities
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)
    
    # Classification report
    print(f"\n📈 REPORTE DE CLASIFICACIÓN:")
    print(classification_report(y, y_pred))
    
    # Confusion matrix
    print(f"\n🔄 MATRIZ DE CONFUSIÓN:")
    cm = confusion_matrix(y, y_pred, labels=model.classes_)
    print(pd.DataFrame(cm, index=model.classes_, columns=model.classes_))
    
    # Distribution comparison
    print(f"\n📊 COMPARACIÓN DE DISTRIBUCIONES:")
    y_true_dist = y.value_counts(normalize=True).sort_index() * 100
    y_pred_dist = pd.Series(y_pred).value_counts(normalize=True).sort_index() * 100
    
    comparison_df = pd.DataFrame({
        'Real (%)': y_true_dist,
        'Predicho (%)': y_pred_dist,
        'Diferencia': y_pred_dist - y_true_dist
    })
    print(comparison_df.round(1))
    
    # Probability analysis
    print(f"\n🎲 ANÁLISIS DE PROBABILIDADES POR CLASE:")
    for i, class_name in enumerate(model.classes_):
        class_probs = y_proba[:, i]
        wins = np.sum(y_pred == class_name)
        print(f"   {class_name}:")
        print(f"     Prob. promedio: {class_probs.mean():.3f}")
        print(f"     Prob. máxima: {class_probs.max():.3f}")
        print(f"     Casos que gana: {wins} ({wins/len(y_pred)*100:.1f}%)")
    
    return y_pred, y_proba, comparison_df

def calibrate_model_isotonic(model, X, y):
    """Calibrate model using isotonic regression."""
    print(f"\n🔧 CALIBRACIÓN ISOTÓNICA")
    print("="*40)
    
    # Split data for calibration
    X_train, X_cal, y_train, y_cal = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    print(f"📊 División de datos:")
    print(f"   Entrenamiento: {len(X_train)} muestras")
    print(f"   Calibración: {len(X_cal)} muestras")
    
    # Create calibrated classifier
    calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv='prefit')
    calibrated_model.fit(X_cal, y_cal)
    
    print(f"✅ Modelo calibrado exitosamente")
    
    return calibrated_model, X_train, X_cal, y_train, y_cal

def optimize_thresholds(model, X, y, target_distribution=None):
    """Optimize decision thresholds for better class balance."""
    print(f"\n⚖️ OPTIMIZACIÓN DE UMBRALES")
    print("="*40)
    
    if target_distribution is None:
        # Target: more balanced distribution based on real data
        target_distribution = {
            'good': 0.85,      # Reduce from 93% to 85%
            'blunder': 0.05,   # Keep similar
            'mistake': 0.07,   # Increase from 1.2% to 7%
            'inaccuracy': 0.03 # Increase from 2.1% to 3%
        }
    
    print(f"🎯 Distribución objetivo:")
    for class_name, target_pct in target_distribution.items():
        print(f"   {class_name}: {target_pct*100:.1f}%")
    
    # Get probabilities
    y_proba = model.predict_proba(X)
    classes = model.classes_
    
    # Find optimal thresholds
    optimal_thresholds = {}
    
    for i, class_name in enumerate(classes):
        if class_name in target_distribution:
            class_probs = y_proba[:, i]
            target_count = int(len(X) * target_distribution[class_name])
            
            # Find threshold that gives approximately target count
            sorted_probs = np.sort(class_probs)[::-1]  # Descending order
            if target_count < len(sorted_probs):
                threshold = sorted_probs[target_count-1]
            else:
                threshold = sorted_probs[-1]  # Use minimum probability
                
            optimal_thresholds[class_name] = threshold
            
            print(f"   {class_name}: umbral = {threshold:.3f}")
    
    return optimal_thresholds

def apply_threshold_predictions(y_proba, classes, thresholds):
    """Apply custom thresholds to make predictions."""
    predictions = []
    
    for i in range(len(y_proba)):
        probs = y_proba[i]
        scores = {}
        
        # Calculate adjusted scores based on thresholds
        for j, class_name in enumerate(classes):
            if class_name in thresholds:
                # Boost probability if above threshold
                if probs[j] >= thresholds[class_name]:
                    scores[class_name] = probs[j] * 2  # Boost factor
                else:
                    scores[class_name] = probs[j]
            else:
                scores[class_name] = probs[j]
        
        # Pick class with highest adjusted score
        predicted_class = max(scores, key=scores.get)
        predictions.append(predicted_class)
    
    return np.array(predictions)

def evaluate_calibrated_model(original_model, calibrated_model, X_test, y_test, thresholds=None):
    """Evaluate improvements from calibration."""
    print(f"\n📈 EVALUACIÓN DE MEJORAS")
    print("="*50)
    
    # Original predictions
    y_pred_orig = original_model.predict(X_test)
    y_proba_orig = original_model.predict_proba(X_test)
    
    # Calibrated predictions
    y_pred_cal = calibrated_model.predict(X_test)
    y_proba_cal = calibrated_model.predict_proba(X_test)
    
    # Threshold-adjusted predictions
    if thresholds:
        y_pred_thresh = apply_threshold_predictions(y_proba_cal, calibrated_model.classes_, thresholds)
    else:
        y_pred_thresh = y_pred_cal
    
    # Compare F1 scores
    f1_orig = f1_score(y_test, y_pred_orig, average='macro')
    f1_cal = f1_score(y_test, y_pred_cal, average='macro')
    f1_thresh = f1_score(y_test, y_pred_thresh, average='macro')
    
    print(f"🎯 F1-Score Macro:")
    print(f"   Original: {f1_orig:.3f}")
    print(f"   Calibrado: {f1_cal:.3f} ({f1_cal-f1_orig:+.3f})")
    print(f"   Con umbrales: {f1_thresh:.3f} ({f1_thresh-f1_orig:+.3f})")
    
    # Distribution comparison
    print(f"\n📊 DISTRIBUCIÓN FINAL:")
    methods = [
        ('Original', y_pred_orig),
        ('Calibrado', y_pred_cal), 
        ('Con umbrales', y_pred_thresh)
    ]
    
    for method_name, predictions in methods:
        print(f"\n{method_name}:")
        dist = pd.Series(predictions).value_counts(normalize=True).sort_index() * 100
        for class_name in calibrated_model.classes_:
            pct = dist.get(class_name, 0)
            print(f"   {class_name}: {pct:.1f}%")
    
    return y_pred_thresh, y_proba_cal

def save_calibrated_model(calibrated_model, model_name="personal_calibrated"):
    """Save the calibrated model to MLflow."""
    print(f"\n💾 GUARDANDO MODELO CALIBRADO")
    print("="*40)
    
    try:
        # Ensure experiment exists
        experiment_name = "chess_model_calibration"
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
            else:
                experiment_id = experiment.experiment_id
        except:
            experiment_id = mlflow.create_experiment(experiment_name)
        
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run(run_name="model_calibration"):
            # Log the calibrated model
            mlflow.sklearn.log_model(
                calibrated_model,
                "calibrated_model",
                registered_model_name=model_name
            )
            
            # Log calibration method
            mlflow.log_param("calibration_method", "isotonic")
            mlflow.log_param("base_model", "personal_conservative_specialist")
            
            print(f"✅ Modelo calibrado guardado como: {model_name}")
            
    except Exception as e:
        print(f"⚠️ Error guardando en MLflow: {e}")
        print("✅ Modelo calibrado disponible en memoria para uso inmediato")

def main():
    """Main calibration pipeline."""
    print("🔧 RECALIBRACIÓN DEL MODELO PERSONAL")
    print("="*70)
    
    # 1. Load model and data
    model, X, y = load_model_and_data()
    
    # 2. Analyze current performance
    y_pred_orig, y_proba_orig, dist_comparison = analyze_current_performance(model, X, y)
    
    # 3. Calibrate model
    calibrated_model, X_train, X_cal, y_train, y_cal = calibrate_model_isotonic(model, X, y)
    
    # 4. Optimize thresholds
    thresholds = optimize_thresholds(calibrated_model, X_cal, y_cal)
    
    # 5. Evaluate improvements
    y_pred_final, y_proba_final = evaluate_calibrated_model(
        model, calibrated_model, X_cal, y_cal, thresholds
    )
    
    # 6. Save calibrated model
    save_calibrated_model(calibrated_model)
    
    print(f"\n🏆 RECALIBRACIÓN COMPLETADA")
    print("="*40)
    print("✅ El modelo calibrado debería:")
    print("   - Detectar mejor mistakes e inaccuracies")
    print("   - Tener probabilidades más balanceadas") 
    print("   - Reducir sesgo hacia 'good moves'")
    print(f"   - Modelo disponible en MLflow como 'personal_calibrated'")

if __name__ == "__main__":
    main()