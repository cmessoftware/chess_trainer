"""
🔮 Pipeline Completo con MLflow
Tutorial paso a paso para usar MLflow en predicciones de ajedrez
"""

import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from pathlib import Path
import logging
import time
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLflowChessPredictor:
    """Pipeline completo de ML con MLflow para predicción de errores en ajedrez"""

    def __init__(self, mlflow_tracking_uri="http://localhost:5000"):
        """
        Inicializar predictor con MLflow

        Args:
            mlflow_tracking_uri: URI del servidor MLflow
        """
        self.mlflow_uri = mlflow_tracking_uri
        self.experiment_name = "chess_error_prediction"
        self.model = None
        self.features = [
            "material_balance",
            "material_total",
            "num_pieces",
            "branching_factor",
            "self_mobility",
            "opponent_mobility",
            "score_diff",
            "move_number",
            "white_elo",
            "black_elo",
        ]

    def setup_mlflow(self):
        """Configurar MLflow"""

        logger.info(f"🔄 Configurando MLflow en: {self.mlflow_uri}")

        try:
            # Configurar tracking URI
            mlflow.set_tracking_uri(self.mlflow_uri)

            # Crear o configurar experimento
            try:
                experiment_id = mlflow.create_experiment(self.experiment_name)
                logger.info(f"✅ Nuevo experimento creado: {self.experiment_name}")
            except mlflow.exceptions.MlflowException:
                experiment = mlflow.get_experiment_by_name(self.experiment_name)
                experiment_id = experiment.experiment_id
                logger.info(f"✅ Usando experimento existente: {self.experiment_name}")

            mlflow.set_experiment(self.experiment_name)

            # Verificar conexión
            mlflow.search_experiments()
            logger.info("✅ MLflow configurado correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error configurando MLflow: {e}")
            return False

    def load_and_prepare_data(self):
        """Cargar y preparar datos"""

        logger.info("📊 Cargando y preparando datos...")

        # Buscar dataset
        dataset_paths = [
            "data/export/unified_small_sources.parquet",
            "data/processed/unified_small_sources.parquet",
        ]

        dataset_path = None
        for path in dataset_paths:
            if Path(path).exists():
                dataset_path = path
                break

        if not dataset_path:
            raise FileNotFoundError(
                "❌ Dataset no encontrado en las ubicaciones esperadas"
            )

        logger.info(f"📂 Cargando dataset: {dataset_path}")
        df = pd.read_parquet(dataset_path)

        # Filtrar datos válidos
        df_valid = df[df["error_label"].notna()].copy()
        logger.info(f"📊 Dataset shape: {df.shape}")
        logger.info(f"📊 Datos válidos: {df_valid.shape}")

        # Preparar features y target
        X = df_valid[self.features].fillna(0)
        y = df_valid["error_label"]

        # Log de estadísticas de datos
        mlflow.log_param("total_samples", len(df))
        mlflow.log_param("valid_samples", len(df_valid))
        mlflow.log_param("features_count", len(self.features))

        # Log distribución de clases
        class_dist = y.value_counts().to_dict()
        for class_name, count in class_dist.items():
            mlflow.log_metric(f"class_count_{class_name}", count)
            mlflow.log_metric(f"class_pct_{class_name}", count / len(y) * 100)

        return X, y, df_valid

    def train_model_with_mlflow(self, X, y):
        """Entrenar modelo con seguimiento MLflow"""

        logger.info("🎯 Entrenando modelo con MLflow...")

        with mlflow.start_run(run_name="chess_error_classification"):

            # Log parámetros del experimento
            mlflow.log_param("algorithm", "RandomForest")
            mlflow.log_param("n_estimators", 100)
            mlflow.log_param("random_state", 42)
            mlflow.log_param("features", self.features)

            # Split de datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            mlflow.log_param("train_size", len(X_train))
            mlflow.log_param("test_size", len(X_test))

            # Entrenar modelo
            start_time = time.time()

            self.model = RandomForestClassifier(
                n_estimators=100, random_state=42, n_jobs=-1
            )
            self.model.fit(X_train, y_train)

            training_time = time.time() - start_time
            mlflow.log_metric("training_time_seconds", training_time)

            # Evaluación
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)

            y_pred = self.model.predict(X_test)

            # Log métricas principales
            mlflow.log_metric("train_accuracy", train_score)
            mlflow.log_metric("test_accuracy", test_score)
            mlflow.log_metric("accuracy", test_score)

            # Reporte de clasificación detallado
            report = classification_report(y_test, y_pred, output_dict=True)

            for class_name in report:
                if class_name not in ["accuracy", "macro avg", "weighted avg"]:
                    mlflow.log_metric(
                        f"precision_{class_name}", report[class_name]["precision"]
                    )
                    mlflow.log_metric(
                        f"recall_{class_name}", report[class_name]["recall"]
                    )
                    mlflow.log_metric(
                        f"f1_{class_name}", report[class_name]["f1-score"]
                    )

            # Métricas agregadas
            mlflow.log_metric("macro_avg_precision", report["macro avg"]["precision"])
            mlflow.log_metric("macro_avg_recall", report["macro avg"]["recall"])
            mlflow.log_metric("macro_avg_f1", report["macro avg"]["f1-score"])

            # Importancia de features
            feature_importance = dict(
                zip(self.features, self.model.feature_importances_)
            )
            for feature, importance in feature_importance.items():
                mlflow.log_metric(f"feature_importance_{feature}", importance)

            # Log feature más importante
            most_important_feature = max(feature_importance, key=feature_importance.get)
            mlflow.log_param("most_important_feature", most_important_feature)
            mlflow.log_metric(
                "most_important_feature_score",
                feature_importance[most_important_feature],
            )

            # Guardar modelo en MLflow
            mlflow.sklearn.log_model(
                self.model, "model", registered_model_name="chess_error_classifier"
            )

            # Guardar artefactos adicionales

            # 1. Lista de features
            with open("temp_features.txt", "w") as f:
                f.write("\n".join(self.features))
            mlflow.log_artifact("temp_features.txt", "model_artifacts")
            os.remove("temp_features.txt")

            # 2. Reporte de clasificación
            report_str = classification_report(y_test, y_pred)
            with open("temp_classification_report.txt", "w") as f:
                f.write(report_str)
            mlflow.log_artifact("temp_classification_report.txt", "evaluation")
            os.remove("temp_classification_report.txt")

            # 3. Matriz de confusión
            cm = confusion_matrix(y_test, y_pred)
            np.savetxt("temp_confusion_matrix.csv", cm, delimiter=",", fmt="%d")
            mlflow.log_artifact("temp_confusion_matrix.csv", "evaluation")
            os.remove("temp_confusion_matrix.csv")

            # Log información del run
            run_id = mlflow.active_run().info.run_id
            logger.info(f"✅ Modelo entrenado - Run ID: {run_id}")
            logger.info(f"🎯 Test Accuracy: {test_score:.4f}")
            logger.info(
                f"⭐ Feature más importante: {most_important_feature} ({feature_importance[most_important_feature]:.4f})"
            )

            return run_id, test_score

    def make_predictions_with_mlflow(self, run_id=None):
        """Hacer predicciones usando modelo de MLflow"""

        logger.info("🔮 Haciendo predicciones con modelo MLflow...")

        # Cargar modelo desde MLflow
        if run_id:
            model_uri = f"runs:/{run_id}/model"
            logger.info(f"📦 Cargando modelo desde run: {run_id}")
        else:
            # Usar último modelo registrado
            model_uri = "models:/chess_error_classifier/latest"
            logger.info("📦 Cargando último modelo registrado")

        try:
            loaded_model = mlflow.sklearn.load_model(model_uri)
            logger.info("✅ Modelo cargado desde MLflow")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo desde MLflow: {e}")
            logger.info("🔄 Usando modelo en memoria...")
            loaded_model = self.model

        # Cargar datos completos para predicciones
        X, y, df_valid = self.load_and_prepare_data()

        with mlflow.start_run(run_name="chess_predictions"):

            # Log información de predicción
            mlflow.log_param("prediction_samples", len(X))
            mlflow.log_param("model_uri", model_uri)

            # Hacer predicciones
            start_time = time.time()
            predictions = loaded_model.predict(X)
            probabilities = loaded_model.predict_proba(X)
            prediction_time = time.time() - start_time

            mlflow.log_metric("prediction_time_seconds", prediction_time)
            mlflow.log_metric("predictions_per_second", len(X) / prediction_time)

            # Agregar predicciones al DataFrame
            df_results = df_valid.copy()
            df_results["predicted_error"] = predictions
            df_results["prediction_confidence"] = probabilities.max(axis=1)

            # Log estadísticas de predicciones
            pred_dist = pd.Series(predictions).value_counts()
            for class_name, count in pred_dist.items():
                mlflow.log_metric(f"predicted_count_{class_name}", count)
                mlflow.log_metric(
                    f"predicted_pct_{class_name}", count / len(predictions) * 100
                )

            # Estadísticas de confianza
            confidence_stats = {
                "mean_confidence": probabilities.max(axis=1).mean(),
                "median_confidence": np.median(probabilities.max(axis=1)),
                "min_confidence": probabilities.max(axis=1).min(),
                "max_confidence": probabilities.max(axis=1).max(),
                "high_confidence_pct": (probabilities.max(axis=1) > 0.9).sum()
                / len(predictions)
                * 100,
                "low_confidence_pct": (probabilities.max(axis=1) < 0.6).sum()
                / len(predictions)
                * 100,
            }

            for metric, value in confidence_stats.items():
                mlflow.log_metric(metric, value)

            # Guardar resultados
            output_path = "predictions_results_mlflow.parquet"
            df_results.to_parquet(output_path, index=False)
            mlflow.log_artifact(output_path, "predictions")

            # Crear resumen CSV
            summary_path = "predictions_summary_mlflow.csv"
            summary_cols = ["move_san", "predicted_error", "prediction_confidence"]
            if "error_label" in df_results.columns:
                summary_cols.append("error_label")

            available_cols = [col for col in summary_cols if col in df_results.columns]
            df_summary = df_results[available_cols].head(1000)
            df_summary.to_csv(summary_path, index=False)
            mlflow.log_artifact(summary_path, "predictions")

            # Log información del run
            prediction_run_id = mlflow.active_run().info.run_id
            logger.info(f"✅ Predicciones completadas - Run ID: {prediction_run_id}")
            logger.info(f"📊 {len(predictions)} predicciones generadas")
            logger.info(
                f"🎯 Confianza promedio: {confidence_stats['mean_confidence']:.3f}"
            )

            return df_results, prediction_run_id


