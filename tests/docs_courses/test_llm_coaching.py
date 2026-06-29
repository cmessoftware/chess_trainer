"""Tests for Module 6.5 LLM coaching pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.context_builder import build_coaching_context, validate_coaching_context
from coaching.human_brief import build_verbal_game_brief
from coaching.pattern_engine import PatternObservation, detect_patterns_for_row
from coaching.prompt_builder import (
    build_coaching_prompt,
    build_single_game_coaching_prompt,
    prepare_single_game_brief_for_llm,
    prompt_contains_forbidden_jargon,
)
from llm.dry_run_provider import DryRunProvider
from llm.provider_factory import create_provider
from llm.settings import LLMSettings


def test_create_provider_without_api_key_uses_dry_run():
    settings = LLMSettings(provider="gemini", model="gemini-2.5-flash", api_key="")
    provider = create_provider(settings)
    assert isinstance(provider, DryRunProvider)
    text = provider.generate("hello")
    assert "MODO LOCAL" in text


def test_create_provider_unsupported_raises():
    settings = LLMSettings(provider="openai", model="gpt-4", api_key="x")
    with pytest.raises(ValueError, match="Unsupported"):
        create_provider(settings)


def test_context_schema_has_no_forbidden_fields():
    observations = [
        PatternObservation("unsafe_king", 0.8, "high", "King safety is weak."),
        PatternObservation("low_mobility", 0.6, "medium", "Limited mobility."),
    ]
    rows = pd.DataFrame(
        {
            "player_elo": [1450, 1470],
            "king_safety": [-2, -1],
            "self_mobility": [4, 5],
            "opening_French Defense": [1, 0],
            "error_label": ["mistake", "blunder"],
        }
    )
    context = build_coaching_context(
        pattern_observations=observations,
        sample_rows=rows,
        sample_labels=rows["error_label"],
        player_name="cmess1315",
        analysis_scope="player_profile_sample",
        games_analyzed=[
            {
                "game_id": "g1",
                "opponent": "rival",
                "result": "1-0",
                "player_moves_analyzed": 2,
            }
        ],
    )
    validate_coaching_context(context)
    assert "dominant_patterns" in context
    assert context["dominant_patterns"][0]["pattern"] == "unsafe_king"
    assert "shap" not in json.dumps(context).lower()


def test_forbidden_context_field_rejected():
    with pytest.raises(ValueError, match="Forbidden"):
        validate_coaching_context({"score_cp": 120})


def test_prompt_includes_context_not_shap_jargon():
    context = {
        "player_elo": 1500,
        "dominant_patterns": [{"pattern": "unsafe_king", "count": 3}],
        "trend": "stable",
        "sample_classes": {"mistake": 0.2},
        "top_openings": ["French Defense"],
        "total_moves_analyzed": 5,
        "games_count": 1,
        "games_analyzed": [
            {
                "game_id": "game_001",
                "opponent": "Opponent",
                "result": "1-0",
                "player_moves_analyzed": 5,
            }
        ],
        "player_name": "cmess1315",
        "analysis_scope": "single_game",
    }
    prompt = build_coaching_prompt(context)
    assert "unsafe_king" in prompt
    assert "French Defense" in prompt
    assert "español" in prompt.lower()
    assert not prompt_contains_forbidden_jargon(prompt)


def test_load_course_env_reads_repo_dotenv(tmp_path, monkeypatch):
    import llm.settings as settings_module

    settings_module._ENV_LOADED = False
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test-key-from-dotenv\n", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    loaded = settings_module.load_course_env(env_file=env_file)
    assert loaded == env_file.resolve()

    llm_settings = settings_module.load_llm_settings()
    assert llm_settings.api_key == "test-key-from-dotenv"
    assert llm_settings.has_api_key


def test_single_game_prompt_is_verbal_and_names_opponent():
    brief = build_verbal_game_brief(
        game_summary={
            "game_id": "g1",
            "opponent": "HaseebNurul",
            "result": "0-1",
            "opening": "French Defense",
            "player_moves_analyzed": 40,
        },
        pattern_observations=[
            PatternObservation("unsafe_king", 0.8, "high", ""),
            PatternObservation("unsafe_king", 0.7, "high", ""),
        ],
        sample_labels=pd.Series(["good"] * 30 + ["mistake"] * 10),
        player_name="cmess1315",
    )
    prompt = build_single_game_coaching_prompt(brief)
    assert "HaseebNurul" in prompt
    assert "cmess1315" in prompt
    assert "no uses [alumno]" in prompt.lower()
    assert "critical_moves" in prompt
    assert "CONTROL RULES" in prompt
    assert "player_move" in prompt
    assert "lesson_clusters" in prompt
    assert "Responde SIEMPRE en español" in prompt
    assert "recurring_themes" not in prompt
    assert '"move"' not in prompt or "player_move" in prompt
    assert not prompt_contains_forbidden_jargon(prompt)


def test_prepare_single_game_brief_normalizes_v3_contract():
    prepared = prepare_single_game_brief_for_llm(
        {
            "focus": "single_game_review",
            "language": "es",
            "player": "p1",
            "game": {"opponent": "rival"},
            "recurring_themes": ["unsafe_king"],
            "critical_moves": [
                {
                    "move_number": 21,
                    "move": "21. c4",
                    "phase": "middlegame",
                    "severity": "blunder",
                    "root_cause": True,
                    "pattern": "undefended_pawn",
                    "concept": "peón indefenso",
                    "lesson": "defiende antes de empujar",
                    "context_pgn": "1. e4 e6",
                    "tactical_line": "21... Nxe5",
                    "diagnosis_type": "tactical",
                    "concepts": ["legacy"],
                }
            ],
        }
    )
    assert "recurring_themes" not in prepared
    moment = prepared["critical_moves"][0]
    assert moment["player_move"] == "21. c4"
    assert moment["issue"] == "peón indefenso"
    assert moment["lesson_hint"] == "defiende antes de empujar"
    assert moment["opponent_reply"] == "21... Nxe5"
    assert "move" not in moment
    assert "concepts" not in moment
    assert "lesson_clusters" in prepared
    assert len(prepared["lesson_clusters"]) >= 1


def test_profile_prompt_in_spanish():
    context = {
        "player_name": "cmess1315",
        "games_count": 2,
        "total_moves_analyzed": 100,
        "dominant_patterns": [{"pattern": "unsafe_king", "count": 3}],
    }
    prompt = build_coaching_prompt(context)
    assert "Responde SIEMPRE en español" in prompt
    assert "Sin porcentajes" in prompt


def test_pattern_engine_unsafe_king():
    row = pd.Series({"king_safety": -3, "self_mobility": 12, "move_number": 20})
    explanation = {
        "predicted_label": "mistake",
        "top_positive_features": [{"feature": "king_safety", "impact": 0.12}],
        "top_negative_features": [],
    }
    patterns = detect_patterns_for_row(row, explanation)
    names = {pattern.pattern_name for pattern in patterns}
    assert "unsafe_king" in names
