# Tasks: implement-course-modules-04

## 1. Notebook Implementation
- [ ] Create or update `04_ml_training.ipynb` as the canonical Module 04 artifact.
- [ ] Add a module introduction describing the goal: compare baselines for `error_level` prediction and confirm XGBoost as the expected champion.

## 2. Data Preparation
- [ ] Load the dataset produced by previous modules using the course pipeline conventions.
- [ ] Apply a consistent `train/validation/test` split and document the split ratios and random seed.
- [ ] Build a preprocessing pipeline that includes scaling and encoding as needed for all models.

## 3. Baseline Training
- [ ] Train a multiclass `LogisticRegression` baseline inside an `sklearn.pipeline`.
- [ ] Train a multiclass `KNN` baseline inside an `sklearn.pipeline`.
- [ ] Train a multiclass `RandomForestClassifier` baseline inside an `sklearn.pipeline`.
- [ ] Train a multiclass `LightGBM` baseline inside an `sklearn.pipeline`.
- [ ] Train a multiclass `XGBoost` baseline inside an `sklearn.pipeline`.
- [ ] Train a multiclass `CatBoost` baseline inside an `sklearn.pipeline`.
- [ ] Implement imbalance handling for `error_level`, using class weights and/or resampling techniques such as SMOTE from `imbalanced-learn`.
- [ ] Evaluate whether SMOTE or weight balancing improves recall and precision for the rare `blunder` class.

## 4. Hyperparameter Optimization
- [ ] Define search spaces for each model, including at least one relevant parameter per estimator.
- [ ] Run `GridSearchCV` for one or more baseline models with small, representative grids.
- [ ] Run `RandomizedSearchCV` for one or more additional baseline models to compare tuning strategies.
- [ ] Capture the best parameters and validation scores for each tuned model.
- [ ] Include imbalance-specific hyperparameters such as `class_weight`, `scale_pos_weight`, or SMOTE sampling ratios when appropriate.

## 5. Metrics and Comparison
- [ ] Calculate and report AUC, ROC, Precision, and F1 for all baselines.
- [ ] Generate learning curves for selected models to show training vs validation behavior.
- [ ] Create a metrics comparison table that ranks models by the chosen primary metric.
- [ ] Highlight `XGBoost` as the selected baseline if it outperforms the references and other tree models.

## 6. Documentation and Validation
- [ ] Verify top-to-bottom notebook execution in the target environment.
- [ ] Add a conclusions section that summarizes the best baseline and the practical lesson from the comparison.
- [ ] Document assumptions, model limitations, and any dataset constraints.
