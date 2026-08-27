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


def repo_root(start: Path | None = None) -> Path:
    """Repository root (directory that contains ``src/`` and usually ``.env``)."""
    start = (start or course_root()).resolve()
    for folder in [start, *start.parents]:
        if (folder / "src" / "db" / "database.py").is_file():
            return folder
    return start


def find_repo_env(start: Path | None = None) -> Path | None:
    root = repo_root(start)
    env_path = root / ".env"
    return env_path if env_path.is_file() else None


def load_repo_dotenv(start: Path | None = None, *, override: bool = True) -> Path | None:
    """Load repo ``.env`` so Jupyter sees ``CHESS_TRAINER_DB_URL``."""
    env_path = find_repo_env(start)
    if env_path is None:
        return None
    from dotenv import load_dotenv

    load_dotenv(env_path, override=override)
    return env_path


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
