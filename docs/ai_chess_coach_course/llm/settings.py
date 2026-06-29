"""LLM configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

_COURSE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _COURSE_ROOT.parents[1]
_ENV_LOADED = False


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())


def load_course_env(*, env_file: str | Path | None = None) -> Path | None:
    """Load repo or course `.env` into os.environ (no override of existing vars)."""
    global _ENV_LOADED
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None

    if env_file is not None:
        candidate = Path(env_file)
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            _ENV_LOADED = True
            return candidate.resolve()
        return None

    loaded: Path | None = None
    for candidate in (_REPO_ROOT / ".env", _COURSE_ROOT / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            loaded = candidate.resolve()
    _ENV_LOADED = loaded is not None
    return loaded


def load_llm_settings(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    env_file: str | Path | None = None,
) -> LLMSettings:
    if not _ENV_LOADED:
        load_course_env(env_file=env_file)
    return LLMSettings(
        provider=(provider or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER)).lower(),
        model=model or os.getenv("LLM_MODEL", DEFAULT_GEMINI_MODEL),
        api_key=api_key if api_key is not None else os.getenv("GEMINI_API_KEY", ""),
    )
