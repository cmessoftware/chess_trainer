"""V5-lite diagnosis builder — tags + features + SHAP before LLM."""

from coaching.diagnosis_builder.builder import DiagnosisBuilder
from coaching.diagnosis_builder.classifier import classify_diagnosis_type
from coaching.diagnosis_builder.tactical_interpreter import TacticalInterpretation, interpret_tactical_tags

__all__ = [
    "DiagnosisBuilder",
    "TacticalInterpretation",
    "classify_diagnosis_type",
    "interpret_tactical_tags",
]
