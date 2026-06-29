"""Course-local MLflow tracking (SQLite backend, no PostgreSQL)."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient

COURSE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MLFLOW_DIR = COURSE_ROOT / "mlflow"
DEFAULT_MLFLOW_DB = DEFAULT_MLFLOW_DIR / "mlflow.db"
DEFAULT_ARTIFACTS_DIR = COURSE_ROOT / "artifacts" / "module05"
HUMAN_EXPERIMENT = "chess_course_human_pattern"
PROXY_EXPERIMENT = "chess_course_proxy_sanity"
LABEL_ORDER = ("good", "inaccuracy", "mistake", "blunder")


def sqlite_uri_for_path(path: Path) -> str:
    """Build an MLflow-compatible sqlite URI (forward slashes, absolute path)."""
    return f"sqlite:///{path.expanduser().resolve().as_posix()}"


def default_db_path(*, db_path: Path | None = None) -> Path:
    return Path(db_path or DEFAULT_MLFLOW_DB)


def configure_course_mlflow(*, db_path: Path | None = None) -> str:
    destination = default_db_path(db_path=db_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tracking_uri = sqlite_uri_for_path(destination)
    mlflow.set_tracking_uri(tracking_uri)
    return tracking_uri


def mlflow_ui_command(*, db_path: Path | None = None, port: int = 5000) -> str:
    """Shell command to launch MLflow UI against the course SQLite store."""
    destination = default_db_path(db_path=db_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    uri = sqlite_uri_for_path(destination)
    return f"mlflow ui --backend-store-uri {uri} --port {port}"


def ensure_experiment(name: str) -> str:
    client = MlflowClient()
    experiment = client.get_experiment_by_name(name)
    if experiment is None:
        return client.create_experiment(name)
    return experiment.experiment_id


def _truncate_params(params: dict[str, Any]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in params.items():
        text = str(value)
        if len(text) > 450:
            text = text[:447] + "..."
        cleaned[key] = text
    return cleaned


def log_split_params(
    *,
    feature_set: str,
    model_family: str,
    imbalance_strategy: str,
    dataset_path: Path,
    n_train: int,
    n_val: int,
    n_test: int,
    n_features: int,
    extra: dict[str, Any] | None = None,
) -> None:
    params = {
        "feature_set": feature_set,
        "model_family": model_family,
        "imbalance_strategy": imbalance_strategy,
        "dataset_path": str(dataset_path),
        "n_train_rows": n_train,
        "n_val_rows": n_val,
        "n_test_rows": n_test,
        "n_features": n_features,
        "split_policy": "game_level",
        "random_state": 42,
        "train_ratio": 0.70,
        "val_ratio": 0.15,
        "test_ratio": 0.15,
        "target_column": "error_label",
        "course_module": "05",
    }
    if extra:
        params.update(extra)
    mlflow.log_params(_truncate_params(params))


def log_validation_metrics(
    metrics: dict[str, float],
    *,
    prefix: str = "",
) -> None:
    for name, value in metrics.items():
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric != numeric:  # NaN
            continue
        key = f"{prefix}{name}" if prefix else name
        mlflow.log_metric(key, numeric)


def log_classification_artifacts(
    *,
    model,
    feature_columns: list[str],
    label_order: list[str] | tuple[str, ...],
    classification_report_text: str,
    confusion_matrix_path: Path | None = None,
) -> None:
    DEFAULT_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    feature_payload = {"feature_columns": feature_columns}
    label_payload = {"label_order": list(label_order)}

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        (tmp / "feature_columns.json").write_text(
            json.dumps(feature_payload, indent=2),
            encoding="utf-8",
        )
        (tmp / "label_order.json").write_text(
            json.dumps(label_payload, indent=2),
            encoding="utf-8",
        )
        (tmp / "classification_report.txt").write_text(
            classification_report_text,
            encoding="utf-8",
        )
        if confusion_matrix_path and confusion_matrix_path.exists():
            mlflow.log_artifact(str(confusion_matrix_path), artifact_path="plots")
        mlflow.log_artifacts(str(tmp), artifact_path="metrics")

    mlflow.sklearn.log_model(model, artifact_path="model")


def select_best_human_run(
    *,
    experiment_name: str = HUMAN_EXPERIMENT,
    metric: str = "f1_macro",
) -> dict[str, Any]:
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"Experiment not found: {experiment_name}")

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} DESC"],
        max_results=1,
    )
    if not runs:
        raise ValueError(f"No runs found in experiment {experiment_name!r}")

    best = runs[0]
    return {
        "run_id": best.info.run_id,
        "experiment_name": experiment_name,
        "model_family": best.data.tags.get("model_family"),
        "feature_set": best.data.tags.get("feature_set"),
        "imbalance_strategy": best.data.tags.get("imbalance_strategy"),
        "val_f1_macro": best.data.metrics.get(metric),
        "selected_at": datetime.now(timezone.utc).isoformat(),
    }


def save_best_human_run_manifest(
    manifest: dict[str, Any],
    *,
    output_path: Path | None = None,
) -> Path:
    destination = output_path or (DEFAULT_ARTIFACTS_DIR / "best_human_run.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return destination
