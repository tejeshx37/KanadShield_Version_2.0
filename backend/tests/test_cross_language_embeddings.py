"""Verifies the real BAAI/bge-m3 embedding model actually retrieves
cross-language (Gujarati query -> English document) as claimed in the
master spec — never assumed from the model's marketing description.

This test uses the REAL LocalEmbeddingProvider, not a fake. It is skipped
(not faked, not silently passed) if the model cannot be downloaded — this
sandbox's network proxy blocks huggingface.co (confirmed via
`curl -sI https://huggingface.co` -> 403 Forbidden from the proxy itself,
see docs/CONNECTOR_STATUS.md), so this test cannot run to completion here.
It is written to run for real, unmodified, wherever HF access is
available."""

import numpy as np
import pytest

from app.core.config import get_settings
from app.intelligence.providers.embedding_local import LocalEmbeddingProvider


@pytest.mark.asyncio
async def test_cross_language_semantic_retrieval_gujarati_query_english_document():
    settings = get_settings()
    provider = LocalEmbeddingProvider(settings)

    try:
        vectors = await provider.embed(
            [
                "પેન્શન યોજના",  # Gujarati: "pension scheme"
                "This government resolution establishes a pension scheme for retired workers.",
                "This notification concerns road traffic signal timing.",
            ]
        )
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"BAAI/bge-m3 model unavailable in this environment: {exc}")

    query_vec, pension_doc_vec, unrelated_doc_vec = (np.array(v) for v in vectors)

    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_to_pension = cosine_sim(query_vec, pension_doc_vec)
    sim_to_unrelated = cosine_sim(query_vec, unrelated_doc_vec)

    assert sim_to_pension > sim_to_unrelated, (
        "Gujarati 'pension scheme' query should be semantically closer to the "
        "English pension document than to the unrelated traffic notification"
    )
