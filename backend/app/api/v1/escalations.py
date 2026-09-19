from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.domain import (
    Escalation, Patient, Call, Conversation, TriageAssessment, ConsensusDecision,
    EscalationAssessment, EscalationStateEnum, User, RoleEnum, AuditLog,
    Documentation, EHRRecord, OutreachTask, TaskStateEnum
)
from app.schemas.domain import EscalationOut, EscalationUpdate
from app.core.dependencies import get_current_user, get_tenant_hospital_id, require_roles
from app.tools.controlled_tools import ControlledTools

router = APIRouter()

@router.get("/", response_model=List[EscalationOut])
async def list_escalations(
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Escalation, Patient, User).join(Patient, Escalation.patient_id == Patient.id).outerjoin(User, Escalation.assigned_reviewer_id == User.id).where(Escalation.hospital_id == hospital_id)
    
    if state:
        stmt = stmt.where(Escalation.state == state.upper())
        
    stmt = stmt.order_by(Escalation.created_at.desc())
    res = await db.execute(stmt)
    rows = res.all()
    
    out = []
    for esc, patient, reviewer in rows:
        out.append({
            "id": esc.id,
            "hospital_id": esc.hospital_id,
            "patient_id": esc.patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "call_id": esc.call_id,
            "campaign_id": esc.campaign_id,
            "priority": esc.priority,
            "state": esc.state,
            "assigned_reviewer_id": esc.assigned_reviewer_id,
            "assigned_reviewer_name": reviewer.full_name if reviewer else None,
            "trigger_reason": esc.trigger_reason,
            "clinical_indicators": esc.clinical_indicators or [],
            "evidence": esc.evidence or [],
            "resolution_notes": esc.resolution_notes,
            "resolved_at": esc.resolved_at,
            "created_at": esc.created_at
        })
    return out

