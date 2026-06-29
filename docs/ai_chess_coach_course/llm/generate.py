"""Safe generation with quota fallback for course notebooks."""

from __future__ import annotations

import os

from llm.base import LLMProvider
from llm.dry_run_provider import DryRunProvider
from llm.errors import GeminiQuotaError, quota_user_message
from llm.settings import LLMSettings, load_llm_settings


def _fallback_on_quota_enabled() -> bool:
    value = os.getenv("LLM_FALLBACK_ON_QUOTA", "true").strip().lower()
    return value not in {"0", "false", "no"}


def generate_coaching_text(
    prompt: str,
    settings: LLMSettings | None = None,
    *,
    provider: LLMProvider | None = None,
    fallback_on_quota: bool | None = None,
) -> tuple[str, str | None]:
    """
    Call the LLM and return (text, warning).

    On quota errors, returns a Spanish placeholder instead of raising
    when fallback_on_quota is True (default for the course).
    """
    resolved_settings = settings or load_llm_settings()
    if provider is None:
        from llm.provider_factory import create_provider

        llm = create_provider(resolved_settings)
    else:
        llm = provider
    use_fallback = _fallback_on_quota_enabled() if fallback_on_quota is None else fallback_on_quota

    try:
        return llm.generate(prompt), None
    except GeminiQuotaError as exc:
        if not use_fallback:
            raise
        warning = quota_user_message(exc)
        preview = prompt[:900].rstrip()
        if len(prompt) > 900:
            preview += "\n...(prompt truncado)..."
        return (
            "[GEMINI NO DISPONIBLE — cuota agotada]\n\n"
            f"{warning}\n\n"
            "El prompt se construyó correctamente. Cuando se restablezca la cuota, "
            "vuelve a ejecutar solo esta celda (no hace falta recomputar SHAP).\n\n"
            "--- Vista previa del prompt enviado ---\n"
            f"{preview}",
            warning,
        )
