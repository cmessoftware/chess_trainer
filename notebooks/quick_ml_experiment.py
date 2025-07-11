#!/usr/bin/env python3
"""
Quick ML experiment with MLflow tracking for chess_trainer
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import mlflow
import mlflow.sklearn
from datetime import datetime

print("🚀 CHESS TRAINER - Quick ML Experiment")
print("=" * 50)

# Set MLflow tracking URI to connect to our MLflow server
mlflow.set_tracking_uri("http://mlflow:5000")

# Create experiment
experiment_name = f"chess_error_prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
try:
    experiment_id = mlflow.create_experiment(experiment_name)
    print(f"✅ Created experiment: {experiment_name}")
except:
    experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
    print(f"✅ Using existing experiment: {experiment_name}")

mlflow.set_experiment(experiment_name)

# Generate synthetic chess data for demonstration
print("\n📊 Generating synthetic chess data...")
np.random.seed(42)

n_samples = 1000
data = {
    'score_diff': np.random.normal(0, 50, n_samples),
    'material_balance': np.random.normal(0, 3, n_samples),
    'branching_factor': np.random.uniform(2, 35, n_samples),
    'self_mobility': np.random.uniform(0, 30, n_samples),
    'opponent_mobility': np.random.uniform(0, 30, n_samples),
    'num_pieces': np.random.randint(4, 32, n_samples),
    'move_number': np.random.randint(1, 80, n_samples)
}

# Create target variable (error types)
# Simulate different types of chess errors
error_probability = 1 / (1 + np.exp(-data['score_diff'] / 100))  # Sigmoid based on score
data['error_label'] = np.random.choice(
    ['no_error', 'blunder', 'mistake', 'inaccuracy'], 
    n_samples, 
    p=[0.6, 0.1, 0.15, 0.15]
)

df = pd.DataFrame(data)
print(f"✅ Generated {len(df)} samples with {len(df.columns)} features")
print(f"📈 Error distribution:")
print(df['error_label'].value_counts())

# Prepare features and target
feature_columns = ['score_diff', 'material_balance', 'branching_factor', 
                  'self_mobility', 'opponent_mobility', 'num_pieces', 'move_number']
X = df[feature_columns]
y = df['error_label']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n🔧 Training set: {len(X_train)} samples")
print(f"🔧 Test set: {len(X_test)} samples")

# Start MLflow run
with mlflow.start_run():
    print("\n🤖 Training Random Forest model...")
    
    # Log parameters
    n_estimators = 100
    max_depth = 10
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("features", feature_columns)
    mlflow.log_param("n_samples", len(df))
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    
    # Log metrics
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("train_samples", len(X_train))
    mlflow.log_metric("test_samples", len(X_test))
    
    # Log model
    mlflow.sklearn.log_model(model, "chess_error_model")
    
    # Log feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n📊 Model Performance:")
    print(f"   Accuracy: {accuracy:.3f}")
    print(f"\n🎯 Feature Importance:")
    for _, row in feature_importance.iterrows():
        print(f"   {row['feature']}: {row['importance']:.3f}")
    
    # Save detailed classification report
    class_report = classification_report(y_test, y_pred)
    print(f"\n📋 Classification Report:")
    print(class_report)
    
    # Log additional info
    mlflow.log_text(class_report, "classification_report.txt")
    mlflow.log_text(str(feature_importance.to_dict()), "feature_importance.txt")
    
    run_id = mlflow.active_run().info.run_id
    print(f"\n✅ MLflow run completed: {run_id}")
    print(f"🌐 View results at: http://localhost:5000")

print("\n🎉 ML Experiment completed successfully!")
print("🔗 Check MLflow UI for detailed results and model artifacts")