def run_complete_mlflow_pipeline():
    """Ejecutar pipeline completo con MLflow"""

    print("🚀 PIPELINE COMPLETO CON MLflow")
    print("🎯 Chess Error Prediction - Tutorial MLflow")
    print("=" * 80)

    # Inicializar predictor
    predictor = MLflowChessPredictor()

    # PASO 1: Configurar MLflow
    print("\n" + "=" * 60)
    print("📋 PASO 1: Configurando MLflow")
    print("=" * 60)

    if not predictor.setup_mlflow():
        print("❌ Error configurando MLflow. Verifica que esté ejecutándose.")
        return False

    try:
        # PASO 2: Cargar datos
        print("\n" + "=" * 60)
        print("📊 PASO 2: Cargando y preparando datos")
        print("=" * 60)

        X, y, df_valid = predictor.load_and_prepare_data()

        print(f"✅ Datos cargados: {X.shape[0]} muestras, {X.shape[1]} features")
        print(f"📊 Distribución de clases:")
        class_dist = y.value_counts()
        for class_name, count in class_dist.items():
            print(f"   • {class_name}: {count} ({count/len(y)*100:.1f}%)")

        # PASO 3: Entrenar modelo
        print("\n" + "=" * 60)
        print("🎯 PASO 3: Entrenando modelo con MLflow")
        print("=" * 60)

        run_id, accuracy = predictor.train_model_with_mlflow(X, y)

        print(f"✅ Entrenamiento completado")
        print(f"🎯 Accuracy: {accuracy:.4f}")
        print(f"📋 MLflow Run ID: {run_id}")

        # PASO 4: Hacer predicciones
        print("\n" + "=" * 60)
        print("🔮 PASO 4: Generando predicciones con MLflow")
        print("=" * 60)

        df_results, pred_run_id = predictor.make_predictions_with_mlflow(run_id)

        print(f"✅ Predicciones completadas")
        print(f"📊 {len(df_results)} predicciones generadas")
        print(f"📋 Prediction Run ID: {pred_run_id}")

        # PASO 5: Mostrar resultados
        print("\n" + "=" * 60)
        print("📈 PASO 5: Resumen de resultados")
        print("=" * 60)

        pred_dist = df_results["predicted_error"].value_counts()
        print("📊 Distribución de predicciones:")
        for class_name, count in pred_dist.items():
            print(f"   • {class_name}: {count} ({count/len(df_results)*100:.1f}%)")

        confidence = df_results["prediction_confidence"]
        print(f"\n🎯 Estadísticas de confianza:")
        print(f"   • Promedio: {confidence.mean():.3f}")
        print(
            f"   • Alta confianza (>90%): {(confidence > 0.9).sum()} ({(confidence > 0.9).sum()/len(confidence)*100:.1f}%)"
        )

        # Archivos generados
        print(f"\n💾 Archivos generados:")
        print("   • predictions_results_mlflow.parquet")
        print("   • predictions_summary_mlflow.csv")
        print("   • Artefactos en MLflow (features, reportes, matriz confusión)")

        # URLs de MLflow
        print(f"\n🌐 MLflow URLs:")
        print(f"   • UI Principal: http://localhost:5000")
        print(f"   • Experimento: http://localhost:5000/#/experiments/1")
        print(f"   • Training Run: http://localhost:5000/#/experiments/1/runs/{run_id}")
        print(
            f"   • Prediction Run: http://localhost:5000/#/experiments/1/runs/{pred_run_id}"
        )

        print(f"\n🎉 ¡PIPELINE MLflow COMPLETADO EXITOSAMENTE!")

        return True

    except Exception as e:
        logger.error(f"❌ Error en pipeline MLflow: {e}")
        return False


def main():
    """Función principal"""

    success = run_complete_mlflow_pipeline()

    if success:
        print(f"\n✅ TUTORIAL MLflow COMPLETADO")
        print("🎯 Revisa la UI de MLflow en: http://localhost:5000")
        print("📊 Todos los experimentos y métricas están registrados")
    else:
        print(f"\n❌ TUTORIAL MLflow FALLÓ")
        print("🔍 Verifica que MLflow esté ejecutándose")
        print("💡 Comando: docker-compose up -d mlflow")


if __name__ == "__main__":
    main()
