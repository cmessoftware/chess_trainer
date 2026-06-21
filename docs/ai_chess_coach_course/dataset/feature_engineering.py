from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from dataset.skill_groups import (
    COURSE_SKILL_GROUP_GAME_QUOTAS,
    COURSE_TARGET_GAME_COUNT,
    derive_skill_group,
    derive_skill_group_description,
)

EXCLUDED_SOURCES = frozenset({"stockfish"})
PLAYER_ELO_MIN = 600
PLAYER_ELO_MAX = 3000

ELO_BIN_EDGES = [600, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 3000]
ELO_BAND_LABELS = [
    "<1200",
    "1200-1399",
    "1400-1599",
    "1600-1799",
    "1800-1999",
    "2000-2199",
    "2200-2399",
    "2400+",
]

TIME_CONTROL_BUCKET_ORDER = ("bullet", "blitz", "rapid", "classical")
TIME_CONTROL_TARGET_SHARES = {
    "bullet": 0.15,
    "blitz": 0.40,
    "rapid": 0.40,
    "classical": 0.05,
}

SKILL_GROUP_TARGET_SHARES = {
    name: quota / COURSE_TARGET_GAME_COUNT
    for name, quota in COURSE_SKILL_GROUP_GAME_QUOTAS.items()
}
SKILL_GROUP_TOLERANCE = 0.12
IMPORT_COMPLETION_THRESHOLD = 0.95
TIME_CONTROL_WARNING_TOLERANCE = 0.20

MAX_GOOD_SHARE = 0.55
MIN_BLUNDER_SHARE = 0.08


class DatasetQualityError(Exception):
    """Raised when the prepared dataset fails course quality checks."""

    def __init__(self, report: dict):
        self.report = report
        failures = report.get("failures", [])
        message = "Dataset quality checks failed:\n" + "\n".join(f"- {item}" for item in failures)
        super().__init__(message)


@dataclass
class QualityReport:
    row_count: int
    game_count: int
    label_distribution: dict[str, float] = field(default_factory=dict)
    source_game_distribution: dict[str, float] = field(default_factory=dict)
    skill_group_game_distribution: dict[str, float] = field(default_factory=dict)
    skill_group_game_counts: dict[str, int] = field(default_factory=dict)
    target_game_count: int = COURSE_TARGET_GAME_COUNT
    import_completion_ratio: float = 0.0
    import_complete: bool = False
    time_control_game_distribution: dict[str, float] = field(default_factory=dict)
    elo_band_game_distribution: dict[str, float] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "row_count": self.row_count,
            "game_count": self.game_count,
            "label_distribution": self.label_distribution,
            "source_game_distribution": self.source_game_distribution,
            "skill_group_game_distribution": self.skill_group_game_distribution,
            "skill_group_game_counts": self.skill_group_game_counts,
            "target_game_count": self.target_game_count,
            "import_completion_ratio": self.import_completion_ratio,
            "import_complete": self.import_complete,
            "time_control_game_distribution": self.time_control_game_distribution,
            "elo_band_game_distribution": self.elo_band_game_distribution,
            "failures": self.failures,
            "warnings": self.warnings,
        }


