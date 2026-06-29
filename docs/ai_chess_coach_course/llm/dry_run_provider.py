"""Placeholder LLM for notebooks and CI when no API key is configured."""

from __future__ import annotations

from llm.base import LLMProvider


class DryRunProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return (
            "[MODO LOCAL — sin llamada a Gemini]\n\n"
            "Configura GEMINI_API_KEY en el .env del repo para respuestas reales.\n"
            "El pipeline (partida completa, momentos críticos, context_pgn) sigue funcionando."
        )
