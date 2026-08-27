"""Tests for OpenAI-compatible LLM provider (DeepSeek)."""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from llm.dry_run_provider import DryRunProvider
from llm.openai_compatible_provider import OpenAICompatibleProvider
from llm.provider_factory import create_provider
from llm.settings import LLMSettings, load_llm_settings


def test_create_deepseek_provider_without_api_key_uses_dry_run():
    settings = LLMSettings(provider="deepseek", model="deepseek-chat", api_key="")
    provider = create_provider(settings)
    assert isinstance(provider, DryRunProvider)


def test_load_llm_settings_reads_deepseek_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-deepseek")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    import llm.settings as settings_module

    settings_module._ENV_LOADED = True
    settings = load_llm_settings()
    assert settings.provider == "deepseek"
    assert settings.model == "deepseek-chat"
    assert settings.api_key == "sk-test-deepseek"
    assert settings.base_url == "https://api.deepseek.com"


def test_openai_compatible_provider_parses_chat_response():
    payload = {
        "choices": [{"message": {"content": "Hola, coaching listo."}}],
    }
    fake_response = BytesIO(json.dumps(payload).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=fake_response):
        provider = OpenAICompatibleProvider(
            "sk-test",
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
        )
        text = provider.generate("prompt")
    assert text == "Hola, coaching listo."


def test_openai_compatible_provider_raises_on_http_402():
    error = HTTPError(
        url="https://api.deepseek.com/v1/chat/completions",
        code=402,
        msg="Payment Required",
        hdrs=None,
        fp=BytesIO(b'{"error":"insufficient balance"}'),
    )
    with patch("urllib.request.urlopen", side_effect=error):
        provider = OpenAICompatibleProvider("sk-test", model="deepseek-chat")
        with pytest.raises(Exception, match="402"):
            provider.generate("prompt")
