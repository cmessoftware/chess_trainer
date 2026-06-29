"""Training + evaluation helpers for Module 05 MLflow runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import seaborn as sns
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from dataset.build_training_dataset import DEFAULT_TRAINING_DATASET_PATH
from dataset.feature_engineering import (
    encode_training_features,
    resolve_model_feature_columns,
    split_features_and_target,
)
from dataset.game_splits import split_by_game_id
from experiment_tracking.course_mlflow import (
    HUMAN_EXPERIMENT,
    PROXY_EXPERIMENT,
    ensure_experiment,
    log_classification_artifacts,
    log_split_params,
    log_validation_metrics,
)

LABEL_ORDER = ("good", "inaccuracy", "mistake", "blunder")


def resolve_dataset_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit)
    course_local = Path(__file__).resolve().parents[1] / "data" / "datasets" / "course_training_dataset.parquet"
    if course_local.exists():
        return course_local
    return Path(DEFAULT_TRAINING_DATASET_PATH)


def load_encoded_dataset(
    dataset_path: Path | None = None,
    *,
    db_url: str | Path | None = None,
    refresh_if_missing_game_id: bool = True,
) -> pd.DataFrame:
    path = resolve_dataset_path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Training dataset not found at {path}. Run Module 02 dataset builder first."
        )
    frame = pd.read_parquet(path)
    if "error_label" not in frame.columns:
        raise ValueError(f"Dataset at {path} is missing error_label.")
    if "game_id" not in frame.columns:
        if not refresh_if_missing_game_id:
            raise ValueError(
                f"Dataset at {path} is missing game_id for game-level splits. "
                "Re-run Module 02 dataset builder to regenerate the parquet."
            )
        from dataset.build_training_dataset import build_training_dataset

        frame = build_training_dataset(
            db_url=db_url,
            output_path=path,
            validate_quality=False,
        )
        if "game_id" not in frame.columns:
            raise ValueError(
                f"Rebuilt dataset at {path} is still missing game_id. "
                "Check that the course database includes game_id in feature rows."
            )
    return frame


def build_game_level_splits(encoded: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return split_by_game_id(encoded, target_column="error_label")


def compute_multiclass_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray | None,
    *,
    labels: list[str],
) -> dict[str, float]:
    metrics: dict[str, float] = {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
    }
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )
    metrics["precision_macro"] = float(precision)
    metrics["recall_macro"] = float(recall)
    metrics["f1_macro"] = float(f1)

    if y_score is not None:
        y_true_bin = pd.get_dummies(pd.Series(y_true, dtype=str)).reindex(
            columns=labels,
            fill_value=0,
        ).to_numpy()
        try:
            metrics["roc_auc_weighted"] = float(
                roc_auc_score(y_true_bin, y_score, average="weighted", multi_class="ovr")
            )
            metrics["pr_auc_macro"] = float(
                average_precision_score(y_true_bin, y_score, average="macro")
            )
        except ValueError:
            metrics["roc_auc_weighted"] = float("nan")
            metrics["pr_auc_macro"] = float("nan")

    for label in labels:
        label_mask = y_true == label
        if label_mask.any():
            metrics[f"f1_{label}"] = float(
                f1_score(y_true == label, y_pred == label, zero_division=0)
            )
    return metrics


def _build_model(model_family: str, imbalance_strategy: str) -> Any:
    if imbalance_strategy not in {"class_weight", "smote", "none"}:
        raise ValueError(f"Unknown imbalance_strategy: {imbalance_strategy}")

    class_weight = "balanced" if imbalance_strategy == "class_weight" else None

    if model_family == "LogisticRegression":
        estimator = LogisticRegression(
            solver="saga",
            max_iter=2000,
            class_weight=class_weight,
            random_state=42,
        )
        steps: list[tuple[str, Any]] = [("scaler", StandardScaler()), ("clf", estimator)]
        if imbalance_strategy == "smote":
            return ImbPipeline(
                [
                    ("scaler", StandardScaler()),
                    ("smote", SMOTE(random_state=42)),
                    ("clf", LogisticRegression(solver="saga", max_iter=2000, random_state=42)),
                ]
            )
        return Pipeline(steps)

    if model_family == "KNN":
        estimator = KNeighborsClassifier(n_neighbors=7)
        if imbalance_strategy == "smote":
            return ImbPipeline([("smote", SMOTE(random_state=42)), ("clf", estimator)])
        return Pipeline([("scaler", StandardScaler()), ("clf", estimator)])

    if model_family == "RandomForest":
        estimator = RandomForestClassifier(
            n_estimators=150,
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1,
        )
        if imbalance_strategy == "smote":
            return ImbPipeline([("smote", SMOTE(random_state=42)), ("clf", estimator)])
        return Pipeline([("clf", estimator)])

    if model_family == "LightGBM":
        estimator = LGBMClassifier(
            objective="multiclass",
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1,
            verbosity=-1,
        )
        if imbalance_strategy == "smote":
            return ImbPipeline([("smote", SMOTE(random_state=42)), ("clf", estimator)])
        return Pipeline([("clf", estimator)])

    raise ValueError(f"Unsupported model_family: {model_family}")


def default_model_grid(*, fast: bool = False) -> list[tuple[str, str]]:
    models = ["LogisticRegression", "RandomForest", "LightGBM"]
    if not fast:
        models.extend(["KNN"])
    strategies = ["class_weight"]
    if not fast:
        strategies.append("smote")
    return [(model, strategy) for model in models for strategy in strategies]


def train_and_log_run(
    *,
    feature_set: str,
    model_family: str,
    imbalance_strategy: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    dataset_path: Path,
    artifacts_dir: Path,
) -> dict[str, float]:
    feature_columns = resolve_model_feature_columns(train_df, feature_set=feature_set)
    X_train, y_train = split_features_and_target(
        train_df,
        feature_columns=feature_columns,
        sanitize_feature_names=True,
    )
    X_val, y_val = split_features_and_target(
        val_df,
        feature_columns=feature_columns,
        sanitize_feature_names=True,
    )
    X_test, y_test = split_features_and_target(
        test_df,
        feature_columns=feature_columns,
        sanitize_feature_names=True,
    )

    encoder = LabelEncoder()
    encoder.fit(list(LABEL_ORDER))
    y_train_enc = encoder.transform(y_train)
    y_val_enc = encoder.transform(y_val)
    y_test_enc = encoder.transform(y_test)
    labels = list(encoder.classes_)

    experiment_name = HUMAN_EXPERIMENT if feature_set == "human" else PROXY_EXPERIMENT
    ensure_experiment(experiment_name)

    model = _build_model(model_family, imbalance_strategy)
    run_name = f"{feature_set}_{model_family}_{imbalance_strategy}"

    with mlflow.start_run(run_name=run_name, experiment_id=ensure_experiment(experiment_name)):
        mlflow.set_tags(
            {
                "feature_set": feature_set,
                "model_family": model_family,
                "imbalance_strategy": imbalance_strategy,
                "split_policy": "game_level",
                "course_module": "05",
            }
        )
        log_split_params(
            feature_set=feature_set,
            model_family=model_family,
            imbalance_strategy=imbalance_strategy,
            dataset_path=dataset_path,
            n_train=len(X_train),
            n_val=len(X_val),
            n_test=len(X_test),
            n_features=len(feature_columns),
        )

        model.fit(X_train, y_train_enc)
        y_train_pred = model.predict(X_train)
        y_val_pred = model.predict(X_val)
        y_test_pred = model.predict(X_test)

        y_val_score = model.predict_proba(X_val) if hasattr(model, "predict_proba") else None
        y_test_score = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

        train_metrics = compute_multiclass_metrics(y_train_enc, y_train_pred, None, labels=labels)
        val_metrics = compute_multiclass_metrics(y_val_enc, y_val_pred, y_val_score, labels=labels)
        test_metrics = compute_multiclass_metrics(y_test_enc, y_test_pred, y_test_score, labels=labels)

        log_validation_metrics({f"train_{key}": value for key, value in train_metrics.items()})
        log_validation_metrics(val_metrics)
        log_validation_metrics({f"test_{key}": value for key, value in test_metrics.items()})

        report_text = classification_report(
            y_val_enc,
            y_val_pred,
            labels=list(range(len(labels))),
            target_names=labels,
            zero_division=0,
        )
        cm = confusion_matrix(y_val_enc, y_val_pred)

        artifacts_dir.mkdir(parents=True, exist_ok=True)
        cm_path = artifacts_dir / f"cm_{feature_set}_{model_family}_{imbalance_strategy}.png"
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax)
        ax.set_title(f"{run_name} — validation")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        fig.tight_layout()
        fig.savefig(cm_path, dpi=120)
        plt.close(fig)

        log_classification_artifacts(
            model=model,
            feature_columns=list(X_train.columns),
            label_order=labels,
            classification_report_text=report_text,
            confusion_matrix_path=cm_path,
        )

    return val_metrics


def run_experiment_grid(
    *,
    encoded: pd.DataFrame,
    dataset_path: Path,
    artifacts_dir: Path,
    feature_sets: tuple[str, ...] = ("human", "proxy"),
    model_grid: list[tuple[str, str]] | None = None,
    progress: Callable[[str], None] | None = None,
) -> pd.DataFrame:
    train_df, val_df, test_df = build_game_level_splits(encoded)
    grid = model_grid or default_model_grid(fast=True)
    summaries: list[dict[str, Any]] = []

    for feature_set in feature_sets:
        for model_family, imbalance_strategy in grid:
            message = f"{feature_set} | {model_family} | {imbalance_strategy}"
            if progress:
                progress(message)
            metrics = train_and_log_run(
                feature_set=feature_set,
                model_family=model_family,
                imbalance_strategy=imbalance_strategy,
                train_df=train_df,
                val_df=val_df,
                test_df=test_df,
                dataset_path=dataset_path,
                artifacts_dir=artifacts_dir,
            )
            summaries.append(
                {
                    "feature_set": feature_set,
                    "model_family": model_family,
                    "imbalance_strategy": imbalance_strategy,
                    **metrics,
                }
            )

    return pd.DataFrame(summaries).sort_values(by="f1_macro", ascending=False)
