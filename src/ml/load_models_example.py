#!/usr/bin/env python3
"""
Ejemplos de cómo cargar y usar los modelos de MLflow
Ejecutar después de completar phase1_baseline_mvp.py
"""

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

def load_phase1_models():
    """Cargar los modelos registrados de Phase 1"""
    
    # Configurar MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    
    print("🤖 Cargando modelos de Phase 1...")
    
    try:
        # Cargar el mejor modelo (Random Forest)
        best_model = mlflow.sklearn.load_model("models:/phase1_random_forest/1")
        print("✅ Random Forest cargado")
        
        # Cargar Logistic Regression L2  
        lr_l2_model = mlflow.sklearn.load_model("models:/phase1_logistic_l2/1")
        print("✅ Logistic Regression L2 cargado")
        
        # Cargar Logistic Regression L1
        lr_l1_model = mlflow.sklearn.load_model("models:/phase1_logistic_l1/1")
        print("✅ Logistic Regression L1 cargado")
        
        return {
            'random_forest': best_model,
            'logistic_l2': lr_l2_model, 
            'logistic_l1': lr_l1_model
        }
        
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")
        print("💡 Asegúrate de que MLflow esté corriendo: docker-compose up -d notebooks")
        return None

def predict_move_quality(models, move_features):
    """
    Predecir calidad de un movimiento usando los modelos
    
    Args:
        models: Dict con modelos cargados
        move_features: Array con las 9 características del movimiento
                      [material_balance, score_diff, player_color, move_number,
                       has_discovered_attack, has_fork, has_pin, has_skewer, has_check]
    
    Returns:
        Dict con predicciones de cada modelo
    """
    
    # Convertir a DataFrame (necesario para algunos modelos)
    feature_names = [
        'material_balance', 'score_diff', 'player_color', 'move_number',
        'has_discovered_attack', 'has_fork', 'has_pin', 'has_skewer', 'has_check'
    ]
    
    df = pd.DataFrame([move_features], columns=feature_names)
    
    predictions = {}
    
    for model_name, model in models.items():
        try:
            pred = model.predict(df)[0]
            prob = model.predict_proba(df)[0]
            
            predictions[model_name] = {
                'prediction': pred,
                'probabilities': {
                    'blunder': prob[0],
                    'good': prob[1], 
                    'inaccuracy': prob[2],
                    'mistake': prob[3]
                }
            }
        except Exception as e:
            print(f"❌ Error con modelo {model_name}: {e}")
    
    return predictions

def example_usage():
    """Ejemplo de uso de los modelos"""
    
    # Cargar modelos
    models = load_phase1_models()
    
    if models is None:
        return
    
    # Ejemplo: Analizar un movimiento
    # [material_balance, score_diff, player_color, move_number, 
    #  discovered_attack, fork, pin, skewer, check]
    example_move = [
        50,    # material_balance: ventaja de 50 centipeones
        -100,  # score_diff: movimiento empeoró posición en 100 cp
        1,     # player_color: blancas
        15,    # move_number: movimiento 15
        0, 0, 0, 0, 0  # sin tácticas especiales
    ]
    
    print("\n🎯 Analizando movimiento de ejemplo...")
    print(f"Características: {example_move}")
    
    predictions = predict_move_quality(models, example_move)
    
    print("\n📊 Predicciones:")
    for model_name, pred in predictions.items():
        print(f"\n{model_name.upper()}:")
        print(f"  Predicción: {pred['prediction']}")
        print(f"  Probabilidades:")
        for label, prob in pred['probabilities'].items():
            print(f"    {label}: {prob:.3f}")

if __name__ == "__main__":
    print("🚀 Ejemplo de uso de modelos MLflow Phase 1")
    print("=" * 50)
    
    example_usage()