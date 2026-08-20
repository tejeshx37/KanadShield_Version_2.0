import hashlib

import pytest

from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction


@pytest.mark.asyncio
async def test_list_and_get_document(client, db_session):
    text = "The Gujarat Pension Rules provide for retirement benefits."
    doc = Document(
        source="test_source",
        source_document_id="TEST-001",
        title="Gujarat Pension Rules, 1979",
        document_type=DocumentType.RULE,
        jurisdiction=Jurisdiction.STATE,
        state="Gujarat",
        source_language="en",
        year=1979,
        extracted_text=text,
        text_available=True,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    list_resp = await client.get("/api/v1/documents", params={"document_type": "RULE"})
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] >= 1
    assert any(item["id"] == str(doc.id) for item in body["items"])

    detail_resp = await client.get(f"/api/v1/documents/{doc.id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "Gujarat Pension Rules, 1979"

    missing_resp = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error"]["code"] == "not_found"
