"""Notebook bootstrap for 07.0 — avoids colliding with src/analysis."""

from __future__ import annotations

import sys
from pathlib import Path


def course_root() -> Path:
    here = Path.cwd().resolve()
    candidates = [
        here,
        here / "docs" / "ai_chess_coach_course",
        Path(__file__).resolve().parent,
    ]
    for candidate in candidates:
        if (candidate / "analysis" / "position_extractor.py").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find course analysis/position_extractor.py. "
        "Open the notebook from docs/ai_chess_coach_course or the repo root."
    )


def prepare_sys_path(root: Path | None = None) -> Path:
    root = root or course_root()
    src_dir = root.parents[1] / "src"
    cleaned = []
    seen = {str(root)}
    cleaned.append(str(root))
    for entry in sys.path:
        resolved = Path(entry).resolve() if entry else None
        if resolved == src_dir:
            continue
        if entry in seen:
            continue
        seen.add(entry)
        cleaned.append(entry)
    sys.path[:] = cleaned

    for key in list(sys.modules):
        if key != "analysis" and not key.startswith("analysis."):
            continue
        loaded = sys.modules[key]
        loaded_file = Path(getattr(loaded, "__file__", "") or "")
        try:
            loaded_file.relative_to(root / "analysis")
        except ValueError:
            del sys.modules[key]
    return root
