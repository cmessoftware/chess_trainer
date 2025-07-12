"""
Pipeline completo de entrenamiento y predicción con MLflow
Este script entrena un modelo de clasificación de errores y hace predicciones fiables.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import mlflow
import mlflow.sklearn
import joblib

# Añadir path de src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar utilidades del proyecto
from db.repository.features_repository import FeaturesRepository
from ml.mlflow_utils import ChessMLflowTracker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChessErrorPredictor:
    """
    Predictor de errores de ajedrez usando MLflow para tracking y gestión de modelos.
    """

    def __init__(self):
        """Inicializar el predictor con MLflow tracker"""
        self.tracker = ChessMLflowTracker()
        self.features_repo = FeaturesRepository()
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = [
            "score_diff",
            "material_balance",
            "material_total",
            "num_pieces",
            "branching_factor",
            "self_mobility",
            "opponent_mobility",
            "move_number",
            "player_color",
            "has_castling_rights",
            "is_repetition",
            "is_low_mobility",
            "is_center_controlled",
            "is_pawn_endgame",
            "threatens_mate",
            "is_forced_move",
        ]

    def load_training_data(self):
        """Cargar datos de entrenamiento desde la base de datos"""
        logger.info("Cargando datos de entrenamiento...")

        # Obtener features desde la base de datos
        features_df = self.features_repo.get_all_features_as_dataframe()

        if features_df.empty:
            raise ValueError("No hay datos de features en la base de datos")

        # Filtrar solo las columnas necesarias
        available_columns = [
            col for col in self.feature_columns if col in features_df.columns
        ]
        features_df = features_df[available_columns + ["error_label"]].dropna()

        # Filtrar solo errores válidos
        valid_errors = ["good", "inaccuracy", "mistake", "blunder"]
        features_df = features_df[features_df["error_label"].isin(valid_errors)]

        logger.info(f"Datos cargados: {len(features_df)} registros")
        logger.info(
            f"Distribución de errores: {features_df['error_label'].value_counts().to_dict()}"
        )

        return features_df

    def preprocess_data(self, df):
        """Preprocesar datos para entrenamiento"""
        logger.info("Preprocesando datos...")

        # Separar features y target
        X = df[self.feature_columns].copy()
        y = df["error_label"].copy()

        # Codificar variables categóricas si es necesario
        categorical_cols = X.select_dtypes(include=["object"]).columns
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])

        # Escalar features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

        # Codificar etiquetas
        y_encoded = self.label_encoder.fit_transform(y)

        return X_scaled, y_encoded

    def train_model(self, experiment_name="chess_error_prediction_v2"):
        """Entrenar modelo con MLflow tracking"""
        logger.info("Iniciando entrenamiento del modelo...")

        # Configurar experimento
        mlflow.set_experiment(experiment_name)

        # Cargar y preprocesar datos
        df = self.load_training_data()
        X, y = self.preprocess_data(df)

        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        with mlflow.start_run(run_name="random_forest_optimized") as run:
            # Registrar información del dataset
            mlflow.log_param("dataset_size", len(df))
            mlflow.log_param("features_count", len(self.feature_columns))
            mlflow.log_param("train_size", len(X_train))
            mlflow.log_param("test_size", len(X_test))

            # Distribución de clases
            class_distribution = pd.Series(y_train).value_counts().to_dict()
            for label, count in class_distribution.items():
                mlflow.log_param(
                    f"class_{self.label_encoder.classes_[label]}_count", count
                )

            # Optimización de hiperparámetros
            logger.info("Optimizando hiperparámetros...")
            param_grid = {
                "n_estimators": [100, 200, 300],
                "max_depth": [10, 20, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
            }

            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(
                rf, param_grid, cv=5, scoring="f1_weighted", n_jobs=-1
            )
            grid_search.fit(X_train, y_train)

            # Mejor modelo
            self.model = grid_search.best_estimator_

            # Registrar mejores parámetros
            for param, value in grid_search.best_params_.items():
                mlflow.log_param(f"best_{param}", value)

            # Predicciones
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)

            # Métricas
            accuracy = accuracy_score(y_test, y_pred)
            cv_scores = cross_val_score(
                self.model, X_train, y_train, cv=5, scoring="f1_weighted"
            )

            # Registrar métricas
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("cv_mean_f1", cv_scores.mean())
            mlflow.log_metric("cv_std_f1", cv_scores.std())
            mlflow.log_metric("best_cv_score", grid_search.best_score_)

            # Métricas por clase
            report = classification_report(
                y_test,
                y_pred,
                target_names=self.label_encoder.classes_,
                output_dict=True,
            )

            for label, metrics in report.items():
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        mlflow.log_metric(f"{label}_{metric}", value)

            # Importancia de features
            feature_importance = pd.DataFrame(
                {
                    "feature": self.feature_columns,
                    "importance": self.model.feature_importances_,
                }
            ).sort_values("importance", ascending=False)

            # Registrar top features
            top_features = feature_importance.head(10)
            for idx, row in top_features.iterrows():
                mlflow.log_metric(f"importance_{row['feature']}", row["importance"])

            # Guardar modelo y preprocessors
            model_artifacts = {
                "model": self.model,
                "scaler": self.scaler,
                "label_encoder": self.label_encoder,
                "feature_columns": self.feature_columns,
            }

            # Registrar modelo en MLflow
            mlflow.sklearn.log_model(
                self.model,
                "chess_error_classifier",
                registered_model_name="ChessErrorClassifier",
            )

            # Guardar artefactos adicionales
            import tempfile
            import pickle

            with tempfile.TemporaryDirectory() as temp_dir:
                # Guardar preprocessors
                scaler_path = Path(temp_dir) / "scaler.pkl"
                encoder_path = Path(temp_dir) / "label_encoder.pkl"

                joblib.dump(self.scaler, scaler_path)
                joblib.dump(self.label_encoder, encoder_path)

                mlflow.log_artifact(str(scaler_path))
                mlflow.log_artifact(str(encoder_path))

            # Reporte de clasificación
            logger.info("\\n=== REPORTE DE ENTRENAMIENTO ===")
            logger.info(f"Accuracy: {accuracy:.4f}")
            logger.info(f"CV F1-Score: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
            logger.info("\\nTop 5 Features más importantes:")
            for idx, row in feature_importance.head().iterrows():
                logger.info(f"  {row['feature']}: {row['importance']:.4f}")

            logger.info("\\nDistribución de predicciones:")
            pred_distribution = pd.Series(y_pred).value_counts()
            for label_idx, count in pred_distribution.items():
                label_name = self.label_encoder.classes_[label_idx]
                logger.info(f"  {label_name}: {count}")

            run_id = run.info.run_id
            logger.info(f"\\n✅ Modelo entrenado exitosamente. Run ID: {run_id}")

            return run_id, accuracy, cv_scores.mean()

    def load_model(
        self, run_id=None, model_name="ChessErrorClassifier", version="latest"
    ):
        """Cargar modelo desde MLflow"""
        logger.info(f"Cargando modelo {model_name} versión {version}...")

        try:
            if run_id:
                # Cargar desde run específico
                model_uri = f"runs:/{run_id}/chess_error_classifier"
            else:
                # Cargar desde modelo registrado
                model_uri = f"models:/{model_name}/{version}"

            self.model = mlflow.sklearn.load_model(model_uri)
            logger.info("✅ Modelo cargado exitosamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            return False

    def predict_move_error(self, features_dict):
        """Predecir error para una jugada específica"""
        if self.model is None:
            raise ValueError("Modelo no cargado. Usa load_model() primero.")

        # Convertir a DataFrame
        df = pd.DataFrame([features_dict])

        # Aplicar preprocesamiento
        X = df[self.feature_columns].copy()
        X_scaled = self.scaler.transform(X)

        # Predicción
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]

        # Decodificar predicción
        predicted_label = self.label_encoder.classes_[prediction]

        # Crear diccionario de probabilidades
        prob_dict = {
            self.label_encoder.classes_[i]: prob for i, prob in enumerate(probabilities)
        }

        return {
            "predicted_error": predicted_label,
            "confidence": probabilities.max(),
            "probabilities": prob_dict,
        }

    def batch_predict(self, features_df):
        """Predicciones en lote"""
        if self.model is None:
            raise ValueError("Modelo no cargado. Usa load_model() primero.")

        # Preprocesar
        X = features_df[self.feature_columns].copy()
        X_scaled = self.scaler.transform(X)

        # Predicciones
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)

        # Crear DataFrame de resultados
        results = features_df.copy()
        results["predicted_error"] = [
            self.label_encoder.classes_[p] for p in predictions
        ]
        results["confidence"] = probabilities.max(axis=1)

        return results


def main():
    """Función principal para entrenar y probar el modelo"""
    predictor = ChessErrorPredictor()

    # Entrenar modelo
    run_id, accuracy, cv_score = predictor.train_model()

    # Ejemplo de predicción
    logger.info("\\n=== EJEMPLO DE PREDICCIÓN ===")
    sample_features = {
        "score_diff": 150,
        "material_balance": -2,
        "material_total": 28,
        "num_pieces": 16,
        "branching_factor": 45,
        "self_mobility": 20,
        "opponent_mobility": 25,
        "move_number": 15,
        "player_color": 1,
        "has_castling_rights": 0,
        "is_repetition": 0,
        "is_low_mobility": 0,
        "is_center_controlled": 1,
        "is_pawn_endgame": 0,
        "threatens_mate": 0,
        "is_forced_move": 0,
    }

    prediction = predictor.predict_move_error(sample_features)
    logger.info(f"Predicción: {prediction['predicted_error']}")
    logger.info(f"Confianza: {prediction['confidence']:.4f}")
    logger.info("Probabilidades:")
    for error, prob in prediction["probabilities"].items():
        logger.info(f"  {error}: {prob:.4f}")

    return predictor, run_id


if __name__ == "__main__":
    predictor, run_id = main()
