"""Gemini provider via google-genai SDK."""

from __future__ import annotations

import time

from llm.base import LLMProvider
from llm.errors import GeminiQuotaError, is_quota_error, parse_retry_seconds


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-2.5-flash",
        max_retries: int = 2,
    ) -> None:
        if not api_key.strip():
            raise ValueError("GeminiProvider requires a non-empty api_key.")
        from google import genai

        self._model = model
        self._client = genai.Client(api_key=api_key)
        self._max_retries = max(0, max_retries)

    def generate(self, prompt: str) -> str:
        last_error: BaseException | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                text = getattr(response, "text", None)
                if text:
                    return text
                return str(response)
            except Exception as exc:
                last_error = exc
                if not is_quota_error(exc) or attempt >= self._max_retries:
                    break
                time.sleep(parse_retry_seconds(exc))

        assert last_error is not None
        if is_quota_error(last_error):
            raise GeminiQuotaError(str(last_error)) from last_error
        raise last_error
