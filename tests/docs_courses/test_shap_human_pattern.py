from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

shap = pytest.importorskip("shap")

from explainability.human_pattern_models import (
    LABEL_ORDER,
    train_and_compare_human_pattern_models,
)
from explainability.shap_analysis import (
    aggregate_mean_abs_shap,
    compute_global_shap_importance,
    explain_prediction,
    grouped_feature_name,
    sample_rows_by_game_id,
)


def _toy_human_dataset(rows: int = 120) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(42)
    game_ids = [f"g{i // 6}" for i in range(rows)]
    frame = pd.DataFrame(
        {
            "player_elo": rng.integers(1200, 2000, size=rows),
            "move_number": rng.integers(1, 40, size=rows),
            "material_total": rng.normal(40, 10, size=rows),
            "king_safety": rng.integers(-5, 5, size=rows),
            "opening_A": rng.integers(0, 2, size=rows),
            "opening_B": rng.integers(0, 2, size=rows),
            "phase_middlegame": rng.integers(0, 2, size=rows),
            "game_id": game_ids,
            "error_label": rng.choice(list(LABEL_ORDER), size=rows),
        }
    )
    feature_columns = [
        column
        for column in frame.columns
        if column not in {"game_id", "error_label"}
    ]
    split_at = max(int(rows * 0.75), 1)
    train = frame.iloc[:split_at]
    val = frame.iloc[split_at:]
    if val.empty:
        val = train.iloc[: max(len(train) // 4, 1)].copy()
    X_train = train[feature_columns]
    y_train = train["error_label"]
    X_val = val[feature_columns]
    y_val = val["error_label"]
    return X_train, y_train, X_val, y_val


def test_grouped_feature_name():
    assert grouped_feature_name("opening_Sicilian") == "opening (grouped)"
    assert grouped_feature_name("king_safety") == "king_safety"


def test_aggregate_mean_abs_shap_groups_openings():
    importance = aggregate_mean_abs_shap(
        ["king_safety", "opening_A", "opening_B"],
        np.array([0.5, 0.2, 0.3]),
    )
    opening_row = importance.loc[importance["feature"] == "opening (grouped)", "mean_abs_shap"].iloc[0]
    assert opening_row == pytest.approx(0.5)


def test_sample_rows_by_game_id_keeps_whole_games():
    frame = pd.DataFrame(
        {
            "game_id": ["g1", "g1", "g2", "g2", "g3", "g3"],
            "value": [1, 2, 3, 4, 5, 6],
        }
    )
    sample = sample_rows_by_game_id(frame, max_rows=4, random_state=42)
    assert len(sample) <= 4
    assert sample["game_id"].nunique() >= 1


def test_train_and_compare_human_pattern_models():
    X_train, y_train, X_val, y_val = _toy_human_dataset()
    fitted, comparison_df, selected = train_and_compare_human_pattern_models(
        X_train,
        y_train,
        X_val,
        y_val,
        n_estimators=10,
    )
    assert selected in fitted
    assert {"lightgbm", "xgboost", "catboost"}.issubset(comparison_df.index)
    assert comparison_df.loc[selected, "f1_macro"] >= 0.0


def test_explain_prediction_structure():
    X_train, y_train, X_val, y_val = _toy_human_dataset(rows=80)
    fitted, _, selected = train_and_compare_human_pattern_models(
        X_train,
        y_train,
        X_val,
        y_val,
        n_estimators=10,
    )
    model = fitted[selected]
    _, _, explainer, _ = compute_global_shap_importance(model, X_val.iloc[:10])
    explanation = explain_prediction(model, explainer, X_val.iloc[[0]])
    assert "predicted_label" in explanation
    assert "top_positive_features" in explanation
    assert explanation["predicted_label"] in LABEL_ORDER
