import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import (
    ConsensusDecision, EscalationAssessment, TriageClassificationEnum,
    AuditLog, AIUsage
)
from app.ai.provider import get_ai_provider
from app.ai.prompts import (
    ASSESSMENT_A_SYSTEM_PROMPT, ASSESSMENT_B_SYSTEM_PROMPT, CURRENT_PROMPT_VERSION,
    format_rag_prompt_context
)
from app.tools.controlled_tools import ControlledTools
from app.core.config import settings

class ConsensusEngine:
    """
    Multi-Assessment & Consensus Escalation System.
    Combines Assessment A (Protocol Focus), Assessment B (Holistic Focus), and Rule Engine.
    Detects disagreements and applies configurable conservative escalation policies.
    """
    
    def __init__(self, db: AsyncSession, hospital_id: str):
        self.db = db
        self.hospital_id = hospital_id
        self.ai_provider = get_ai_provider()
        self.tools = ControlledTools(db, hospital_id)

    def run_rule_engine(self, transcript: str, protocol_red_flags: List[str]) -> Dict[str, Any]:
        t_lower = transcript.lower()
        triggered_flags = []
        
        # Protocol Red Flags Check
        for flag in protocol_red_flags:
            if flag.lower() in t_lower:
                triggered_flags.append(flag)
                
        # Baseline Red Flags
        base_flags = [
            ("chest pain", "CHEST_PAIN"),
            ("shortness of breath", "SHORTNESS_OF_BREATH"),
            ("difficulty breathing", "DYSPNEA"),
            ("severe bleeding", "HEMORRHAGE"),
            ("fainting", "SYNCOPE"),
            ("high fever", "FEVER")
        ]
        for term, code in base_flags:
            if term in t_lower:
                triggered_flags.append(code)
                
        if any(code in ["CHEST_PAIN", "SHORTNESS_OF_BREATH", "DYSPNEA", "HEMORRHAGE"] for code in triggered_flags):
            classification = TriageClassificationEnum.URGENT
        elif triggered_flags:
            classification = TriageClassificationEnum.CONCERNING
        else:
            classification = TriageClassificationEnum.ROUTINE
            
        return {
            "classification": classification.value,
            "triggered_flags": triggered_flags,
            "rule_escalate": classification in [TriageClassificationEnum.URGENT, TriageClassificationEnum.CONCERNING]
        }

    async def evaluate_consensus(
        self,
        call_id: str,
        patient_id: str,
        campaign_id: str,
        transcript: str,
        protocol_red_flags: List[str],
        rag_evidence: Optional[List[Dict[str, Any]]] = None
    ) -> ConsensusDecision:
        schema = {
            "classification": "ROUTINE | CONCERNING | URGENT | UNCERTAIN",
            "observations": ["string"],
            "red_flags": ["string"],
            "evidence": ["string"],
            "confidence": 0.9,
            "escalation_recommendation": True
        }
        
        evidence_context = rag_evidence or []
        formatted_prompt = format_rag_prompt_context(transcript, evidence_context)
        
        # 1. Execute Assessment A (Protocol Focus)
        t0 = time.time()
        try:
            assessment_a = await self.ai_provider.generate_structured(
                prompt=formatted_prompt,
                system_instruction=ASSESSMENT_A_SYSTEM_PROMPT,
                response_schema=schema,
                prompt_version=CURRENT_PROMPT_VERSION
            )
            assessment_a["provider"] = settings.AI_PROVIDER
            assessment_a["model"] = settings.AI_MODEL
            assessment_a["agent_role"] = "Protocol Focus"
            lat_a = int((time.time() - t0) * 1000)
            self.db.add(AIUsage(
                id=str(uuid.uuid4()),
                hospital_id=self.hospital_id,
                agent_name="Assessment A (Protocol Focus)",
                provider=settings.AI_PROVIDER,
                model=settings.AI_MODEL,
                prompt_version=CURRENT_PROMPT_VERSION,
                latency_ms=lat_a,
                success=True,
                created_at=datetime.utcnow()
            ))
        except Exception as err:
            lat_a = int((time.time() - t0) * 1000)
            self.db.add(AIUsage(
                id=str(uuid.uuid4()),
                hospital_id=self.hospital_id,
                agent_name="Assessment A (Protocol Focus)",
                provider=settings.AI_PROVIDER,
                model=settings.AI_MODEL,
                prompt_version=CURRENT_PROMPT_VERSION,
                latency_ms=lat_a,
                success=False,
                error_message=str(err),
                created_at=datetime.utcnow()
            ))
            await self.db.commit()
            raise err

        # 2. Execute Assessment B (Holistic Focus)
        t1 = time.time()
        try:
            assessment_b = await self.ai_provider.generate_structured(
                prompt=formatted_prompt,
                system_instruction=ASSESSMENT_B_SYSTEM_PROMPT,
                response_schema=schema,
                prompt_version=CURRENT_PROMPT_VERSION
            )
            assessment_b["provider"] = settings.AI_PROVIDER
            assessment_b["model"] = settings.AI_MODEL
            assessment_b["agent_role"] = "Holistic Focus"
            lat_b = int((time.time() - t1) * 1000)
            self.db.add(AIUsage(
                id=str(uuid.uuid4()),
                hospital_id=self.hospital_id,
                agent_name="Assessment B (Holistic Focus)",
                provider=settings.AI_PROVIDER,
                model=settings.AI_MODEL,
                prompt_version=CURRENT_PROMPT_VERSION,
                latency_ms=lat_b,
                success=True,
                created_at=datetime.utcnow()
            ))
        except Exception as err:
            lat_b = int((time.time() - t1) * 1000)
            self.db.add(AIUsage(
                id=str(uuid.uuid4()),
                hospital_id=self.hospital_id,
                agent_name="Assessment B (Holistic Focus)",
                provider=settings.AI_PROVIDER,
                model=settings.AI_MODEL,
                prompt_version=CURRENT_PROMPT_VERSION,
                latency_ms=lat_b,
                success=False,
                error_message=str(err),
                created_at=datetime.utcnow()
            ))
            await self.db.commit()
            raise err


        # 3. Execute Rule Engine
        rule_res = self.run_rule_engine(transcript, protocol_red_flags)
        
        # Record EscalationAssessment record
        ea_id = str(uuid.uuid4())
        esc_assessment = EscalationAssessment(
            id=ea_id,
            call_id=call_id,
            hospital_id=self.hospital_id,
            assessment_a=assessment_a,
            assessment_b=assessment_b,
            rule_engine_result=rule_res,
            prompt_version=CURRENT_PROMPT_VERSION,
            created_at=datetime.utcnow()
        )
        self.db.add(esc_assessment)
        
        # 4. Consensus Decision Logic
        class_a = assessment_a.get("classification", "ROUTINE").upper()
        class_b = assessment_b.get("classification", "ROUTINE").upper()
        class_rule = rule_res["classification"].upper()
        
        classifications = [class_a, class_b, class_rule]
        
        # Detect disagreement
        is_disagreement = len(set(classifications)) > 1
        
        policy = settings.CONSENSUS_POLICY
        final_classification = TriageClassificationEnum.ROUTINE
        should_escalate = False
        rationale = ""
        
        if policy == "STRICT_CONSERVATIVE":
            if "URGENT" in classifications:
                final_classification = TriageClassificationEnum.URGENT
                should_escalate = True
                rationale = f"Strict conservative policy triggered by URGENT classification (A: {class_a}, B: {class_b}, Rule: {class_rule})."
            elif "CONCERNING" in classifications or "UNCERTAIN" in classifications:
                final_classification = TriageClassificationEnum.CONCERNING if "CONCERNING" in classifications else TriageClassificationEnum.UNCERTAIN
                should_escalate = True
                rationale = f"Strict conservative policy triggered by concerning/uncertain status (A: {class_a}, B: {class_b}, Rule: {class_rule})."
            else:
                final_classification = TriageClassificationEnum.ROUTINE
                should_escalate = False
                rationale = "All assessments converged on ROUTINE status."
        elif policy == "MAJORITY_VOTE":
            urgent_count = classifications.count("URGENT")
            concerning_count = classifications.count("CONCERNING")
            if urgent_count >= 2:
                final_classification = TriageClassificationEnum.URGENT
                should_escalate = True
            elif concerning_count >= 2 or (urgent_count + concerning_count) >= 2:
                final_classification = TriageClassificationEnum.CONCERNING
                should_escalate = True
            else:
                final_classification = TriageClassificationEnum.ROUTINE
                should_escalate = False
            rationale = f"Majority vote result: {final_classification.value} (A: {class_a}, B: {class_b}, Rule: {class_rule})."
        else: # RULE_OVERRIDE_ONLY
            if class_rule in ["URGENT", "CONCERNING"]:
                final_classification = TriageClassificationEnum(class_rule)
                should_escalate = True
                rationale = f"Rule engine override triggered escalation: {class_rule}."
            else:
                final_classification = TriageClassificationEnum(class_a)
                should_escalate = assessment_a.get("escalation_recommendation", False)
                rationale = f"Assessment A classification: {class_a}."

        decision_id = str(uuid.uuid4())
        decision = ConsensusDecision(
            id=decision_id,
            call_id=call_id,
            hospital_id=self.hospital_id,
            patient_id=patient_id,
            consensus_classification=final_classification,
            is_disagreement=is_disagreement,
            consensus_policy_used=policy,
            final_escalation_recommendation=should_escalate,
            rationale=rationale,
            created_at=datetime.utcnow()
        )
        self.db.add(decision)
        
        # 5. Execute controlled escalation tool if recommended
        if should_escalate:
            evidence_list = assessment_a.get("evidence", []) + assessment_b.get("evidence", []) + [f"Rule flags: {rule_res['triggered_flags']}"]
            if evidence_context:
                for item in evidence_context:
                    t_name = item.get("title", item.get("document_title", "Protocol"))
                    txt = item.get("text", "")[:120]
                    sc = item.get("score", 0.0)
                    evidence_list.append(f"RAG Evidence [{t_name} v{item.get('version', '1.0.0')} - Score {sc}]: {txt}")
                    
            indicators = assessment_a.get("red_flags", []) + assessment_b.get("red_flags", []) + rule_res["triggered_flags"]
            await self.tools.create_escalation(
                patient_id=patient_id,
                call_id=call_id,
                campaign_id=campaign_id,
                priority=final_classification.value,
                trigger_reason=rationale,
                clinical_indicators=list(set(indicators)),
                evidence=list(set(evidence_list))
            )
            
        await self.db.flush()
        return decision

