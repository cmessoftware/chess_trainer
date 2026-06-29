"""Debug artifact writers for Gemini coaching (V3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_coaching_debug_artifacts(
    debug_dir: str | Path,
    *,
    prompt: str,
    llm_payload: dict[str, Any],
) -> None:
    """Persist exact prompt and payload immediately before an LLM call."""
    root = Path(debug_dir)
    root.mkdir(parents=True, exist_ok=True)

    critical_moves = llm_payload.get("critical_moves") or []
    (root / "prompt_final_sent_to_gemini.txt").write_text(prompt, encoding="utf-8")
    (root / "critical_moves_payload.json").write_text(
        json.dumps(critical_moves, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "full_llm_payload.json").write_text(
        json.dumps(llm_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_gemini_response_artifact(
    debug_dir: str | Path,
    *,
    response_text: str,
    validation_ok: bool,
) -> None:
    root = Path(debug_dir)
    root.mkdir(parents=True, exist_ok=True)
    suffix = "valid" if validation_ok else "rejected"
    (root / f"gemini_response_{suffix}.txt").write_text(response_text, encoding="utf-8")
