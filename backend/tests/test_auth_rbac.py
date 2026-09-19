import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_login_success(async_client: AsyncClient, seed_test_data):
    res = await async_client.post("/api/v1/auth/login", json={
        "email": "mgr@hospa.test",
        "password": "Pass123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "CAMPAIGN_MANAGER"

@pytest.mark.asyncio
async def test_auth_login_failure(async_client: AsyncClient, seed_test_data):
    res = await async_client.post("/api/v1/auth/login", json={
        "email": "mgr@hospa.test",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_rbac_platform_admin_access(async_client: AsyncClient, seed_test_data):
    headers = {"Authorization": f"Bearer {seed_test_data['admin_token']}"}
    res = await async_client.get("/api/v1/hospitals/", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 2

@pytest.mark.asyncio
async def test_rbac_campaign_manager_forbidden_action(async_client: AsyncClient, seed_test_data):
    # Campaign manager attempting platform-only hospital creation should fail with 403
    headers = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}
    res = await async_client.post("/api/v1/hospitals/", headers=headers, json={
        "name": "Unauthorized Hospital",
        "code": "UNAUTH"
    })
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_hospital_admin_protocol_management_and_tenant_isolation(async_client: AsyncClient, seed_test_data):
    # Manager A lists protocols
    headers_a = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}
    res_list_a = await async_client.get("/api/v1/protocols/", headers=headers_a)
    assert res_list_a.status_code == 200
    
    # Manager A creates a new clinical protocol
    res_create = await async_client.post("/api/v1/protocols/", headers=headers_a, json={
        "name": "Post-Op Orthopedic Care Standard",
        "category": "Orthopedics",
        "target_conditions": ["Post-CABG", "Knee Replacement"],
        "red_flags": ["severe bleeding", "wound dehiscence"]
    })
    assert res_create.status_code == 200
    proto = res_create.json()
    assert proto["name"] == "Post-Op Orthopedic Care Standard"
    assert proto["hospital_id"] == "hosp-a"

    # Manager B lists protocols -> Should NOT see Hospital A's protocol
    headers_b = {"Authorization": f"Bearer {seed_test_data['mgr_b_token']}"}
    res_list_b = await async_client.get("/api/v1/protocols/", headers=headers_b)
    assert res_list_b.status_code == 200
    protos_b = res_list_b.json()
    assert not any(p["id"] == proto["id"] for p in protos_b)

@pytest.mark.asyncio
async def test_hospital_admin_ehr_records_tenant_isolation(async_client: AsyncClient, seed_test_data):
    headers_a = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}
    res_a = await async_client.get("/api/v1/ehr/records", headers=headers_a)
    assert res_a.status_code == 200
    records_a = res_a.json()
    assert all(r["hospital_id"] == "hosp-a" for r in records_a)
