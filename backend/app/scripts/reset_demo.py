import asyncio
import logging
import os
import sys
from sqlalchemy import delete

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import AsyncSessionLocal
from app.models.domain import (
    EHRRecord, AuditLog, Notification, AIUsage, Event, SystemHealth,
    Documentation, ConsensusDecision, EscalationAssessment, TriageAssessment, Escalation,
    Conversation, Call, OutreachTask, CampaignEligibility, Campaign,
    KnowledgeChunk, KnowledgeDocument, Protocol,
    Procedure, CarePlan, Medication, Observation, Condition, Discharge, Encounter, Patient
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reset_demo")

async def reset_demo_data():
    """
    Safely reset operational and demo data from the database while preserving:
    - Database schema & Alembic tables
    - Tenant hospitals and system auth users
    - Startup configurations
    """
    logger.info("Resetting operational database records...")
    async with AsyncSessionLocal() as db:
        # Delete operational tables in strict reverse-dependency order
        operational_models = [
            # 1. Independent logs, system events, and health metrics
            EHRRecord,
            AuditLog,
            Notification,
            AIUsage,
            Event,
            SystemHealth,
            
            # 2. AI assessments, consensus decisions, and clinical escalations
            Documentation,
            ConsensusDecision,
            EscalationAssessment,
            TriageAssessment,
            Escalation,
            
            # 3. Conversations and Calls
            Conversation,
            Call,
            
            # 4. Outreach queue tasks and campaign eligibility records
            OutreachTask,
            CampaignEligibility,
            
            # 5. Campaigns, Protocols, and Knowledge Base Resources
            Campaign,
            KnowledgeChunk,
            KnowledgeDocument,
            Protocol,
            
            # 6. Patient EHR clinical records
            Procedure,
            CarePlan,
            Medication,
            Observation,
            Condition,
            Discharge,
            Encounter,
            
            # 7. Patients
            Patient,
        ]

        for model in operational_models:
            await db.execute(delete(model))
        
        await db.commit()
        logger.info("Operational database tables cleared successfully. Users and Hospitals preserved.")

if __name__ == "__main__":
    asyncio.run(reset_demo_data())
