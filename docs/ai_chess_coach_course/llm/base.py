"""LLM provider abstraction for Module 6.5."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return model text for the given prompt."""
