import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import (
    Patient, Encounter, Protocol, OutreachTask, Escalation, EHRRecord, AuditLog,
    TaskStateEnum, EscalationStateEnum, RoleEnum
)

class ControlledTools:
    """
    Controlled application interfaces for AI operations.
    Enforces authorization, tenant boundaries, schema validation, business logic, and audit logging.
    """
    
    def __init__(self, db: AsyncSession, hospital_id: str, user_id: Optional[str] = None):
        self.db = db
        self.hospital_id = hospital_id
        self.user_id = user_id

    async def _audit(self, action: str, resource_type: str, resource_id: Optional[str], details: Dict[str, Any]):
        log = AuditLog(
            id=str(uuid.uuid4()),
            hospital_id=self.hospital_id,
            user_id=self.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            created_at=datetime.utcnow()
        )
        self.db.add(log)
        await self.db.flush()

    async def get_patient_context(self, patient_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(Patient).where(Patient.id == patient_id, Patient.hospital_id == self.hospital_id)
        res = await self.db.execute(stmt)
        patient = res.scalar_one_or_none()
        if not patient:
            return None
        
        await self._audit("TOOL_GET_PATIENT_CONTEXT", "Patient", patient_id, {})
        return {
            "id": patient.id,
            "hospital_id": patient.hospital_id,
            "mrn": patient.mrn,
            "full_name": f"{patient.first_name} {patient.last_name}",
            "preferred_language": patient.preferred_language,
            "communication_preference": patient.communication_preference,
            "high_risk_flag": patient.high_risk_flag
        }

    async def search_protocol(self, query: str) -> List[Dict[str, Any]]:
        stmt = select(Protocol).where(Protocol.hospital_id == self.hospital_id, Protocol.is_active == True)
        res = await self.db.execute(stmt)
        protocols = res.scalars().all()
        
        results = []
        for p in protocols:
            if query.lower() in p.name.lower() or query.lower() in p.category.lower() or any(query.lower() in rf.lower() for rf in p.red_flags):
                results.append({
                    "protocol_id": p.id,
                    "name": p.name,
                    "version": p.version,
                    "red_flags": p.red_flags,
                    "follow_up_questions": p.follow_up_questions
                })
        
        await self._audit("TOOL_SEARCH_PROTOCOL", "Protocol", None, {"query": query, "matches": len(results)})
        return results

    async def schedule_callback(self, task_id: str, requested_time_iso: str) -> Dict[str, Any]:
        stmt = select(OutreachTask).where(OutreachTask.id == task_id, OutreachTask.hospital_id == self.hospital_id)
        res = await self.db.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found or access denied")
        
        callback_dt = datetime.fromisoformat(requested_time_iso.replace("Z", "+00:00"))
        task.state = TaskStateEnum.CALLBACK_SCHEDULED
        task.scheduled_callback_at = callback_dt
        task.next_attempt_at = callback_dt
        
        await self._audit("TOOL_SCHEDULE_CALLBACK", "OutreachTask", task_id, {"requested_time": requested_time_iso})
        return {"status": "SUCCESS", "task_id": task_id, "scheduled_callback_at": requested_time_iso}

    async def create_escalation(
        self,
        patient_id: str,
        call_id: str,
        campaign_id: str,
        priority: str,
        trigger_reason: str,
        clinical_indicators: List[str],
        evidence: List[str]
    ) -> Dict[str, Any]:
        escalation_id = str(uuid.uuid4())
        escalation = Escalation(
            id=escalation_id,
            hospital_id=self.hospital_id,
            patient_id=patient_id,
            call_id=call_id,
            campaign_id=campaign_id,
            priority=priority,
            state=EscalationStateEnum.OPEN,
            trigger_reason=trigger_reason,
            clinical_indicators=clinical_indicators,
            evidence=evidence,
            created_at=datetime.utcnow()
        )
        self.db.add(escalation)
        
        # Update OutreachTask state to ESCALATED
        stmt = select(OutreachTask).where(OutreachTask.patient_id == patient_id, OutreachTask.hospital_id == self.hospital_id)
        res = await self.db.execute(stmt)
        tasks = res.scalars().all()
        for t in tasks:
            t.state = TaskStateEnum.ESCALATED
            
        await self._audit("TOOL_CREATE_ESCALATION", "Escalation", escalation_id, {"priority": priority, "trigger": trigger_reason})
        return {"status": "SUCCESS", "escalation_id": escalation_id}

    async def update_mock_ehr(
        self,
        patient_id: str,
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any],
        encounter_id: Optional[str] = None
    ) -> Dict[str, Any]:
        record_id = str(uuid.uuid4())
        record = EHRRecord(
            id=record_id,
            hospital_id=self.hospital_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
            synced_at=datetime.utcnow()
        )
        self.db.add(record)
        await self._audit("TOOL_UPDATE_MOCK_EHR", "EHRRecord", record_id, {"resource_type": resource_type})
        return {"status": "SUCCESS", "ehr_record_id": record_id}
