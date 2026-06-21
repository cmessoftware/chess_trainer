#!/usr/bin/env python3
"""Export Kaggle competition CSV files from course SQLite (Option A: best-effort)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COMPETITION_ROOT = Path(__file__).resolve().parent
if str(COMPETITION_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPETITION_ROOT))

from kaggle_package.config import DEFAULT_OUTPUT_DIR, DEFAULT_SQLITE_PATH  # noqa: E402
from kaggle_package.export_pipeline import export_competition_dataset  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export ChessTrainer Kaggle competition CSVs.")
    parser.add_argument(
        "--db-url",
        default=str(DEFAULT_SQLITE_PATH),
        help=f"Course SQLite path (default: {DEFAULT_SQLITE_PATH})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = export_competition_dataset(args.db_url, args.output)

    print(f"Exported to: {result.output_dir.resolve()}")
    print(f"Games (train/test): {result.train_games:,} / {result.test_games:,}")
    print(f"Rows   (train/test): {result.train_rows:,} / {result.test_rows:,}")
    print(f"Completion vs 9,700 quota: {result.gap_report.completion_ratio:.1%}")

    if result.gap_report.warnings:
        print("\nWarnings:")
        for warning in result.gap_report.warnings[:5]:
            print(f"  - {warning}")

    print("\nFiles: train.csv, test.csv, sample_submission.csv, solution.csv,")
    print("       competition_description.md, data_dictionary.md, export_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
