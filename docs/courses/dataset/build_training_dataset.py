from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = COURSE_ROOT.parents[1]
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository  # noqa: E402

TARGET_CLASSES = ("good", "inaccuracy", "mistake", "blunder")
TRAINING_FEATURE_COLUMNS = [
    "game_id",
    "move_number",
    "elo",
    "opening",
    "material_total",
    "num_pieces",
    "king_safety",
    "center_control",
    "has_castling_rights",
    "is_pawn_endgame",
    "score_cp",
    "mate_in",
    "depth_score_diff",
    "error_label",
]
DEFAULT_TRAINING_DATASET_PATH = REPO_ROOT / "data" / "datasets" / "course_training_dataset.parquet"



def build_training_dataset(
    *,
    db_url: str | Path | None = None,
    output_path: str | Path | None = None,
    target_column: str = "error_label",
) -> pd.DataFrame:
    repository = CourseFeaturesRepository(db_url)
    dataset = repository.load_features(columns=TRAINING_FEATURE_COLUMNS)
    if dataset.empty:
        return dataset

    dataset = dataset.dropna(subset=[target_column]).copy()
    dataset = dataset[dataset[target_column].isin(TARGET_CLASSES)].copy()
    if dataset.empty:
        return dataset

    dataset["opening"] = dataset["opening"].fillna("unknown").astype(str)

    numeric_columns = [
        "move_number",
        "elo",
        "material_total",
        "num_pieces",
        "king_safety",
        "center_control",
        "score_cp",
        "mate_in",
        "depth_score_diff",
    ]
    for column in numeric_columns:
        dataset[column] = pd.to_numeric(dataset[column], errors="coerce")

    for column in ("has_castling_rights", "is_pawn_endgame"):
        dataset[column] = dataset[column].fillna(False).astype(int)

    dataset["mate_in"] = dataset["mate_in"].fillna(0)
    dataset["depth_score_diff"] = dataset["depth_score_diff"].fillna(0)
    dataset = dataset.dropna(
        subset=[
            "move_number",
            "elo",
            "material_total",
            "num_pieces",
            "king_safety",
            "center_control",
            "score_cp",
        ]
    )

    encoded = pd.get_dummies(dataset, columns=["opening"], prefix="opening")

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
    return parser.parse_args(argv)



def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dataset = build_training_dataset(
        db_url=args.db_url,
        output_path=args.output,
        target_column=args.target_column,
    )
    print(
        f"Built dataset with {len(dataset):,} row(s) and {dataset.shape[1] if not dataset.empty else 0} column(s)."
    )
    print(f"Target classes: {', '.join(TARGET_CLASSES)}")
    print(f"Output: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
