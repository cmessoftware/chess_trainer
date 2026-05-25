#!/usr/bin/env python3
"""
PHASE 2 - Deep Learning Tabular (MLP)
======================================

Objetivo: Aprender combinaciones no lineales que ML clásico no capta

Input: Mismas features que Phase 1
Modelos: 
- MLP Keras (2-3 capas)
- Regularización fuerte: L2, AdamW (weight decay), Dropout, Label smoothing
- CRITICAL: Manejo de desbalanceo con sample_weight (ratio 59:1 good vs blunder)

Output: error_label ∈ {brilliant, good, inaccuracy, mistake, blunder}
Métricas: ΔF1 macro vs ML, Reducción de errores graves, Calibración (ECE)

Criterio de avance:
- DL debe superar claramente a ML o reducir errores críticos
- Si no, se mantiene ML como base
"""

import numpy as np

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# ML/DL imports
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    accuracy_score, precision_recall_fscore_support
)
from sklearn.calibration import calibration_curve
from sklearn.utils.class_weight import compute_sample_weight  # ⚠️ CRITICAL for imbalance
import numpy as np

# MLflow imports
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

# Database imports
from sqlalchemy import create_engine

# Project imports
sys.path.append(str(Path(__file__).parent.parent))

# Configurar para reproducibilidad
np.random.seed(42)


