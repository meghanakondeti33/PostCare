import random
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import OutreachTask, Patient, Campaign, Call, TaskStateEnum
from app.schemas.domain import OutreachTaskOut, QueueSummaryOut
from app.queue.queue_engine import QueueEngine
from app.core.dependencies import get_tenant_hospital_id

router = APIRouter()

@router.get("/summary", response_model=QueueSummaryOut)
async def get_queue_summary(
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    qe = QueueEngine(db, hospital_id)
    return await qe.get_queue_summary()

@router.get("/tasks", response_model=List[OutreachTaskOut])
async def list_queue_tasks(
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(OutreachTask, Patient).join(Patient, OutreachTask.patient_id == Patient.id).where(OutreachTask.hospital_id == hospital_id)
    
    if state:
        stmt = stmt.where(OutreachTask.state == state.upper())
        
    stmt = stmt.order_by(OutreachTask.priority_score.desc()).limit(100)
    res = await db.execute(stmt)
    rows = res.all()
    
    tasks_out = []
    for task, patient in rows:
        t_dict = {
            "id": task.id,
            "hospital_id": task.hospital_id,
            "campaign_id": task.campaign_id,
            "patient_id": task.patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "patient_mrn": patient.mrn,
            "state": task.state,
            "priority_score": task.priority_score,
            "attempt_count": task.attempt_count,
            "max_attempts": task.max_attempts,
            "next_attempt_at": task.next_attempt_at,
            "scheduled_callback_at": task.scheduled_callback_at,
            "clinical_cutoff_at": task.clinical_cutoff_at,
            "partial_context": task.partial_context or {},
            "created_at": task.created_at
        }
        tasks_out.append(t_dict)
    return tasks_out

@router.post("/simulate_step")
async def simulate_queue_step(
    simulated_outcome: Optional[str] = Query(None, description="Force outcome: COMPLETED, NO_ANSWER, BUSY, VOICEMAIL, DROPPED, CALLBACK_REQUESTED, ESCALATED"),
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    """
    Executes a single step of the Intelligent Queue Simulation:
    1. Reserves highest priority task respecting hospital concurrency limit (FOR UPDATE SKIP LOCKED).
    2. Simulates or processes call outcome.
    3. Handles retries with exponential backoff, callbacks, or manual escalation.
    """
    qe = QueueEngine(db, hospital_id)
    worker_id = f"sim-worker-{random.randint(100, 999)}"
    
    task = await qe.reserve_next_task(worker_id=worker_id)
    if not task:
        summary = await qe.get_queue_summary()
        return {
            "status": "NO_WORK_RESERVED",
            "message": "Capacity limit reached or no pending tasks due for attempt.",
            "summary": summary
        }
        
    # Determine outcome
    possible_outcomes = ["COMPLETED", "COMPLETED", "NO_ANSWER", "BUSY", "VOICEMAIL", "DROPPED"]
    outcome = simulated_outcome if simulated_outcome else random.choice(possible_outcomes)
    
    updated_task = await qe.record_task_outcome(
        task_id=task.id,
        outcome=outcome,
        conversation_context={"simulated_by": worker_id, "last_outcome": outcome}
    )
    await db.commit()
    
    return {
        "status": "STEP_EXECUTED",
        "reserved_task_id": task.id,
        "patient_id": task.patient_id,
        "worker_id": worker_id,
        "outcome": outcome,
        "new_task_state": str(updated_task.state),
        "attempt_count": updated_task.attempt_count
    }

@router.post("/schedule_callback")
async def schedule_callback(
    task_id: str,
    requested_time_iso: str,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    from app.tools.controlled_tools import ControlledTools
    tools = ControlledTools(db, hospital_id)
    res = await tools.schedule_callback(task_id, requested_time_iso)
    await db.commit()
    return res

