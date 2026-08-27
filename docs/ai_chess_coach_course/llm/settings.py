"""LLM configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROVIDER = "deepseek"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"

_COURSE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _COURSE_ROOT.parents[1]
_ENV_LOADED = False


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str
    base_url: str = ""
    temperature: float = 0.4

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


def _resolve_api_key(explicit: str | None, provider: str) -> str:
    if explicit is not None:
        return explicit
    for env_name in ("LLM_API_KEY", f"{provider.upper()}_API_KEY"):
        value = os.getenv(env_name, "")
        if value.strip():
            return value
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY", "")
    if provider == "deepseek":
        return os.getenv("DEEPSEEK_API_KEY", "")
    return os.getenv("GEMINI_API_KEY", "")


def _default_model(provider: str) -> str:
    if provider == "gemini":
        return DEFAULT_GEMINI_MODEL
    if provider == "deepseek":
        return DEFAULT_DEEPSEEK_MODEL
    return os.getenv("LLM_MODEL", DEFAULT_DEEPSEEK_MODEL)


def _default_base_url(provider: str) -> str:
    explicit = os.getenv("LLM_BASE_URL", "").strip()
    if explicit:
        return explicit
    if provider == "deepseek":
        return DEFAULT_DEEPSEEK_BASE_URL
    return ""


def load_llm_settings(
    *,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float | None = None,
    env_file: str | Path | None = None,
) -> LLMSettings:
    if not _ENV_LOADED:
        load_course_env(env_file=env_file)
    resolved_provider = (provider or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER)).lower()
    resolved_model = model or os.getenv("LLM_MODEL") or _default_model(resolved_provider)
    resolved_temperature = (
        temperature
        if temperature is not None
        else float(os.getenv("LLM_TEMPERATURE", "0.4"))
    )
    return LLMSettings(
        provider=resolved_provider,
        model=resolved_model,
        api_key=_resolve_api_key(api_key, resolved_provider),
        base_url=(base_url if base_url is not None else _default_base_url(resolved_provider)),
        temperature=resolved_temperature,
    )
