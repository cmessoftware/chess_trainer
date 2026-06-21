"""Build competition feature frame from course SQLite."""

from __future__ import annotations

import json
import sys
from typing import Sequence

import numpy as np
import pandas as pd

from kaggle_package.config import (
    COURSE_ROOT,
    FEATURE_LOAD_COLUMNS,
    PUBLIC_FEATURE_COLUMNS,
    TACTICAL_TAG_VALUES,
    TARGET_CLASSES,
    TARGET_COLUMN,
)

if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository  # noqa: E402
from dataset.feature_engineering import prepare_feature_frame  # noqa: E402


DEFAULT_GAME_CHUNK_SIZE = 400


def _load_raw_competition_features(db_url: str, game_ids: Sequence[str]) -> pd.DataFrame:
    repository = CourseFeaturesRepository(db_url)
    ids = list(game_ids)
    if not ids:
        return pd.DataFrame()

    columns = list(FEATURE_LOAD_COLUMNS)
    if len(ids) <= DEFAULT_GAME_CHUNK_SIZE:
        return repository.load_features(columns=columns, game_ids=ids)

    chunks: list[pd.DataFrame] = []
    for start in range(0, len(ids), DEFAULT_GAME_CHUNK_SIZE):
        batch_ids = ids[start : start + DEFAULT_GAME_CHUNK_SIZE]
        chunks.append(repository.load_features(columns=columns, game_ids=batch_ids))
    return pd.concat(chunks, ignore_index=True)


def load_prepared_competition_features(
    db_url: str,
    game_ids: Sequence[str],
) -> pd.DataFrame:
    raw = _load_raw_competition_features(db_url, game_ids)

    if raw.empty:
        return raw

    from dataset.feature_engineering import parse_time_control_seconds  # noqa: E402
    import dataset.feature_engineering as feature_engineering  # noqa: E402

    cleaned = raw.copy()
    if "time_control" in cleaned.columns:
        tc_seconds = cleaned["time_control"].map(parse_time_control_seconds)
        cleaned = cleaned.loc[tc_seconds.notna()].copy()

    original_bucket_fn = feature_engineering.derive_time_control_bucket

    def _safe_time_control_bucket(seconds: object) -> str | None:
        if seconds is None:
            return None
        try:
            if pd.isna(seconds):
                return None
        except (TypeError, ValueError):
            return None
        return original_bucket_fn(seconds)

    feature_engineering.derive_time_control_bucket = _safe_time_control_bucket
    try:
        prepared = prepare_feature_frame(
            cleaned,
            target_column=TARGET_COLUMN,
            target_classes=TARGET_CLASSES,
        )
    finally:
        feature_engineering.derive_time_control_bucket = original_bucket_fn
    return prepared.reset_index(drop=True)


def _primary_tactical_tag(raw_tags: object) -> str:
    if raw_tags is None or (isinstance(raw_tags, float) and pd.isna(raw_tags)):
        return "normal"

    tags = raw_tags
    if isinstance(tags, str):
        text = tags.strip()
        if not text:
            return "normal"
        try:
            tags = json.loads(text)
        except json.JSONDecodeError:
            return text

    if isinstance(tags, list):
        if not tags:
            return "normal"
        return str(tags[0])

    return str(tags)


def attach_tactical_export_columns(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = frame.copy()
    if "tags" in enriched.columns:
        enriched["tactical_tag"] = enriched["tags"].map(_primary_tactical_tag)
    else:
        enriched["tactical_tag"] = "normal"

    for tag in TACTICAL_TAG_VALUES:
        enriched[f"tag_{tag}"] = (enriched["tactical_tag"] == tag).astype(int)

    return enriched


def assign_competition_ids(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.sort_values(["game_id", "move_number"]).reset_index(drop=True)
    ordered["id"] = np.arange(1, len(ordered) + 1, dtype=np.int64)
    return ordered


def to_public_export_frame(frame: pd.DataFrame, *, include_target: bool) -> pd.DataFrame:
    columns = ["id", *PUBLIC_FEATURE_COLUMNS]
    if include_target:
        columns.append(TARGET_COLUMN)

    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Prepared frame missing export columns: {missing}")

    export = frame[columns].copy()
    if "opening" in export.columns:
        export["opening"] = export["opening"].fillna("unknown").replace("", "unknown")
    for column in ("has_castling_rights", "is_pawn_endgame", "is_low_mobility", "is_center_controlled"):
        if column in export.columns:
            export[column] = export[column].fillna(0).astype(int)
    return export
