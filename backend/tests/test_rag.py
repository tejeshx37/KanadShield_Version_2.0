import hashlib
import json

import pytest

from app.core.config import get_settings
from app.intelligence.providers.base import LLMProvider
from app.models.document import Document, DocumentChunk
from app.models.enums import ChunkType, DocumentType, Jurisdiction
from app.services.rag.ask_service import answer_question
from app.services.rag.summarize_service import SummarizationError, summarize_document


class _FakeEmbeddings:
    model_name = "fake-embed"

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    async def embed(self, texts):
        return [[0.2] * self.dimensions for _ in texts]


class _GroundedFakeLLM(LLMProvider):
    """Simulates an LLM that answers strictly from the excerpts it was
    given, echoing the real document_id back — proves the pipeline is
    grounded rather than testing a hardcoded answer."""

    def __init__(self, response: dict):
        self._response = response

    @property
    def model_name(self) -> str:
        return "fake-grounded"

    async def complete(self, prompt, *, system=None, json_schema=None, max_tokens=None, temperature=0.1) -> str:
        return json.dumps(self._response)


class _HallucinatingFakeLLM(LLMProvider):
    @property
    def model_name(self) -> str:
        return "fake-hallucinating"

    async def complete(self, prompt, *, system=None, json_schema=None, max_tokens=None, temperature=0.1) -> str:
        return json.dumps(
            {
                "answer": "Some fabricated answer",
                "citations": [{"document_id": "00000000-0000-0000-0000-000000000000", "section": None}],
                "insufficient_evidence": False,
            }
        )


async def _seed_document_with_chunks(db_session, settings):
    text = "Eligibility: retired mill workers with 10 years of service qualify for pension."
    doc = Document(
        source="test_source",
        source_document_id="RAG-1",
        title="Pension Scheme GR",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        state="Gujarat",
        source_language="en",
        year=2021,
        extracted_text=text,
        subject=text,
        text_available=True,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db_session.add(doc)
    await db_session.flush()

    db_session.add(
        DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            chunk_type=ChunkType.ELIGIBILITY,
            text=text,
            section_ref="eligibility",
            language="en",
            embedding=[0.2] * settings.EMBEDDING_DIMENSIONS,
        )
    )
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.mark.asyncio
async def test_summarize_grounded_in_retrieved_chunks(db_session):
    settings = get_settings()
    doc = await _seed_document_with_chunks(db_session, settings)

    fake_llm = _GroundedFakeLLM(
        {
            "summary": "Provides pension to retired mill workers.",
            "key_provisions": ["10 years of service required"],
            "eligibility": ["Retired mill workers with 10 years of service"],
            "conditions": [],
            "dates": [],
            "limitations": [],
        }
    )
    summary = await summarize_document(
        db_session, settings, fake_llm, _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS), doc.id
    )
    assert "pension" in summary.summary.lower()
    assert summary.source_references
    assert summary.source_references[0].document_id == str(doc.id)


@pytest.mark.asyncio
async def test_summarize_raises_when_no_chunks_indexed(db_session):
    settings = get_settings()
    doc = Document(
        source="test_source",
        source_document_id="RAG-EMPTY",
        title="Unindexed Document",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        content_hash="x" * 64,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    with pytest.raises(SummarizationError):
        await summarize_document(
            db_session, settings, _GroundedFakeLLM({}), _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS), doc.id
        )


@pytest.mark.asyncio
async def test_ask_validates_citations_and_rejects_hallucinated_document_id(db_session):
    settings = get_settings()
    doc = await _seed_document_with_chunks(db_session, settings)

    fake_llm = _GroundedFakeLLM(
        {
            "answer": "Retired mill workers with 10 years of service qualify for pension.",
            "citations": [{"document_id": str(doc.id), "section": "eligibility"}],
            "insufficient_evidence": False,
        }
    )
    answer = await answer_question(
        db_session, settings, fake_llm, _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS), "Who is eligible for pension?"
    )
    assert answer.citations
    assert answer.citations[0].document_id == str(doc.id)
    assert not answer.insufficient_evidence

    # Hallucinated document_id must never be trusted or passed through.
    hallucinating_answer = await answer_question(
        db_session,
        settings,
        _HallucinatingFakeLLM(),
        _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS),
        "Who is eligible for pension?",
    )
    assert hallucinating_answer.citations == []
    assert hallucinating_answer.insufficient_evidence is True


@pytest.mark.asyncio
async def test_ask_returns_insufficient_evidence_when_no_relevant_chunks(db_session):
    settings = get_settings()
    answer = await answer_question(
        db_session,
        settings,
        _GroundedFakeLLM({}),
        _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS),
        "What is the capital of France?",
    )
    assert answer.insufficient_evidence is True
