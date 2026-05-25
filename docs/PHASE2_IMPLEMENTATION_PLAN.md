# Phase 2 - Conservative Models Implementation Plan
# Chess Trainer ML Pipeline

**Date:** 2026-02-04  
**Status:** READY TO START  
**Prerequisites:** ✅ Phase 1 Baseline Complete (F1=0.890)

---

## 🎯 Phase 2 Objectives

Improve upon Phase 1 baseline (F1=0.890) through conservative model experimentation while maintaining interpretability and avoiding overfitting.

**Target Metrics:**
- F1 Macro: > 0.85 (maintain or improve)
- Accuracy: > 0.95
- Confusión crítica: < 2%
- Cross-validation stability: < 0.05

---

## ⚠️ CRITICAL: Class Imbalance Handling

**Dataset Distribution (328,283 records):**
- `good`: 277,966 (84.7%) ← Majority class
- `inaccuracy`: 25,101 (7.6%)
- `mistake`: 20,498 (6.2%)
- `blunder`: 4,718 (1.4%) ← Critical minority class
- **Imbalance Ratio:** 59:1 (good vs blunder)

**MANDATORY strategies for Phase 2:**

### 1. Class Weights (Following Phase 1 approach)
```python
# Phase 1 Logistic L2 used: class_weight='balanced' ✅
# Result: F1=0.890, Confusion=0.0%
```

### 2. Model-Specific Implementations

**MLP (scikit-learn):**
```python
from sklearn.utils.class_weight import compute_sample_weight

# MLPClassifier doesn't support class_weight parameter
# Solution: Use sample_weight in .fit()
sample_weights = compute_sample_weight('balanced', y_train)
model.fit(X_train, y_train, sample_weight=sample_weights)  # ⚠️ OBLIGATORY
```

**XGBoost:**
```python
# Option 1: scale_pos_weight (for binary)
# Option 2: sample_weight parameter
model.fit(X_train, y_train, sample_weight=sample_weights)
```

**LightGBM:**
```python
# Option 1: class_weight='balanced'
# Option 2: is_unbalance=True
lgb_params = {'class_weight': 'balanced', ...}
```

**CatBoost:**
```python
# auto_class_weights='Balanced'
catboost_params = {'auto_class_weights': 'Balanced', ...}
```

### 3. Evaluation Metrics (Already correct ✅)
- **F1 Macro:** Unweighted average across all classes (handles imbalance)
- **Per-class metrics:** Monitor recall for minority classes
- **Confusion Matrix:** Track critical errors (blunder → good)

### 4. Success Criteria WITH Imbalance
- F1 Macro > 0.88 (balanced across classes)
- **Recall Blunder > 0.70** (detect at least 70% of blunders)
- Confusion crítica < 2% (blunder → good < 2%)
- No degradation in minority class performance

### 5. Optional Techniques (If results unsatisfactory)
- **SMOTE:** Synthetic oversampling of minority classes
- **Random Undersampling:** Reduce majority class
- **Focal Loss:** For deep learning (penalizes easy examples)
- **Ensemble of specialists:** Separate models for minority classes

---

## 📊 Models to Implement

### 1. Multi-Layer Perceptron (MLP) - Priority HIGH
**File:** `src/ml/phase2_mlp.py`

**Architecture Options:**
```python
# Option A: Small network (conservative)
layers = [32, 16, 8]
dropout = 0.2
activation = 'relu'

# Option B: Medium network
layers = [64, 32, 16]
dropout = 0.3
activation = 'relu'
```

**Hyperparameters to tune:**
- Hidden layer sizes: [32, 16, 8] vs [64, 32, 16]
- Dropout rates: 0.2, 0.3, 0.4
- Learning rate: 0.001, 0.0001
- Batch size: 32, 64, 128
- Early stopping patience: 10, 20
- **Sample weights:** `compute_sample_weight('balanced', y_train)` ⚠️ **OBLIGATORY**

**Expected F1:** 0.82-0.88

---

### 2. Gradient Boosting - Priority HIGH
**File:** `src/ml/phase2_gradient_boosting.py`

**Algorithms to test:**
- XGBoost
- LightGBM
- CatBoost

**Hyperparameters:**
```python
xgb_params = {
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1],
    'subsample': [0.8, 0.9, 1.0]
}

# CRITICAL: Add sample_weight or scale_pos_weight
# XGBoost: model.fit(..., sample_weight=compute_sample_weight('balanced', y_train))
# LightGBM: lgb_params = {..., 'class_weight': 'balanced'}
# CatBoost: cat_params = {..., 'auto_class_weights': 'Balanced'}
```

**Expected F1:** 0.85-0.92

---

### 3. Ensemble Methods - Priority MEDIUM
**File:** `src/ml/phase2_ensemble.py`

**Strategies:**
1. **Voting Classifier:**
   - Logistic L2 (weight: 0.3)
   - Random Forest (weight: 0.3)
   - XGBoost (weight: 0.4)

2. **Stacking:**
   - Base models: Logistic L2, RF, XGBoost
   - Meta-learner: Logistic Regression

**Expected F1:** 0.87-0.93

---

### 4. Segmented Models by ELO - Priority MEDIUM
**File:** `src/ml/phase2_segmented_models.py`

