import hashlib

import pytest

from app.core.config import get_settings
from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction
from app.models.organizations import Department
from app.models.users import DocumentView, SearchHistory
from app.services.analytics_service import corpus_health, department_insights, frequently_accessed_documents, trending_searches


@pytest.mark.asyncio
async def test_trending_searches_aggregates_without_exposing_user(db_session):
    settings = get_settings()
    db_session.add_all(
        [
            SearchHistory(user_id=None, query="pension", filters={}, result_count=5),
            SearchHistory(user_id=None, query="pension", filters={}, result_count=3),
            SearchHistory(user_id=None, query="gazette", filters={}, result_count=1),
        ]
    )
    await db_session.commit()

    results = await trending_searches(db_session, settings)
    assert results[0]["query"] == "pension"
    assert results[0]["count"] == 2
    assert all("user_id" not in r for r in results)


@pytest.mark.asyncio
async def test_frequently_accessed_documents_counts_views(db_session):
    doc = Document(
        source="test_source",
        source_document_id="DASH-1",
        title="Popular Document",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        content_hash=hashlib.sha256(b"dash").hexdigest(),
    )
    db_session.add(doc)
    await db_session.flush()
    db_session.add_all([DocumentView(document_id=doc.id) for _ in range(3)])
    await db_session.commit()

    results = await frequently_accessed_documents(db_session)
    assert results[0]["title"] == "Popular Document"
    assert results[0]["views"] == 3


@pytest.mark.asyncio
async def test_department_insights_and_corpus_health(db_session):
    dept = Department(name="Labour Department", source_value="Labour Department")
    db_session.add(dept)
    await db_session.flush()

    doc = Document(
        source="test_source",
        source_document_id="DASH-2",
        title="Dept Doc",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        department_id=dept.id,
        source_language="en",
        classification_confidence=0.9,
        date_confidence=0.6,
        content_hash=hashlib.sha256(b"dept").hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()

    dept_results = await department_insights(db_session)
    labour = next(r for r in dept_results if r["name"] == "Labour Department")
    assert labour["document_count"] == 1

    health = await corpus_health(db_session)
    assert health["total_documents"] >= 1
    assert health["classification_confidence_distribution"]["high"] >= 1
    assert health["date_extraction_confidence_distribution"]["medium"] >= 1
