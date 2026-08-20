import json
from typing import Any

import httpx

from app.core.config import Settings
from app.intelligence.providers.base import LLMProvider


class OllamaLLMProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.OLLAMA_LLM_MODEL
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
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        if json_schema:
            payload["format"] = json_schema

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(self._max_retries + 1):
                try:
                    resp = await client.post(f"{self._base_url}/api/generate", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("response", "")
                except (httpx.HTTPError, json.JSONDecodeError) as exc:
                    last_error = exc
        raise RuntimeError(f"Ollama completion failed after retries: {last_error}") from last_error
