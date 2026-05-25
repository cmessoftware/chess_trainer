#!/usr/bin/env python3
"""
PHASE 3 - Análisis Temporal CORREGIDO (Sin Data Leakage)
========================================================

CORRECCIONES:
1. Features temporales solo usan información pasada
2. Ventanas predicen el SIGUIENTE movimiento (no el actual)
3. Split temporal por partidas (primeras partidas = train, últimas = test)
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
import psycopg2
import warnings
warnings.filterwarnings('ignore')

class Phase3TemporalCorrected:
    def __init__(self, window_size=5):
        """
        Phase 3 CORREGIDO: Sin data leakage temporal
        """
        self.window_size = window_size
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        self.previous_results = {
            'phase1_rf_f1': 1.000,
            'phase1_lr_f1': 0.872,
            'phase2_mlp_f1': 0.9679
        }
        
        print("🕐 Chess Trainer - Phase 3 CORREGIDO (Sin Data Leakage)")
        print("=" * 60)
        print(f"📊 Window Size: {window_size} moves")
        
    def load_sequential_data_from_db(self, limit=15000):
        """Cargar datos con orden estricto por game_id y move_number"""
        print("📊 Cargando datos secuenciales...")
        
        conn = psycopg2.connect(
            host="localhost", port="5432", database="chess_trainer_db",
            user="chess", password="chess_pass"
        )
        
        query = f"""
        SELECT 
            f.game_id, f.move_number,
            f.material_balance, f.material_total, f.num_pieces,
            f.branching_factor, f.self_mobility, f.opponent_mobility,
            f.has_castling_rights, f.is_repetition, f.is_low_mobility,
            f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
            f.player_color, f.error_label
        FROM features f 
        WHERE f.error_label IS NOT NULL
        ORDER BY f.game_id, f.move_number
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"📈 Datos cargados: {len(df)} registros de {df['game_id'].nunique()} partidas")
        return df
    
    def create_temporal_features_corrected(self, df):
        """
        Crear features temporales SIN LEAKAGE - solo información pasada
        """
        print("🕐 Generando features temporales SIN LEAKAGE...")
        
        df = df.sort_values(['game_id', 'move_number']).reset_index(drop=True)
        temporal_features = []
        
        for game_id in df['game_id'].unique():
            game_data = df[df['game_id'] == game_id].copy().reset_index(drop=True)
            
            if len(game_data) < 3:
                continue
            
            # 1. Score differences - SOLO PASADO
            game_data['score_cp_diff_prev'] = game_data['score_diff'].shift(1).fillna(0) - game_data['score_diff'].shift(2).fillna(0)
            
            # 2. Errores consecutivos - SOLO PASADO  
            error_mapping = {'good': 0, 'inaccuracy': 1, 'mistake': 2, 'blunder': 3, 'brilliant': -1}
            game_data['error_numeric'] = game_data['error_label'].map(error_mapping)
            game_data['prev_error'] = game_data['error_numeric'].shift(1).fillna(0)
            game_data['consecutive_errors_past'] = ((game_data['prev_error'] >= 1) & (game_data['error_numeric'].shift(2).fillna(0) >= 1)).astype(int)
            
            # 3. Tendencia del score - SOLO PASADO (últimas 2 jugadas)
            game_data['score_trend_past'] = game_data['score_diff'].shift(1).fillna(0) - game_data['score_diff'].shift(2).fillna(0)
            game_data['worsening_trend_past'] = (game_data['score_trend_past'] < -50).astype(int)
            
            # 4. Presión de tiempo - BASADO EN POSICIÓN EN PARTIDA
            max_move = game_data['move_number'].max()
            game_data['time_pressure'] = (game_data['move_number'] / max_move > 0.7).astype(int)
            
            # 5. Volatilidad pasada
            game_data['score_volatility_past'] = game_data['score_diff'].rolling(2, min_periods=1).std().shift(1).fillna(0)
            
            temporal_features.append(game_data)
        
        result_df = pd.concat(temporal_features, ignore_index=True)
        
        print(f"✅ Features temporales SIN LEAKAGE: {len(result_df)} registros")
        print("📊 Nuevas columnas: score_cp_diff_prev, consecutive_errors_past, score_trend_past")
        
        return result_df
    
    def create_sequences_corrected(self, df):
        """
        Crear secuencias CORREGIDAS - predecir jugada SIGUIENTE, no actual
        """
        print(f"🔄 Creando secuencias CORREGIDAS (ventana {self.window_size} -> predice siguiente)...")
        
        # Features base + temporales corregidas
        feature_cols = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color', 'score_cp_diff_prev', 'consecutive_errors_past',
            'score_trend_past', 'worsening_trend_past', 'time_pressure', 'score_volatility_past'
        ]
        
        # Limpiar features
        for col in feature_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        X_sequences = []
        y_sequences = []
        game_ids = []
        
        for game_id in df['game_id'].unique():
            game_data = df[df['game_id'] == game_id].copy()
            
            if len(game_data) <= self.window_size:  # Necesitamos window_size + 1
                continue
            
            # CORRECCIÓN: Ventana predice la SIGUIENTE jugada
            for i in range(len(game_data) - self.window_size):
                
                # Ventana de los movimientos i hasta i+window_size-1
                window = game_data.iloc[i:i + self.window_size]
                
                # Label del movimiento SIGUIENTE (i+window_size)
                next_move = game_data.iloc[i + self.window_size]
                
                X_window = window[feature_cols].values
                y_label = next_move['error_label']
                
                X_sequences.append(X_window)
                y_sequences.append(y_label)
                game_ids.append(game_id)
        
        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)
        
        print(f"✅ Secuencias CORREGIDAS: {X_sequences.shape}")
        print(f"📊 Ventana {self.window_size} movimientos -> predice movimiento {self.window_size + 1}")
        
        return X_sequences, y_sequences, game_ids
    
    def temporal_train_test_split(self, X_sequences, y_sequences, game_ids, test_size=0.2):
        """
        Split temporal CORRECTO - primeras partidas = train, últimas = test
        """
        print("📊 Split temporal por partidas...")
        
        unique_games = list(set(game_ids))
        unique_games.sort()  # Orden determinístico
        
        split_idx = int(len(unique_games) * (1 - test_size))
        train_games = set(unique_games[:split_idx])
        test_games = set(unique_games[split_idx:])
        
        # Separar secuencias por partidas
        train_mask = [game_id in train_games for game_id in game_ids]
        test_mask = [game_id in test_games for game_id in game_ids]
        
        X_train = X_sequences[train_mask]
        X_test = X_sequences[test_mask]
        y_train = y_sequences[train_mask]
        y_test = y_sequences[test_mask]
        
        print(f"🎯 Train: {len(train_games)} partidas, {len(X_train)} secuencias")
        print(f"🎯 Test: {len(test_games)} partidas, {len(X_test)} secuencias")
        
        return X_train, X_test, y_train, y_test
    
    def train_corrected_model(self, X_train, X_test, y_train, y_test):
        """
        Entrenar modelo temporal CORREGIDO
        """
        print("🧠 Entrenando modelo temporal CORREGIDO...")
        
        # Aplanar secuencias para Random Forest (no puede usar 3D)
        X_train_flat = X_train.reshape(X_train.shape[0], -1)
        X_test_flat = X_test.reshape(X_test.shape[0], -1)
        
        # Modelo conservador
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,      # Limitar profundidad para evitar overfitting
            min_samples_split=20,
            min_samples_leaf=5,
            random_state=42
        )
        
        rf.fit(X_train_flat, y_train)
        
        # Predicciones
        y_pred = rf.predict(X_test_flat)
        
        # Métricas
        f1 = f1_score(y_test, y_pred, average='macro')
        acc = accuracy_score(y_test, y_pred)
        
        print(f"✅ Modelo CORREGIDO - F1: {f1:.4f}, Acc: {acc:.4f}")
        
        return {'f1_score': f1, 'accuracy': acc, 'model': rf}
    
    def run_corrected_phase3(self):
        """
        Ejecutar Phase 3 CORREGIDO sin data leakage
        """
        print("🚀 Iniciando Phase 3 CORREGIDO")
        
        # 1. Cargar datos
        df = self.load_sequential_data_from_db()
        
        # 2. Features temporales SIN LEAKAGE
        df_temporal = self.create_temporal_features_corrected(df)
        
        # 3. Secuencias CORREGIDAS
        X_sequences, y_sequences, game_ids = self.create_sequences_corrected(df_temporal)
        
        # 4. Split temporal CORRECTO
        X_train, X_test, y_train, y_test = self.temporal_train_test_split(
            X_sequences, y_sequences, game_ids
        )
        
        # 5. Entrenar modelo CORREGIDO
        result = self.train_corrected_model(X_train, X_test, y_train, y_test)
        
        # 6. Comparar con fases anteriores
        self.compare_corrected_results(result)
        
        return result
    
    def compare_corrected_results(self, result):
        """
        Comparar resultados CORREGIDOS con fases anteriores
        """
        print("\n🏆 COMPARACIÓN CORREGIDA (SIN DATA LEAKAGE)")
        print("=" * 50)
        print(f"Phase 1 - Random Forest: F1 = {self.previous_results['phase1_rf_f1']:.4f}")
        print(f"Phase 1 - Logistic Reg:  F1 = {self.previous_results['phase1_lr_f1']:.4f}")
        print(f"Phase 2 - MLP:          F1 = {self.previous_results['phase2_mlp_f1']:.4f}")
        
        f1 = result['f1_score']
        delta_vs_rf = f1 - self.previous_results['phase1_rf_f1']
        delta_vs_mlp = f1 - self.previous_results['phase2_mlp_f1']
        
        print(f"\nPhase 3 CORREGIDO:")
        print(f"  Temporal RF:    F1 = {f1:.4f} (Δ vs RF: {delta_vs_rf:+.4f}, Δ vs MLP: {delta_vs_mlp:+.4f})")
        
        if f1 > 0.95:
            print("⚠️ ADVERTENCIA: F1 > 0.95 - Verificar posible overfitting residual")
        elif f1 > self.previous_results['phase2_mlp_f1']:
            print("✅ Phase 3 supera a Phase 2 - El análisis temporal añade valor legítimo")
        else:
            print("📊 Phase 3 no supera significativamente - Temporal patterns son limitados")

if __name__ == "__main__":
    analyzer = Phase3TemporalCorrected(window_size=4)
    result = analyzer.run_corrected_phase3()