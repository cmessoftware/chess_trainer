"""V3 LLM contract for critical_moves (player vs opponent, validation)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

REQUIRED_LLM_FIELDS = (
    "move_number",
    "player_move",
    "phase",
    "severity",
    "issue",
    "lesson_hint",
    "context_pgn",
)

OPTIONAL_LLM_FIELDS = (
    "opponent_reply",
    "pattern",
    "consequence",
    "root_cause",
    "material_change",
    "tactical_motif",
    "affected_piece",
    "strategic_theme",
    "opened_file",
    "weak_square",
    "secondary_patterns",
    "theme",
    "supporting_features",
    "diagnosis_type",
    "sections",
)

DEPRECATED_LLM_FIELDS = ("move", "tactical_line", "concept", "lesson", "consequence_moves")

_OPPONENT_REPLY_PATTERN = re.compile(r"(\d+\.\.\.\s*\S+)")


def extract_opponent_reply(tactical_line: str | None) -> str | None:
    if not tactical_line or not str(tactical_line).strip():
        return None
    match = _OPPONENT_REPLY_PATTERN.search(str(tactical_line))
    if match:
        return match.group(1)
    parts = str(tactical_line).split()
    return parts[0] if parts else None


def normalize_critical_move_for_llm(moment: dict[str, Any]) -> dict[str, Any]:
    """Map internal RCA moment → strict V3 payload for Gemini."""
    player_move = moment.get("player_move") or moment.get("move")
    opponent_reply = moment.get("opponent_reply") or extract_opponent_reply(
        moment.get("tactical_line")
    )
    issue = moment.get("issue") or moment.get("concept") or ""
    lesson_hint = moment.get("lesson_hint") or moment.get("lesson") or ""

    normalized: dict[str, Any] = {
        "move_number": int(moment["move_number"]),
        "player_move": str(player_move),
        "phase": moment.get("phase"),
        "severity": moment.get("severity"),
        "issue": str(issue),
        "lesson_hint": str(lesson_hint),
        "context_pgn": str(moment.get("context_pgn") or ""),
    }
    if opponent_reply:
        normalized["opponent_reply"] = opponent_reply
    if moment.get("diagnosis_type") != "tactical":
        normalized.pop("opponent_reply", None)
    if moment.get("pattern"):
        normalized["pattern"] = moment["pattern"]
    if moment.get("consequence"):
        normalized["consequence"] = moment["consequence"]
    if moment.get("root_cause") is not None:
        normalized["root_cause"] = bool(moment["root_cause"])
    for optional in (
        "material_change",
        "tactical_motif",
        "affected_piece",
        "strategic_theme",
        "opened_file",
        "weak_square",
        "secondary_patterns",
        "theme",
        "supporting_features",
        "diagnosis_type",
        "sections",
    ):
        if moment.get(optional) not in (None, "", []):
            normalized[optional] = moment[optional]
    return normalized


@dataclass
class CriticalMovesValidation:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_critical_moves(
    critical_moves: list[dict[str, Any]] | None,
    *,
    strict: bool = True,
) -> CriticalMovesValidation:
    result = CriticalMovesValidation(ok=True)
    if critical_moves is None:
        result.ok = False
        result.errors.append("critical_moves is None")
        return result
    if len(critical_moves) == 0:
        result.ok = False
        result.errors.append("critical_moves is empty")
        return result

    for index, moment in enumerate(critical_moves):
        prefix = f"critical_moves[{index}]"
        for deprecated in DEPRECATED_LLM_FIELDS:
            if deprecated in moment:
                result.warnings.append(f"{prefix}: deprecated field '{deprecated}' present")
        for required in REQUIRED_LLM_FIELDS:
            if required not in moment or moment[required] in (None, ""):
                result.ok = False
                result.errors.append(f"{prefix}: missing required field '{required}'")
        if "move" in moment and strict:
            result.ok = False
            result.errors.append(f"{prefix}: ambiguous field 'move' must not be sent to LLM")

    return result
