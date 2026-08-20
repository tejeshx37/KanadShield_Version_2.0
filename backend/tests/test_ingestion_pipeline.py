import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.intelligence.providers.base import LLMProvider, OCRProvider, OCRResult
from app.models.document import DocumentChunk
from app.models.enums import DocumentType
from app.services.ingestion.base import FetchedDocument, RawContentFormat, SourceConnector, SourceDocumentRef
from app.services.ingestion.pipeline import IngestionPipeline

GR_HTML = """
<html><body>
<h1>Government of Gujarat</h1>
<p>Labour and Employment Department</p>
<p>Subject: Pension scheme for retired mill workers</p>
<p>dated 15th March, 2021</p>
<p>Eligibility: Workers who have completed 10 years of continuous service.</p>
<p>Conditions: Application must be submitted within 60 days of retirement.</p>
</body></html>
""".strip()


class _FakeConnector(SourceConnector):
    """Serves synthetic in-memory content — not a claim of real government
    data. Used only to exercise the deterministic pipeline logic
    (categorization, metadata extraction, idempotent upsert, chunking)
    without network access, which this sandbox's proxy policy blocks for
    *.gov.in / *.nic.in (see docs/CONNECTOR_STATUS.md)."""

    def __init__(self, html: bytes = GR_HTML.encode()):
        self._html = html

    @property
    def source_name(self) -> str:
        return "SOURCE_GUJARAT_GR"

    async def list_documents(self, *, since=None):
        return [SourceDocumentRef(source_document_id="GR-2021-001", source_url="https://example.test/gr/1", title="Pension GR")]

    async def fetch_document(self, ref: SourceDocumentRef) -> FetchedDocument:
        return FetchedDocument(
            source_document_id=ref.source_document_id,
            source_url=ref.source_url,
            title="Pension Scheme GR 2021",
            raw_bytes=self._html,
            content_format=RawContentFormat.HTML,
        )


class _FakeLLM(LLMProvider):
    @property
    def model_name(self) -> str:
        return "fake-test-model"

    async def complete(self, prompt, *, system=None, json_schema=None, max_tokens=None, temperature=0.1) -> str:
        return '{"document_type": "GR", "confidence": 0.5}'


class _FakeEmbeddings:
    model_name = "fake-embed"

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self.dimensions for _ in texts]


class _FakeOCR(OCRProvider):
    async def extract_text(self, image_bytes: bytes, languages: list[str]) -> OCRResult:
        return OCRResult(text="", language="en", confidence=0.0)


@pytest.mark.asyncio
async def test_ingestion_pipeline_categorizes_extracts_and_chunks(db_session):
    settings = get_settings()
    pipeline = IngestionPipeline(db_session, settings, _FakeLLM(), _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS), _FakeOCR())
    connector = _FakeConnector()

    run = await pipeline.run(connector)
    await db_session.commit()

    assert run.status == "completed"
    assert run.documents_new == 1
    assert run.documents_failed == 0

    doc = await pipeline.documents.get_by_natural_key("SOURCE_GUJARAT_GR", "GR-2021-001")
    assert doc is not None
    # SOURCE_GUJARAT_GR is deterministically GR — never needed the fake LLM call.
    assert doc.document_type == DocumentType.GR
    assert doc.classification_confidence == 1.0
    assert doc.jurisdiction.value == "STATE"
    assert doc.state == "Gujarat"
    assert doc.date is not None and doc.date.year == 2021

    chunks = (
        (await db_session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc.id)))
        .scalars()
        .all()
    )
    assert len(chunks) > 0
    assert any(c.chunk_type.value == "ELIGIBILITY" for c in chunks)

    # Re-running against unchanged content must not create a duplicate or reprocess.
    second_run = await pipeline.run(connector)
    await db_session.commit()
    assert second_run.documents_unchanged == 1
    assert second_run.documents_new == 0
