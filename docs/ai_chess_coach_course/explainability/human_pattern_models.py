"""Human Pattern model training and comparison for Module 06."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

LABEL_ORDER = ("good", "inaccuracy", "mistake", "blunder")
DEFAULT_RANDOM_STATE = 42
LABEL_TO_INDEX = {label: index for index, label in enumerate(LABEL_ORDER)}


def encode_labels(y: pd.Series) -> np.ndarray:
    return y.map(LABEL_TO_INDEX).to_numpy()


def decode_labels(values: np.ndarray | list[int]) -> np.ndarray:
    return np.array([LABEL_ORDER[int(value)] for value in values])


@dataclass(frozen=True)
class ModelMetrics:
    model_name: str
    balanced_accuracy: float
    f1_macro: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "balanced_accuracy": self.balanced_accuracy,
            "f1_macro": self.f1_macro,
        }


def build_human_pattern_classifiers(
    *,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_estimators: int = 200,
) -> dict[str, Any]:
    return {
        "lightgbm": LGBMClassifier(
            objective="multiclass",
            num_class=len(LABEL_ORDER),
            class_weight="balanced",
            n_estimators=n_estimators,
            learning_rate=0.05,
            num_leaves=31,
            random_state=random_state,
            n_jobs=-1,
            verbose=-1,
        ),
        "xgboost": XGBClassifier(
            objective="multi:softprob",
            num_class=len(LABEL_ORDER),
            n_estimators=n_estimators,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="mlogloss",
            random_state=random_state,
            n_jobs=-1,
        ),
        "catboost": CatBoostClassifier(
            loss_function="MultiClass",
            iterations=n_estimators,
            learning_rate=0.05,
            depth=6,
            auto_class_weights="Balanced",
            random_state=random_state,
            verbose=0,
        ),
    }


def evaluate_human_pattern_model(
    model_name: str,
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
) -> ModelMetrics:
    predictions = model.predict(X)
    if np.issubdtype(np.asarray(predictions).dtype, np.number):
        predictions = decode_labels(np.asarray(predictions).astype(int))

    return ModelMetrics(
        model_name=model_name,
        balanced_accuracy=float(balanced_accuracy_score(y, predictions)),
        f1_macro=float(
            f1_score(
                y,
                predictions,
                average="macro",
                labels=list(LABEL_ORDER),
                zero_division=0,
            )
        ),
    )


def _fit_model(
    model_name: str,
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
) -> Any:
    y_encoded = encode_labels(y)
    if model_name == "xgboost":
        sample_weight = compute_sample_weight(class_weight="balanced", y=y_encoded)
        model.fit(X, y_encoded, sample_weight=sample_weight)
    else:
        model.fit(X, y)
    return model


def train_and_compare_human_pattern_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    *,
    random_state: int = DEFAULT_RANDOM_STATE,
    n_estimators: int = 200,
) -> tuple[dict[str, Any], pd.DataFrame, str]:
    fitted: dict[str, Any] = {}
    metrics_rows: list[dict[str, Any]] = []

    for model_name, model in build_human_pattern_classifiers(
        random_state=random_state,
        n_estimators=n_estimators,
    ).items():
        fitted_model = _fit_model(model_name, model, X_train, y_train)
        metrics = evaluate_human_pattern_model(model_name, fitted_model, X_val, y_val)
        fitted[model_name] = fitted_model
        metrics_rows.append(metrics.to_dict())

    comparison_df = pd.DataFrame(metrics_rows).set_index("model_name")
    selected_name = comparison_df.sort_values(
        ["f1_macro", "balanced_accuracy"],
        ascending=False,
    ).index[0]
    return fitted, comparison_df, selected_name


def save_human_pattern_artifacts(
    output_dir: str | Path,
    *,
    model: Any,
    model_name: str,
    feature_columns: list[str],
    comparison_df: pd.DataFrame,
) -> dict[str, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    paths = {
        "model": destination / "human_model.joblib",
        "comparison": destination / "model_comparison.json",
        "features": destination / "feature_columns.json",
        "labels": destination / "label_order.json",
        "selected": destination / "selected_model_name.txt",
    }
    joblib.dump(model, paths["model"])
    paths["comparison"].write_text(
        json.dumps(comparison_df.reset_index().to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )
    paths["features"].write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")
    paths["labels"].write_text(json.dumps(list(LABEL_ORDER), indent=2), encoding="utf-8")
    paths["selected"].write_text(model_name, encoding="utf-8")
    return paths


def load_human_pattern_model(model_path: str | Path) -> Any:
    return joblib.load(model_path)
