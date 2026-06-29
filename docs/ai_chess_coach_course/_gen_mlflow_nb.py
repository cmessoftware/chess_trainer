"""Generate 05_mlflow_experiment_tracking.ipynb."""

import json
from pathlib import Path

cells = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Module 05 — MLflow Experiment Tracking\n",
            "\n",
            "Track Module 04 training runs in **MLflow** (portable SQLite backend).\n",
            "\n",
            "Open UI in another terminal:\n",
            "\n",
            "```powershell\n",
            ".\\start_mlflow_ui.ps1\n",
            "```\n",
            "\n",
            "Or:\n",
            "\n",
            "```python\n",
            "from experiment_tracking.course_mlflow import mlflow_ui_command\n",
            "print(mlflow_ui_command())\n",
            "```\n",
            "\n",
            "Then visit http://localhost:5000\n",
        ],
    },
    {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [
            "from pathlib import Path\n",
            "\n",
            "import pandas as pd\n",
            "\n",
            "from experiment_tracking.course_mlflow import (\n",
            "    configure_course_mlflow,\n",
            "    save_best_human_run_manifest,\n",
            "    select_best_human_run,\n",
            ")\n",
            "from experiment_tracking.training_runner import (\n",
            "    default_model_grid,\n",
            "    load_encoded_dataset,\n",
            "    resolve_dataset_path,\n",
            "    run_experiment_grid,\n",
            ")\n",
            "\n",
            "COURSE_ROOT = Path('.').resolve()\n",
            "ARTIFACTS_DIR = COURSE_ROOT / 'artifacts' / 'module05'\n",
            "tracking_uri = configure_course_mlflow()\n",
            "print('MLflow tracking URI:', tracking_uri)\n",
        ],
    },
    {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [
            "dataset_path = resolve_dataset_path()\n",
            "encoded = load_encoded_dataset(dataset_path)\n",
            "print('Dataset:', dataset_path)\n",
            "print('Shape:', encoded.shape)\n",
            "print('Games:', encoded['game_id'].nunique())\n",
            "encoded['error_label'].value_counts(normalize=True).round(3)\n",
        ],
    },
    {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [
            "# fast=True: LR + RF + LightGBM with class_weight (expand grid by setting fast=False)\n",
            "summary = run_experiment_grid(\n",
            "    encoded=encoded,\n",
            "    dataset_path=dataset_path,\n",
            "    artifacts_dir=ARTIFACTS_DIR,\n",
            "    feature_sets=('human', 'proxy'),\n",
            "    model_grid=default_model_grid(fast=True),\n",
            "    progress=print,\n",
            ")\n",
            "summary\n",
        ],
    },
    {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [
            "human_summary = summary.loc[summary['feature_set'] == 'human'].sort_values('f1_macro', ascending=False)\n",
            "human_summary.head(10)\n",
        ],
    },
    {
        "cell_type": "code",
        "metadata": {},
        "outputs": [],
        "execution_count": None,
        "source": [
            "best_human = select_best_human_run()\n",
            "manifest_path = save_best_human_run_manifest(best_human)\n",
            "print('Best Human run manifest:', manifest_path)\n",
            "best_human\n",
        ],
    },
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

path = Path(__file__).resolve().parent / "05_mlflow_experiment_tracking.ipynb"
path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
print(path)
