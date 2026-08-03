"""Factory for LLM providers."""

from __future__ import annotations

import os

from llm.base import LLMProvider
from llm.dry_run_provider import DryRunProvider
from llm.gemini_provider import GeminiProvider
from llm.openai_compatible_provider import OpenAICompatibleProvider
from llm.resilient_provider import ResilientProvider
from llm.settings import LLMSettings


def _wrap_resilient(inner: LLMProvider) -> LLMProvider:
    if os.getenv("LLM_FALLBACK_ON_QUOTA", "true").strip().lower() in {"0", "false", "no"}:
        return inner
    return ResilientProvider(inner)


def create_provider(settings: LLMSettings) -> LLMProvider:
    if not settings.has_api_key:
        return DryRunProvider()

    if settings.provider == "gemini":
        max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
        inner = GeminiProvider(settings.api_key, model=settings.model, max_retries=max_retries)
        return _wrap_resilient(inner)

    if settings.provider in {"deepseek", "openai", "openai_compatible"}:
        inner = OpenAICompatibleProvider(
            settings.api_key,
            model=settings.model,
            base_url=settings.base_url or "https://api.deepseek.com",
            temperature=settings.temperature,
        )
        return _wrap_resilient(inner)

    raise ValueError(
        f"Unsupported LLM provider {settings.provider!r}. "
        "Supported: gemini, deepseek, openai, openai_compatible."
    )
