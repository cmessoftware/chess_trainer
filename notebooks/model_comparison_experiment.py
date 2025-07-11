#!/usr/bin/env python3
"""
Second ML experiment with different hyperparameters for comparison
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import mlflow
import mlflow.sklearn
from datetime import datetime

print("🚀 CHESS TRAINER - Hyperparameter Comparison Experiment")
print("=" * 60)

# Set MLflow tracking URI
mlflow.set_tracking_uri("http://mlflow:5000")

# Set experiment
experiment_name = "chess_model_comparison"
try:
    experiment_id = mlflow.create_experiment(experiment_name)
    print(f"✅ Created experiment: {experiment_name}")
except Exception:
    experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
    print(f"✅ Using existing experiment: {experiment_name}")

mlflow.set_experiment(experiment_name)

# Generate more sophisticated synthetic data
print("\n📊 Generating enhanced synthetic chess data...")
np.random.seed(123)  # Different seed for variety

n_samples = 2000  # More samples
data = {
    'score_diff': np.random.normal(0, 75, n_samples),
    'material_balance': np.random.normal(0, 4, n_samples),
    'branching_factor': np.random.uniform(1, 40, n_samples),
    'self_mobility': np.random.uniform(0, 35, n_samples),
    'opponent_mobility': np.random.uniform(0, 35, n_samples),
    'num_pieces': np.random.randint(2, 32, n_samples),
    'move_number': np.random.randint(1, 100, n_samples),
    'time_left': np.random.uniform(0, 300, n_samples),  # New feature
    'is_endgame': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])  # New feature
}

# More realistic error distribution based on multiple factors
score_factor = 1 / (1 + np.exp(-data['score_diff'] / 100))
time_pressure = np.where(np.array(data['time_left']) < 30, 0.3, 0.1)
endgame_factor = np.where(np.array(data['is_endgame']) == 1, 0.2, 0.1)

# Combine factors for more realistic error probability
error_prob = score_factor * 0.4 + time_pressure + endgame_factor

data['error_label'] = np.where(
    error_prob > 0.6, 'blunder',
    np.where(error_prob > 0.4, 'mistake',
             np.where(error_prob > 0.25, 'inaccuracy', 'no_error'))
)

df = pd.DataFrame(data)
print(f"✅ Generated {len(df)} samples with {len(df.columns)} features")
print("📈 Error distribution:")
print(df['error_label'].value_counts())

# Prepare features
feature_columns = ['score_diff', 'material_balance', 'branching_factor', 
                  'self_mobility', 'opponent_mobility', 'num_pieces', 
                  'move_number', 'time_left', 'is_endgame']
X = df[feature_columns]
y = df['error_label']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n🔧 Training set: {len(X_train)} samples")
print(f"🔧 Test set: {len(X_test)} samples")

# Experiment 1: Random Forest with different parameters
experiments = [
    {
        'name': 'RandomForest_v1',
        'model': RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42),
        'params': {'n_estimators': 50, 'max_depth': 5, 'model_type': 'RandomForest'}
    },
    {
        'name': 'RandomForest_v2',
        'model': RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42),
        'params': {'n_estimators': 200, 'max_depth': 15, 'model_type': 'RandomForest'}
    },
    {
        'name': 'LogisticRegression',
        'model': LogisticRegression(random_state=42, max_iter=1000),
        'params': {'model_type': 'LogisticRegression', 'max_iter': 1000},
        'use_scaling': True
    }
]

for exp in experiments:
    print(f"\n🤖 Training {exp['name']}...")
    
    with mlflow.start_run(run_name=exp['name']):
        # Log parameters
        for key, value in exp['params'].items():
            mlflow.log_param(key, value)
        mlflow.log_param("features", feature_columns)
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        
        # Prepare data (scaling if needed)
        X_train_processed = X_train.copy()
        X_test_processed = X_test.copy()
        
        if exp.get('use_scaling', False):
            scaler = StandardScaler()
            X_train_processed = scaler.fit_transform(X_train)
            X_test_processed = scaler.transform(X_test)
            mlflow.log_param("scaling", "StandardScaler")
        else:
            mlflow.log_param("scaling", "None")
        
        # Train model
        model = exp['model']
        model.fit(X_train_processed, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test_processed)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        
        # Log metrics
        mlflow.log_metric("accuracy", accuracy)
        
        # Calculate per-class metrics
        classes = ['no_error', 'inaccuracy', 'mistake', 'blunder']
        for cls in classes:
            class_mask = y_test == cls
            if class_mask.sum() > 0:
                class_acc = accuracy_score(y_test[class_mask], y_pred[class_mask])
                mlflow.log_metric(f"accuracy_{cls}", class_acc)
        
        # Log model
        mlflow.sklearn.log_model(model, f"chess_model_{exp['name']}")
        
        # Feature importance (if available)
        if hasattr(model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': feature_columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"🎯 Feature Importance for {exp['name']}:")
            for _, row in feature_importance.head(5).iterrows():
                print(f"   {row['feature']}: {row['importance']:.3f}")
            
            # Log top features as metrics
            for i, (_, row) in enumerate(feature_importance.head(3).iterrows()):
                mlflow.log_metric(f"top_feature_{i+1}_importance", row['importance'])
                mlflow.log_param(f"top_feature_{i+1}_name", row['feature'])
        
        # Classification report
        class_report = classification_report(y_test, y_pred)
        mlflow.log_text(class_report, f"classification_report_{exp['name']}.txt")
        
        print(f"📊 {exp['name']} Accuracy: {accuracy:.3f}")
        
        run_id = mlflow.active_run().info.run_id
        print(f"✅ MLflow run completed: {run_id}")

print("\n🎉 Model Comparison Experiment completed!")
print("🔗 Compare models in MLflow UI at: http://localhost:5000")
print("📊 Check the experiments tab to compare metrics across different models")
