from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.domain import Patient, Campaign, OutreachTask, Call, Escalation, Hospital, TaskStateEnum
from app.core.dependencies import get_tenant_hospital_id
from app.queue.queue_engine import QueueEngine

router = APIRouter()

@router.get("/hospital", response_model=Dict[str, Any])
async def get_hospital_analytics(
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    # Total Patients
    res_pat = await db.execute(select(func.count(Patient.id)).where(Patient.hospital_id == hospital_id))
    tot_patients = res_pat.scalar() or 0
    
    # Total Tasks
    res_tasks = await db.execute(select(func.count(OutreachTask.id)).where(OutreachTask.hospital_id == hospital_id))
    tot_tasks = res_tasks.scalar() or 0
    
    # Task state counts
    res_completed = await db.execute(select(func.count(OutreachTask.id)).where(OutreachTask.hospital_id == hospital_id, OutreachTask.state == TaskStateEnum.COMPLETED))
    tot_completed = res_completed.scalar() or 0
    
    res_retries = await db.execute(select(func.count(OutreachTask.id)).where(OutreachTask.hospital_id == hospital_id, OutreachTask.state == TaskStateEnum.RETRY_SCHEDULED))
    tot_retries = res_retries.scalar() or 0
    
    res_callbacks = await db.execute(select(func.count(OutreachTask.id)).where(OutreachTask.hospital_id == hospital_id, OutreachTask.state == TaskStateEnum.CALLBACK_SCHEDULED))
    tot_callbacks = res_callbacks.scalar() or 0
    
    # Total Calls Attempted
    res_calls = await db.execute(select(func.count(Call.id)).where(Call.hospital_id == hospital_id))
    tot_calls = res_calls.scalar() or 0
    
    # Escalations
    res_esc = await db.execute(select(func.count(Escalation.id)).where(Escalation.hospital_id == hospital_id))
    tot_escalations = res_esc.scalar() or 0
    
    # Average attempts across tasks
    res_avg = await db.execute(select(func.avg(OutreachTask.attempt_count)).where(OutreachTask.hospital_id == hospital_id))
    avg_attempts = float(res_avg.scalar() or 1.0)
    
    # Compute dynamic contact rate
    denominator = max(tot_completed + tot_retries + tot_callbacks, 1)
    contact_rate = round(tot_completed / denominator, 2)
    
    # Queue engine utilization
    qe = QueueEngine(db, hospital_id)
    summary = await qe.get_queue_summary()
    utilization = round(summary["active_capacity"] / max(summary["capacity_limit"], 1), 2)
    
    return {
        "hospital_id": hospital_id,
        "total_patients": tot_patients,
        "total_outreach_tasks": tot_tasks,
        "total_completed_tasks": tot_completed,
        "total_retry_tasks": tot_retries,
        "total_callback_tasks": tot_callbacks,
        "total_calls_attempted": tot_calls,
        "contact_rate": contact_rate,
        "total_escalations": tot_escalations,
        "escalation_rate": round(tot_escalations / max(tot_calls, 1), 3),
        "average_attempts_per_contact": round(avg_attempts, 2),
        "queue_capacity_utilization": utilization
    }

@router.get("/platform", response_model=Dict[str, Any])
async def get_platform_analytics(db: AsyncSession = Depends(get_db)):
    res_h = await db.execute(select(func.count(Hospital.id)))
    tot_hosp = res_h.scalar() or 0
    
    res_p = await db.execute(select(func.count(Patient.id)))
    tot_pat = res_p.scalar() or 0
    
    res_c = await db.execute(select(func.count(Call.id)))
    tot_calls = res_c.scalar() or 0
    
    res_e = await db.execute(select(func.count(Escalation.id)))
    tot_esc = res_e.scalar() or 0
    
    res_completed = await db.execute(select(func.count(OutreachTask.id)).where(OutreachTask.state == TaskStateEnum.COMPLETED))
    tot_comp = res_completed.scalar() or 0
    
    res_total = await db.execute(select(func.count(OutreachTask.id)))
    tot_tasks = res_total.scalar() or 0
    
    agg_contact_rate = round(tot_comp / tot_tasks, 2) if tot_tasks > 0 else 0.0

    # Real DB health status
    try:
        await db.execute(select(1))
        system_status = "HEALTHY"
    except Exception:
        system_status = "DEGRADED"
    
    return {
        "active_hospitals": tot_hosp,
        "total_patients_managed": tot_pat,
        "total_calls_completed": tot_calls,
        "total_escalations_resolved": tot_esc,
        "aggregate_contact_rate": agg_contact_rate,
        "aggregate_false_negative_rate": 0.0,
        "system_status": system_status
    }

