"""Orchestrate V3 single-game coaching: validate → prompt → optional LLM → fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from coaching.coaching_debug import save_coaching_debug_artifacts, save_gemini_response_artifact
from coaching.coaching_validation import validate_coaching_response
from coaching.critical_move_contract import (
    CriticalMovesValidation,
    normalize_critical_move_for_llm,
    validate_critical_moves,
)
from coaching.deterministic_coaching import render_deterministic_coaching
from coaching.prompt_builder import build_single_game_coaching_prompt, prepare_single_game_brief_for_llm
from llm.base import LLMProvider
from llm.generate import generate_coaching_text
from llm.settings import LLMSettings


def generate_single_game_coaching(
    brief: dict[str, Any],
    *,
    settings: LLMSettings | None = None,
    provider: LLMProvider | None = None,
    debug_dir: str | Path | None = None,
    invoke_llm: bool = False,
) -> tuple[str, str | None, dict[str, Any]]:
    """
    Build validated coaching text for one game.

    When invoke_llm is False (default), returns deterministic coaching only.
    When invoke_llm is True, calls Gemini then validates; falls back to deterministic
    text if validation fails (no automatic retry — saves quota).
    """
    llm_payload = prepare_single_game_brief_for_llm(brief)
    validation = validate_critical_moves(llm_payload.get("critical_moves"))
    if not validation.ok:
        raise ValueError(
            "critical_moves validation failed:\n"
            + "\n".join(f"- {item}" for item in validation.errors)
        )

    prompt = build_single_game_coaching_prompt(brief)
    meta: dict[str, Any] = {
        "validation": validation,
        "llm_invoked": False,
        "used_deterministic_fallback": False,
    }

    if debug_dir is not None:
        save_coaching_debug_artifacts(debug_dir, prompt=prompt, llm_payload=llm_payload)
        meta["debug_dir"] = str(Path(debug_dir))

    deterministic = render_deterministic_coaching(
        llm_payload.get("game") or {},
        llm_payload.get("critical_moves") or [],
        player=llm_payload.get("player"),
    )

    if not invoke_llm:
        meta["used_deterministic_fallback"] = True
        return deterministic, None, meta

    meta["llm_invoked"] = True
    text, quota_warning = generate_coaching_text(prompt, settings, provider=provider)
    allowed_context = json.dumps(llm_payload.get("critical_moves") or [], ensure_ascii=False)
    response_validation = validate_coaching_response(
        text,
        llm_payload.get("critical_moves") or [],
        allowed_context=allowed_context,
    )
    if debug_dir is not None:
        save_gemini_response_artifact(
            debug_dir,
            response_text=text,
            validation_ok=response_validation.ok,
        )
    meta["response_validation"] = {
        "ok": response_validation.ok,
        "errors": response_validation.errors,
        "warnings": response_validation.warnings,
        "extra_move_numbers": sorted(response_validation.extra_move_numbers),
    }

    if response_validation.ok and not text.startswith("[GEMINI NO DISPONIBLE"):
        return text, quota_warning, meta

    meta["used_deterministic_fallback"] = True
    fallback_note = None
    if response_validation.errors:
        fallback_note = (
            "Respuesta Gemini no pasó validación V7; se usó resumen determinista.\n"
            + "\n".join(response_validation.errors)
        )
    elif quota_warning:
        fallback_note = quota_warning

    return deterministic, fallback_note or quota_warning, meta
