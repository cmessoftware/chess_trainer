#!/usr/bin/env python3
"""
Script para investigar las clases reales del modelo PERSONAL
y ver qué está prediciendo exactamente.

INVESTIGACIÓN PROFUNDA:
- ¿Por qué solo predice blunders y good moves?
- ¿Cuáles son los umbrales de decisión?
- ¿Cómo se distribuyen las probabilidades?
"""

import os
import sys
import mlflow
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix
import sqlite3

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def load_and_inspect_personal_model():
    """Load and inspect the PERSONAL model."""
    print("🔍 INVESTIGANDO MODELO PERSONAL")
    print("="*50)
    
    try:
        # Set MLflow tracking URI to local
        mlflow.set_tracking_uri("file:./mlruns")
        
        # Load model
        model_name = "personal_conservative_specialist"
        print(f"📥 Cargando modelo: {model_name}")
        
        model = mlflow.sklearn.load_model(f"models:/{model_name}/latest")
        print("✅ Modelo cargado exitosamente")
        
        # Inspect model classes
        if hasattr(model, 'classes_'):
            print(f"\n🎯 CLASES DEL MODELO:")
            print(f"   Tipo: {type(model.classes_)}")
            print(f"   Clases: {model.classes_}")
            print(f"   Cantidad: {len(model.classes_)} clases")
            
            # Convert to list if numpy array
            if isinstance(model.classes_, np.ndarray):
                classes_list = list(model.classes_)
                print(f"   Como lista: {classes_list}")
            
        else:
            print("❌ El modelo no tiene atributo 'classes_'")
        
        # Inspect model type
        print(f"\n🤖 INFORMACIÓN DEL MODELO:")
        print(f"   Tipo: {type(model)}")
        
        # Check if it's a pipeline
        if hasattr(model, 'steps'):
            print(f"   Es un Pipeline con pasos:")
            for i, (step_name, step_obj) in enumerate(model.steps):
                print(f"     {i+1}. {step_name}: {type(step_obj)}")
                
                # Check if final estimator has classes
                if i == len(model.steps) - 1 and hasattr(step_obj, 'classes_'):
                    print(f"       Clases del estimador final: {step_obj.classes_}")
        
        return model
        
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return None