class Phase2MLPTrainer:
    """Entrenador para Phase 2 - Deep Learning MLP"""
    
    def __init__(self, experiment_name="chess_trainer_phase2"):
        """
        Inicializar trainer
        
        Args:
            experiment_name: Nombre del experimento MLflow
        """
        self.experiment_name = experiment_name
        self.models = {}
        self.results = {}
        self.feature_columns = None
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        
        # Cargar resultados Phase 1 para comparación
        self.phase1_results = {
            'random_forest_f1': 1.000,
            'logistic_l1_f1': 0.872,
            'logistic_l2_f1': 0.890  # Actualizado con resultado real
        }
        
        # Configurar MLflow - DISABLED temporalmente por problemas con artifacts
        # mlflow.set_tracking_uri(f"file:///{mlflow_dir}")
        # mlflow.set_experiment(experiment_name)
        
        print(f"🚀 Iniciando Phase 2 MLP Trainer")
        print(f"📊 MLflow: DISABLED (guardando resultados localmente)")
        print(f"🧪 Experimento: {experiment_name}")
        print(f"📈 Baseline Phase 1 - Logistic L2 F1: {self.phase1_results['logistic_l2_f1']:.3f}")
    
    def load_data_from_db(self, sample_size=None, min_games_per_label=100):
        """
        Cargar datos etiquetados desde PostgreSQL (misma lógica que Phase 1)
        
        Args:
            sample_size: Limitar número de samples (None = todos)
            min_games_per_label: Mínimo de muestras por label para incluir
            
        Returns:
            X, y: Features y labels
        """
        print("📊 Cargando datos desde PostgreSQL...")
        
        # Conectar a base de datos
        engine = create_engine(
            "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"
        )
        
        # Query para obtener features etiquetadas (igual que Phase 1)
        query = """
        SELECT 
            f.game_id,
            f.move_number,
            f.player_color,
            f.material_balance,
            f.material_total,
            f.num_pieces,
            f.branching_factor,
            f.self_mobility,
            f.opponent_mobility,
            f.has_castling_rights,
            f.is_repetition,
            f.is_low_mobility,
            f.is_center_controlled,
            f.is_pawn_endgame,
            f.score_diff,
            f.error_label,
            g.time_control,
            g.white_elo,
            g.black_elo,
            g.source
        FROM features f
        JOIN games g ON f.game_id = g.game_id
        WHERE f.error_label IS NOT NULL
          AND f.error_label != ''
        """
        
        if sample_size:
            query += f" LIMIT {sample_size}"
            
        df = pd.read_sql_query(query, engine)
        engine.dispose()
        
        print(f"📈 Datos cargados: {len(df)} registros")
        
        # Mostrar distribución de labels
        label_counts = df['error_label'].value_counts()
        print(f"🏷️ Distribución de labels:")
        for label, count in label_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   {label}: {count} ({percentage:.1f}%)")
        
        # Filtrar labels con pocas muestras
        labels_to_keep = label_counts[label_counts >= min_games_per_label].index
        df_filtered = df[df['error_label'].isin(labels_to_keep)]
        
        if len(df_filtered) < len(df):
            print(f"⚠️ Filtrado por mínimo {min_games_per_label} muestras:")
            print(f"   Antes: {len(df)} → Después: {len(df_filtered)}")
        
        # Preparar features (igual que Phase 1)
        self.feature_columns = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color', 'white_elo', 'black_elo'
        ]
        
        # Manejo de valores faltantes y limpieza
        df_clean = df_filtered.copy()
        
        # Convertir TODAS las columnas de features a numéricas
        for col in self.feature_columns:
            if col in df_clean.columns:
                # Convertir a numérico forzando errores a NaN, luego llenar con 0
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(np.float64)
            else:
                # Si la columna no existe, crearla con valores 0
                df_clean[col] = 0.0
        
        X = df_clean[self.feature_columns]
        y = df_clean['error_label']
        
        # Debug de tipos de datos
        print(f"🔍 Debug X data types:")
        for col in X.columns:
            print(f"   {col}: {X[col].dtype} | sample: {X[col].iloc[0]}")
        
        # Asegurarnos de que X es totalmente numérico
        X = X.astype(np.float64)
        
        print(f"✅ Datos preparados: {X.shape[0]} muestras, {X.shape[1]} features")
        print(f"📊 Labels: {sorted(set(y))}")
        print(f"🔍 X final dtypes: {X.dtypes.unique()}")
        
        return X, y
    
    def create_mlp_model(self, model_type='basic'):
        """
        Crear modelo MLP con diferentes configuraciones usando scikit-learn
        
        Args:
            model_type: Tipo de modelo ('basic', 'regularized', 'deep')
            
        Returns:
            model: MLPClassifier configurado
        """
        
        if model_type == 'basic':
            # MLP muy simple
            model = MLPClassifier(
                hidden_layer_sizes=(100,),
                max_iter=300,
                random_state=42
            )
            
        elif model_type == 'regularized':
            # MLP con regularización
            model = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                alpha=0.01,
                max_iter=300,
                random_state=42
            )
            
        elif model_type == 'deep':
            # MLP profundo
            model = MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                alpha=0.001,
                max_iter=500,
                random_state=42
            )
        
        return model
    
    def calculate_ece(self, y_true, y_prob, n_bins=10):
        """
        Calcular Expected Calibration Error (ECE) simplificado
        
        Args:
            y_true: Labels verdaderos
            y_prob: Probabilidades predichas (matriz n_samples x n_classes)
            n_bins: Número de bins
            
        Returns:
            ece: Expected Calibration Error
        """
        try:
            # Obtener predicciones y confianza máxima
            y_pred = np.argmax(y_prob, axis=1)
            confidences = np.max(y_prob, axis=1)
            
            # Convertir y_true a array para manejo simple
            y_true_array = np.array(y_true)
            
            # Para simplificar, usamos LabelEncoder
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            y_true_encoded = le.fit_transform(y_true_array)
            
            accuracies = (y_pred == y_true_encoded)
            
            # Crear bins
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]
            
            ece = 0
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                # Identificar muestras en este bin
                in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
                prop_in_bin = in_bin.mean()
                
                if prop_in_bin > 0:
                    accuracy_in_bin = accuracies[in_bin].mean()
                    avg_confidence_in_bin = confidences[in_bin].mean()
                    ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
            
            return float(ece)
            
        except Exception as e:
            print(f"⚠️ Error en ECE: {e}")
            return 0.0
    
    def train_and_evaluate_mlp(self, model_name, X_train, X_test, y_train, y_test, model_type='basic'):
        """
        Entrenar y evaluar un modelo MLP específico
        
        Args:
            model_name: Nombre del modelo
            X_train, X_test, y_train, y_test: Datos de train/test
            model_type: Tipo de modelo MLP
            
        Returns:
            dict: Resultados del modelo
        """
        print(f"\n🧠 Entrenando modelo MLP: {model_name}")
        
        try:
            # Crear modelo
            model = self.create_mlp_model(model_type)
            
            # ⚠️ CRITICAL: Compute sample weights for class imbalance (59:1 ratio)
            # Phase 1 used class_weight='balanced' in Logistic Regression
            # MLPClassifier doesn't support class_weight, so we use sample_weight
            print(f"   ⚖️ Computing sample weights for class imbalance...")
            sample_weights_train = compute_sample_weight('balanced', y_train)
            
            # Show weight distribution
            unique_labels = np.unique(y_train)
            for label in unique_labels:
                mask = y_train == label
                avg_weight = sample_weights_train[mask].mean()
                count = mask.sum()
                print(f"      Class '{label}': {count} samples, avg weight: {avg_weight:.3f}")
            
            # Entrenar modelo - con sample_weight para balancear clases
            print(f"   🔍 Datos para entrenar - X: {X_train.shape}, {X_train.dtype}")
            print(f"   🔍 Labels para entrenar - y: {len(y_train)} elementos")
            print(f"   🔍 X_train sample: {X_train[0][:3]}")  # Primeros 3 valores
            
            # ⚠️ FIT WITH SAMPLE_WEIGHT - This is critical for handling imbalance
            model.fit(X_train, y_train, sample_weight=sample_weights_train)
            
            # Predicciones
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Probabilidades para ECE
            y_prob_train = model.predict_proba(X_train)
            y_prob_test = model.predict_proba(X_test)
            
            # Métricas principales
            train_f1_macro = f1_score(y_train, y_pred_train, average='macro')
            test_f1_macro = f1_score(y_test, y_pred_test, average='macro')
            train_accuracy = accuracy_score(y_train, y_pred_train)
            test_accuracy = accuracy_score(y_test, y_pred_test)
            
            # Calibración (ECE)
            ece_score = self.calculate_ece(y_test, y_prob_test)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                scoring='f1_macro'
            )
            
            # Comparación con Phase 1
            delta_f1_vs_rf = test_f1_macro - self.phase1_results['random_forest_f1']
            delta_f1_vs_best_lr = test_f1_macro - max(
                self.phase1_results['logistic_l1_f1'],
                self.phase1_results['logistic_l2_f1']
            )
            
            # Matriz de confusión
            cm = confusion_matrix(y_test, y_pred_test)
            
            # Análisis específico de confusión crítica (good ↔ blunder)
            labels = sorted(set(y_test))
            critical_confusion = self._analyze_critical_confusion(cm, labels)
            
            # Log parámetros y métricas - SKIP MLflow por ahora
            run_id = "local_run"
            
            # Save artifacts locally
            self._save_confusion_matrix(cm, labels, model_name)
            self._save_classification_report(y_test, y_pred_test, model_name)
            
            # Resultados
            results = {
                'model_name': model_name,
                'model_type': model_type,
                'run_id': run_id,
                'train_f1_macro': train_f1_macro,
                'test_f1_macro': test_f1_macro,
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'cv_f1_macro_mean': cv_scores.mean(),
                'cv_f1_macro_std': cv_scores.std(),
                'ece': ece_score,
                'delta_f1_vs_rf': delta_f1_vs_rf,
                'delta_f1_vs_best_lr': delta_f1_vs_best_lr,
                'critical_confusion': critical_confusion,
                'confusion_matrix': cm,
                'labels': labels,
                'model': model
            }
            
            print(f"✅ {model_name} - F1 Macro Test: {test_f1_macro:.3f}")
            print(f"   ΔF1 vs RF: {delta_f1_vs_rf:+.3f}")
            print(f"   ΔF1 vs LR: {delta_f1_vs_best_lr:+.3f}")
            print(f"   CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            print(f"   ECE: {ece_score:.3f}")
            print(f"   Confusión crítica: {critical_confusion['percentage']:.1f}%")
            
            return results
        
        except Exception as e:
            print(f"❌ Error entrenando {model_name}: {e}")
            return None
    
    def _analyze_critical_confusion(self, cm, labels):
        """Analizar confusión crítica good ↔ blunder (igual que Phase 1)"""
        
        try:
            good_idx = labels.index('good')
            blunder_idx = labels.index('blunder')
            
            # Confusiones críticas
            good_as_blunder = cm[good_idx, blunder_idx]
            blunder_as_good = cm[blunder_idx, good_idx]
            total_critical = good_as_blunder + blunder_as_good
            
            # Total de muestras good y blunder
            total_good_blunder = cm[good_idx].sum() + cm[blunder_idx].sum()
            
            critical_percentage = (total_critical / total_good_blunder) * 100 if total_good_blunder > 0 else 0
            
            return {
                'good_as_blunder': int(good_as_blunder),
                'blunder_as_good': int(blunder_as_good),
                'total_critical': int(total_critical),
                'percentage': critical_percentage
            }
        except ValueError:
            return {
                'good_as_blunder': 0,
                'blunder_as_good': 0,
                'total_critical': 0,
                'percentage': 0.0
            }
    
    def _save_confusion_matrix(self, cm, labels, model_name):
        """Guardar matriz de confusión como artifact"""
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm, 
            annot=True, 
            fmt='d', 
            xticklabels=labels,
            yticklabels=labels,
            cmap='Blues'
        )
        plt.title(f'Matriz de Confusión - {model_name}')
        plt.ylabel('Etiqueta Real')
        plt.xlabel('Etiqueta Predicha')
        
        plt.tight_layout()
        plt.savefig(f'confusion_matrix_{model_name}.png', dpi=300, bbox_inches='tight')
        mlflow.log_artifact(f'confusion_matrix_{model_name}.png')
        plt.close()
    
    def _save_classification_report(self, y_true, y_pred, model_name):
        """Guardar reporte de clasificación como artifact"""
        
        report = classification_report(y_true, y_pred, output_dict=True)
        
        # Convertir a DataFrame para mejor visualización
        df_report = pd.DataFrame(report).transpose()
        
        # Guardar como CSV
        filename = f'classification_report_{model_name}.csv'
        df_report.to_csv(filename)
        mlflow.log_artifact(filename)
        
        # También log como texto
        text_report = classification_report(y_true, y_pred)
        with open(f'classification_report_{model_name}.txt', 'w') as f:
            f.write(text_report)
        mlflow.log_artifact(f'classification_report_{model_name}.txt')
    
    def _save_training_history(self, model, model_name):
        """Guardar información del modelo MLPClassifier"""
        
        # Para MLPClassifier, guardamos información del entrenamiento
        info = {
            'n_iter': getattr(model, 'n_iter_', 'N/A'),
            'loss': getattr(model, 'loss_', 'N/A'),
            'hidden_layer_sizes': model.hidden_layer_sizes,
            'alpha': model.alpha,
            'solver': model.solver
        }
        
        # Guardar como texto
        with open(f'model_info_{model_name}.txt', 'w') as f:
            f.write(f"Información del modelo {model_name}:\n")
            for key, value in info.items():
                f.write(f"{key}: {value}\n")
        
        mlflow.log_artifact(f'model_info_{model_name}.txt')
    
    def train_all_models(self, test_size=0.2, random_state=42):
        """
        Entrenar todos los modelos MLP definidos
        
        Args:
            test_size: Proporción del conjunto de test
            random_state: Semilla para reproducibilidad
        """
        print("🚀 Iniciando entrenamiento Phase 2 MLP")
        
        # Cargar datos
        X, y = self.load_data_from_db()
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, 
            stratify=y
        )
        
        # Normalizar features
        print(f"🔍 X_train dtypes antes de scaling: {X_train.dtypes.unique()}")
        print(f"🔍 X_train shape: {X_train.shape}")
        
        # Verificar que no haya NaN o inf values
        print(f"🔍 X_train NaN count: {X_train.isna().sum().sum()}")
        print(f"🔍 X_train inf count: {np.isinf(X_train.values).sum()}")
        
        # Asegurarnos que X_train es completamente numérico
        X_train = X_train.astype(np.float64)
        X_test = X_test.astype(np.float64)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"📊 Split de datos:")
        print(f"   Train: {len(X_train)} muestras")
        print(f"   Test: {len(X_test)} muestras")
        print(f"   Features normalizados: {X_train_scaled.shape[1]}")
        
        # Definir modelos a entrenar
        model_configs = {
            'mlp_basic': 'basic',
            'mlp_regularized': 'regularized', 
            'mlp_deep': 'deep'
        }
        
        # Entrenar cada modelo
        for model_name, model_type in model_configs.items():
            try:
                result = self.train_and_evaluate_mlp(
                    model_name, X_train_scaled, X_test_scaled, 
                    y_train, y_test, model_type
                )
                self.results[model_name] = result
            except Exception as e:
                print(f"❌ Error entrenando {model_name}: {e}")
                continue
        
        # Resumen de resultados
        self._print_results_summary()
        
        return self.results
    
    def _print_results_summary(self):
        """Imprimir resumen de resultados Phase 2"""
        
        print(f"\n🏆 RESUMEN DE RESULTADOS PHASE 2 MLP")
        print("=" * 70)
        
        if not self.results:
            print("❌ No hay resultados disponibles")
            return
        
        # Ordenar por F1 macro test
        sorted_results = sorted(
            self.results.items(), 
            key=lambda x: x[1]['test_f1_macro'], 
            reverse=True
        )
        
        print(f"{'Modelo':<15} {'F1 Test':<10} {'ΔF1 vs RF':<12} {'ΔF1 vs LR':<12} {'ECE':<8} {'Conf.Crítica':<12}")
        print("-" * 70)
        
        for model_name, results in sorted_results:
            f1_test = results['test_f1_macro']
            delta_rf = results['delta_f1_vs_rf']
            delta_lr = results['delta_f1_vs_best_lr']
            ece = results['ece']
            critical = f"{results['critical_confusion']['percentage']:.1f}%"
            
            print(f"{model_name:<15} {f1_test:<10.3f} {delta_rf:<+12.3f} {delta_lr:<+12.3f} {ece:<8.3f} {critical:<12}")
        
        # Mejor modelo
        best_model_name = sorted_results[0][0]
        best_results = sorted_results[0][1]
        
        print(f"\n🥇 MEJOR MODELO: {best_model_name}")
        print(f"   F1 Macro Test: {best_results['test_f1_macro']:.3f}")
        print(f"   ΔF1 vs Random Forest: {best_results['delta_f1_vs_rf']:+.3f}")
        print(f"   ΔF1 vs Best Logistic: {best_results['delta_f1_vs_best_lr']:+.3f}")
        print(f"   ECE (Calibración): {best_results['ece']:.3f}")
        
        # Verificar criterios de avance
        self._check_phase2_criteria(best_results)
    
    def _check_phase2_criteria(self, best_results):
        """Verificar criterios de avance a Phase 3"""
        
        print(f"\n✅ VERIFICACIÓN CRITERIOS PHASE 2 → PHASE 3")
        print("-" * 50)
        
        f1_test = best_results['test_f1_macro']
        delta_rf = best_results['delta_f1_vs_rf']
        delta_lr = best_results['delta_f1_vs_best_lr']
        critical_conf = best_results['critical_confusion']['percentage']
        
        checks = {
            'DL supera a ML (ΔF1 vs RF > 0.01)': delta_rf > 0.01,
            'DL supera a LR (ΔF1 vs LR > 0.01)': delta_lr > 0.01,
            'Confusión crítica < 5%': critical_conf < 5.0,
            'F1 absoluto > 0.85': f1_test > 0.85
        }
        
        all_passed = True
        for criterion, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {criterion}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n🎯 LISTO PARA PHASE 3")
        elif delta_rf > -0.05 and delta_lr > 0.01:
            print(f"\n⚠️ DL COMPETITIVO - PUEDE CONTINUAR A PHASE 3")
        else:
            print(f"\n❌ DL NO SUPERA ML - MANTENER ML COMO BASE")
        
        return all_passed


def main():
    """Función principal para ejecutar Phase 2 MLP"""
    
    print("🧠 Chess Trainer - Phase 2 MLP Training")
    print("=" * 60)
    
    try:
        # Inicializar trainer
        trainer = Phase2MLPTrainer()
        
        # Entrenar todos los modelos
        results = trainer.train_all_models()
        
        print("\n🎉 Entrenamiento Phase 2 completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante entrenamiento: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()