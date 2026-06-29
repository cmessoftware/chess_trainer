"""Gemini API error helpers."""

from __future__ import annotations

import re


class GeminiQuotaError(RuntimeError):
    """Raised when Gemini free-tier or rate quota is exhausted."""


def is_quota_error(exc: BaseException) -> bool:
    message = str(exc)
    return "429" in message or "RESOURCE_EXHAUSTED" in message or "quota" in message.lower()


def parse_retry_seconds(exc: BaseException, *, default: float = 30.0) -> float:
    match = re.search(r"retry in ([0-9.]+)s", str(exc), flags=re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.0
    return default


def quota_user_message(exc: BaseException) -> str:
    text = str(exc)
    if "FreeTier" in text or "free_tier" in text:
        return (
            "Cuota gratuita de Gemini agotada (p. ej. 20 solicitudes/día en gemini-2.5-flash). "
            "Espera al reinicio diario, activa facturación en Google AI Studio, "
            "o ejecuta solo una celda LLM por sesión."
        )
    if "Please retry in" in text:
        seconds = int(parse_retry_seconds(exc))
        return f"Límite de velocidad de Gemini alcanzado. Reintenta en ~{seconds} segundos."
    return "Cuota o límite de Gemini alcanzado. Revisa https://ai.google.dev/gemini-api/docs/rate-limits"
