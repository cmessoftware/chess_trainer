from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvaluationResult:
    model_name: str
    accuracy: float


def summarize_metrics(model_name: str, accuracy: float) -> EvaluationResult:
    return EvaluationResult(model_name=model_name, accuracy=accuracy)