def parse_time_control_seconds(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    text = str(value).strip().lower()
    if not text or text == "-":
        return None
    if "day" in text or "per move" in text:
        return None
    if text.startswith("1/"):
        return None

    match = re.match(r"^(\d+)\+(\d+)$", text)
    if match:
        return int(match.group(1))
    if text.isdigit():
        return int(text)
    return None


def derive_time_control_bucket(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    if seconds < 180:
        return "bullet"
    if seconds < 600:
        return "blitz"
    if seconds < 1800:
        return "rapid"
    return "classical"


def derive_player_elo(
    df: pd.DataFrame,
    *,
    white_elo_column: str = "white_elo",
    black_elo_column: str = "black_elo",
    player_color_column: str = "player_color",
) -> pd.Series:
    if not {white_elo_column, black_elo_column, player_color_column}.issubset(df.columns):
        raise ValueError(
            "Cannot derive player_elo: missing "
            f"{sorted({white_elo_column, black_elo_column, player_color_column} - set(df.columns))}"
        )

    white_elo = pd.to_numeric(df[white_elo_column], errors="coerce")
    black_elo = pd.to_numeric(df[black_elo_column], errors="coerce")
    return np.where(df[player_color_column] == 1, white_elo, black_elo)


def derive_elo_band(player_elo: pd.Series) -> pd.Categorical:
    numeric_elo = pd.to_numeric(player_elo, errors="coerce")
    bands = pd.cut(
        numeric_elo,
        bins=ELO_BIN_EDGES,
        labels=ELO_BAND_LABELS,
        include_lowest=True,
    )
    return bands.astype("category")


def exclude_sources(df: pd.DataFrame, *, source_column: str = "source") -> pd.DataFrame:
    if source_column not in df.columns or not EXCLUDED_SOURCES:
        return df.copy()
    mask = ~df[source_column].isin(EXCLUDED_SOURCES)
    return df.loc[mask].copy()


def ensure_chess_feature_columns(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset.copy()

    if "opening" not in frame.columns:
        if "phase" in frame.columns:
            frame["opening"] = frame["phase"].fillna("unknown").astype(str)
        else:
            frame["opening"] = "unknown"

    if "score_cp" not in frame.columns and "score_diff" in frame.columns:
        frame["score_cp"] = frame["score_diff"]

    if "king_safety" not in frame.columns:
        if {"self_mobility", "opponent_mobility"}.issubset(frame.columns):
            frame["king_safety"] = frame["self_mobility"] - frame["opponent_mobility"]
        else:
            frame["king_safety"] = 0

    if "center_control" not in frame.columns and "branching_factor" in frame.columns:
        frame["center_control"] = frame["branching_factor"]

    if "mate_in" not in frame.columns:
        frame["mate_in"] = 0

    if "depth_score_diff" not in frame.columns:
        frame["depth_score_diff"] = 0

    return frame


def prepare_feature_frame(
    dataset: pd.DataFrame,
    *,
    target_column: str = "error_label",
    target_classes: tuple[str, ...] = ("good", "inaccuracy", "mistake", "blunder"),
) -> pd.DataFrame:
    if dataset.empty:
        return dataset.copy()

    frame = dataset.copy()
    frame = frame.dropna(subset=[target_column])
    frame = frame[frame[target_column].isin(target_classes)].copy()
    frame = exclude_sources(frame)
    frame = ensure_chess_feature_columns(frame)

    if "player_elo" not in frame.columns:
        if {"white_elo", "black_elo", "player_color"}.issubset(frame.columns):
            frame["player_elo"] = derive_player_elo(frame)
        elif "elo" in frame.columns:
            frame["player_elo"] = pd.to_numeric(frame["elo"], errors="coerce")
        else:
            frame["player_elo"] = pd.NA

    frame["player_elo"] = pd.to_numeric(frame["player_elo"], errors="coerce")
    frame["elo_band"] = derive_elo_band(frame["player_elo"])
    if "skill_group" in frame.columns:
        if "game_id" in frame.columns:
            frame["export_skill_group"] = frame.groupby("game_id")["skill_group"].transform("first")
        else:
            frame["export_skill_group"] = frame["skill_group"]
    frame["skill_group"] = derive_skill_group(frame["player_elo"])
    frame["skill_group_description"] = derive_skill_group_description(frame["skill_group"])

    if "time_control" in frame.columns:
        frame["time_control_seconds"] = frame["time_control"].map(parse_time_control_seconds)
    else:
        frame["time_control_seconds"] = pd.NA

    frame["time_control_bucket"] = frame["time_control_seconds"].map(derive_time_control_bucket)
    frame["opening"] = frame["opening"].fillna("unknown").astype(str)

    numeric_columns = [
        "move_number",
        "player_elo",
        "material_total",
        "num_pieces",
        "king_safety",
        "center_control",
        "score_cp",
        "mate_in",
        "depth_score_diff",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    for column in ("king_safety", "center_control"):
        if column in frame.columns:
            frame[column] = frame[column].fillna(0)

    for column in ("has_castling_rights", "is_pawn_endgame"):
        if column in frame.columns:
            frame[column] = frame[column].fillna(False).astype(int)

    frame["mate_in"] = frame["mate_in"].fillna(0)
    frame["depth_score_diff"] = frame["depth_score_diff"].fillna(0)

    frame = frame[
        frame["player_elo"].between(PLAYER_ELO_MIN, PLAYER_ELO_MAX, inclusive="both")
    ].copy()
    frame = frame.dropna(subset=["time_control_bucket"]).copy()
    frame = frame.dropna(
        subset=[
            "move_number",
            "player_elo",
            "material_total",
            "num_pieces",
            "king_safety",
            "center_control",
            "score_cp",
        ]
    )
    return frame.reset_index(drop=True)


def encode_training_features(dataset: pd.DataFrame) -> pd.DataFrame:
    frame = dataset.copy()
    categorical_columns = [
        column
        for column in ("opening", "time_control_bucket")
        if column in frame.columns
    ]
    encoded = pd.get_dummies(frame, columns=categorical_columns, prefix=categorical_columns)

    drop_columns = [
        column
        for column in (
            "source",
            "elo_band",
            "skill_group",
            "skill_group_description",
            "export_skill_group",
            "time_control",
            "time_control_seconds",
            "white_elo",
            "black_elo",
            "player_color",
            "elo",
        )
        if column in encoded.columns
    ]
    return encoded.drop(columns=drop_columns).reset_index(drop=True)


def build_quality_report(
    dataset: pd.DataFrame,
    *,
    target_column: str = "error_label",
    min_rows_for_distribution_checks: int = 1000,
) -> QualityReport:
    if dataset.empty:
        return QualityReport(row_count=0, game_count=0, failures=["Dataset is empty"])

    report = QualityReport(
        row_count=len(dataset),
        game_count=int(dataset["game_id"].nunique()) if "game_id" in dataset.columns else len(dataset),
    )

    label_counts = dataset[target_column].value_counts(normalize=True)
    report.label_distribution = {key: float(value) for key, value in label_counts.items()}

    good_share = report.label_distribution.get("good", 0.0)
    blunder_share = report.label_distribution.get("blunder", 0.0)
    if good_share > MAX_GOOD_SHARE:
        report.failures.append(
            f"'good' share is {good_share:.1%}; expected below {MAX_GOOD_SHARE:.0%}"
        )
    if blunder_share < MIN_BLUNDER_SHARE:
        report.failures.append(
            f"'blunder' share is {blunder_share:.1%}; expected at least {MIN_BLUNDER_SHARE:.0%}"
        )

    if "source" in dataset.columns and "game_id" in dataset.columns:
        source_games = dataset.groupby("source")["game_id"].nunique()
        total_games = source_games.sum()
        if total_games > 0:
            report.source_game_distribution = {
                key: float(value / total_games) for key, value in source_games.items()
            }

    if len(dataset) >= min_rows_for_distribution_checks and "game_id" in dataset.columns:
        quota_column = (
            "export_skill_group"
            if "export_skill_group" in dataset.columns
            else "skill_group"
        )
        if quota_column in dataset.columns:
            skill_counts = dataset.groupby("game_id")[quota_column].first().value_counts()
            report.skill_group_game_counts = {
                str(key): int(value) for key, value in skill_counts.items()
            }
            report.skill_group_game_distribution = {
                str(key): float(value / report.game_count)
                for key, value in skill_counts.items()
            }
            report.import_completion_ratio = report.game_count / COURSE_TARGET_GAME_COUNT
            report.import_complete = report.import_completion_ratio >= IMPORT_COMPLETION_THRESHOLD

            if not report.import_complete:
                report.warnings.append(
                    f"Import appears incomplete: {report.game_count:,} / "
                    f"{COURSE_TARGET_GAME_COUNT:,} target games "
                    f"({report.import_completion_ratio:.1%})"
                )

            for group, quota in COURSE_SKILL_GROUP_GAME_QUOTAS.items():
                actual_count = report.skill_group_game_counts.get(group, 0)
                target_share = quota / COURSE_TARGET_GAME_COUNT
                actual_share = report.skill_group_game_distribution.get(group, 0.0)
                count_drift = abs(actual_count - quota) / quota if quota else 0.0

                if actual_count > quota * (1 + SKILL_GROUP_TOLERANCE):
                    report.failures.append(
                        f"Export skill group '{group}' has {actual_count:,} games; "
                        f"quota is {quota:,} (+{SKILL_GROUP_TOLERANCE:.0%} max)"
                    )
                    continue

                if report.import_complete:
                    if count_drift > SKILL_GROUP_TOLERANCE:
                        report.failures.append(
                            f"Export skill group '{group}' has {actual_count:,} games; "
                            f"quota is {quota:,} ({actual_share:.1%} of dataset)"
                        )
                    elif count_drift > SKILL_GROUP_TOLERANCE * 0.75:
                        report.warnings.append(
                            f"Export skill group '{group}' has {actual_count:,} games; "
                            f"quota is {quota:,} (target share {target_share:.1%})"
                        )
                elif actual_count < quota * 0.85:
                    report.warnings.append(
                        f"Export skill group '{group}' has {actual_count:,} / {quota:,} games "
                        f"(batch may be missing)"
                    )

        if "time_control_bucket" in dataset.columns:
            bucket_games = dataset.groupby("game_id")["time_control_bucket"].first().value_counts(normalize=True)
            report.time_control_game_distribution = {
                key: float(value) for key, value in bucket_games.items()
            }
            for bucket, target in TIME_CONTROL_TARGET_SHARES.items():
                actual = report.time_control_game_distribution.get(bucket, 0.0)
                if actual == 0.0:
                    report.warnings.append(
                        f"Time control bucket '{bucket}' has no games (target {target:.0%})"
                    )
                elif abs(actual - target) > TIME_CONTROL_WARNING_TOLERANCE:
                    report.warnings.append(
                        f"Time control bucket '{bucket}' is {actual:.1%}; "
                        f"target {target:.0%} ± {TIME_CONTROL_WARNING_TOLERANCE:.0%}"
                    )

        if "elo_band" in dataset.columns:
            elo_games = dataset.groupby("game_id")["elo_band"].first().value_counts(normalize=True)
            report.elo_band_game_distribution = {
                str(key): float(value) for key, value in elo_games.items()
            }

    return report


def validate_dataset_quality(
    dataset: pd.DataFrame,
    *,
    target_column: str = "error_label",
    min_rows_for_distribution_checks: int = 1000,
) -> dict:
    report = build_quality_report(
        dataset,
        target_column=target_column,
        min_rows_for_distribution_checks=min_rows_for_distribution_checks,
    )
    payload = report.to_dict()
    if report.failures:
        raise DatasetQualityError(payload)
    return payload
