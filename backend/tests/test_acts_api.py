import hashlib

import pytest

from app.models.document import Act, Document, Section
from app.models.enums import DocumentType, Jurisdiction


@pytest.mark.asyncio
async def test_get_act_returns_sections_in_order(client, db_session):
    text = "An Act to provide for pensions."
    doc = Document(
        source="test_source",
        source_document_id="ACT-1",
        title="Gujarat Pension Act, 1990",
        document_type=DocumentType.ACT,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        source_url="https://example.test/act",
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db_session.add(doc)
    await db_session.flush()

    act = Act(document_id=doc.id, act_number="12", year=1990, short_title="Gujarat Pension Act")
    db_session.add(act)
    await db_session.flush()

    db_session.add_all(
        [
            Section(act_id=act.id, section_number="2", heading="Definitions", text="...", order_index=1),
            Section(act_id=act.id, section_number="1", heading="Short title", text="...", order_index=0),
        ]
    )
    await db_session.commit()

    resp = await client.get(f"/api/v1/acts/{act.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["short_title"] == "Gujarat Pension Act"
    assert [s["section_number"] for s in body["sections"]] == ["1", "2"]
    assert body["document"]["source_url"] == "https://example.test/act"


@pytest.mark.asyncio
async def test_get_act_not_found(client):
    resp = await client.get("/api/v1/acts/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