@router.get("/{escalation_id}", response_model=Dict[str, Any])
async def get_escalation_detail(
    escalation_id: str,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Escalation, Patient).join(Patient, Escalation.patient_id == Patient.id).where(Escalation.id == escalation_id, Escalation.hospital_id == hospital_id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Escalation not found")
        
    esc, patient = row
    
    # Fetch related call & conversation
    res_call = await db.execute(select(Call).where(Call.id == esc.call_id))
    call = res_call.scalar_one_or_none()
    
    res_conv = await db.execute(select(Conversation).where(Conversation.call_id == esc.call_id))
    conv = res_conv.scalar_one_or_none()
    
    # Fetch Assessments & Consensus
    res_ea = await db.execute(select(EscalationAssessment).where(EscalationAssessment.call_id == esc.call_id))
    ea = res_ea.scalar_one_or_none()
    
    res_cd = await db.execute(select(ConsensusDecision).where(ConsensusDecision.call_id == esc.call_id))
    cd = res_cd.scalar_one_or_none()
    
    from fastapi.encoders import jsonable_encoder
    return jsonable_encoder({
        "escalation": esc,
        "patient": patient,
        "call": call,
        "conversation": conv,
        "dual_assessment": ea,
        "consensus_decision": cd
    })

@router.put("/{escalation_id}/action", response_model=EscalationOut)
async def update_escalation_action(
    escalation_id: str,
    data: EscalationUpdate,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id),
    current_user: User = Depends(require_roles([RoleEnum.CLINICAL_REVIEWER, RoleEnum.HOSPITAL_ADMIN]))
):
    stmt = select(Escalation).where(Escalation.id == escalation_id, Escalation.hospital_id == hospital_id)
    res = await db.execute(stmt)
    esc = res.scalar_one_or_none()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
        
    if not esc.assigned_reviewer_id:
        esc.assigned_reviewer_id = current_user.id

    if data.state:
        esc.state = data.state
        if data.state in [EscalationStateEnum.RESOLVED, EscalationStateEnum.CLOSED]:
            esc.resolved_at = datetime.utcnow()

            # Idempotently sync resolution to Mock EHR
            res_ehr = await db.execute(
                select(EHRRecord).where(
                    EHRRecord.hospital_id == hospital_id,
                    EHRRecord.patient_id == esc.patient_id,
                    EHRRecord.resource_type == "EscalationResolution",
                    EHRRecord.resource_id == esc.id
                )
            )
            existing_ehr = res_ehr.scalar_one_or_none()
            if not existing_ehr:
                tools = ControlledTools(db, hospital_id, user_id=current_user.id)
                await tools.update_mock_ehr(
                    patient_id=esc.patient_id,
                    resource_type="EscalationResolution",
                    resource_id=esc.id,
                    data={
                        "escalation_id": esc.id,
                        "priority": esc.priority,
                        "state": data.state,
                        "resolution_notes": data.resolution_notes or "Resolved by Clinical Reviewer",
                        "resolved_by": current_user.full_name,
                        "resolved_at": datetime.utcnow().isoformat()
                    }
                )

            # Idempotently update or create Clinical Documentation
            if esc.call_id:
                res_doc = await db.execute(select(Documentation).where(Documentation.call_id == esc.call_id))
                doc = res_doc.scalar_one_or_none()
                if doc:
                    doc.triage_result = data.state
                    doc.ehr_synced = True
                    if data.resolution_notes:
                        doc.summary = f"{doc.summary} | Clinical Resolution: {data.resolution_notes}"
                else:
                    doc = Documentation(
                        id=f"doc-{esc.call_id or esc.id}",
                        call_id=esc.call_id or f"call-{esc.id}",
                        hospital_id=hospital_id,
                        patient_id=esc.patient_id,
                        summary=f"Clinical Escalation Resolution ({esc.priority}): {data.resolution_notes or 'Resolved'}",
                        patient_reported_symptoms=esc.clinical_indicators or [],
                        triage_result=data.state,
                        ehr_synced=True
                    )
                    db.add(doc)

                # Update associated OutreachTask state
                res_call = await db.execute(select(Call).where(Call.id == esc.call_id))
                call = res_call.scalar_one_or_none()
                if call and call.task_id:
                    res_task = await db.execute(select(OutreachTask).where(OutreachTask.id == call.task_id))
                    task = res_task.scalar_one_or_none()
                    if task and task.state == TaskStateEnum.ESCALATED:
                        task.state = TaskStateEnum.COMPLETED

    if data.assigned_reviewer_id:
        esc.assigned_reviewer_id = data.assigned_reviewer_id
        if esc.state == EscalationStateEnum.OPEN:
            esc.state = EscalationStateEnum.ASSIGNED
            
    if data.resolution_notes:
        esc.resolution_notes = data.resolution_notes
        
    # Audit trail entry
    log = AuditLog(
        id=f"audit-{datetime.utcnow().timestamp()}",
        hospital_id=hospital_id,
        user_id=current_user.id,
        action="ESCALATION_UPDATED",
        resource_type="Escalation",
        resource_id=esc.id,
        details={"state": str(esc.state), "resolution": data.resolution_notes},
        created_at=datetime.utcnow()
    )
    db.add(log)
    
    await db.commit()
    await db.refresh(esc)
    
    stmt_pat = select(Patient).where(Patient.id == esc.patient_id)
    res_pat = await db.execute(stmt_pat)
    patient = res_pat.scalar_one()
    
    return {
        "id": esc.id,
        "hospital_id": esc.hospital_id,
        "patient_id": esc.patient_id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "call_id": esc.call_id,
        "campaign_id": esc.campaign_id,
        "priority": esc.priority,
        "state": esc.state,
        "assigned_reviewer_id": esc.assigned_reviewer_id,
        "assigned_reviewer_name": current_user.full_name,
        "trigger_reason": esc.trigger_reason,
        "clinical_indicators": esc.clinical_indicators or [],
        "evidence": esc.evidence or [],
        "resolution_notes": esc.resolution_notes,
        "resolved_at": esc.resolved_at,
        "created_at": esc.created_at
    }
