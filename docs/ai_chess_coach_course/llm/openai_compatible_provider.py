"""OpenAI-compatible chat completions provider (DeepSeek, OpenAI, etc.)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from llm.base import LLMProvider
from llm.errors import GeminiQuotaError, is_quota_error


class OpenAICompatibleProvider(LLMProvider):
    """POST /v1/chat/completions against any OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        base_url: str = "https://api.deepseek.com",
        timeout: float = 120.0,
        temperature: float = 0.4,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAICompatibleProvider requires a non-empty api_key.")
        self._api_key = api_key.strip()
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._temperature = temperature

    def generate(self, prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
        }
        request = urllib.request.Request(
            f"{self._base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            message = f"HTTP {exc.code}: {error_body}"
            if exc.code in {402, 429} or is_quota_error(exc):
                raise GeminiQuotaError(message) from exc
            raise RuntimeError(message) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected LLM response shape: {body!r}") from exc
        if not content:
            raise RuntimeError(f"Empty LLM response: {body!r}")
        return str(content).strip()
