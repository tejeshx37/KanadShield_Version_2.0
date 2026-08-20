import pytest
from sqlalchemy import select

from app.models.enums import UserRole
from app.models.users import AuditLog, User


async def _register_and_login(client, email: str, role: UserRole | None = None, db_session=None) -> dict:
    await client.post("/api/v1/auth/register", json={"email": email, "password": "securitypass123"})
    if role is not None and db_session is not None:
        user = (await db_session.execute(select(User).where(User.email == email))).scalar_one()
        user.role = role
        await db_session.commit()
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "securitypass123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_security_headers_present(client):
    resp = await client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in resp.headers
    assert resp.headers["content-security-policy"] != "ALLOWALL"


@pytest.mark.asyncio
async def test_error_shape_never_leaks_internals(client):
    resp = await client.get("/api/v1/documents/not-a-uuid")
    assert resp.status_code in (404, 422)
    body = resp.json()
    text = str(body)
    assert "Traceback" not in text
    assert "sqlalchemy" not in text.lower()
    assert "/home/" not in text


@pytest.mark.asyncio
async def test_rbac_blocks_non_admin_from_dead_letters(client, db_session):
    headers = await _register_and_login(client, "plain_user@example.com")
    resp = await client.get("/api/v1/admin/dead-letters", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_rbac_allows_admin_to_view_dead_letters(client, db_session):
    headers = await _register_and_login(client, "admin_user@example.com", role=UserRole.ADMIN, db_session=db_session)
    resp = await client.get("/api/v1/admin/dead-letters", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_request_to_protected_endpoint_is_401(client):
    resp = await client.get("/api/v1/bookmarks")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_failed_login_is_audit_logged(client, db_session):
    await client.post("/api/v1/auth/register", json={"email": "audituser@example.com", "password": "correctpass123"})
    resp = await client.post("/api/v1/auth/login", json={"email": "audituser@example.com", "password": "wrongpass"})
    assert resp.status_code == 401

    logs = (await db_session.execute(select(AuditLog).where(AuditLog.action == "login", AuditLog.result == "failure"))).scalars().all()
    assert any(log.resource_id == "audituser@example.com" for log in logs)


@pytest.mark.asyncio
async def test_successful_login_is_audit_logged(client, db_session):
    await client.post("/api/v1/auth/register", json={"email": "audituser2@example.com", "password": "correctpass123"})
    resp = await client.post("/api/v1/auth/login", json={"email": "audituser2@example.com", "password": "correctpass123"})
    assert resp.status_code == 200

    logs = (await db_session.execute(select(AuditLog).where(AuditLog.action == "login", AuditLog.result == "success"))).scalars().all()
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_auth_endpoint_rate_limited(client):
    # RATE_LIMIT_AUTH defaults to 10/minute — the 11th rapid request in the
    # same minute must be rejected, proving default_limits + SlowAPIMiddleware
    # are actually wired up, not just configured.
    last_status = None
    for _ in range(15):
        resp = await client.post("/api/v1/auth/login", json={"email": "ratelimit@example.com", "password": "x"})
        last_status = resp.status_code
        if last_status == 429:
            break
    assert last_status == 429
