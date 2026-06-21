"""Gap analysis between SQLite inventory and Kaggle elo_band quotas."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from kaggle_package.config import (
    BAND_UNDERFILL_WARNING_RATIO,
    COMPLETION_THRESHOLD,
    KAGGLE_ELO_BAND_GAME_QUOTAS,
    KAGGLE_TARGET_GAME_COUNT,
    TIME_CONTROL_TARGET_SHARES,
    TIME_CONTROL_WARNING_TOLERANCE,
)


@dataclass
class KaggleGapReport:
    band_table: pd.DataFrame
    total_available: int
    total_quota: int
    total_exportable: int
    completion_ratio: float
    import_complete: bool
    time_control_distribution: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    feature_row_count: int = 0

    def to_dict(self) -> dict:
        return {
            "total_available": self.total_available,
            "total_quota": self.total_quota,
            "total_exportable": self.total_exportable,
            "completion_ratio": self.completion_ratio,
            "import_complete": self.import_complete,
            "time_control_distribution": self.time_control_distribution,
            "warnings": self.warnings,
            "feature_row_count": self.feature_row_count,
            "bands": self.band_table.to_dict(orient="records"),
        }


def build_kaggle_gap_report(
    games: pd.DataFrame,
    *,
    feature_row_count: int = 0,
) -> KaggleGapReport:
    if games.empty:
        empty = pd.DataFrame(
            columns=[
                "elo_band",
                "quota",
                "available",
                "exportable",
                "fill_pct",
                "gap",
                "status",
            ]
        )
        return KaggleGapReport(
            band_table=empty,
            total_available=0,
            total_quota=KAGGLE_TARGET_GAME_COUNT,
            total_exportable=0,
            completion_ratio=0.0,
            import_complete=False,
            warnings=["No human games found in SQLite (after excluding stockfish)."],
            feature_row_count=feature_row_count,
        )

    available_counts = games["elo_band"].value_counts()
    rows: list[dict[str, object]] = []
    warnings: list[str] = []
    total_available = int(len(games))
    total_exportable = 0

    for band, quota in KAGGLE_ELO_BAND_GAME_QUOTAS.items():
        available = int(available_counts.get(band, 0))
        exportable = min(available, quota)
        gap = quota - exportable
        fill_pct = exportable / quota if quota else 0.0

        if available >= quota:
            status = "cap (sample down)"
        elif available == 0:
            status = "empty"
        elif fill_pct < BAND_UNDERFILL_WARNING_RATIO:
            status = "underfilled"
        else:
            status = "partial ok"

        if fill_pct < BAND_UNDERFILL_WARNING_RATIO:
            warnings.append(
                f"elo_band '{band}': {exportable:,} / {quota:,} games "
                f"({fill_pct:.1%} of quota; {available:,} available)"
            )

        rows.append(
            {
                "elo_band": band,
                "quota": quota,
                "available": available,
                "exportable": exportable,
                "fill_pct": round(fill_pct, 4),
                "gap": gap,
                "status": status,
            }
        )
        total_exportable += exportable

    completion_ratio = total_exportable / KAGGLE_TARGET_GAME_COUNT
    import_complete = completion_ratio >= COMPLETION_THRESHOLD
    if not import_complete:
        warnings.insert(
            0,
            f"Export would reach {total_exportable:,} / {KAGGLE_TARGET_GAME_COUNT:,} games "
            f"({completion_ratio:.1%}); target is {COMPLETION_THRESHOLD:.0%}.",
        )

    time_control_distribution: dict[str, float] = {}
    bucket_games = games.dropna(subset=["time_control_bucket"])
    if not bucket_games.empty:
        tc_counts = bucket_games["time_control_bucket"].value_counts(normalize=True)
        time_control_distribution = {str(k): float(v) for k, v in tc_counts.items()}
        for bucket, target_share in TIME_CONTROL_TARGET_SHARES.items():
            actual_share = time_control_distribution.get(bucket, 0.0)
            if abs(actual_share - target_share) > TIME_CONTROL_WARNING_TOLERANCE:
                warnings.append(
                    f"time_control_bucket '{bucket}': {actual_share:.1%} "
                    f"(target {target_share:.0%} ± {TIME_CONTROL_WARNING_TOLERANCE:.0%})"
                )

    band_table = pd.DataFrame(rows)
    return KaggleGapReport(
        band_table=band_table,
        total_available=total_available,
        total_quota=KAGGLE_TARGET_GAME_COUNT,
        total_exportable=total_exportable,
        completion_ratio=completion_ratio,
        import_complete=import_complete,
        time_control_distribution=time_control_distribution,
        warnings=warnings,
        feature_row_count=feature_row_count,
    )
