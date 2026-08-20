import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.intelligence.providers.base import LLMProvider, OCRProvider, OCRResult
from app.models.ingestion import ChangeRadarReport
from app.services.ingestion.base import FetchedDocument, RawContentFormat, SourceConnector, SourceDocumentRef
from app.services.ingestion.pipeline import IngestionPipeline

V1_HTML = "<html><body><p>Government of Gujarat</p><p>Subject: Pension GR</p><p>Eligibility: workers with 5 years of service. Penalty is Rs. 500.</p></body></html>"
V2_HTML = "<html><body><p>Government of Gujarat</p><p>Subject: Pension GR</p><p>Eligibility: workers with 10 years of service. Penalty is Rs. 2000.</p></body></html>"


class _VersionedFakeConnector(SourceConnector):
    def __init__(self, html: str):
        self._html = html.encode()

    @property
    def source_name(self) -> str:
        return "SOURCE_GUJARAT_GR"

    async def list_documents(self, *, since=None):
        return [SourceDocumentRef(source_document_id="GR-CHANGE-1", source_url="https://example.test/gr/1", title="Pension GR")]

    async def fetch_document(self, ref):
        return FetchedDocument(
            source_document_id=ref.source_document_id,
            source_url=ref.source_url,
            title="Pension Scheme GR",
            raw_bytes=self._html,
            content_format=RawContentFormat.HTML,
        )


class _FakeLLM(LLMProvider):
    @property
    def model_name(self):
        return "fake"

    async def complete(self, prompt, *, system=None, json_schema=None, max_tokens=None, temperature=0.1):
        return '{"document_type": "GR", "confidence": 0.5}'


class _FakeEmbeddings:
    model_name = "fake-embed"

    def __init__(self, dimensions):
        self.dimensions = dimensions

    async def embed(self, texts):
        return [[0.1] * self.dimensions for _ in texts]


class _FakeOCR(OCRProvider):
    async def extract_text(self, image_bytes, languages):
        return OCRResult(text="", language="en", confidence=0.0)


@pytest.mark.asyncio
async def test_change_radar_report_generated_on_material_change(db_session):
    settings = get_settings()
    pipeline = IngestionPipeline(
        db_session, settings, _FakeLLM(), _FakeEmbeddings(settings.EMBEDDING_DIMENSIONS), _FakeOCR()
    )

    await pipeline.run(_VersionedFakeConnector(V1_HTML))
    await db_session.commit()

    reports_before = (await db_session.execute(select(ChangeRadarReport))).scalars().all()
    assert len(reports_before) == 0  # first ingest is a new document, not a change

    await pipeline.run(_VersionedFakeConnector(V2_HTML))
    await db_session.commit()

    reports_after = (await db_session.execute(select(ChangeRadarReport))).scalars().all()
    assert len(reports_after) == 1
    report = reports_after[0]
    assert report.change_type in {"eligibility", "monetary_limits", "penalties"}
    assert report.impact_level.value in {"MEDIUM", "HIGH", "CRITICAL"}
    assert "potential impact" in report.evidence["note"]
