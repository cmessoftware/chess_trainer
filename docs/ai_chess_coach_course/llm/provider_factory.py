"""Factory for LLM providers."""

from __future__ import annotations

import os

from llm.base import LLMProvider
from llm.dry_run_provider import DryRunProvider
from llm.gemini_provider import GeminiProvider
from llm.resilient_provider import ResilientProvider
from llm.settings import LLMSettings


def create_provider(settings: LLMSettings) -> LLMProvider:
    if settings.provider == "gemini":
        if not settings.has_api_key:
            return DryRunProvider()
        max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
        inner = GeminiProvider(settings.api_key, model=settings.model, max_retries=max_retries)
        if os.getenv("LLM_FALLBACK_ON_QUOTA", "true").strip().lower() in {"0", "false", "no"}:
            return inner
        return ResilientProvider(inner)
    raise ValueError(
        f"Unsupported LLM provider {settings.provider!r}. "
        "Module 6.5 supports provider='gemini' only."
    )
