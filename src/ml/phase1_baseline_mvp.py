#!/usr/bin/env python3
"""
Phase 1 Baseline MVP - Machine Learning Pipeline
Baseline models for chess error classification using currently available labeled data.

This script implements the baseline models required by the roadmap:
- Logistic Regression L2 (primary baseline)
- Logistic Regression L1 (feature selection)
- Random Forest (comparison)

Usage:
    python src/ml/phase1_baseline_mvp.py --experiment-name "phase1_mvp"
"""

import os
import sys
import argparse
import warnings
import logging
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    f1_score,
    accuracy_score,
    precision_recall_fscore_support
)
from sqlalchemy import create_engine, text
import joblib
import mlflow
import mlflow.sklearn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore')

class Phase1BaselineMVP:
    """Phase 1 Baseline MVP for chess error classification"""
    
    def __init__(self, db_connection_string=None):
        self.db_connection_string = db_connection_string or os.getenv(
            'DATABASE_URL', 
            'postgresql://chess:chess_pass@localhost:5432/chess_trainer_db'
        )
        self.engine = create_engine(self.db_connection_string)
        self.feature_cols = []
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        
    def load_data(self):
        """Load labeled features from database"""
        query = """
        SELECT 
            -- Solo columnas básicas garantizadas
            material_balance,
            score_diff,
            player_color,
            move_number,
            
            -- Características tácticas basadas en tags (convertir JSON a texto)
            CASE WHEN tags::text LIKE '%discovered_attack%' THEN 1 ELSE 0 END as has_discovered_attack,
            CASE WHEN tags::text LIKE '%fork%' THEN 1 ELSE 0 END as has_fork,
            CASE WHEN tags::text LIKE '%pin%' THEN 1 ELSE 0 END as has_pin,
            CASE WHEN tags::text LIKE '%skewer%' THEN 1 ELSE 0 END as has_skewer,
            CASE WHEN tags::text LIKE '%check%' THEN 1 ELSE 0 END as has_check,
            
            -- Target
            error_label
            
        FROM features 
        WHERE error_label IS NOT NULL 
        AND error_label != ''
        ORDER BY RANDOM()
        """
        
        logger.info("Loading labeled data from database...")
        
        # Use text() to wrap the query for SQLAlchemy
        with self.engine.connect() as connection:
            df = pd.read_sql(text(query), connection)
        
        logger.info(f"Loaded {len(df)} labeled samples")
        
        # Handle missing values
        df = df.fillna(0)
        
        return df
    
    def prepare_features(self, df):
        """Prepare features and target variables"""
        
        # Define feature columns (exclude target)
        self.feature_cols = [col for col in df.columns if col != 'error_label']
        
        X = df[self.feature_cols]
        y = df['error_label']
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=self.feature_cols)
        
        logger.info(f"Feature shape: {X_scaled.shape}")
        logger.info(f"Label distribution:")
        for label, count in zip(*np.unique(y, return_counts=True)):
            logger.info(f"  {label}: {count} ({count/len(y)*100:.1f}%)")
        
        return X_scaled, y_encoded, y
    
    def train_models(self, X, y, experiment_name="phase1_baseline_mvp"):
        """Train baseline models as specified in roadmap"""
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Cross-validation setup
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        models = {
            'logistic_l2': LogisticRegression(
                penalty='l2', 
                C=1.0, 
                random_state=42, 
                max_iter=1000,
                multi_class='multinomial',
                solver='lbfgs'
            ),
            'logistic_l1': LogisticRegression(
                penalty='l1', 
                C=1.0, 
                random_state=42, 
                max_iter=1000,
                solver='liblinear'
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2
            )
        }
        
        results = {}
        
        # Start MLflow experiment
        mlflow.set_experiment(experiment_name)
        
        for model_name, model in models.items():
            
            with mlflow.start_run(run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"):
                
                logger.info(f"\n=== Training {model_name} ===")
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1_macro')
                
                # Train final model
                model.fit(X_train, y_train)
                
                # Predictions
                y_pred = model.predict(X_test)
                
                # Metrics
                f1_macro = f1_score(y_test, y_pred, average='macro')
                f1_micro = f1_score(y_test, y_pred, average='micro')
                accuracy = accuracy_score(y_test, y_pred)
                
                # Confusion matrix
                cm = confusion_matrix(y_test, y_pred)
                
                # Classification report
                report = classification_report(
                    y_test, y_pred, 
                    target_names=self.label_encoder.classes_,
                    output_dict=True
                )
                
                # Calculate critical confusion (good <-> blunder)
                label_names = self.label_encoder.classes_
                try:
                    good_idx = list(label_names).index('good')
                    blunder_idx = list(label_names).index('blunder')
                    critical_confusion = cm[good_idx, blunder_idx] + cm[blunder_idx, good_idx]
                    critical_confusion_pct = critical_confusion / len(y_test) * 100
                except ValueError:
                    critical_confusion_pct = 0
                
                # Log parameters
                if hasattr(model, 'get_params'):
                    mlflow.log_params(model.get_params())
                
                # Log metrics
                mlflow.log_metrics({
                    'f1_macro': f1_macro,
                    'f1_micro': f1_micro,
                    'accuracy': accuracy,
                    'cv_f1_mean': cv_scores.mean(),
                    'cv_f1_std': cv_scores.std(),
                    'critical_confusion_pct': critical_confusion_pct,
                    'train_samples': len(X_train),
                    'test_samples': len(X_test)
                })
                
                # Log model
                mlflow.sklearn.log_model(
                    model, 
                    f"model_{model_name}",
                    registered_model_name=f"phase1_{model_name}"
                )
                
                # Log artifacts
                # Confusion matrix
                cm_df = pd.DataFrame(
                    cm, 
                    index=label_names, 
                    columns=label_names
                )
                cm_df.to_csv(f"confusion_matrix_{model_name}.csv")
                mlflow.log_artifact(f"confusion_matrix_{model_name}.csv")
                
                # Classification report
                report_df = pd.DataFrame(report).transpose()
                report_df.to_csv(f"classification_report_{model_name}.csv")
                mlflow.log_artifact(f"classification_report_{model_name}.csv")
                
                results[model_name] = {
                    'model': model,
                    'f1_macro': f1_macro,
                    'accuracy': accuracy,
                    'cv_scores': cv_scores,
                    'confusion_matrix': cm,
                    'classification_report': report,
                    'critical_confusion_pct': critical_confusion_pct
                }
                
                logger.info(f"F1 Macro: {f1_macro:.3f}")
                logger.info(f"Accuracy: {accuracy:.3f}")
                logger.info(f"CV F1 Mean ± Std: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
                logger.info(f"Critical confusion (good↔blunder): {critical_confusion_pct:.1f}%")
        
        return results
    
    def evaluate_models(self, results):
        """Evaluate models against roadmap criteria"""
        
        logger.info("\n=== MODEL EVALUATION SUMMARY ===")
        
        best_model = None
        best_f1 = 0
        
        for model_name, result in results.items():
            f1_macro = result['f1_macro']
            critical_confusion = result['critical_confusion_pct']
            
            logger.info(f"\n{model_name.upper()}:")
            logger.info(f"  F1 Macro: {f1_macro:.3f}")
            logger.info(f"  Critical Confusion: {critical_confusion:.1f}%")
            
            # Roadmap criteria
            criteria_met = []
            if f1_macro >= 0.70:
                criteria_met.append("✅ F1 macro ≥ 0.70")
            else:
                criteria_met.append(f"❌ F1 macro < 0.70 ({f1_macro:.3f})")
            
            if critical_confusion < 5.0:
                criteria_met.append("✅ Critical confusion < 5%")
            else:
                criteria_met.append(f"❌ Critical confusion ≥ 5% ({critical_confusion:.1f}%)")
            
            for criterion in criteria_met:
                logger.info(f"  {criterion}")
            
            if f1_macro > best_f1:
                best_f1 = f1_macro
                best_model = model_name
        
        logger.info(f"\n🏆 BEST MODEL: {best_model} (F1 Macro: {best_f1:.3f})")
        
        # Check if ready for Phase 2
        best_result = results[best_model]
        phase2_ready = (
            best_result['f1_macro'] >= 0.70 and 
            best_result['critical_confusion_pct'] < 5.0
        )
        
        if phase2_ready:
            logger.info("🎯 PHASE 1 COMPLETE - Ready to advance to Phase 2!")
        else:
            logger.info("⚠️  PHASE 1 needs improvement before advancing to Phase 2")
        
        return best_model, phase2_ready
    
    def save_artifacts(self, results, best_model):
        """Save model artifacts"""
        
        # Create artifacts directory
        artifacts_dir = Path("artifacts/phase1_baseline_mvp")
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Save best model
        best_model_obj = results[best_model]['model']
        joblib.dump(best_model_obj, artifacts_dir / f"best_model_{best_model}.pkl")
        joblib.dump(self.scaler, artifacts_dir / "scaler.pkl")
        joblib.dump(self.label_encoder, artifacts_dir / "label_encoder.pkl")
        
        # Save feature names
        with open(artifacts_dir / "feature_names.txt", 'w') as f:
            for feature in self.feature_cols:
                f.write(f"{feature}\n")
        
        logger.info(f"Artifacts saved to {artifacts_dir}")

def main():
    parser = argparse.ArgumentParser(description='Phase 1 Baseline MVP')
    parser.add_argument('--experiment-name', default='phase1_baseline_mvp', 
                       help='MLflow experiment name')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = Phase1BaselineMVP()
    
    try:
        # Load and prepare data
        df = pipeline.load_data()
        X, y_encoded, y_original = pipeline.prepare_features(df)
        
        # Train models
        results = pipeline.train_models(X, y_encoded, args.experiment_name)
        
        # Evaluate results
        best_model, phase2_ready = pipeline.evaluate_models(results)
        
        # Save artifacts
        pipeline.save_artifacts(results, best_model)
        
        logger.info("✅ Phase 1 Baseline MVP completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in Phase 1 Baseline MVP: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()