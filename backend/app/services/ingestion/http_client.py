import asyncio

import httpx

from app.core.config import Settings


class RetryingHTTPClient:
    """Shared HTTP fetch helper for connectors: configured user agent,
    timeout, and exponential backoff retry — never a source-specific
    ad-hoc requests call scattered through connector code."""

    def __init__(self, settings: Settings):
        self._settings = settings

    async def get(self, url: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", self._settings.INGESTION_USER_AGENT)
        last_exc: Exception | None = None
        async with httpx.AsyncClient(timeout=self._settings.INGESTION_REQUEST_TIMEOUT_SECONDS) as client:
            for attempt in range(self._settings.INGESTION_MAX_RETRIES + 1):
                try:
                    resp = await client.get(url, headers=headers, **kwargs)
                    resp.raise_for_status()
                    return resp
                except httpx.HTTPError as exc:
                    last_exc = exc
                    if attempt < self._settings.INGESTION_MAX_RETRIES:
                        await asyncio.sleep(self._settings.INGESTION_RETRY_BACKOFF_SECONDS * (2**attempt))
        raise RuntimeError(f"GET {url} failed after retries: {last_exc}") from last_exc