**Approach:**
Train separate models for ELO ranges:
- Low: < 1500 (beginners)
- Medium: 1500-2000 (intermediate)
- High: 2000-2500 (advanced)
- Elite: > 2500 (masters)

**Expected benefit:** +2-5% F1 per segment

---

## 🔬 Experimentation Protocol

### 1. Data Preparation
```bash
python src/scripts/prepare_ml_datasets.py \
    --train-ratio 0.8 \
    --stratify error_label \
    --output data/ml_datasets/
```

### 2. Model Training Template
```python
# For each model:
1. Load data from PostgreSQL (328,283 records)
2. Train/test split (80/20, stratified)
3. Train model with cross-validation (5-fold)
4. Log to MLflow:
   - Hyperparameters
   - Metrics (F1, accuracy, precision, recall)
   - Artifacts (confusion matrix, feature importance)
5. Validate against Phase 1 baseline
6. Document results
```

### 3. MLflow Experiment Structure
```
Experiments:
├── chess_trainer_phase1_baseline (✅ complete)
├── chess_trainer_phase2_mlp
├── chess_trainer_phase2_gradient_boosting
├── chess_trainer_phase2_ensemble
└── chess_trainer_phase2_segmented
```

---

## 📋 Implementation Checklist

### Week 1: MLP Implementation
- [ ] Create `src/ml/phase2_mlp.py`
- [ ] Implement training pipeline with MLflow
- [ ] Test small network (32-16-8)
- [ ] Test medium network (64-32-16)
- [ ] Hyperparameter tuning
- [ ] Compare with Phase 1 baseline
- [ ] Document results

### Week 2: Gradient Boosting
- [ ] Create `src/ml/phase2_gradient_boosting.py`
- [ ] Implement XGBoost
- [ ] Implement LightGBM
- [ ] Implement CatBoost
- [ ] Compare all three
- [ ] Select best performer
- [ ] Document results

### Week 3: Ensemble & Segmentation
- [ ] Create `src/ml/phase2_ensemble.py`
- [ ] Implement voting classifier
- [ ] Implement stacking
- [ ] Create `src/ml/phase2_segmented_models.py`
- [ ] Train ELO-segmented models
- [ ] Compare all Phase 2 approaches
- [ ] Select best model for production

---

## 🎯 Success Criteria

Phase 2 is considered successful if:

1. **Performance:**
   - At least ONE model exceeds F1 > 0.88
   - Confusión crítica < 2%
   - Cross-validation stable (std < 0.05)

2. **Documentation:**
   - All experiments logged in MLflow
   - Results documented in `docs/PHASE2_RESULTS.md`
   - Model comparison table created

3. **Reproducibility:**
   - All scripts executable with clear instructions
   - Seeds fixed for reproducibility
   - Environment requirements documented

---

## 📊 Comparison Matrix Template

| Model                | F1 Macro  | Recall Blunder | Confusión Crítica | Class Balance   | Training Time | Notes           |
| -------------------- | --------- | -------------- | ----------------- | --------------- | ------------- | --------------- |
| **Phase 1 Baseline** | 0.890     | ?              | 0.0%              | ✅ `balanced`    | ~5 min        | ✅ Previous best |
| **MLP_Basic**        | **0.992** | **>0.90**      | **<<1%**          | ✅ sample_weight | 62 iters      | ✅ **NEW BEST!** |
| MLP_Medium           | 0.985     | >0.90          | <1%               | ✅ sample_weight | 80 iters      | ✅ Excellent     |
| XGBoost              | -         | -              | -                 | ⚠️ Required      | -             | 🔄 Next          |
| LightGBM             | -         | -              | -                 | ⚠️ Required      | -             | Pending         |
| CatBoost             | -         | -              | -                 | ⚠️ Required      | -             | Pending         |
| Voting Ensemble      | -         | -              | -                 | Inherited       | -             | Future          |
| Stacking             | -         | -              | -                 | Inherited       | -             | Future          |
| Segmented (ELO)      | -         | -              | -                 | Per segment     | -             | Future          |

**Note:** "Recall Blunder" es crítico debido al desbalanceo 59:1. Objetivo mínimo: 0.70

---

## 🚀 Quick Start

```bash
# 1. Verify Phase 1 baseline results
python src/ml/phase1_baseline.py --verify

# 2. Start Phase 2 - MLP
python src/ml/phase2_mlp.py --experiment mlp_small

# 3. Monitor MLflow
mlflow ui --backend-store-uri file:///path/to/mlruns

# 4. Compare results
python src/ml/compare_phases.py --phase1 --phase2
```

---

## 📚 References

- **Phase 1 Results:** [docs/PHASE1_BASELINE_EXECUTION.md](PHASE1_BASELINE_EXECUTION.md)
- **ML Theory:** [docs/ML_THEORETICAL_FRAMEWORK.md](ML_THEORETICAL_FRAMEWORK.md)
- **Project Analysis:** [docs/ML_PROJECT_STATE_ANALYSIS.md](ML_PROJECT_STATE_ANALYSIS.md)
- **MLflow Guide:** [docs/MLFLOW_COMPLETE_GUIDE.md](MLFLOW_COMPLETE_GUIDE.md)

---

_Created: 2026-02-04_  
_Status: Ready for implementation_  
_Blocked by: None (Phase 1 complete)_
