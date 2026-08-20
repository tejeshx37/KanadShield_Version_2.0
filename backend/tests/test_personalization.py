import hashlib

import pytest

from app.core.config import get_settings
from app.models.document import Document
from app.models.enums import DocumentType, Jurisdiction
from app.models.users import Alert
from app.services.alert_evaluation import evaluate_alert


async def _register_and_login(client, email: str) -> dict:
    await client.post("/api/v1/auth/register", json={"email": email, "password": "personalpass123"})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "personalpass123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_bookmark_and_saved_search_lifecycle(client, db_session):
    headers = await _register_and_login(client, "bookmarker@example.com")

    doc = Document(
        source="test_source",
        source_document_id="BOOKMARK-1",
        title="Bookmarkable Document",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        content_hash=hashlib.sha256(b"bm").hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    create_resp = await client.post("/api/v1/bookmarks", json={"document_id": str(doc.id), "note": "check later"}, headers=headers)
    assert create_resp.status_code == 201
    bookmark_id = create_resp.json()["id"]

    list_resp = await client.get("/api/v1/bookmarks", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 1

    delete_resp = await client.delete(f"/api/v1/bookmarks/{bookmark_id}", headers=headers)
    assert delete_resp.status_code == 204

    save_search_resp = await client.post(
        "/api/v1/saved-searches", json={"name": "pension", "query": "pension", "filters": {}}, headers=headers
    )
    assert save_search_resp.status_code == 201


@pytest.mark.asyncio
async def test_alert_matches_recently_updated_documents(db_session):
    from app.core.security import hash_password
    from app.models.users import User

    user = User(email="alertowner@example.com", hashed_password=hash_password("x"))
    db_session.add(user)
    await db_session.flush()

    alert = Alert(
        user_id=user.id,
        alert_type="topic",
        target={"topic": "pension"},
    )
    db_session.add(alert)
    await db_session.flush()

    doc = Document(
        source="test_source",
        source_document_id="ALERT-1",
        title="New Pension Scheme GR",
        document_type=DocumentType.GR,
        jurisdiction=Jurisdiction.STATE,
        source_language="en",
        content_hash=hashlib.sha256(b"alert").hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()

    matches = await evaluate_alert(db_session, alert)
    assert any(d.title == "New Pension Scheme GR" for d in matches)
    assert alert.last_checked_at is not None


@pytest.mark.asyncio
async def test_research_collection_export_produces_markdown(client, db_session):
    headers = await _register_and_login(client, "researcher@example.com")

    doc = Document(
        source="test_source",
        source_document_id="RESEARCH-1",
        title="Research Doc",
        document_type=DocumentType.ACT,
        jurisdiction=Jurisdiction.CENTRAL,
        source_language="en",
        source_url="https://example.test/doc",
        content_hash=hashlib.sha256(b"research").hexdigest(),
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    collection_resp = await client.post("/api/v1/research/collections", json={"name": "My Research"}, headers=headers)
    collection_id = collection_resp.json()["id"]

    await client.post(
        f"/api/v1/research/collections/{collection_id}/items",
        json={"document_id": str(doc.id), "note": "Important clause"},
        headers=headers,
    )

    export_resp = await client.get(f"/api/v1/research/collections/{collection_id}/export", headers=headers)
    assert export_resp.status_code == 200
    assert "Research Doc" in export_resp.text
    assert "Important clause" in export_resp.text
