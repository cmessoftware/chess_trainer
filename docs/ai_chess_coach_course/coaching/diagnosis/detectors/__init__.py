"""Pattern detectors for V4 diagnosis."""

from coaching.diagnosis.detectors.positional import KingSafetyDetector, PassiveRookDetector
from coaching.diagnosis.detectors.tactical import (
    ForkDetector,
    HangingPieceDetector,
    LoosePieceAfterPawnPushDetector,
    PinDetector,
    SkewerDetector,
    UndefendedPawnDetector,
)

__all__ = [
    "ForkDetector",
    "HangingPieceDetector",
    "KingSafetyDetector",
    "LoosePieceAfterPawnPushDetector",
    "PassiveRookDetector",
    "PinDetector",
    "SkewerDetector",
    "UndefendedPawnDetector",
]
