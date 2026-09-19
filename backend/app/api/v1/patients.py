from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.domain import (
    Patient, Encounter, Discharge, OutreachTask, Call, TriageAssessment,
    ConsensusDecision, Escalation, EHRRecord, AuditLog, User
)
from app.schemas.domain import PatientOut, PatientTimelineOut, TimelineEvent, PatientCreate
from app.core.dependencies import get_current_user, get_tenant_hospital_id

router = APIRouter()

@router.get("/", response_model=List[PatientOut])
async def list_patients(
    query: Optional[str] = Query(None, description="Search by name or MRN"),
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Patient).where(Patient.hospital_id == hospital_id)
    if query:
        q_like = f"%{query}%"
        stmt = stmt.where(or_(
            Patient.mrn.ilike(q_like),
            Patient.first_name.ilike(q_like),
            Patient.last_name.ilike(q_like)
        ))
    stmt = stmt.order_by(Patient.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{patient_id}/timeline", response_model=PatientTimelineOut)
async def get_patient_timeline(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    # Fetch Patient
    stmt = select(Patient).where(Patient.id == patient_id, Patient.hospital_id == hospital_id)
    res = await db.execute(stmt)
    patient = res.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or tenant access denied")

    # Encounters
    res_enc = await db.execute(select(Encounter).where(Encounter.patient_id == patient_id))
    encounters = res_enc.scalars().all()

    # Discharges
    res_dis = await db.execute(select(Discharge).where(Discharge.patient_id == patient_id))
    discharges = res_dis.scalars().all()

    # Tasks
    res_tasks = await db.execute(select(OutreachTask).where(OutreachTask.patient_id == patient_id))
    tasks = res_tasks.scalars().all()

    # Calls
    res_calls = await db.execute(select(Call).where(Call.patient_id == patient_id))
    calls = res_calls.scalars().all()

    # Escalations
    res_esc = await db.execute(select(Escalation).where(Escalation.patient_id == patient_id))
    escalations = res_esc.scalars().all()

    # EHR Records
    res_ehr = await db.execute(select(EHRRecord).where(EHRRecord.patient_id == patient_id))
    ehr_records = res_ehr.scalars().all()

    events: List[TimelineEvent] = []

    # Build chronological timeline
    for d in discharges:
        events.append(TimelineEvent(
            event_type="DISCHARGE",
            timestamp=d.discharge_timestamp,
            title="Patient Discharged",
            description=f"Follow-up window: {d.follow_up_window_hours}h. Risk Tier: {d.risk_tier}",
            metadata={"instructions": d.discharge_instructions}
        ))

    for t in tasks:
        events.append(TimelineEvent(
            event_type="QUEUE_TASK",
            timestamp=t.created_at,
            title=f"Outreach Task State: {t.state.value if hasattr(t.state, 'value') else t.state}",
            description=f"Priority score: {t.priority_score}. Attempts: {t.attempt_count}/{t.max_attempts}",
            metadata={"task_id": t.id, "state": str(t.state)}
        ))

    for c in calls:
        events.append(TimelineEvent(
            event_type="CALL_ATTEMPT",
            timestamp=c.started_at,
            title=f"Outbound Call ({c.outcome})",
            description=f"Duration: {c.duration_seconds}s. Status: {c.status}",
            metadata={"call_id": c.id, "outcome": c.outcome}
        ))

    for e in escalations:
        events.append(TimelineEvent(
            event_type="CLINICAL_ESCALATION",
            timestamp=e.created_at,
            title=f"Clinical Escalation Created ({e.priority})",
            description=f"Trigger: {e.trigger_reason}",
            metadata={"escalation_id": e.id, "state": str(e.state), "resolution": e.resolution_notes}
        ))

    for eh in ehr_records:
        events.append(TimelineEvent(
            event_type="EHR_SYNC",
            timestamp=eh.synced_at,
            title=f"Mock EHR Record Created ({eh.resource_type})",
            description=f"Resource ID: {eh.resource_id}",
            metadata=eh.data
        ))

    events.sort(key=lambda x: x.timestamp, reverse=True)

    return {
        "patient": patient,
        "encounters": encounters,
        "discharges": discharges,
        "timeline": events
    }
