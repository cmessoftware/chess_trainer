"""Tests for course MLflow tracking helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import mlflow

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from experiment_tracking.course_mlflow import (  # noqa: E402
    configure_course_mlflow,
    ensure_experiment,
    mlflow_ui_command,
    save_best_human_run_manifest,
    select_best_human_run,
)


def test_configure_and_log_run(tmp_path: Path) -> None:
    db_path = tmp_path / "mlflow.db"
    configure_course_mlflow(db_path=db_path)
    experiment_id = ensure_experiment("chess_course_human_pattern_test")

    with mlflow.start_run(experiment_id=experiment_id, run_name="smoke"):
        mlflow.set_tags({"feature_set": "human", "model_family": "LightGBM"})
        mlflow.log_param("n_features", 12)
        mlflow.log_metric("f1_macro", 0.41)

    best = select_best_human_run(experiment_name="chess_course_human_pattern_test")
    assert best["val_f1_macro"] == 0.41

    manifest_path = save_best_human_run_manifest(best, output_path=tmp_path / "best.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == best["run_id"]

    cmd = mlflow_ui_command(db_path=db_path)
    assert "mlflow ui" in cmd
    assert db_path.as_posix() in cmd
