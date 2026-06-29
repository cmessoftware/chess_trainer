"""Normalize tactical tags from SQLite / parquet feature rows."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

IGNORED_TAGS = frozenset({"normal", "none", "", "phase"})

MATERIAL_TAGS = frozenset(
    {
        "piece_lost",
        "exchange_lost",
        "queen_lost",
        "rook_lost",
        "hanging_piece",
    }
)


def parse_tags(raw: object) -> list[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []

    tags = raw
    if isinstance(tags, str):
        text = tags.strip()
        if not text:
            return []
        try:
            tags = json.loads(text)
        except json.JSONDecodeError:
            return [text.lower().replace(" ", "_")]

    if isinstance(tags, dict):
        collected: list[str] = []
        for key, value in tags.items():
            key_text = str(key).lower().replace(" ", "_")
            if value in (True, 1, "1", "true") or (isinstance(value, str) and value.strip()):
                collected.append(key_text)
            if isinstance(value, list):
                collected.extend(str(item).lower().replace(" ", "_") for item in value)
        return _dedupe(collected)

    if isinstance(tags, list):
        return _dedupe(str(item).lower().replace(" ", "_") for item in tags if item)

    return [str(tags).lower().replace(" ", "_")]


def parse_tags_from_row(row: pd.Series) -> list[str]:
    if "tags" not in row.index:
        return []
    return parse_tags(row.get("tags"))


def _dedupe(items: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = str(item).strip().lower().replace(" ", "_")
        if not normalized or normalized in IGNORED_TAGS or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def primary_tactical_tag(tags: list[str]) -> str | None:
    priority = (
        "mate",
        "mate_threat",
        "fork",
        "skewer",
        "pin",
        "discovered_attack",
        "discovered_check",
        "double_attack",
        "hanging_piece",
        "remove_defender",
        "back_rank",
        "passed_pawn",
        "promotion",
        "check",
    )
    tag_set = set(tags)
    for candidate in priority:
        if candidate in tag_set:
            return candidate
    return tags[0] if tags else None
