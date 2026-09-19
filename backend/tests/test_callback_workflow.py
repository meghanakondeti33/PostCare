import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from sqlalchemy import select
from app.main import app
from app.models.domain import OutreachTask, Call, TaskStateEnum
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_trigger_scheduled_callback_successfully(seed_test_data):
    """Test triggering a scheduled callback task transitions state to COMPLETED/ESCALATED and increments attempt_count."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}

    async with TestingSessionLocal() as db:
        # Create a scheduled callback task
        cb_task = OutreachTask(
            id="task-cb-test-1",
            hospital_id="hosp-a",
            campaign_id="camp-a-1",
            patient_id="pat-a-1",
            state=TaskStateEnum.CALLBACK_SCHEDULED,
            priority_score=95.0,
            attempt_count=0,
            max_attempts=3,
            scheduled_callback_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(cb_task)
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger Call Now via simulate call endpoint
        res = await client.post(
            "/api/v1/calls/simulate",
            json={"task_id": "task-cb-test-1", "simulated_outcome": "COMPLETED"},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert "call_id" in data
        assert data["outcome"] == "COMPLETED"

    async with TestingSessionLocal() as db:
        # Verify task state transitioned to COMPLETED and attempt_count incremented to 1
        res_t = await db.execute(select(OutreachTask).where(OutreachTask.id == "task-cb-test-1"))
        updated_task = res_t.scalar_one()
        assert updated_task.state in [TaskStateEnum.COMPLETED, TaskStateEnum.ESCALATED]
        assert updated_task.attempt_count == 1

        # Verify Call record was created
        res_call = await db.execute(select(Call).where(Call.task_id == "task-cb-test-1"))
        call_rec = res_call.scalar_one_or_none()
        assert call_rec is not None
        assert call_rec.patient_id == "pat-a-1"

@pytest.mark.asyncio
async def test_trigger_callback_invalid_task_returns_404(seed_test_data):
    """Test triggering a nonexistent callback task returns 404 Not Found."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {seed_test_data['mgr_a_token']}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/calls/simulate",
            json={"task_id": "nonexistent-task-99999", "simulated_outcome": "COMPLETED"},
            headers=headers
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_trigger_callback_cross_tenant_denied(seed_test_data):
    """Test Campaign Manager from Hospital B cannot trigger callback for Hospital A task (tenant isolation)."""
    transport = ASGITransport(app=app)
    mgr_b_headers = {"Authorization": f"Bearer {seed_test_data['mgr_b_token']}"}

    async with TestingSessionLocal() as db:
        cb_task = OutreachTask(
            id="task-cb-tenant-1",
            hospital_id="hosp-a",
            campaign_id="camp-a-1",
            patient_id="pat-a-1",
            state=TaskStateEnum.CALLBACK_SCHEDULED,
            priority_score=90.0,
            attempt_count=0,
            max_attempts=3,
            scheduled_callback_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(cb_task)
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Manager B attempts to trigger Hospital A task
        res = await client.post(
            "/api/v1/calls/simulate",
            json={"task_id": "task-cb-tenant-1", "simulated_outcome": "COMPLETED"},
            headers=mgr_b_headers
        )
        assert res.status_code == 404
