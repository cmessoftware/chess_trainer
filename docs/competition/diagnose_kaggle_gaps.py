#!/usr/bin/env python3
"""Diagnose Kaggle elo_band quotas vs games available in course SQLite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COMPETITION_ROOT = Path(__file__).resolve().parent
if str(COMPETITION_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPETITION_ROOT))

from kaggle_package.config import DEFAULT_OUTPUT_DIR, DEFAULT_SQLITE_PATH  # noqa: E402
from kaggle_package.gap_report import build_kaggle_gap_report  # noqa: E402
from kaggle_package.game_inventory import count_feature_rows, load_human_games  # noqa: E402


def _print_table(report) -> None:
    print(f"{'elo_band':<12} {'quota':>8} {'available':>10} {'exportable':>11} {'fill%':>8} {'gap':>8}  status")
    print("-" * 78)
    for row in report.band_table.itertuples(index=False):
        print(
            f"{row.elo_band:<12} {row.quota:>8,} {row.available:>10,} "
            f"{row.exportable:>11,} {row.fill_pct:>7.1%} {row.gap:>8,}  {row.status}"
        )
    print("-" * 78)
    print(
        f"{'TOTAL':<12} {report.total_quota:>8,} {report.total_available:>10,} "
        f"{report.total_exportable:>11,} {report.completion_ratio:>7.1%} "
        f"{report.total_quota - report.total_exportable:>8,}"
    )
    print(f"\nFeature rows in SQLite (all sources): {report.feature_row_count:,}")
    if report.time_control_distribution:
        print("\nTime control distribution (games):")
        for bucket, share in sorted(report.time_control_distribution.items()):
            print(f"  {bucket:<12} {share:>6.1%}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Kaggle elo_band quotas with human games in course SQLite.",
    )
    parser.add_argument(
        "--db-url",
        default=str(DEFAULT_SQLITE_PATH),
        help=f"Course SQLite path or DB URL (default: {DEFAULT_SQLITE_PATH})",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional path to write gap report JSON (e.g. output/kaggle_gap_report.json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_url = args.db_url

    print(f"Course DB: {Path(db_url).resolve() if not str(db_url).startswith('sqlite') else db_url}")
    games = load_human_games(db_url)
    feature_rows = count_feature_rows(db_url)
    report = build_kaggle_gap_report(games, feature_row_count=feature_rows)

    _print_table(report)

    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"  - {warning}")

    if report.import_complete:
        print("\n[OK] Best-effort export would meet the 95% game target.")
    else:
        print("\n[WARN] Best-effort export is below the 95% game target — review gaps before publishing.")

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(f"\nWrote {out_path.resolve()}")

    return 0 if report.import_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
