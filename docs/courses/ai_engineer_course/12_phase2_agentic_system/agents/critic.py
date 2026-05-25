from __future__ import annotations


def validate_explanation(explanation: str) -> bool:
    return bool(explanation and explanation.strip())
