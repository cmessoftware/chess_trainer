from pathlib import Path
import sys

import pandas as pd
import pytest

COMPETITION_ROOT = Path(__file__).resolve().parents[2] / "docs" / "competition"
if str(COMPETITION_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPETITION_ROOT))

from kaggle_package.gap_report import build_kaggle_gap_report


def test_gap_report_caps_and_underfill():
    games = pd.DataFrame(
        {
            "game_id": [f"g{i}" for i in range(10)],
            "elo_band": ["<1200"] * 5 + ["2400+"] * 3 + ["1800-1999"] * 2,
            "time_control_bucket": ["blitz"] * 10,
        }
    )
    report = build_kaggle_gap_report(games, feature_row_count=100)
    row_lt_1200 = report.band_table.loc[report.band_table["elo_band"] == "<1200"].iloc[0]
    row_2400 = report.band_table.loc[report.band_table["elo_band"] == "2400+"].iloc[0]

    assert row_lt_1200["available"] == 5
    assert row_lt_1200["exportable"] == 5
    assert row_lt_1200["status"] == "underfilled"
    assert row_2400["exportable"] == 3
    assert report.total_exportable == 10
    assert not report.import_complete


def test_gap_report_empty_games():
    report = build_kaggle_gap_report(pd.DataFrame(), feature_row_count=0)
    assert report.total_exportable == 0
    assert report.warnings
