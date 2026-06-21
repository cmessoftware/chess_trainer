"""Orchestrate Kaggle competition CSV export."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from kaggle_package.config import (
    DEFAULT_OUTPUT_DIR,
    RANDOM_STATE,
    TARGET_COLUMN,
    TRAIN_TEST_SPLIT,
)
from kaggle_package.docs_generator import write_competition_description, write_data_dictionary
from kaggle_package.feature_export import (
    assign_competition_ids,
    attach_tactical_export_columns,
    load_prepared_competition_features,
    to_public_export_frame,
)
from kaggle_package.gap_report import KaggleGapReport, build_kaggle_gap_report
from kaggle_package.game_inventory import count_feature_rows, load_human_games
from kaggle_package.game_selection import select_games_by_elo_band
from kaggle_package.splits import split_train_test_by_game_id
from kaggle_package.validation import (
    assert_no_leakage_columns,
    build_eda_summary,
)


@dataclass
class ExportResult:
    output_dir: Path
    gap_report: KaggleGapReport
    train_rows: int
    test_rows: int
    train_games: int
    test_games: int
    eda_summary: dict


def export_competition_dataset(
    db_url: str | Path,
    output_dir: str | Path | None = None,
    *,
    random_state: int = RANDOM_STATE,
) -> ExportResult:
    destination = Path(output_dir or DEFAULT_OUTPUT_DIR)
    destination.mkdir(parents=True, exist_ok=True)

    games = load_human_games(db_url)
    gap_report = build_kaggle_gap_report(games, feature_row_count=count_feature_rows(db_url))
    selected_games = select_games_by_elo_band(games, random_state=random_state)
    selected_ids = selected_games["game_id"].tolist()

    prepared = load_prepared_competition_features(str(db_url), selected_ids)
    if prepared.empty:
        raise ValueError("No feature rows loaded for selected games.")

    prepared = attach_tactical_export_columns(prepared)
    prepared = assign_competition_ids(prepared)
    train_frame, test_frame = split_train_test_by_game_id(
        prepared,
        test_size=TRAIN_TEST_SPLIT,
        random_state=random_state,
    )

    train_export = to_public_export_frame(train_frame, include_target=True)
    test_export = to_public_export_frame(test_frame, include_target=False)

    assert_no_leakage_columns(train_export, label="train.csv")
    assert_no_leakage_columns(test_export, label="test.csv")

    train_export.to_csv(destination / "train.csv", index=False)
    test_export.to_csv(destination / "test.csv", index=False)

    solution = test_frame[["id", TARGET_COLUMN]].copy()
    solution.to_csv(destination / "solution.csv", index=False)

    sample = test_export[["id"]].copy()
    sample[TARGET_COLUMN] = "good"
    sample.to_csv(destination / "sample_submission.csv", index=False)

    prepared[["id", "game_id"]].to_csv(destination / "id_game_map.csv", index=False)

    eda_summary = build_eda_summary(train_export)
    export_meta = {
        "gap_report": gap_report.to_dict(),
        "eda_summary": eda_summary,
        "train_games": int(train_frame["game_id"].nunique()),
        "test_games": int(test_frame["game_id"].nunique()),
        "train_rows": int(len(train_export)),
        "test_rows": int(len(test_export)),
        "option": "A (best-effort export as-is)",
    }
    (destination / "export_report.json").write_text(
        json.dumps(export_meta, indent=2),
        encoding="utf-8",
    )

    write_competition_description(
        destination / "competition_description.md",
        gap_report=gap_report,
        train_games=export_meta["train_games"],
        test_games=export_meta["test_games"],
        train_rows=export_meta["train_rows"],
        test_rows=export_meta["test_rows"],
    )
    write_data_dictionary(destination / "data_dictionary.md")

    return ExportResult(
        output_dir=destination,
        gap_report=gap_report,
        train_rows=export_meta["train_rows"],
        test_rows=export_meta["test_rows"],
        train_games=export_meta["train_games"],
        test_games=export_meta["test_games"],
        eda_summary=eda_summary,
    )
