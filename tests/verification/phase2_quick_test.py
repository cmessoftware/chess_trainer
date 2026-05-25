#!/usr/bin/env python3
"""
PHASE 2 - Diagnóstico rápido MLP vs Phase 1
==========================================
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score
import psycopg2
import warnings
warnings.filterwarnings('ignore')

def quick_phase2_test():
    print("🧠 Diagnóstico rápido - Phase 2 vs Phase 1")
    print("=" * 50)
    
    try:
        # Conectar a DB
        print("📊 Conectando a PostgreSQL...")
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="chess_trainer_db",
            user="chess",
            password="chess_pass"
        )
        
        # Query simple
        query = """
        SELECT 
            f.material_balance, f.material_total, f.num_pieces,
            f.branching_factor, f.self_mobility, f.opponent_mobility,
            f.has_castling_rights, f.is_repetition, f.is_low_mobility,
            f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
            f.player_color,
            f.error_label
        FROM features f 
        WHERE f.error_label IS NOT NULL
        LIMIT 10000
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"✅ Datos cargados: {len(df)} registros")
        
        # Preparar datos
        feature_cols = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color'
        ]
        
        # Limpiar datos
        for col in feature_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        X = df[feature_cols].values
        y = df['error_label'].values
        
        print(f"📊 Features: {X.shape[1]}, Samples: {X.shape[0]}")
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Normalizar
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print("🧠 Entrenando MLP básico...")
        
        # MLP muy simple
        mlp = MLPClassifier(
            hidden_layer_sizes=(20,),  # Muy pequeño
            max_iter=50,               # Muy pocas iteraciones
            random_state=42,
            verbose=False
        )
        
        # Entrenar con timeout
        import time
        start_time = time.time()
        
        mlp.fit(X_train_scaled, y_train)
        
        end_time = time.time()
        train_time = end_time - start_time
        
        print(f"✅ Entrenamiento completado en {train_time:.1f}s ({mlp.n_iter_} iter)")
        
        # Evaluar
        y_pred = mlp.predict(X_test_scaled)
        f1 = f1_score(y_test, y_pred, average='macro')
        acc = accuracy_score(y_test, y_pred)
        
        print("\n🏆 RESULTADOS")
        print(f"📊 F1 Score: {f1:.4f}")
        print(f"📊 Accuracy: {acc:.4f}")
        print(f"🕒 Tiempo: {train_time:.1f}s")
        
        # Comparación con Phase 1
        rf_f1 = 1.000  # Phase 1 resultado
        delta = f1 - rf_f1
        
        print(f"\n📈 COMPARACIÓN vs PHASE 1")
        print(f"Random Forest F1: {rf_f1:.4f}")
        print(f"MLP F1: {f1:.4f}")
        print(f"Δ: {delta:+.4f}")
        
        if delta > 0:
            print("✅ MLP supera a Random Forest")
        else:
            print("⚠️ MLP no supera a Random Forest")
            
        if train_time > 300:  # 5 minutos
            print("⚠️ Entrenamiento demasiado lento")
        else:
            print("✅ Tiempo de entrenamiento aceptable")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    quick_phase2_test()