import pytest
import asyncio
from datetime import datetime, timedelta
from app.queue.queue_engine import QueueEngine
from app.models.domain import OutreachTask, TaskStateEnum
from tests.conftest import TestingSessionLocal

@pytest.mark.asyncio
async def test_queue_prioritization_formula(seed_test_data):
    async with TestingSessionLocal() as db:
        qe = QueueEngine(db, "hosp-a")
        now = datetime.utcnow()

        # High risk vs Low risk
        score_high = qe.calculate_priority_score("HIGH", now, None, None, 5, 0)
        score_low = qe.calculate_priority_score("LOW", now, None, None, 5, 0)
        assert score_high > score_low

        # Deadline pressure
        score_cutoff_near = qe.calculate_priority_score("MEDIUM", now, now + timedelta(hours=2), None, 5, 0)
        score_cutoff_far = qe.calculate_priority_score("MEDIUM", now, now + timedelta(hours=48), None, 5, 0)
        assert score_cutoff_near > score_cutoff_far

        # Callback urgency
        score_callback_due = qe.calculate_priority_score("MEDIUM", now, None, now - timedelta(minutes=10), 5, 0)
        assert score_callback_due > score_low

@pytest.mark.asyncio
async def test_concurrent_capacity_reservation(seed_test_data):
    async with TestingSessionLocal() as db:
        qe = QueueEngine(db, "hosp-a") # Max concurrent calls = 2
        now = datetime.utcnow()

        # Create 3 pending tasks
        task1 = OutreachTask(id="task-c1", hospital_id="hosp-a", campaign_id="camp-a-1", patient_id="pat-a-1", state=TaskStateEnum.PENDING, priority_score=90.0)
        task2 = OutreachTask(id="task-c2", hospital_id="hosp-a", campaign_id="camp-a-1", patient_id="pat-a-1", state=TaskStateEnum.PENDING, priority_score=80.0)
        task3 = OutreachTask(id="task-c3", hospital_id="hosp-a", campaign_id="camp-a-1", patient_id="pat-a-1", state=TaskStateEnum.PENDING, priority_score=70.0)
        db.add_all([task1, task2, task3])
        await db.commit()

        # Reserve slot 1 & slot 2
        res1 = await qe.reserve_next_task(worker_id="worker-1")
        res2 = await qe.reserve_next_task(worker_id="worker-2")
        assert res1 is not None and res1.id == "task-c1"
        assert res2 is not None and res2.id == "task-c2"

        # Attempt to reserve slot 3 -> Must fail because capacity limit (2) is reached
        res3 = await qe.reserve_next_task(worker_id="worker-3")
        assert res3 is None

@pytest.mark.asyncio
async def test_retries_and_exponential_backoff(seed_test_data):
    async with TestingSessionLocal() as db:
        qe = QueueEngine(db, "hosp-a")
        task = OutreachTask(id="task-retry-1", hospital_id="hosp-a", campaign_id="camp-a-1", patient_id="pat-a-1", state=TaskStateEnum.CALLING, attempt_count=0, max_attempts=3)
        db.add(task)
        await db.commit()

        # Attempt 1 NO_ANSWER -> RETRY_SCHEDULED with 15m delay
        updated1 = await qe.record_task_outcome("task-retry-1", "NO_ANSWER")
        assert updated1.state == TaskStateEnum.RETRY_SCHEDULED
        assert updated1.attempt_count == 1
        assert updated1.next_attempt_at > datetime.utcnow()

        # Attempt 3 NO_ANSWER -> Exhausted retries -> MANUAL_FOLLOW_UP
        updated1.attempt_count = 2
        updated1.state = TaskStateEnum.CALLING
        await db.commit()

        updated3 = await qe.record_task_outcome("task-retry-1", "NO_ANSWER")
        assert updated3.state == TaskStateEnum.MANUAL_FOLLOW_UP

@pytest.mark.asyncio
async def test_callback_explicit_scheduling(seed_test_data):
    async with TestingSessionLocal() as db:
        qe = QueueEngine(db, "hosp-a")
        task = OutreachTask(id="task-cb-1", hospital_id="hosp-a", campaign_id="camp-a-1", patient_id="pat-a-1", state=TaskStateEnum.CALLING)
        db.add(task)
        await db.commit()

        cb_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        updated = await qe.record_task_outcome("task-cb-1", "CALLBACK_REQUESTED", requested_callback_iso=cb_time)
        assert updated.state == TaskStateEnum.CALLBACK_SCHEDULED
        assert updated.scheduled_callback_at is not None

@pytest.mark.asyncio
async def test_worker_failure_recovery(seed_test_data):
    async with TestingSessionLocal() as db:
        qe = QueueEngine(db, "hosp-a")
        stale_time = datetime.utcnow() - timedelta(minutes=10)
        task = OutreachTask(id="task-stale-1", hospital_id="hosp-a", campaign_id="camp-a-1", patient_id="pat-a-1", state=TaskStateEnum.CALLING, worker_id="crashed-worker", locked_at=stale_time, attempt_count=0, max_attempts=3)
        db.add(task)
        await db.commit()

        recovered_count = await qe.recover_stale_tasks(timeout_minutes=5)
        assert recovered_count == 1
        await db.refresh(task)
        assert task.state == TaskStateEnum.RETRY_SCHEDULED
        assert task.worker_id is None
