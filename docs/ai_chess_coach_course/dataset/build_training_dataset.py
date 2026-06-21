from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = COURSE_ROOT.parents[1]
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository  # noqa: E402
from dataset.feature_engineering import (  # noqa: E402
    encode_training_features,
    prepare_feature_frame,
    validate_dataset_quality,
)
from dataset.game_splits import save_game_splits, split_by_game_id  # noqa: E402

TARGET_CLASSES = ("good", "inaccuracy", "mistake", "blunder")
TRAINING_FEATURE_COLUMNS = [
    "game_id",
    "move_number",
    "player_color",
    "white_player",
    "black_player",
    "white_elo",
    "black_elo",
    "source",  # metadata only — used to drop stockfish, excluded from ML encoding
    "skill_group",
    "skill_group_description",
    "time_control",
    "opening",
    "result",
    "material_total",
    "num_pieces",
    "king_safety",
    "center_control",
    "has_castling_rights",
    "is_pawn_endgame",
    "score_cp",
    "score_diff",
    "phase",
    "branching_factor",
    "self_mobility",
    "opponent_mobility",
    "error_label",
]
DEFAULT_TRAINING_DATASET_PATH = REPO_ROOT / "data" / "datasets" / "course_training_dataset.parquet"
ML_FEATURE_COLUMNS = [
    "move_number",
    "player_elo",
    "material_total",
    "num_pieces",
    "king_safety",
    "center_control",
    "has_castling_rights",
    "is_pawn_endgame",
    "score_cp",
    "mate_in",
    "depth_score_diff",
]


def build_training_dataset(
    *,
    db_url: str | Path | None = None,
    output_path: str | Path | None = None,
    target_column: str = "error_label",
    validate_quality: bool = True,
    min_rows_for_distribution_checks: int = 1000,
    split_output_dir: str | Path | None = None,
    quality_report_path: str | Path | None = None,
) -> pd.DataFrame:
    repository = CourseFeaturesRepository(db_url)
    dataset = repository.load_features(columns=TRAINING_FEATURE_COLUMNS)
    if dataset.empty:
        return dataset

    prepared = prepare_feature_frame(
        dataset,
        target_column=target_column,
        target_classes=TARGET_CLASSES,
    )
    if prepared.empty:
        return prepared

    if validate_quality:
        quality_report = validate_dataset_quality(
            prepared,
            target_column=target_column,
            min_rows_for_distribution_checks=min_rows_for_distribution_checks,
        )
        if quality_report_path:
            report_destination = Path(quality_report_path)
            report_destination.parent.mkdir(parents=True, exist_ok=True)
            report_destination.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")

    encoded = encode_training_features(prepared)

    if split_output_dir:
        train_df, val_df, test_df = split_by_game_id(
            encoded,
            target_column=target_column,
        )
        save_game_splits(train_df, val_df, test_df, split_output_dir)

    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.suffix.lower() == ".csv":
            encoded.to_csv(destination, index=False)
        else:
            encoded.to_parquet(destination, index=False)

    return encoded.reset_index(drop=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the portable course training dataset from the configured course database.",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="Database URL override. Defaults to CHESS_COURSE_DB_URL or the local SQLite file.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_TRAINING_DATASET_PATH),
        help=f"Destination file (.parquet or .csv). Default: {DEFAULT_TRAINING_DATASET_PATH}",
    )
    parser.add_argument(
        "--target-column",
        default="error_label",
        help="Target column for supervised training. Default: error_label",
    )
    parser.add_argument(
        "--skip-quality-check",
        action="store_true",
        help="Skip dataset quality validation (not recommended for production exports).",
    )
    parser.add_argument(
        "--split-output-dir",
        default=None,
        help="Optional directory for train/validation/test parquet splits grouped by game_id.",
    )
    parser.add_argument(
        "--quality-report",
        default=None,
        help="Optional JSON path for the quality report when validation passes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dataset = build_training_dataset(
        db_url=args.db_url,
        output_path=args.output,
        target_column=args.target_column,
        validate_quality=not args.skip_quality_check,
        split_output_dir=args.split_output_dir,
        quality_report_path=args.quality_report,
    )
    print(
        f"Built dataset with {len(dataset):,} row(s) and {dataset.shape[1] if not dataset.empty else 0} column(s)."
    )
    print(f"Target classes: {', '.join(TARGET_CLASSES)}")
    print(f"Output: {Path(args.output).resolve()}")
    if args.split_output_dir:
        print(f"Splits : {Path(args.split_output_dir).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
