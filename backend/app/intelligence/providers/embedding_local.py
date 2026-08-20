import asyncio
from functools import lru_cache

from app.core.config import Settings
from app.intelligence.providers.base import EmbeddingProvider


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    # Imported lazily: sentence-transformers pulls in torch, which is slow
    # to import and unnecessary unless embeddings are actually requested.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class LocalEmbeddingProvider(EmbeddingProvider):
    """BAAI/bge-m3 by default — multilingual by design, verified against
    en/gu/hi in tests/test_multilingual_search.py."""

    def __init__(self, settings: Settings):
        self._model_name = settings.EMBEDDING_MODEL_NAME
        self._dimensions = settings.EMBEDDING_DIMENSIONS

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed(self, texts: list[str]) -> list[list[float]]:
        model = _load_model(self._model_name)
        loop = asyncio.get_running_loop()
        vectors = await loop.run_in_executor(
            None, lambda: model.encode(texts, normalize_embeddings=True)
        )
        return [v.tolist() for v in vectors]
