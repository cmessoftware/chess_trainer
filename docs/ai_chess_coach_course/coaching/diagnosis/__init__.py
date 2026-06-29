"""V4 diagnosis engine — structured chess understanding before LLM."""

from coaching.diagnosis.engine import DiagnosisEngine, DEFAULT_DETECTORS
from coaching.diagnosis.models import PatternMatch, StructuredDiagnosis

__all__ = [
    "DEFAULT_DETECTORS",
    "DiagnosisEngine",
    "PatternMatch",
    "StructuredDiagnosis",
]
