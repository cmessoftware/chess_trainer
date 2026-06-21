"""SHAP analysis helpers for the Human Pattern model (Module 06)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap

from explainability.human_pattern_models import LABEL_ORDER

OPENING_PREFIX = "opening_"
TIME_CONTROL_PREFIX = "time_control_bucket_"
PHASE_PREFIX = "phase_"


def sample_rows_by_game_id(
    frame: pd.DataFrame,
    *,
    game_id_column: str = "game_id",
    max_rows: int = 5000,
    random_state: int = 42,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    if len(frame) <= max_rows:
        return frame.copy().reset_index(drop=True)

    games = frame[game_id_column].drop_duplicates().sample(frac=1.0, random_state=random_state)
    sampled_rows: list[pd.DataFrame] = []
    rows_collected = 0
    for game_id in games:
        game_rows = frame[frame[game_id_column] == game_id]
        sampled_rows.append(game_rows)
        rows_collected += len(game_rows)
        if rows_collected >= max_rows:
            break

    sample = pd.concat(sampled_rows, ignore_index=True)
    return sample.iloc[:max_rows].reset_index(drop=True)


def grouped_feature_name(feature_name: str) -> str:
    if feature_name.startswith(OPENING_PREFIX):
        return "opening (grouped)"
    if feature_name.startswith(TIME_CONTROL_PREFIX):
        return "time_control_bucket (grouped)"
    if feature_name.startswith(PHASE_PREFIX):
        return "phase (grouped)"
    return feature_name


def aggregate_mean_abs_shap(
    feature_names: list[str],
    mean_abs_values: np.ndarray,
) -> pd.DataFrame:
    grouped: dict[str, float] = {}
    for feature_name, value in zip(feature_names, mean_abs_values, strict=True):
        group_name = grouped_feature_name(feature_name)
        grouped[group_name] = grouped.get(group_name, 0.0) + float(value)

    importance = (
        pd.DataFrame(
            {"feature": list(grouped.keys()), "mean_abs_shap": list(grouped.values())}
        )
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    return importance


def _predicted_class_index(model: Any, row: pd.DataFrame) -> int:
    probabilities = model.predict_proba(row)
    return int(np.argmax(probabilities, axis=1)[0])


def _multiclass_shap_tensor(explainer: shap.TreeExplainer, X: pd.DataFrame) -> np.ndarray:
    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        return np.stack(shap_values, axis=-1)
    if getattr(shap_values, "values", None) is not None:
        values = shap_values.values
        if values.ndim == 3:
            return values
    array = np.asarray(shap_values)
    if array.ndim == 2:
        return array[..., np.newaxis]
    return array


def compute_global_shap_importance(
    model: Any,
    X_sample: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, shap.TreeExplainer, np.ndarray]:
    explainer = shap.TreeExplainer(model)
    shap_tensor = _multiclass_shap_tensor(explainer, X_sample)
    mean_abs = np.mean(np.abs(shap_tensor), axis=(0, 2))

    raw_importance = (
        pd.DataFrame({"feature": list(X_sample.columns), "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    grouped_importance = aggregate_mean_abs_shap(list(X_sample.columns), mean_abs)
    return raw_importance, grouped_importance, explainer, shap_tensor


def compute_class_shap_importance(
    shap_tensor: np.ndarray,
    feature_names: list[str],
    *,
    class_labels: tuple[str, ...] = LABEL_ORDER,
) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    for class_index, class_label in enumerate(class_labels):
        class_values = np.mean(np.abs(shap_tensor[:, :, class_index]), axis=0)
        raw = (
            pd.DataFrame({"feature": feature_names, "mean_abs_shap": class_values})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True)
        )
        grouped = aggregate_mean_abs_shap(feature_names, class_values)
        results[class_label] = grouped if not grouped.empty else raw
    return results


def explain_prediction(
    model: Any,
    explainer: shap.TreeExplainer,
    row: pd.DataFrame,
    *,
    class_labels: tuple[str, ...] = LABEL_ORDER,
    top_k: int = 5,
) -> dict[str, Any]:
    if len(row) != 1:
        raise ValueError("explain_prediction expects a single-row dataframe")

    probabilities = model.predict_proba(row)[0]
    predicted_index = int(np.argmax(probabilities))
    predicted_label = class_labels[predicted_index]

    shap_tensor = _multiclass_shap_tensor(explainer, row)
    if shap_tensor.ndim == 2:
        impacts = shap_tensor[0]
    else:
        impacts = shap_tensor[0, :, predicted_index]
    feature_names = list(row.columns)

    contributions = [
        {"feature": feature_name, "impact": float(impact)}
        for feature_name, impact in zip(feature_names, impacts, strict=True)
    ]
    contributions.sort(key=lambda item: item["impact"], reverse=True)
    top_positive = [item for item in contributions if item["impact"] > 0][:top_k]
    top_negative = sorted(
        [item for item in contributions if item["impact"] < 0],
        key=lambda item: item["impact"],
    )[:top_k]

    return {
        "predicted_label": predicted_label,
        "predicted_probabilities": {
            class_labels[index]: float(probabilities[index]) for index in range(len(class_labels))
        },
        "top_positive_features": top_positive,
        "top_negative_features": top_negative,
    }
