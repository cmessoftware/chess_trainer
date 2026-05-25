from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from ..data_access.features_repository import FeaturesRepository
except ImportError:  # direct script execution
    COURSE_ROOT = Path(__file__).resolve().parents[1]
    if str(COURSE_ROOT) not in sys.path:
        sys.path.insert(0, str(COURSE_ROOT))
    from data_access.features_repository import FeaturesRepository

TARGET_LABELS = ("good", "inaccuracy", "mistake", "blunder")
NUMERIC_FEATURES = [
    "move_number",
    "player_color",
    "material_balance",
    "material_total",
    "num_pieces",
    "branching_factor",
    "self_mobility",
    "opponent_mobility",
    "has_castling_rights",
    "move_number_global",
    "is_repetition",
    "is_low_mobility",
    "is_center_controlled",
    "is_pawn_endgame",
    "score_diff",
    "elo",
]
CATEGORICAL_FEATURES = ["opening", "eco", "phase"]


def _normalize_target(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def build_training_dataset(features_df: pd.DataFrame, labels: Iterable[str] = TARGET_LABELS) -> pd.DataFrame:
    labels = tuple(label.lower() for label in labels)
    if features_df.empty:
        raise ValueError("No feature rows found to build training dataset")

    df = features_df.copy()
    df["error_label"] = _normalize_target(df["error_label"])
    df = df[df["error_label"].isin(labels)]

    if df.empty:
        raise ValueError("No rows matched expected target classes: good, inaccuracy, mistake, blunder")

    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median() if not df[col].dropna().empty else 0)

    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").astype(str)

    feature_cols = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c in df.columns]
    model_df = df[feature_cols + ["error_label"]].copy()
    model_df = pd.get_dummies(model_df, columns=[c for c in CATEGORICAL_FEATURES if c in model_df.columns], drop_first=False)

    return model_df


def build_from_repository(db_url: str | None, output_path: Path, limit: int | None = None) -> pd.DataFrame:
    repo = FeaturesRepository(db_url=db_url)
    raw_df = repo.load_features_for_training(labels=TARGET_LABELS, limit=limit)
    training_df = build_training_dataset(raw_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".csv":
        training_df.to_csv(output_path, index=False)
    else:
        training_df.to_parquet(output_path, index=False)

    return training_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build AI course training dataset from PostgreSQL features table")
    parser.add_argument("--db-url", default=None, help="Database URL (defaults to CHESS_TRAINER_DB_URL)")
    parser.add_argument("--limit", type=int, default=None, help="Optional max rows for quick iterations")
    parser.add_argument("--output", default="docs/courses/ai_engineer_course/dataset/training_dataset.parquet", help="Output file (.parquet or .csv)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).resolve()
    df = build_from_repository(db_url=args.db_url, output_path=output_path, limit=args.limit)
    print(f"[OK] Dataset generated: {output_path}")
    print(f"Rows: {len(df)}")
    print(df["error_label"].value_counts().to_string())


if __name__ == "__main__":
    main()
