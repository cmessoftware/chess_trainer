from __future__ import annotations

from .prompt_templates import BASE_EXPLANATION_PROMPT


def build_prompt(prediction: str, patterns: str, retrieved_context: str) -> str:
    return BASE_EXPLANATION_PROMPT.format(
        prediction=prediction,
        patterns=patterns,
        retrieved_context=retrieved_context,
    )
