"""Wraps LLM providers with quota-safe fallback."""

from __future__ import annotations

from llm.base import LLMProvider
from llm.generate import generate_coaching_text


class ResilientProvider(LLMProvider):
    def __init__(self, inner: LLMProvider) -> None:
        self._inner = inner

    def generate(self, prompt: str) -> str:
        text, _ = generate_coaching_text(prompt, provider=self._inner)
        return text
