#!/usr/bin/env python3
"""
PHASE 2 - Deep Learning MLP (Versión Simplificada)
==================================================

Versión simplificada sin colgarse para comparar con Phase 1
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
import mlflow
import mlflow.sklearn
import psycopg2
import os
import sys
import warnings
warnings.filterwarnings('ignore')

class Phase2MLPTrainerSimple:
    def __init__(self):
        # Configurar MLflow
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("chess_trainer_phase2_simple")
        
        # Scaler para normalizar features
        self.scaler = StandardScaler()
        
        # Resultados Phase 1 para comparación
        self.phase1_results = {
            'random_forest_f1': 1.000,
            'logistic_l1_f1': 0.872,
            'logistic_l2_f1': 0.860
        }
        
        print("🧠 Chess Trainer - Phase 2 MLP Simple")
        print("=" * 50)
        print(f"📊 MLflow URI: {mlflow.get_tracking_uri()}")
        
    def load_data_from_db(self):
        """Cargar datos desde PostgreSQL"""
        print("📊 Cargando datos desde PostgreSQL...")
        
        # Conectar a DB
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="chess_trainer_db",
            user="chess",
            password="chess123"
        )
        
        # Query para obtener features y labels
        query = """
        SELECT 
            f.material_balance, f.material_total, f.num_pieces,
            f.branching_factor, f.self_mobility, f.opponent_mobility,
            f.has_castling_rights, f.is_repetition, f.is_low_mobility,
            f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
            f.player_color, f.white_elo, f.black_elo,
            f.error_label
        FROM features f 
        JOIN games g ON f.game_id = g.game_id 
        WHERE f.error_label IS NOT NULL
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"📈 Datos cargados: {len(df)} registros")
        
        # Preparar features
        feature_columns = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color', 'white_elo', 'black_elo'
        ]
        
        # Convertir todo a numérico
        for col in feature_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(np.float64)
        
        X = df[feature_columns]
        y = df['error_label']
        
        print(f"✅ Datos preparados: {X.shape[0]} muestras, {X.shape[1]} features")
        return X, y
    
    def train_simple_mlp(self, X_train, X_test, y_train, y_test):
        """Entrenar MLP simple sin colgarse"""
        print("🧠 Entrenando MLP Simple...")
        
        with mlflow.start_run(run_name="phase2_mlp_simple") as run:
            
            # Modelo MLP muy simple
            model = MLPClassifier(
                hidden_layer_sizes=(50,),  # Solo una capa pequeña
                max_iter=100,              # Pocas iteraciones
                random_state=42,
                warm_start=False,
                verbose=True               # Ver progreso
            )
            
            print("   🔄 Iniciando entrenamiento...")
            
            # Entrenar con timeout implícito por max_iter bajo
            try:
                model.fit(X_train, y_train)
                print(f"   ✅ Entrenamiento completado en {model.n_iter_} iteraciones")
                
                # Predicciones
                y_pred_test = model.predict(X_test)
                
                # Métricas
                test_f1 = f1_score(y_test, y_pred_test, average='macro')
                test_acc = accuracy_score(y_test, y_pred_test)
                
                # Comparación con Phase 1
                delta_vs_rf = test_f1 - self.phase1_results['random_forest_f1']
                
                print(f"   📊 F1 Score: {test_f1:.4f}")
                print(f"   📊 Accuracy: {test_acc:.4f}")
                print(f"   📊 Δ vs Random Forest: {delta_vs_rf:+.4f}")
                
                # Log a MLflow
                mlflow.log_params({
                    'hidden_layer_sizes': str(model.hidden_layer_sizes),
                    'max_iter': model.max_iter,
                    'n_iter': model.n_iter_
                })
                
                mlflow.log_metrics({
                    'test_f1_macro': test_f1,
                    'test_accuracy': test_acc,
                    'delta_vs_random_forest': delta_vs_rf
                })
                
                mlflow.sklearn.log_model(model, "mlp_simple")
                
                return {
                    'f1_score': test_f1,
                    'accuracy': test_acc,
                    'delta_vs_rf': delta_vs_rf,
                    'n_iter': model.n_iter_
                }
                
            except Exception as e:
                print(f"   ❌ Error en entrenamiento: {e}")
                return None
    
    def run_phase2(self):
        """Ejecutar Phase 2 completo"""
        print("🚀 Iniciando Phase 2 MLP Simple")
        
        # Cargar datos
        X, y = self.load_data_from_db()
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Normalizar
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"📊 Train: {len(X_train)} | Test: {len(X_test)}")
        
        # Entrenar
        result = self.train_simple_mlp(X_train_scaled, X_test_scaled, y_train, y_test)
        
        if result:
            print("\n🏆 RESULTADOS PHASE 2 SIMPLE")
            print("=" * 40)
            print(f"📊 F1 Score: {result['f1_score']:.4f}")
            print(f"📊 Accuracy: {result['accuracy']:.4f}")
            print(f"📊 Δ vs RF: {result['delta_vs_rf']:+.4f}")
            print(f"🔄 Iteraciones: {result['n_iter']}")
            
            if result['delta_vs_rf'] > 0.001:
                print("✅ MLP supera ligeramente a Random Forest")
            else:
                print("⚠️ MLP no supera significativamente a Random Forest")
        else:
            print("❌ Phase 2 falló")

if __name__ == "__main__":
    trainer = Phase2MLPTrainerSimple()
    trainer.run_phase2()