import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import (
    Call, Conversation, OutreachTask, Patient, Protocol, TriageAssessment,
    ConsensusDecision, Documentation, TaskStateEnum, AIUsage
)
from app.schemas.domain import CallCreateSimulation, CallOut
from app.ai.provider import get_ai_provider
from app.ai.prompts import (
    VOICE_INTAKE_SYSTEM_PROMPT, CLINICAL_TRIAGE_SYSTEM_PROMPT, CURRENT_PROMPT_VERSION,
    format_rag_prompt_context
)
from app.ai.consensus import ConsensusEngine
from app.rag.protocol_rag import ProtocolRAGService
from app.tools.controlled_tools import ControlledTools
from app.core.dependencies import get_tenant_hospital_id
from app.core.config import settings

router = APIRouter()

@router.post("/simulate", response_model=Dict[str, Any])
async def simulate_outreach_call(
    data: CallCreateSimulation,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    # Fetch task & patient
    stmt = select(OutreachTask, Patient).join(Patient, OutreachTask.patient_id == Patient.id).where(OutreachTask.id == data.task_id, OutreachTask.hospital_id == hospital_id)
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="OutreachTask not found or access denied")
        
    task, patient = row
    call_id = f"call-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow()
    
    # 1. Fetch Hospital Protocol & Red Flags
    res_proto = await db.execute(select(Protocol).where(Protocol.hospital_id == hospital_id, Protocol.is_active == True))
    protocols = res_proto.scalars().all()
    red_flags = []
    for p in protocols:
        red_flags.extend(p.red_flags)

    # 2. Retrieve Tenant-Scoped RAG Evidence via ProtocolRAGService
    rag_service = ProtocolRAGService(db, hospital_id)
    responses = data.patient_responses or [
        f"I'm feeling ok, but I have some {patient.high_risk_flag and 'chest discomfort and shortness of breath' or 'mild pain'}."
    ]
    transcript_text = " ".join(responses)
    
    rag_evidence = await rag_service.retrieve_protocol_evidence(query=transcript_text, top_k=3)

    transcript_json = [
        {"speaker": "AI Voice Agent", "text": f"Hello {patient.first_name}, this is Post-Discharge Outreach checking on your recovery."},
        {"speaker": f"Patient ({patient.first_name} {patient.last_name})", "text": transcript_text},
        {"speaker": "AI Voice Agent", "text": "Thank you for providing that update. I am logging your observations."}
    ]
    
    # 3. Save Call & Conversation Records
    outcome = data.simulated_outcome or ("ESCALATED" if any(rf.lower() in transcript_text.lower() for rf in ["chest", "breath", "fever", "severe"]) else "COMPLETED")
    
    call = Call(
        id=call_id,
        hospital_id=hospital_id,
        task_id=task.id,
        campaign_id=task.campaign_id,
        patient_id=patient.id,
        status="COMPLETED",
        started_at=now,
        ended_at=now,
        duration_seconds=180,
        outcome=outcome,
        recording_url=f"http://localhost:8000/recordings/{call_id}.mp3"
    )
    db.add(call)
    
    conv = Conversation(
        id=f"conv-{call_id}",
        call_id=call_id,
        hospital_id=hospital_id,
        transcript_json=transcript_json,
        collected_data={"responses": responses, "rag_evidence": rag_evidence},
        prompt_version=CURRENT_PROMPT_VERSION
    )
    db.add(conv)
    
    # 4. Execute Clinical Triage Agent with RAG-enhanced Prompt
    ai_provider = get_ai_provider()
    triage_schema = {
        "classification": "ROUTINE | CONCERNING | URGENT | UNCERTAIN",
        "observations": ["string"],
        "red_flags": ["string"],
        "evidence": ["string"],
        "protocol_references": ["string"],
        "confidence": 0.95,
        "uncertainty": ["string"],
        "escalation_recommendation": True
    }
    
    triage_prompt = format_rag_prompt_context(transcript_text, rag_evidence)
    
    t0 = time.time()
    try:
        triage_res = await ai_provider.generate_structured(
            prompt=triage_prompt,
            system_instruction=CLINICAL_TRIAGE_SYSTEM_PROMPT,
            response_schema=triage_schema,
            prompt_version=CURRENT_PROMPT_VERSION
        )
        lat_ms = int((time.time() - t0) * 1000)
        db.add(AIUsage(
            id=str(uuid.uuid4()),
            hospital_id=hospital_id,
            agent_name="Clinical Triage Agent",
            provider=settings.AI_PROVIDER,
            model=settings.AI_MODEL,
            prompt_version=CURRENT_PROMPT_VERSION,
            latency_ms=lat_ms,
            success=True,
            created_at=datetime.utcnow()
        ))
    except Exception as err:
        lat_ms = int((time.time() - t0) * 1000)
        db.add(AIUsage(
            id=str(uuid.uuid4()),
            hospital_id=hospital_id,
            agent_name="Clinical Triage Agent",
            provider=settings.AI_PROVIDER,
            model=settings.AI_MODEL,
            prompt_version=CURRENT_PROMPT_VERSION,
            latency_ms=lat_ms,
            success=False,
            error_message=str(err),
            created_at=datetime.utcnow()
        ))
        await db.commit()
        raise err


    # Store structured RAG protocol references
    protocol_refs = triage_res.get("protocol_references", [])
    for item in rag_evidence:
        t_name = item.get("title", item.get("document_title", "Protocol"))
        ver = item.get("version", "1.0.0")
        protocol_refs.append(f"RAG: {t_name} v{ver} (Chunk {item.get('chunk_id', 'ref')})")
    
    triage = TriageAssessment(
        id=f"triage-{call_id}",
        call_id=call_id,
        hospital_id=hospital_id,
        patient_id=patient.id,
        agent_name="Clinical Triage Agent",
        classification=triage_res.get("classification", "ROUTINE"),
        observations=triage_res.get("observations", []),
        red_flags=triage_res.get("red_flags", []),
        evidence=triage_res.get("evidence", []),
        protocol_references=list(set(protocol_refs)),
        confidence=triage_res.get("confidence", 1.0),
        uncertainty=triage_res.get("uncertainty", []),
        prompt_version=CURRENT_PROMPT_VERSION
    )
    db.add(triage)
    
    # 5. Run Dual Assessment & Consensus Escalation Engine
    ce = ConsensusEngine(db, hospital_id)
    consensus = await ce.evaluate_consensus(
        call_id=call_id,
        patient_id=patient.id,
        campaign_id=task.campaign_id,
        transcript=transcript_text,
        protocol_red_flags=red_flags,
        rag_evidence=rag_evidence
    )

    
    # 6. Generate Documentation & Mock EHR Sync
    tools = ControlledTools(db, hospital_id)
    doc_summary = f"Post-Discharge Call Summary for {patient.first_name} {patient.last_name} (MRN: {patient.mrn}). Outcome: {outcome}. Triage: {consensus.consensus_classification.value}."
    doc = Documentation(
        id=f"doc-{call_id}",
        call_id=call_id,
        hospital_id=hospital_id,
        patient_id=patient.id,
        summary=doc_summary,
        patient_reported_symptoms=triage_res.get("observations", []),
        triage_result=consensus.consensus_classification.value,
        ehr_synced=True
    )
    db.add(doc)
    
    await tools.update_mock_ehr(
        patient_id=patient.id,
        resource_type="Communication",
        resource_id=f"COMM-{call_id}",
        data={"summary": doc_summary, "triage": consensus.consensus_classification.value, "call_id": call_id}
    )

    # 7. Update Task State & Attempt Metrics
    task.attempt_count += 1
    if consensus.final_escalation_recommendation:
        task.state = TaskStateEnum.ESCALATED
    else:
        task.state = TaskStateEnum.COMPLETED
        
    await db.commit()
    
    return {
        "call_id": call_id,
        "patient_id": patient.id,
        "outcome": outcome,
        "transcript": transcript_json,
        "triage_classification": consensus.consensus_classification.value,
        "is_disagreement": consensus.is_disagreement,
        "escalation_created": consensus.final_escalation_recommendation,
        "consensus_rationale": consensus.rationale
    }

@router.get("/{call_id}", response_model=Dict[str, Any])
async def get_call_details(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    hospital_id: str = Depends(get_tenant_hospital_id)
):
    stmt = select(Call).where(Call.id == call_id, Call.hospital_id == hospital_id)
    res = await db.execute(stmt)
    call = res.scalar_one_or_none()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
        
    res_conv = await db.execute(select(Conversation).where(Conversation.call_id == call_id))
    conv = res_conv.scalar_one_or_none()
    
    res_triage = await db.execute(select(TriageAssessment).where(TriageAssessment.call_id == call_id))
    triage = res_triage.scalar_one_or_none()
    
    res_consensus = await db.execute(select(ConsensusDecision).where(ConsensusDecision.call_id == call_id))
    consensus = res_consensus.scalar_one_or_none()
    
    return {
        "call": call,
        "conversation": conv,
        "triage": triage,
        "consensus": consensus
    }
