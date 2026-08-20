from typing import Any

import httpx

from app.core.config import Settings
from app.intelligence.providers.base import LLMProvider


class OpenAICompatibleLLMProvider(LLMProvider):
    """Optional commercial/self-hosted swap-in speaking the OpenAI chat
    completions wire format. Never required — only used when
    AI_PROVIDER=openai_compatible and credentials are configured."""

    def __init__(self, settings: Settings):
        if not settings.OPENAI_COMPATIBLE_BASE_URL or not settings.OPENAI_COMPATIBLE_LLM_MODEL:
            raise RuntimeError(
                "OPENAI_COMPATIBLE_BASE_URL and OPENAI_COMPATIBLE_LLM_MODEL must be set "
                "when AI_PROVIDER=openai_compatible"
            )
        self._base_url = settings.OPENAI_COMPATIBLE_BASE_URL.rstrip("/")
        self._api_key = settings.OPENAI_COMPATIBLE_API_KEY
        self._model = settings.OPENAI_COMPATIBLE_LLM_MODEL
        self._timeout = settings.LLM_REQUEST_TIMEOUT_SECONDS
        self._max_retries = settings.LLM_MAX_RETRIES

    @property
    def model_name(self) -> str:
        return self._model

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.1,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if json_schema:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for _ in range(self._max_retries + 1):
                try:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions", json=payload, headers=headers
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                except (httpx.HTTPError, KeyError, IndexError) as exc:
                    last_error = exc
        raise RuntimeError(f"OpenAI-compatible completion failed after retries: {last_error}") from last_error
