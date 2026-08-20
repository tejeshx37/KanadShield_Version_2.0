import hashlib

import pytest

from app.core.config import get_settings
from app.intelligence.providers.base import EmbeddingProvider
from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction
from app.search.service import HybridSearchService, SearchFilters


class _DeterministicFakeEmbeddings(EmbeddingProvider):
    """Maps text to a fixed-size vector via a simple bag-of-words hash so
    semantically similar synthetic text produces closer vectors, without
    depending on a downloaded model in this unit test."""

    def __init__(self, dimensions: int):
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return "fake-deterministic"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vec = [0.0] * self._dimensions
            for word in text.lower().split():
                idx = hash(word) % self._dimensions
                vec[idx] += 1.0
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


async def _seed_document(db_session, *, title: str, text: str, source_document_id: str, doc_type=DocumentType.RULE, year=2021):
    doc = Document(
        source="test_source",
        source_document_id=source_document_id,
        title=title,
        document_type=doc_type,
        jurisdiction=Jurisdiction.STATE,
        state="Gujarat",
        source_language="en",
        year=year,
        extracted_text=text,
        subject=text,
        text_available=True,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db_session.add(doc)
    await db_session.flush()
    return doc


@pytest.mark.asyncio
async def test_lexical_search_finds_matching_document(db_session):
    settings = get_settings()
    await _seed_document(
        db_session,
        title="Gujarat Pension Rules, 1979",
        text="This rule governs pension and retirement benefits for state employees.",
        source_document_id="SEARCH-1",
    )
    await _seed_document(
        db_session,
        title="Gujarat Road Traffic Notification",
        text="This notification governs traffic signals and road safety.",
        source_document_id="SEARCH-2",
    )
    await db_session.commit()

    service = HybridSearchService(db_session, settings, _DeterministicFakeEmbeddings(settings.EMBEDDING_DIMENSIONS))
    result = await service.search("pension", SearchFilters(), page=1, page_size=10)

    assert result.total >= 1
    assert result.items[0].title == "Gujarat Pension Rules, 1979"
    assert result.search_time_ms >= 0


@pytest.mark.asyncio
async def test_search_filters_by_document_type(db_session):
    settings = get_settings()
    await _seed_document(
        db_session,
        title="Some Judgment",
        text="Court judgment text about pension eligibility.",
        source_document_id="SEARCH-3",
        doc_type=DocumentType.JUDGMENT,
    )
    await db_session.commit()

    service = HybridSearchService(db_session, settings, _DeterministicFakeEmbeddings(settings.EMBEDDING_DIMENSIONS))
    result = await service.search(
        "pension", SearchFilters(document_type=DocumentType.RULE), page=1, page_size=10
    )
    assert all(item.document_type == "RULE" for item in result.items)
