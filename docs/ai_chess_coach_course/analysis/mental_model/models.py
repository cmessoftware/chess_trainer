"""Data models for the human 1600 rapid mental decision flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DecisionMode(str, Enum):
    FAST = "fast"
    CRITICAL = "critical"


class HumanTriggerCode(str, Enum):
    """E1–E11 from algoritmo_posiciones_criticas_ajedrez.html"""

    FREE_MATERIAL = "E1"
    CHECK_CAPTURE_THREAT = "E2"
    UNEXPECTED_MOVE = "E3"
    PAWN_TEMPO = "E4"
    LINE_OPEN_CLOSE = "E5"
    PAWN_STRUCTURE = "E6"
    KING_ATTACK = "E7"
    TRAPPED_OVERLOADED = "E8"
    IRREVERSIBLE = "E9"
    MULTIPLE_CANDIDATES = "E10"
    EVAL_SHIFT = "E11"


class CandidateCategory(str, Enum):
    """D1–D5 from algoritmo_jugadas_candidatas_chessinsight.html"""

    FORCING = "D1"
    TACTICAL_THREAT = "D2"
    ACTIVE = "D3"
    PROPHYLACTIC = "D4"
    POSITIONAL = "D5"


class AntiBlunderCheck(str, Enum):
    S1_MAJOR_HANGING = "S1"
    S2_IN_CHECK = "S2"
    S3_OBVIOUS_CAPTURE = "S3"
    S4_LOST_DEFENDER = "S4"


@dataclass(frozen=True)
class HumanTrigger:
    code: HumanTriggerCode
    label_es: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ThinkingStep:
    node_id: str
    prompt_es: str
    phase: str


@dataclass
class DecisionAssessment:
    mode: DecisionMode
    pause_seconds: int
    triggers: list[HumanTrigger]
    thinking_plan: list[ThinkingStep]
    candidate_categories: list[CandidateCategory]
    anti_blunder_checks: list[AntiBlunderCheck]
    mapped_07_reasons: list[str]
    meta: dict[str, Any] = field(default_factory=dict)
