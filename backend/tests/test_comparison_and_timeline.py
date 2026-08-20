import hashlib

import pytest

from app.models.document import Document, DocumentVersion
from app.models.enums import DocumentType, Jurisdiction
from app.services.comparison_service import DiffChangeType, DiffCategory, compare_texts
from app.services.timeline_service import get_document_timeline


def test_compare_texts_detects_monetary_and_eligibility_changes():
    old_text = "Eligibility: workers with 5 years of service. Penalty is Rs. 500."
    new_text = "Eligibility: workers with 10 years of service. Penalty is Rs. 1000."

    segments = compare_texts(old_text, new_text)
    material = [s for s in segments if s.change_type != DiffChangeType.UNCHANGED]
    assert material
    categories = {s.category for s in material}
    assert DiffCategory.ELIGIBILITY in categories or DiffCategory.MONETARY_LIMITS in categories


def test_compare_texts_identical_documents_have_no_material_changes():
    text = "This is an unchanged clause about eligibility."
    segments = compare_texts(text, text)
    assert all(s.change_type == DiffChangeType.UNCHANGED for s in segments)


@pytest.mark.asyncio
async def test_timeline_includes_publication_and_versions(db_session):
    doc = Document(
        source="test_source",
        source_document_id="TIMELINE-1",
        title="Timeline Test GR",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        year=2020,
        content_hash=hashlib.sha256(b"v1").hexdigest(),
    )
    db_session.add(doc)
    await db_session.flush()

    db_session.add(
        DocumentVersion(document_id=doc.id, version_number=1, content_hash=hashlib.sha256(b"v2").hexdigest())
    )
    await db_session.commit()

    events = await get_document_timeline(db_session, doc.id)
    event_types = [e.event_type for e in events]
    assert "published" in event_types
    assert "version" in event_types
