"""Pattern detector interface (V4)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from coaching.diagnosis.models import DiagnosisContext, PatternMatch


class PatternDetector(ABC):
    pattern_id: str

    @abstractmethod
    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        ...
