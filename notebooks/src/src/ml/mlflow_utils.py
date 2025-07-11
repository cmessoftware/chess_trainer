import mlflow
import mlflow.sklearn
import mlflow.xgboost
import pandas as pd
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ChessMLflowTracker:
    """
    Utilidad para gestionar experiment tracking específico para chess_trainer.
    Simplifica el registro de experimentos, métricas y modelos de ajedrez.
    """
    
    def __init__(self, tracking_uri="http://localhost:5000"):
        """
        Inicializar el tracker MLflow para chess_trainer.
        
        Args:
            tracking_uri: URI del servidor MLflow (por defecto Docker)
        """
        try:
            mlflow.set_tracking_uri(tracking_uri)
            self.client = mlflow.tracking.MlflowClient()
            logger.info(f"✅ Conectado a MLflow: {tracking_uri}")
        except Exception as e:
            logger.error(f"❌ Error conectando a MLflow: {e}")
            raise
    
    def create_chess_experiments(self):
        """Crear experimentos específicos para chess_trainer"""
        experiments = [
            ("chess_error_prediction", "Predecir tipo de error (blunder, mistake, inaccuracy)"),
            ("chess_accuracy_prediction", "Predecir accuracy de partidas"),
            ("chess_phase_classification", "Clasificar fase del juego (opening, middlegame, endgame)"),
            ("chess_opening_recommendation", "Recomendar aperturas basado en estilo de juego"),
            ("chess_stockfish_features", "Optimizar features de Stockfish y análisis táctico"),
            ("chess_elo_prediction", "Predecir ELO basado en características de juego"),
            ("chess_time_analysis", "Análizar patrones de tiempo y presión temporal")
        ]
        
        created_experiments = []
        
        for name, description in experiments:
            try:
                experiment_id = self.client.create_experiment(
                    name=name, 
                    tags={
                        "project": "chess_trainer", 
                        "description": description,
                        "created_by": "ChessMLflowTracker",
                        "version": "1.0"
                    }
                )
                created_experiments.append((name, experiment_id))
                logger.info(f"✅ Experimento creado: {name} (ID: {experiment_id})")
            except mlflow.exceptions.MlflowException as e:
                if "already exists" in str(e):
                    logger.info(f"⚠️ Experimento {name} ya existe")
                else:
                    logger.error(f"❌ Error creando experimento {name}: {e}")
        
        return created_experiments
    
    def log_chess_dataset_info(self, df: pd.DataFrame, source: str, dataset_name: str = ""):
        """
        Registrar información detallada del dataset de ajedrez.
        
        Args:
            df: DataFrame con los datos
            source: Fuente del dataset (personal, elite, novice, fide, stockfish)
            dataset_name: Nombre descriptivo del dataset
        """
        try:
            # Información básica del dataset
            mlflow.log_param("dataset_source", source)
            mlflow.log_param("dataset_name", dataset_name)
            mlflow.log_param("dataset_rows", len(df))
            mlflow.log_param("dataset_columns", len(df.columns))
            mlflow.log_param("dataset_features", list(df.columns.tolist()))
            mlflow.log_param("missing_values_total", df.isnull().sum().sum())
            
            # Información específica de ajedrez
            if 'error_label' in df.columns:
                error_dist = df['error_label'].value_counts().to_dict()
                for error_type, count in error_dist.items():
                    mlflow.log_metric(f"count_{error_type}", count)
                    mlflow.log_metric(f"pct_{error_type}", count / len(df) * 100)
            
            if 'phase' in df.columns:
                phase_dist = df['phase'].value_counts().to_dict()
                for phase, count in phase_dist.items():
                    mlflow.log_metric(f"count_phase_{phase}", count)
            
            if 'score_diff' in df.columns:
                mlflow.log_metric("score_diff_mean", df['score_diff'].mean())
                mlflow.log_metric("score_diff_std", df['score_diff'].std())
                mlflow.log_metric("score_diff_median", df['score_diff'].median())
            
            if 'material_balance' in df.columns:
                mlflow.log_metric("material_balance_mean", df['material_balance'].mean())
                mlflow.log_metric("material_balance_std", df['material_balance'].std())
            
            # Log missing values por columna (solo las importantes)
            chess_columns = ['error_label', 'score_diff', 'material_balance', 'phase', 'elo_standardized']
            for col in chess_columns:
                if col in df.columns:
                    missing_pct = df[col].isnull().sum() / len(df) * 100
                    mlflow.log_metric(f"missing_pct_{col}", missing_pct)
            
            logger.info(f"📊 Dataset info logged: {source} ({len(df)} rows, {len(df.columns)} cols)")
            
        except Exception as e:
            logger.error(f"❌ Error logging dataset info: {e}")
    
    def log_chess_model_metrics(self, y_true, y_pred, model_name: str, feature_names: List[str] = None):
        """
        Registrar métricas específicas para modelos de ajedrez.
        
        Args:
            y_true: Valores reales
            y_pred: Predicciones del modelo
            model_name: Nombre del modelo
            feature_names: Lista de nombres de features usados
        """
        try:
            # Métricas básicas de clasificación
            accuracy = accuracy_score(y_true, y_pred)
            mlflow.log_metric("accuracy", accuracy)
            
            # Métricas macro (promedio de todas las clases)
            precision_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
            recall_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
            f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
            
            mlflow.log_metric("precision_macro", precision_macro)
            mlflow.log_metric("recall_macro", recall_macro)
            mlflow.log_metric("f1_macro", f1_macro)
            
            # Métricas weighted (considera desbalance de clases)
            precision_weighted = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            recall_weighted = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            f1_weighted = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            
            mlflow.log_metric("precision_weighted", precision_weighted)
            mlflow.log_metric("recall_weighted", recall_weighted)
            mlflow.log_metric("f1_weighted", f1_weighted)
            
            # Métricas por clase (importante para error_label)
            unique_labels = sorted(set(y_true) | set(y_pred))
            for label in unique_labels:
                if label in set(y_true):  # Solo si la clase existe en y_true
                    y_true_binary = (y_true == label).astype(int)
                    y_pred_binary = (y_pred == label).astype(int)
                    
                    precision_class = precision_score(y_true_binary, y_pred_binary, zero_division=0)
                    recall_class = recall_score(y_true_binary, y_pred_binary, zero_division=0)
                    f1_class = f1_score(y_true_binary, y_pred_binary, zero_division=0)
                    
                    mlflow.log_metric(f"precision_{label}", precision_class)
                    mlflow.log_metric(f"recall_{label}", recall_class)
                    mlflow.log_metric(f"f1_{label}", f1_class)
            
            # Log classification report como artifact
            report_str = classification_report(y_true, y_pred)
            
            # Guardar reporte como archivo
            report_path = f"classification_report_{model_name}.txt"
            with open(report_path, 'w') as f:
                f.write(f"Classification Report - {model_name}\n")
                f.write("=" * 50 + "\n")
                f.write(report_str)
            
            mlflow.log_artifact(report_path, "reports")
            os.remove(report_path)  # Limpiar archivo temporal
            
            logger.info(f"📈 Métricas registradas para {model_name}: Acc={accuracy:.3f}, F1={f1_macro:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Error logging model metrics: {e}")
    
    def log_feature_importance(self, model, feature_names: List[str], model_name: str):
        """
        Registrar importancia de features para modelos de tree-based.
        
        Args:
            model: Modelo entrenado (debe tener feature_importances_)
            feature_names: Lista de nombres de features
            model_name: Nombre del modelo
        """
        try:
            if hasattr(model, 'feature_importances_'):
                feature_importance = pd.DataFrame({
                    'feature': feature_names,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                # Log importancia de cada feature
                for idx, row in feature_importance.iterrows():
                    mlflow.log_metric(f"importance_{row['feature']}", row['importance'])
                
                # Log top 5 features
                top_features = feature_importance.head(5)['feature'].tolist()
                mlflow.log_param("top_5_features", top_features)
                
                # Guardar tabla completa como artifact
                importance_path = f"feature_importance_{model_name}.csv"
                feature_importance.to_csv(importance_path, index=False)
                mlflow.log_artifact(importance_path, "feature_analysis")
                os.remove(importance_path)
                
                logger.info(f"🎯 Feature importance logged for {model_name}")
                logger.info(f"Top 5 features: {top_features}")
                
                return feature_importance
            else:
                logger.warning(f"⚠️ Model {model_name} no tiene feature_importances_")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error logging feature importance: {e}")
            return None
    
    def log_chess_hyperparameters(self, model, model_name: str, custom_params: Dict[str, Any] = None):
        """
        Registrar hiperparámetros específicos para modelos de ajedrez.
        
        Args:
            model: Modelo entrenado
            model_name: Nombre del modelo
            custom_params: Parámetros personalizados adicionales
        """
        try:
            # Log nombre del modelo
            mlflow.log_param("model_type", model_name)
            
            # Log parámetros específicos según el tipo de modelo
            if hasattr(model, 'get_params'):
                params = model.get_params()
                
                # Filtrar solo parámetros relevantes para evitar noise
                relevant_params = [
                    'n_estimators', 'max_depth', 'min_samples_split', 'min_samples_leaf',
                    'max_features', 'random_state', 'criterion', 'bootstrap',
                    'C', 'penalty', 'solver', 'max_iter', 'tol',
                    'learning_rate', 'n_components', 'alpha', 'fit_intercept'
                ]
                
                for param_name, param_value in params.items():
                    if param_name in relevant_params and param_value is not None:
                        mlflow.log_param(param_name, param_value)
            
            # Log parámetros personalizados
            if custom_params:
                for param_name, param_value in custom_params.items():
                    mlflow.log_param(param_name, param_value)
            
            logger.info(f"⚙️ Hiperparámetros registrados para {model_name}")
            
        except Exception as e:
            logger.error(f"❌ Error logging hyperparameters: {e}")
    
    def get_best_model(self, experiment_name: str, metric: str = "accuracy"):
        """
        Obtener el mejor modelo de un experimento basado en una métrica.
        
        Args:
            experiment_name: Nombre del experimento
            metric: Métrica a optimizar (default: accuracy)
            
        Returns:
            Información del mejor run
        """
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                logger.error(f"❌ Experimento {experiment_name} no encontrado")
                return None
            
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric} DESC"],
                max_results=1
            )
            
            if runs:
                best_run = runs[0]
                logger.info(f"🏆 Mejor modelo: {best_run.info.run_id}")
                logger.info(f"📊 {metric}: {best_run.data.metrics.get(metric, 'N/A')}")
                return best_run
            else:
                logger.warning(f"⚠️ No se encontraron runs en {experiment_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo mejor modelo: {e}")
            return None
    
    def compare_models(self, experiment_name: str, metrics: List[str] = None):
        """
        Comparar todos los modelos de un experimento.
        
        Args:
            experiment_name: Nombre del experimento
            metrics: Lista de métricas a comparar
            
        Returns:
            DataFrame con comparación de modelos
        """
        try:
            if metrics is None:
                metrics = ["accuracy", "f1_macro", "precision_macro", "recall_macro"]
            
            experiment = self.client.get_experiment_by_name(experiment_name)
            if not experiment:
                logger.error(f"❌ Experimento {experiment_name} no encontrado")
                return None
            
            runs = self.client.search_runs(experiment_ids=[experiment.experiment_id])
            
            comparison_data = []
            for run in runs:
                row = {
                    'run_id': run.info.run_id,
                    'run_name': run.data.tags.get('mlflow.runName', 'unnamed'),
                    'model_type': run.data.params.get('model_type', 'unknown'),
                    'status': run.info.status
                }
                
                # Agregar métricas
                for metric in metrics:
                    row[metric] = run.data.metrics.get(metric, None)
                
                # Agregar algunos parámetros importantes
                row['n_estimators'] = run.data.params.get('n_estimators', None)
                row['max_depth'] = run.data.params.get('max_depth', None)
                
                comparison_data.append(row)
            
            comparison_df = pd.DataFrame(comparison_data)
            
            if not comparison_df.empty:
                logger.info(f"📊 Comparación de {len(comparison_df)} modelos en {experiment_name}")
                return comparison_df.sort_values('accuracy', ascending=False, na_position='last')
            else:
                logger.warning(f"⚠️ No hay datos para comparar en {experiment_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error comparando modelos: {e}")
            return None
