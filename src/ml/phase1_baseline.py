#!/usr/bin/env python3
"""
PHASE 1 - Clasificación de errores por jugada (ML clásico)
==========================================================

Objetivo: Responder ¿esta jugada fue buena o mala, y en qué grado?

Input: Features por jugada (material, rey, score, tags tácticos, apertura)
Modelos: 
- Logistic Regression L2 (baseline principal)
- Logistic Regression L1 (selección de features) 
- RandomForest (opcional para comparar)

Output: error_label ∈ {brilliant, good, inaccuracy, mistake, blunder}
Métricas: F1 macro (principal), matriz de confusión

Criterio de avance: 
- Modelo reproducible y estable ✅
- Confusión grave (good ↔ blunder) muy baja (< 5%) ✅
- F1 macro > 0.70 como baseline mínimo ✅
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# ML imports
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, f1_score,
    accuracy_score, precision_recall_fscore_support
)
from sklearn.pipeline import Pipeline
import joblib

# MLflow imports
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

# Database imports
import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine

# Project imports
sys.path.append(str(Path(__file__).parent.parent))
from ml.mlflow_utils import ChessMLflowTracker


class Phase1BaselineTrainer:
    """Entrenador para Phase 1 - ML Clásico baseline"""
    
    def __init__(self, experiment_name="chess_trainer_phase1"):
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
        
        # Configurar MLflow local (file-based)
        mlflow_dir = Path(__file__).parent.parent.parent / "mlruns"
        mlflow_dir.mkdir(exist_ok=True)
        mlflow.set_tracking_uri(f"file:///{mlflow_dir}")
        mlflow.set_experiment(experiment_name)
        
        print(f"🎯 Iniciando Phase 1 Baseline Trainer")
        print(f"📊 MLflow URI: {mlflow.get_tracking_uri()}")
        print(f"🧪 Experimento: {experiment_name}")
    
    def load_data_from_db(self, sample_size=None, min_games_per_label=100):
        """
        Cargar datos etiquetados desde PostgreSQL
        
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
        
        # Query para obtener features etiquetadas
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
            print(f"   Labels removidos: {set(label_counts.index) - set(labels_to_keep)}")
        
        # Preparar features
        self.feature_columns = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'score_diff',
            'player_color', 'white_elo', 'black_elo'
        ]
        
        # Manejo de valores faltantes y limpieza
        df_clean = df_filtered.copy()
        
        # Convertir columnas numéricas y limpiar valores vacíos
        numeric_columns = [
            'material_balance', 'material_total', 'num_pieces',
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'score_diff', 'white_elo', 'black_elo'
        ]
        
        for col in numeric_columns:
            if col in df_clean.columns:
                # Reemplazar strings vacíos con NaN, luego con 0
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        # Manejo de columnas categóricas/booleanas
        categorical_columns = [
            'has_castling_rights', 'is_repetition', 'is_low_mobility',
            'is_center_controlled', 'is_pawn_endgame', 'player_color'
        ]
        
        for col in categorical_columns:
            if col in df_clean.columns:
                # Convertir a numérico, valores no válidos a 0
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
        
        X = df_clean[self.feature_columns]
        y = df_clean['error_label']
        
        # Verificar datos
        print(f"✅ Datos preparados: {X.shape[0]} muestras, {X.shape[1]} features")
        print(f"📊 Labels finales: {y.value_counts().to_dict()}")
        
        return X, y
    
    def prepare_models(self):
        """Definir modelos según roadmap Phase 1"""
        
        self.models = {
            # Baseline principal - Logistic Regression L2
            'logistic_l2': Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(
                    penalty='l2',
                    C=1.0,
                    max_iter=1000,
                    random_state=42,
                    multi_class='ovr'
                ))
            ]),
            
            # Selección de features - Logistic Regression L1  
            'logistic_l1': Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', LogisticRegression(
                    penalty='l1',
                    C=1.0,
                    solver='liblinear',
                    max_iter=1000,
                    random_state=42,
                    multi_class='ovr'
                ))
            ]),
            
            # Opcional - RandomForest para comparar
            'random_forest': Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    class_weight='balanced'
                ))
            ])
        }
        
        print(f"🤖 Modelos preparados: {list(self.models.keys())}")
    
    def train_and_evaluate_model(self, model_name, X_train, X_test, y_train, y_test):
        """
        Entrenar y evaluar un modelo específico
        
        Args:
            model_name: Nombre del modelo
            X_train, X_test, y_train, y_test: Datos de train/test
            
        Returns:
            dict: Resultados del modelo
        """
        print(f"\n🏋️ Entrenando modelo: {model_name}")
        
        model = self.models[model_name]
        
        with mlflow.start_run(run_name=f"phase1_{model_name}") as run:
            
            # Entrenar modelo
            model.fit(X_train, y_train)
            
            # Predicciones
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Métricas principales
            train_f1_macro = f1_score(y_train, y_pred_train, average='macro')
            test_f1_macro = f1_score(y_test, y_pred_test, average='macro')
            train_accuracy = accuracy_score(y_train, y_pred_train)
            test_accuracy = accuracy_score(y_test, y_pred_test)
            
            # Matriz de confusión
            cm = confusion_matrix(y_test, y_pred_test)
            
            # Análisis específico de confusión crítica (good ↔ blunder)
            labels = sorted(set(y_test))
            critical_confusion = self._analyze_critical_confusion(cm, labels)
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train, 
                cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
                scoring='f1_macro'
            )
            
            # Log parámetros y métricas a MLflow
            if hasattr(model.named_steps['classifier'], 'get_params'):
                params = model.named_steps['classifier'].get_params()
                mlflow.log_params(params)
            
            mlflow.log_metrics({
                'train_f1_macro': train_f1_macro,
                'test_f1_macro': test_f1_macro,
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'cv_f1_macro_mean': cv_scores.mean(),
                'cv_f1_macro_std': cv_scores.std(),
                'critical_confusion_pct': critical_confusion['percentage'],
                'n_samples_train': len(X_train),
                'n_samples_test': len(X_test),
                'n_features': X_train.shape[1]
            })
            
            # Guardar artifacts
            self._save_confusion_matrix(cm, labels, model_name)
            self._save_classification_report(y_test, y_pred_test, model_name)
            
            # Log del modelo
            signature = infer_signature(X_test, y_pred_test)
            mlflow.sklearn.log_model(
                model, 
                f"phase1_{model_name}", 
                signature=signature
            )
            
            # Resultados
            results = {
                'model_name': model_name,
                'run_id': run.info.run_id,
                'train_f1_macro': train_f1_macro,
                'test_f1_macro': test_f1_macro,
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'cv_f1_macro_mean': cv_scores.mean(),
                'cv_f1_macro_std': cv_scores.std(),
                'critical_confusion': critical_confusion,
                'confusion_matrix': cm,
                'labels': labels,
                'model': model
            }
            
            print(f"✅ {model_name} - F1 Macro Test: {test_f1_macro:.3f}")
            print(f"   Accuracy Test: {test_accuracy:.3f}")
            print(f"   CV F1 Macro: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            print(f"   Confusión crítica: {critical_confusion['percentage']:.1f}%")
            
            return results
    
    def _analyze_critical_confusion(self, cm, labels):
        """Analizar confusión crítica good ↔ blunder"""
        
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
    
    def train_all_models(self, test_size=0.2, random_state=42):
        """
        Entrenar todos los modelos definidos
        
        Args:
            test_size: Proporción del conjunto de test
            random_state: Semilla para reproducibilidad
        """
        print("🚀 Iniciando entrenamiento Phase 1 Baseline")
        
        # Cargar datos
        X, y = self.load_data_from_db()
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, 
            stratify=y
        )
        
        print(f"📊 Split de datos:")
        print(f"   Train: {len(X_train)} muestras")
        print(f"   Test: {len(X_test)} muestras")
        
        # Preparar modelos
        self.prepare_models()
        
        # Entrenar cada modelo
        for model_name in self.models.keys():
            try:
                result = self.train_and_evaluate_model(
                    model_name, X_train, X_test, y_train, y_test
                )
                self.results[model_name] = result
            except Exception as e:
                print(f"❌ Error entrenando {model_name}: {e}")
                continue
        
        # Resumen de resultados
        self._print_results_summary()
        
        return self.results
    
    def _print_results_summary(self):
        """Imprimir resumen de resultados"""
        
        print(f"\n🏆 RESUMEN DE RESULTADOS PHASE 1 BASELINE")
        print("=" * 60)
        
        if not self.results:
            print("❌ No hay resultados disponibles")
            return
        
        # Ordenar por F1 macro test
        sorted_results = sorted(
            self.results.items(), 
            key=lambda x: x[1]['test_f1_macro'], 
            reverse=True
        )
        
        print(f"{'Modelo':<15} {'F1 Test':<10} {'Accuracy':<10} {'CV F1':<15} {'Conf.Crítica':<12}")
        print("-" * 60)
        
        for model_name, results in sorted_results:
            f1_test = results['test_f1_macro']
            accuracy = results['test_accuracy'] 
            cv_f1 = f"{results['cv_f1_macro_mean']:.3f}±{results['cv_f1_macro_std']:.3f}"
            critical = f"{results['critical_confusion']['percentage']:.1f}%"
            
            print(f"{model_name:<15} {f1_test:<10.3f} {accuracy:<10.3f} {cv_f1:<15} {critical:<12}")
        
        # Mejor modelo
        best_model_name = sorted_results[0][0]
        best_results = sorted_results[0][1]
        
        print(f"\n🥇 MEJOR MODELO: {best_model_name}")
        print(f"   F1 Macro Test: {best_results['test_f1_macro']:.3f}")
        print(f"   Confusión Crítica: {best_results['critical_confusion']['percentage']:.1f}%")
        
        # Verificar criterios de avance
        self._check_phase1_criteria(best_results)
    
    def _check_phase1_criteria(self, best_results):
        """Verificar criterios de avance a Phase 2"""
        
        print(f"\n✅ VERIFICACIÓN CRITERIOS PHASE 1 → PHASE 2")
        print("-" * 50)
        
        criteria = {
            'f1_macro_threshold': 0.70,
            'critical_confusion_threshold': 5.0,
            'stability_cv_std_threshold': 0.05
        }
        
        f1_test = best_results['test_f1_macro']
        critical_conf = best_results['critical_confusion']['percentage']
        cv_std = best_results['cv_f1_macro_std']
        
        checks = {
            'F1 Macro > 0.70': f1_test >= criteria['f1_macro_threshold'],
            'Confusión crítica < 5%': critical_conf < criteria['critical_confusion_threshold'],
            'Modelo estable (CV std < 0.05)': cv_std < criteria['stability_cv_std_threshold']
        }
        
        all_passed = True
        for criterion, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {criterion}")
            if not passed:
                all_passed = False
        
        print(f"\n{'🎯 LISTO PARA PHASE 2' if all_passed else '⚠️ NECESITA MEJORAS ANTES DE PHASE 2'}")
        
        return all_passed


def main():
    """Función principal para ejecutar Phase 1 baseline"""
    
    print("🏁 Chess Trainer - Phase 1 Baseline Training")
    print("=" * 60)
    
    try:
        # Inicializar trainer
        trainer = Phase1BaselineTrainer()
        
        # Entrenar todos los modelos
        results = trainer.train_all_models()
        
        print("\n🎉 Entrenamiento Phase 1 completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante entrenamiento: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()