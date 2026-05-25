#!/usr/bin/env python3
"""
Simple ML test to validate MLflow integration and tactical features
"""

import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os


def create_test_data():
    """Create sample chess data for testing"""
    np.random.seed(42)
    n_samples = 1000

    # Base features including tactical ones
    data = {
        "move_number": np.random.randint(1, 40, n_samples),
        "material_balance": np.random.normal(0, 200, n_samples),
        "material_total": np.random.normal(2000, 500, n_samples),
        "branching_factor": np.random.randint(5, 50, n_samples),
        "self_mobility": np.random.randint(0, 40, n_samples),
        "opponent_mobility": np.random.randint(0, 40, n_samples),
        "score_diff": np.random.normal(0, 100, n_samples),
        "num_pieces": np.random.randint(8, 32, n_samples),
        "white_elo": np.random.normal(1600, 300, n_samples),
        "black_elo": np.random.normal(1600, 300, n_samples),
        # TACTICAL FEATURES (las que probamos)
        "depth_score_diff": np.random.normal(0, 150, n_samples),
        "threatens_mate": np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        "is_forced_move": np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        # Target variable
        "error_label": np.random.choice(
            ["good", "inaccuracy", "mistake", "blunder"], n_samples
        ),
    }

    return pd.DataFrame(data)


def main():
    print("🚀 Simple ML Test with MLflow")
    print("=" * 50)

    # Set MLflow tracking URI to use SQLite for this test
    mlflow_dir = "/tmp/mlruns"
    os.makedirs(mlflow_dir, exist_ok=True)
    mlflow.set_tracking_uri(f"file://{mlflow_dir}")

    # Create or get experiment
    experiment_name = "Chess_Tactical_Features_Test"
    try:
        mlflow.create_experiment(experiment_name)
    except mlflow.exceptions.MlflowException:
        pass  # Experiment already exists

    mlflow.set_experiment(experiment_name)

    # Create test data
    df = create_test_data()
    print(f"📊 Created test data: {len(df)} rows, {len(df.columns)} columns")

    # Check tactical features
    tactical_features = ["depth_score_diff", "threatens_mate", "is_forced_move"]
    print(f"🎯 Tactical features: {[f for f in tactical_features if f in df.columns]}")

    # Prepare features and target
    feature_cols = [col for col in df.columns if col != "error_label"]
    X = df[feature_cols]
    y = df["error_label"]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"📈 Train: {len(X_train)}, Test: {len(X_test)}")

    # Start MLflow experiment
    with mlflow.start_run(run_name="Chess_Tactical_Test"):
        # Log parameters
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("n_features", len(feature_cols))
        mlflow.log_param("tactical_features", tactical_features)

        # Train model
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)

        # Make predictions
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("train_samples", len(X_train))
        mlflow.log_metric("test_samples", len(X_test))

        # Log model
        mlflow.sklearn.log_model(model, "chess_error_predictor")

        print("✅ Model trained successfully!")
        print(f"📊 Accuracy: {accuracy:.3f}")
        print(
            f"🎯 Features used: {len(feature_cols)} (including {len(tactical_features)} tactical)"
        )

        # Feature importance (focusing on tactical features)
        feature_importance = model.feature_importances_
        feature_names = feature_cols

        tactical_importance = {}
        for feature in tactical_features:
            if feature in feature_names:
                idx = feature_names.index(feature)
                tactical_importance[feature] = feature_importance[idx]

        print("\n🎯 Tactical Feature Importance:")
        for feature, importance in tactical_importance.items():
            print(f"   {feature}: {importance:.4f}")
            mlflow.log_metric(f"importance_{feature}", importance)

        # Log run info
        run = mlflow.active_run()
        print(f"\n📈 MLflow Run ID: {run.info.run_id}")
        print(f"📁 Artifact URI: {run.info.artifact_uri}")

    print("\n✅ MLflow test completed successfully!")
    print("🎯 Tactical features integration validated")


if __name__ == "__main__":
    main()
