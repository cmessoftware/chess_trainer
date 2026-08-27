"""
Analysis modules for chess training.

This package contains analysis tools for chess game evaluation,
including survivorship bias detection and other advanced analytics.

Module 07 course code lives in docs/ai_chess_coach_course/analysis/.
That directory is appended to this package's __path__ so notebooks that
import `analysis` via src/ still resolve position_extractor and mental_model.
"""

import sys
from pathlib import Path

from .survivorship_bias import SurvivorshipBiasAnalyzer

_COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
_COURSE_ANALYSIS = _COURSE_ROOT / "analysis"
if _COURSE_ROOT.is_dir() and str(_COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_COURSE_ROOT))
if _COURSE_ANALYSIS.is_dir():
    __path__.append(str(_COURSE_ANALYSIS))

from .position_extractor import (  # noqa: E402
    import_game_from_file,
    import_game_from_pgn,
    load_game_from_db,
)

__all__ = [
    "SurvivorshipBiasAnalyzer",
    "import_game_from_file",
    "import_game_from_pgn",
    "load_game_from_db",
]
