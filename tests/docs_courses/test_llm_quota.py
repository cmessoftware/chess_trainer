"""Tests for Gemini quota handling."""

from __future__ import annotations

import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from llm.base import LLMProvider
from llm.errors import GeminiQuotaError, parse_retry_seconds, quota_user_message
from llm.generate import generate_coaching_text


class _QuotaFailProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        raise GeminiQuotaError("429 RESOURCE_EXHAUSTED free_tier_requests FreeTier")


def test_quota_user_message_in_spanish():
    msg = quota_user_message(GeminiQuotaError("FreeTier limit 20"))
    assert "Cuota gratuita" in msg


def test_parse_retry_seconds():
    assert parse_retry_seconds(GeminiQuotaError("Please retry in 27.25s.")) >= 28


def test_generate_coaching_text_fallback_on_quota():
    text, warning = generate_coaching_text(
        "prompt de prueba",
        provider=_QuotaFailProvider(),
        fallback_on_quota=True,
    )
    assert warning is not None
    assert "GEMINI NO DISPONIBLE" in text
    assert "prompt de prueba" in text
