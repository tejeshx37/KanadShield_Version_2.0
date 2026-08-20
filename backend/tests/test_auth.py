import pytest


@pytest.mark.asyncio
async def test_register_login_me_flow(client):
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "pytest_user@example.com", "password": "pytestpass123", "full_name": "Pytest User"},
    )
    assert register_resp.status_code == 201
    body = register_resp.json()
    assert body["email"] == "pytest_user@example.com"
    assert body["role"] == "USER"

    dup_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "pytest_user@example.com", "password": "pytestpass123"},
    )
    assert dup_resp.status_code == 409

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "pytest_user@example.com", "password": "pytestpass123"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    wrong_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "pytest_user@example.com", "password": "wrongpassword"},
    )
    assert wrong_login.status_code == 401

    me_resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "pytest_user@example.com"

    unauth_resp = await client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401

    refresh_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_resp.status_code == 200

    reuse_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse_resp.status_code == 401  # refresh tokens are single-use
