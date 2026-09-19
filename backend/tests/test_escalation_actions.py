import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.main import app
from app.models.domain import Escalation, EHRRecord, Documentation, EscalationStateEnum
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_escalation_action_acknowledge_and_request_info(seed_test_data):
    """Test Acknowledge (IN_REVIEW) and Request Info (WAITING_FOR_INFORMATION) action transitions."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {seed_test_data['rev_a_token']}"}
    
    async with TestingSessionLocal() as db:
        esc = Escalation(
            id="esc-action-test-1",
            hospital_id="hosp-a",
            patient_id="pat-a-1",
            campaign_id="camp-a-1",
            call_id="call-test-ack",
            priority="URGENT",
            state=EscalationStateEnum.OPEN,
            trigger_reason="Chest pain reported during call"
        )
        db.add(esc)
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Acknowledge case -> IN_REVIEW
        res1 = await client.put(
            "/api/v1/escalations/esc-action-test-1/action",
            json={"state": "IN_REVIEW", "resolution_notes": "Reviewed by attending RN"},
            headers=headers
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["state"] == "IN_REVIEW"
        assert data1["assigned_reviewer_id"] == "user-rev-a"

        # 2. Request Info case -> WAITING_FOR_INFORMATION
        res2 = await client.put(
            "/api/v1/escalations/esc-action-test-1/action",
            json={"state": "WAITING_FOR_INFORMATION", "resolution_notes": "Requested lab records"},
            headers=headers
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["state"] == "WAITING_FOR_INFORMATION"
        assert data2["resolution_notes"] == "Requested lab records"

@pytest.mark.asyncio
async def test_escalation_action_resolve_and_idempotent_ehr_sync(seed_test_data):
    """Test Resolve & Sync EHR action, verifying state transition, Documentation creation, and EHRRecord idempotency."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {seed_test_data['rev_a_token']}"}

    async with TestingSessionLocal() as db:
        esc = Escalation(
            id="esc-resolve-test-2",
            hospital_id="hosp-a",
            patient_id="pat-a-1",
            campaign_id="camp-a-1",
            call_id="call-test-resolve",
            priority="URGENT",
            state=EscalationStateEnum.IN_REVIEW,
            trigger_reason="High blood pressure"
        )
        db.add(esc)
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Resolve & Sync EHR -> RESOLVED
        res1 = await client.put(
            "/api/v1/escalations/esc-resolve-test-2/action",
            json={"state": "RESOLVED", "resolution_notes": "Vitals stable, medication adjusted"},
            headers=headers
        )
        assert res1.status_code == 200
        assert res1.json()["state"] == "RESOLVED"

        # 2. Duplicate Resolve click -> Should be idempotent (no duplicate EHR records)
        res2 = await client.put(
            "/api/v1/escalations/esc-resolve-test-2/action",
            json={"state": "RESOLVED", "resolution_notes": "Vitals stable, medication adjusted"},
            headers=headers
        )
        assert res2.status_code == 200

    async with TestingSessionLocal() as db:
        # Verify EHR record was created exactly once
        stmt_ehr = select(EHRRecord).where(
            EHRRecord.hospital_id == "hosp-a",
            EHRRecord.resource_type == "EscalationResolution",
            EHRRecord.resource_id == "esc-resolve-test-2"
        )
        res_ehr = await db.execute(stmt_ehr)
        ehrs = res_ehr.scalars().all()
        assert len(ehrs) == 1
        assert ehrs[0].data["resolution_notes"] == "Vitals stable, medication adjusted"

        # Verify Documentation was created
        stmt_doc = select(Documentation).where(Documentation.patient_id == "pat-a-1")
        res_doc = await db.execute(stmt_doc)
        docs = res_doc.scalars().all()
        assert len(docs) >= 1
