import pytest

from app.models.document import Scheme
from app.services.scheme_matching import match_schemes


@pytest.mark.asyncio
async def test_match_schemes_evaluates_jsonb_rules(db_session):
    eligible_scheme = Scheme(
        name="Senior Citizen Pension Scheme",
        eligibility_rules={
            "all": [
                {"field": "age", "operator": ">=", "value": 60},
                {"field": "state", "operator": "==", "value": "Gujarat"},
            ]
        },
        required_documents=["Aadhaar", "Age proof"],
        official_source="https://example.test/scheme",
    )
    ineligible_scheme = Scheme(
        name="Youth Skill Development Scheme",
        eligibility_rules={"all": [{"field": "age", "operator": "<=", "value": 25}]},
    )
    empty_rules_scheme = Scheme(name="Scheme With No Rules", eligibility_rules={})
    db_session.add_all([eligible_scheme, ineligible_scheme, empty_rules_scheme])
    await db_session.commit()

    profile = {"age": 65, "state": "Gujarat"}
    results = await match_schemes(db_session, profile)

    by_name = {r.scheme_name: r for r in results}
    assert by_name["Senior Citizen Pension Scheme"].is_potentially_eligible is True
    assert "appear potentially eligible" in by_name["Senior Citizen Pension Scheme"].explanation
    assert by_name["Youth Skill Development Scheme"].is_potentially_eligible is False
    assert by_name["Scheme With No Rules"].is_potentially_eligible is False  # never eligible with zero real conditions


@pytest.mark.asyncio
async def test_citizen_profile_crud_and_consent_revocation(client):
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "citizen@example.com", "password": "citizenpass123"},
    )
    assert register_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "citizen@example.com", "password": "citizenpass123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    upsert_resp = await client.put(
        "/api/v1/citizens/profile",
        json={"derived_attributes": {"age_range": "60_plus", "state": "Gujarat"}},
        headers=headers,
    )
    assert upsert_resp.status_code == 200

    get_resp = await client.get("/api/v1/citizens/profile", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["derived_attributes"]["state"] == "Gujarat"

    revoke_resp = await client.post("/api/v1/citizens/profile/revoke-consent", headers=headers)
    assert revoke_resp.status_code == 200

    delete_resp = await client.delete("/api/v1/citizens/profile", headers=headers)
    assert delete_resp.status_code == 204

    get_after_delete = await client.get("/api/v1/citizens/profile", headers=headers)
    assert get_after_delete.status_code == 404
