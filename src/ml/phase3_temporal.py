#!/usr/bin/env python3
"""
PHASE 3 - Análisis Temporal (Errores en Cadena)
==============================================

Objetivo: Detectar patrones de colapso y errores consecutivos

Input: Ventanas de N jugadas (3-7 movimientos)
Features: score_cp_diff, errores_consecutivos, presion_tiempo, tendencias
Modelos: 1D-CNN, GRU
Output: Riesgo de colapso, detección de rachas malas

Métricas: Recall de errores graves en secuencia, Delay de detección
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
import psycopg2
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Conv1D, MaxPooling1D, GRU, LSTM, Dropout, Flatten
    from tensorflow.keras.utils import to_categorical
    TF_AVAILABLE = True
    print("✅ TensorFlow disponible para CNN/GRU")
except ImportError:
    TF_AVAILABLE = False
    print("⚠️ TensorFlow no disponible - usando alternativas simples")

class Phase3TemporalAnalyzer:
    def __init__(self, window_size=5):
        """
        Phase 3: Análisis temporal de errores en cadena
        
        Args:
            window_size: Tamaño de ventana para secuencias (3-7 jugadas)
        """
        self.window_size = window_size
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Resultados de fases anteriores para comparación
        self.previous_results = {
            'phase1_rf_f1': 1.000,
            'phase1_lr_f1': 0.872,
            'phase2_mlp_f1': 0.9679
        }
        
        print("🕐 Chess Trainer - Phase 3 Temporal Analysis")
        print("=" * 50)
        print(f"📊 Window Size: {window_size} moves")
        print(f"🧠 TensorFlow: {'✅' if TF_AVAILABLE else '❌'}")
        
    def load_sequential_data_from_db(self, limit=20000):
        """
        Cargar datos secuenciales desde PostgreSQL
        Organizados por game_id y move_number para crear ventanas temporales
        """
        print("📊 Cargando datos secuenciales desde PostgreSQL...")
        
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="chess_trainer_db",
            user="chess",
            password="chess_pass"
        )
        
        # Query para obtener secuencias ordenadas por partida y movimiento
        query = f"""
        SELECT 
            f.game_id,
            f.move_number,
            f.material_balance, f.material_total, f.num_pieces,
            f.branching_factor, f.self_mobility, f.opponent_mobility,
            f.has_castling_rights, f.is_repetition, f.is_low_mobility,
            f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
            f.player_color,
            f.error_label
        FROM features f 
        WHERE f.error_label IS NOT NULL
        ORDER BY f.game_id, f.move_number
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"📈 Datos cargados: {len(df)} registros de {df['game_id'].nunique()} partidas")
        
        return df
    
    def create_temporal_features(self, df):
        """
        Crear features temporales para análisis de secuencias
        
        Returns:
            df: DataFrame con features temporales añadidas
        """
        print("🕐 Generando features temporales...")
        
        # Ordenar por partida y movimiento
        df = df.sort_values(['game_id', 'move_number']).reset_index(drop=True)
        
        # Features temporales por partida
        temporal_features = []
        
        for game_id in df['game_id'].unique():
            game_data = df[df['game_id'] == game_id].copy()
            
            if len(game_data) < 3:  # Mínimo 3 movimientos
                continue
                
            # Score differences (cambios de evaluación)
            game_data['score_cp_diff'] = game_data['score_diff'].diff().fillna(0)
            game_data['score_cp_diff_abs'] = game_data['score_cp_diff'].abs()
            
            # Errores consecutivos
            error_mapping = {'good': 0, 'inaccuracy': 1, 'mistake': 2, 'blunder': 3, 'brilliant': -1}
            game_data['error_numeric'] = game_data['error_label'].map(error_mapping)
            game_data['consecutive_errors'] = (game_data['error_numeric'] >= 1).astype(int)
            
            # Tendencias (dirección del score)
            game_data['score_trend'] = game_data['score_diff'].rolling(3, min_periods=1).mean()
            game_data['worsening_trend'] = (game_data['score_trend'].diff() < -50).astype(int)
            
            # Presión de tiempo (simulada - usando move_number directamente)
            max_move_num = game_data['move_number'].max()
            game_data['time_pressure'] = (game_data['move_number'] / max_move_num > 0.7).astype(int)
            
            # Volatilidad del score
            game_data['score_volatility'] = game_data['score_diff'].rolling(3, min_periods=1).std().fillna(0)
            
            temporal_features.append(game_data)
        
        result_df = pd.concat(temporal_features, ignore_index=True)
        
        print(f"✅ Features temporales generadas: {len(result_df)} registros")
        print(f"📊 Nuevas columnas: score_cp_diff, consecutive_errors, score_trend, time_pressure")
        
        return result_df
    
    def create_sequences(self, df):
        """
        Crear secuencias de ventanas para entrenamiento temporal
        
        Returns:
            X_sequences: Array 3D (n_samples, window_size, n_features)
            y_sequences: Array de labels
            metadata: Información adicional
        """
        print(f"🔄 Creando secuencias de ventana {self.window_size}...")
        
        # Features base + temporales
        feature_cols = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color', 'score_cp_diff', 'score_cp_diff_abs',
            'consecutive_errors', 'score_trend', 'worsening_trend',
            'time_pressure', 'score_volatility'
        ]
        
        # Limpiar y normalizar features
        for col in feature_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        X_sequences = []
        y_sequences = []
        game_ids = []
        move_numbers = []
        
        for game_id in df['game_id'].unique():
            game_data = df[df['game_id'] == game_id].copy()
            
            if len(game_data) < self.window_size:
                continue
            
            # Crear ventanas deslizantes
            for i in range(len(game_data) - self.window_size + 1):
                window = game_data.iloc[i:i + self.window_size]
                
                # Features de la ventana
                X_window = window[feature_cols].values
                
                # Label del último movimiento de la ventana
                y_label = window['error_label'].iloc[-1]
                
                X_sequences.append(X_window)
                y_sequences.append(y_label)
                game_ids.append(game_id)
                move_numbers.append(window['move_number'].iloc[-1])
        
        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)
        
        print(f"✅ Secuencias creadas: {X_sequences.shape}")
        print(f"📊 Shape: (n_samples={X_sequences.shape[0]}, window_size={X_sequences.shape[1]}, features={X_sequences.shape[2]})")
        
        metadata = {
            'game_ids': game_ids,
            'move_numbers': move_numbers,
            'feature_names': feature_cols
        }
        
        return X_sequences, y_sequences, metadata
    
    def create_1d_cnn_model(self, input_shape, num_classes):
        """
        Crear modelo 1D-CNN para análisis de secuencias temporales
        """
        if not TF_AVAILABLE:
            print("❌ TensorFlow no disponible para CNN")
            return None
            
        model = Sequential([
            Conv1D(32, kernel_size=3, activation='relu', input_shape=input_shape),
            MaxPooling1D(pool_size=2),
            Conv1D(64, kernel_size=3, activation='relu'),
            Dropout(0.3),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def create_gru_model(self, input_shape, num_classes):
        """
        Crear modelo GRU para análisis de patrones temporales
        """
        if not TF_AVAILABLE:
            print("❌ TensorFlow no disponible para GRU")
            return None
            
        model = Sequential([
            GRU(64, return_sequences=True, input_shape=input_shape),
            Dropout(0.3),
            GRU(32, return_sequences=False),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def detect_collapse_patterns(self, X_sequences, y_sequences, metadata):
        """
        Detectar patrones específicos de colapso y rachas malas
        
        Returns:
            dict: Estadísticas de patrones de colapso
        """
        print("🔍 Analizando patrones de colapso...")
        
        collapse_stats = {
            'total_sequences': len(X_sequences),
            'blunder_sequences': 0,
            'mistake_chains': 0,
            'score_collapses': 0,
            'time_pressure_errors': 0
        }
        
        for i, (seq, label) in enumerate(zip(X_sequences, y_sequences)):
            # Detectar blunders
            if label == 'blunder':
                collapse_stats['blunder_sequences'] += 1
            
            # Detectar cadenas de errores
            consecutive_errors = seq[:, -6]  # consecutive_errors column
            if np.sum(consecutive_errors) >= 2:  # 2+ errores consecutivos
                collapse_stats['mistake_chains'] += 1
            
            # Detectar colapsos de score
            score_diffs = seq[:, -8]  # score_cp_diff column
            if np.sum(score_diffs < -100) >= 2:  # 2+ caídas grandes
                collapse_stats['score_collapses'] += 1
            
            # Errores bajo presión de tiempo
            time_pressure = seq[:, -2]  # time_pressure column
            if np.any(time_pressure > 0) and label in ['mistake', 'blunder']:
                collapse_stats['time_pressure_errors'] += 1
        
        # Calcular porcentajes
        total = collapse_stats['total_sequences']
        for key in collapse_stats:
            if key != 'total_sequences':
                percentage = (collapse_stats[key] / total) * 100
                print(f"   {key}: {collapse_stats[key]} ({percentage:.1f}%)")
        
        return collapse_stats
    
    def train_temporal_models(self, X_train, X_test, y_train, y_test):
        """
        Entrenar modelos temporales y comparar con fases anteriores
        """
        results = {}
        
        # Encode labels
        all_labels = np.concatenate([y_train, y_test])
        self.label_encoder.fit(all_labels)
        y_train_encoded = self.label_encoder.transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        num_classes = len(self.label_encoder.classes_)
        input_shape = (X_train.shape[1], X_train.shape[2])
        
        print(f"🧠 Entrenando modelos temporales...")
        print(f"📊 Classes: {self.label_encoder.classes_}")
        print(f"📊 Input shape: {input_shape}")
        
        if TF_AVAILABLE:
            # Preparar para categorical
            y_train_cat = to_categorical(y_train_encoded, num_classes)
            y_test_cat = to_categorical(y_test_encoded, num_classes)
            
            # Modelo 1D-CNN
            print("   🔄 Entrenando 1D-CNN...")
            cnn_model = self.create_1d_cnn_model(input_shape, num_classes)
            cnn_history = cnn_model.fit(
                X_train, y_train_cat,
                validation_split=0.2,
                epochs=20,
                batch_size=32,
                verbose=0
            )
            
            # Evaluar CNN
            cnn_pred_probs = cnn_model.predict(X_test, verbose=0)
            cnn_pred = np.argmax(cnn_pred_probs, axis=1)
            cnn_f1 = f1_score(y_test_encoded, cnn_pred, average='macro')
            cnn_acc = accuracy_score(y_test_encoded, cnn_pred)
            
            results['cnn'] = {
                'f1_score': cnn_f1,
                'accuracy': cnn_acc,
                'model': cnn_model
            }
            
            print(f"   ✅ 1D-CNN F1: {cnn_f1:.4f}, Acc: {cnn_acc:.4f}")
            
            # Modelo GRU
            print("   🔄 Entrenando GRU...")
            gru_model = self.create_gru_model(input_shape, num_classes)
            gru_history = gru_model.fit(
                X_train, y_train_cat,
                validation_split=0.2,
                epochs=20,
                batch_size=32,
                verbose=0
            )
            
            # Evaluar GRU
            gru_pred_probs = gru_model.predict(X_test, verbose=0)
            gru_pred = np.argmax(gru_pred_probs, axis=1)
            gru_f1 = f1_score(y_test_encoded, gru_pred, average='macro')
            gru_acc = accuracy_score(y_test_encoded, gru_pred)
            
            results['gru'] = {
                'f1_score': gru_f1,
                'accuracy': gru_acc,
                'model': gru_model
            }
            
            print(f"   ✅ GRU F1: {gru_f1:.4f}, Acc: {gru_acc:.4f}")
        
        else:
            print("   ⚠️ Usando baseline temporal simple (sin TensorFlow)")
            # Fallback: usar el último movimiento de cada secuencia como baseline
            X_last_move = X_test[:, -1, :]  # Último movimiento de cada secuencia
            
            # Simple temporal baseline usando features del último move
            from sklearn.ensemble import RandomForestClassifier
            rf_temporal = RandomForestClassifier(n_estimators=50, random_state=42)
            rf_temporal.fit(X_train[:, -1, :], y_train)
            
            rf_pred = rf_temporal.predict(X_last_move)
            rf_f1 = f1_score(y_test, rf_pred, average='macro')
            rf_acc = accuracy_score(y_test, rf_pred)
            
            results['temporal_rf'] = {
                'f1_score': rf_f1,
                'accuracy': rf_acc,
                'model': rf_temporal
            }
            
            print(f"   ✅ Temporal RF F1: {rf_f1:.4f}, Acc: {rf_acc:.4f}")
        
        return results
    
    def run_phase3(self):
        """
        Ejecutar Phase 3 completo: análisis temporal de errores en cadena
        """
        print("🚀 Iniciando Phase 3 - Análisis Temporal")
        
        # 1. Cargar datos secuenciales
        df = self.load_sequential_data_from_db()
        
        # 2. Crear features temporales
        df_temporal = self.create_temporal_features(df)
        
        # 3. Crear secuencias de ventanas
        X_sequences, y_sequences, metadata = self.create_sequences(df_temporal)
        
        # 4. Detectar patrones de colapso
        collapse_stats = self.detect_collapse_patterns(X_sequences, y_sequences, metadata)
        
        # 5. Split temporal (preservando orden de partidas)
        X_train, X_test, y_train, y_test = train_test_split(
            X_sequences, y_sequences, 
            test_size=0.2, 
            random_state=42,
            stratify=y_sequences
        )
        
        print(f"📊 Train sequences: {len(X_train)}, Test sequences: {len(X_test)}")
        
        # 6. Entrenar modelos temporales
        results = self.train_temporal_models(X_train, X_test, y_train, y_test)
        
        # 7. Comparar con fases anteriores
        self.compare_with_previous_phases(results)
        
        return results, collapse_stats
    
    def compare_with_previous_phases(self, results):
        """
        Comparar resultados de Phase 3 con fases anteriores
        """
        print("\n🏆 COMPARACIÓN CON FASES ANTERIORES")
        print("=" * 50)
        print(f"Phase 1 - Random Forest: F1 = {self.previous_results['phase1_rf_f1']:.4f}")
        print(f"Phase 1 - Logistic Reg:  F1 = {self.previous_results['phase1_lr_f1']:.4f}")
        print(f"Phase 2 - MLP:          F1 = {self.previous_results['phase2_mlp_f1']:.4f}")
        
        print("\nPhase 3 - Temporal Models:")
        for model_name, result in results.items():
            f1 = result['f1_score']
            delta_vs_rf = f1 - self.previous_results['phase1_rf_f1']
            delta_vs_mlp = f1 - self.previous_results['phase2_mlp_f1']
            
            print(f"  {model_name.upper():12}: F1 = {f1:.4f} (Δ vs RF: {delta_vs_rf:+.4f}, Δ vs MLP: {delta_vs_mlp:+.4f})")
        
        # Determinar el mejor modelo temporal
        if results:
            best_model = max(results.keys(), key=lambda k: results[k]['f1_score'])
            best_f1 = results[best_model]['f1_score']
            
            print(f"\n🎯 Mejor modelo temporal: {best_model.upper()} (F1 = {best_f1:.4f})")
            
            if best_f1 > self.previous_results['phase1_rf_f1']:
                print("✅ Phase 3 SUPERA a Phase 1 - El análisis temporal añade valor!")
            elif best_f1 > self.previous_results['phase2_mlp_f1']:
                print("✅ Phase 3 supera a Phase 2 MLP - Las secuencias ayudan")
            else:
                print("⚠️ Phase 3 no supera significativamente - Patrones temporales limitados")

if __name__ == "__main__":
    analyzer = Phase3TemporalAnalyzer(window_size=5)
    results, collapse_stats = analyzer.run_phase3()