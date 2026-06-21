# Design: implement-course-modules-04

## Design Goals
- Keep Module 04 focused and independently deliverable.
- Preserve compatibility with previous modules.
- Ensure outputs are reproducible in the course environment.

## Canonical Artifact
- Notebook: 04_ml_training.ipynb

## Module Objective
- Train baseline classifiers and compare metrics, using simple models as reference and tree boosting as the expected champion.

## Required Deliverables
- Train and compare Multi class LogisticRegression, KNN, RandomForest, LightGBM, XGBoost, and CatBoost baselines using sklearn pipelines.
- Use LogisticRegression and KNN as reference baselines, with XGBoost expected as the winning model for `error_level` prediction.
- Generate metrics: AUC, ROC, PR AUC, Balanced Accuracy, Learning Curves, Precision and F1.
- Use a consistent train/validation/test split.
- Apply imbalance handling strategies for `error_level`, such as class weights, resampling, or `imbalanced-learn` techniques like SMOTE.
- Evaluate hyperparameters using GridSearchCV and RandomizedSearchCV within sklearn pipelines.
- Publish a metrics comparison table and selected baseline.

## Dependencies
- Outputs from completed previous modules.