def analyze_prediction_distribution():
    """Analyze how predictions are distributed in real data."""
    print(f"\n📊 ANÁLISIS DE DISTRIBUCIÓN DE PREDICCIONES")
    print("="*60)
    
    try:
        # Connect to database and get sample data
        import psycopg2
        import pandas as pd
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Get database connection from environment
        db_url = os.getenv('CHESS_TRAINER_DB_URL')
        if not db_url:
            print("❌ CHESS_TRAINER_DB_URL no está configurado")
            return None, None, None, None
        
        # Extract connection parameters
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            port=parsed.port
        )
        
        # Get sample of personal games features
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
        LIMIT 1000
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) == 0:
            print("❌ No hay datos de features personales")
            return
        
        print(f"📈 Datos obtenidos: {len(df)} registros")
        
        # Prepare features
        feature_cols = [
            'material_total', 'num_pieces', 'branching_factor',
            'self_mobility', 'opponent_mobility', 'has_castling_rights',
            'move_number_global', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'num_moves'
        ]
        
        X = df[feature_cols].fillna(0)
        y_true = df['error_label'].fillna('good')
        
        # Load model
        model = load_and_inspect_personal_model()
        if model is None:
            return
        
        # Make predictions
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        
        # Analyze results
        print(f"\n🎯 DISTRIBUCIÓN DE PREDICCIONES:")
        unique, counts = np.unique(predictions, return_counts=True)
        for class_name, count in zip(unique, counts):
            percentage = (count / len(predictions)) * 100
            print(f"   {class_name}: {count} ({percentage:.1f}%)")
        
        print(f"\n🎯 DISTRIBUCIÓN DE ETIQUETAS REALES:")
        unique_true, counts_true = np.unique(y_true, return_counts=True)
        for class_name, count in zip(unique_true, counts_true):
            percentage = (count / len(y_true)) * 100
            print(f"   {class_name}: {count} ({percentage:.1f}%)")
        
        # Analyze probability thresholds
        print(f"\n🎚️ ANÁLISIS DE UMBRALES DE PROBABILIDAD:")
        classes = model.classes_
        
        for i, class_name in enumerate(classes):
            class_probs = probabilities[:, i]
            print(f"   {class_name}:")
            print(f"     Min: {class_probs.min():.3f}")
            print(f"     Max: {class_probs.max():.3f}")
            print(f"     Media: {class_probs.mean():.3f}")
            print(f"     Mediana: {np.median(class_probs):.3f}")
            
            # Show cases where this class has high probability
            high_prob_mask = class_probs > 0.5
            high_prob_count = np.sum(high_prob_mask)
            print(f"     Casos con P > 0.5: {high_prob_count} ({high_prob_count/len(class_probs)*100:.1f}%)")
            
            # Show some examples where this class has highest probability
            if high_prob_count > 0:
                max_prob_idx = np.argmax(class_probs)
                predicted_class = predictions[max_prob_idx]
                actual_class = y_true.iloc[max_prob_idx]
                max_prob_value = class_probs[max_prob_idx]
                print(f"     Ejemplo de máx prob: P={max_prob_value:.3f}, Predicho='{predicted_class}', Real='{actual_class}'")
        
        return df, predictions, probabilities, y_true
        
    except Exception as e:
        print(f"❌ Error en análisis de distribución: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None

def investigate_decision_boundaries():
    """Investigate why the model only predicts certain classes."""
    print(f"\n🧠 INVESTIGACIÓN DE FRONTERAS DE DECISIÓN")
    print("="*60)
    
    # Get data and predictions
    df, predictions, probabilities, y_true = analyze_prediction_distribution()
    
    if df is None:
        return
    
    model = load_and_inspect_personal_model()
    if model is None:
        return
    
    # Analyze prediction logic
    print(f"\n🔍 LÓGICA DE PREDICCIÓN:")
    
    # Check if it's using argmax
    manual_predictions = []
    for prob_row in probabilities:
        predicted_class_idx = np.argmax(prob_row)
        predicted_class = model.classes_[predicted_class_idx]
        manual_predictions.append(predicted_class)
    
    manual_predictions = np.array(manual_predictions)
    matches_argmax = np.all(predictions == manual_predictions)
    print(f"   ¿Usa argmax? {matches_argmax}")
    
    if matches_argmax:
        print(f"   ✅ El modelo predice la clase con mayor probabilidad")
        
        # Analyze why certain classes never win
        print(f"\n🤔 ¿POR QUÉ CIERTAS CLASES NUNCA GANAN?")
        
        for i, class_name in enumerate(model.classes_):
            class_wins = np.sum(predictions == class_name)
            max_prob_for_class = np.max(probabilities[:, i])
            avg_prob_for_class = np.mean(probabilities[:, i])
            
            print(f"   {class_name}:")
            print(f"     Veces que ganó: {class_wins}")
            print(f"     Probabilidad máxima: {max_prob_for_class:.3f}")
            print(f"     Probabilidad promedio: {avg_prob_for_class:.3f}")
            
            if class_wins == 0:
                print(f"     ❌ NUNCA GANA - Nunca tiene la máxima probabilidad")
                
                # Find cases where this class is close to winning
                prob_diff_to_winner = []
                for j, prob_row in enumerate(probabilities):
                    winner_prob = np.max(prob_row)
                    this_class_prob = prob_row[i]
                    diff = winner_prob - this_class_prob
                    prob_diff_to_winner.append(diff)
                
                min_diff = np.min(prob_diff_to_winner)
                min_diff_idx = np.argmin(prob_diff_to_winner)
                
                print(f"     Caso más cercano a ganar: diferencia de {min_diff:.3f}")
                print(f"     En ese caso, probabilidades:")
                for k, other_class in enumerate(model.classes_):
                    prob_val = probabilities[min_diff_idx, k]
                    print(f"       {other_class}: {prob_val:.3f}")
    
    print(f"\n📈 CONCLUSIONES:")
    if 'mistake' in model.classes_ and np.sum(predictions == 'mistake') == 0:
        print(f"   ❌ 'mistake' nunca se predice")
    if 'inaccuracy' in model.classes_ and np.sum(predictions == 'inaccuracy') == 0:
        print(f"   ❌ 'inaccuracy' nunca se predice")
    if np.sum(predictions == 'blunder') > 0:
        print(f"   ✅ 'blunder' sí se predice")
    if np.sum(predictions == 'good') > 0:
        print(f"   ✅ 'good' sí se predice")

def test_model_predictions():
    """Test what the model actually predicts."""
    model = load_and_inspect_personal_model()
    
    if model is None:
        return
    
    # Create some dummy features to test prediction
    print(f"\n🧪 PRUEBA DE PREDICCIONES:")
    
    # Multiple test cases with different characteristics
    test_cases = [
        {
            'name': 'Caso normal',
            'features': [1000, 16, 20, 15, 12, 1, 10, 0, 0, 1, 0, 25]
        },
        {
            'name': 'Posición complicada (alta ramificación)',
            'features': [800, 12, 45, 8, 20, 0, 25, 0, 1, 0, 0, 40]
        },
        {
            'name': 'Endgame con pocas piezas',
            'features': [300, 6, 10, 5, 4, 0, 45, 1, 0, 0, 1, 60]
        },
        {
            'name': 'Posición muy activa',
            'features': [1200, 20, 30, 25, 8, 1, 15, 0, 0, 1, 0, 30]
        }
    ]
    
    for case in test_cases:
        print(f"\n   🎯 {case['name']}:")
        features = [case['features']]
        
        try:
            predictions = model.predict(features)
            probabilities = model.predict_proba(features)
            
            print(f"     Predicción: {predictions[0]}")
            print(f"     Probabilidades:")
            
            if hasattr(model, 'classes_'):
                classes = model.classes_
                for i, class_name in enumerate(classes):
                    if i < len(probabilities[0]):
                        prob = probabilities[0][i]
                        marker = "🏆" if predictions[0] == class_name else "  "
                        print(f"       {marker} {class_name}: {prob:.3f}")
                        
        except Exception as e:
            print(f"❌ Error en predicción de prueba: {e}")

if __name__ == "__main__":
    print("🔬 INVESTIGACIÓN COMPLETA DEL MODELO")
    print("="*80)
    
    # 1. Inspeccionar modelo básico
    test_model_predictions()
    
    # 2. Analizar distribución real de predicciones
    investigate_decision_boundaries()