import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
import random

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.domain import (
    Hospital, User, Patient, Encounter, Discharge, Condition, Observation,
    Medication, CarePlan, Procedure, Campaign, CampaignEligibility, OutreachTask,
    Call, Conversation, Protocol, KnowledgeDocument, KnowledgeChunk, TriageAssessment,
    EscalationAssessment, ConsensusDecision, Escalation, Documentation, EHRRecord,
    Notification, AuditLog, SystemHealth, RoleEnum, CampaignStatusEnum, TaskStateEnum,
    EscalationStateEnum, TriageClassificationEnum
)
from app.rag.protocol_rag import ProtocolRAGService



async def seed_database(drop_existing: bool = True):

    print("Initializing Database Schema...")
    async with engine.begin() as conn:
        if drop_existing:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        print("Seeding Hospitals...")
        hospitals = [
            Hospital(
                id="hosp-metro-1",
                name="MetroHealth System",
                code="METRO",
                timezone="America/New_York",
                calling_start_hour=8,
                calling_end_hour=20,
                max_concurrent_calls=10,
                retry_rules={"max_attempts": 3, "backoff_minutes": [15, 60, 240]},
                notification_config={"escalation_channel": "dashboard", "email_alerts": True},
                ehr_config={"sync_mode": "MOCK_FHIR_V4", "auto_sync_escalations": True},
                is_active=True
            ),
            Hospital(
                id="hosp-stjude-2",
                name="St. Jude Regional Medical Center",
                code="STJUDE",
                timezone="America/Chicago",
                calling_start_hour=8,
                calling_end_hour=19,
                max_concurrent_calls=5,
                retry_rules={"max_attempts": 3, "backoff_minutes": [15, 60]},
                is_active=True
            ),
            Hospital(
                id="hosp-cedar-3",
                name="Cedar Valley Community Hospital",
                code="CEDAR",
                timezone="America/Denver",
                calling_start_hour=9,
                calling_end_hour=20,
                max_concurrent_calls=8,
                is_active=True
            ),
            Hospital(
                id="hosp-apex-4",
                name="Apex Heart & Vascular Institute",
                code="APEX",
                timezone="America/Los_Angeles",
                calling_start_hour=8,
                calling_end_hour=21,
                max_concurrent_calls=15,
                is_active=True
            )
        ]
        db.add_all(hospitals)
        await db.flush()

        print("Seeding Demo Users...")
        default_pwd = get_password_hash("Pass123!")
        users = [
            User(id="usr-admin-0", hospital_id=None, email="admin@platform.gov", hashed_password=get_password_hash("AdminPass123!"), full_name="Platform Lead Administrator", role=RoleEnum.PLATFORM_ADMIN),
            User(id="usr-metro-admin", hospital_id="hosp-metro-1", email="admin@metrohealth.org", hashed_password=get_password_hash("MetroAdmin123!"), full_name="Dr. Eleanor Vance (Hospital Admin)", role=RoleEnum.HOSPITAL_ADMIN),
            User(id="usr-metro-mgr", hospital_id="hosp-metro-1", email="manager@metrohealth.org", hashed_password=get_password_hash("Manager123!"), full_name="Marcus Brody (Campaign Manager)", role=RoleEnum.CAMPAIGN_MANAGER),
            User(id="usr-metro-rev", hospital_id="hosp-metro-1", email="reviewer@metrohealth.org", hashed_password=get_password_hash("Reviewer123!"), full_name="Nurse Sarah Connor, RN (Clinical Reviewer)", role=RoleEnum.CLINICAL_REVIEWER),
            User(id="usr-stjude-mgr", hospital_id="hosp-stjude-2", email="manager@stjude.org", hashed_password=default_pwd, full_name="Rachel Green (St. Jude Manager)", role=RoleEnum.CAMPAIGN_MANAGER),
            User(id="usr-stjude-rev", hospital_id="hosp-stjude-2", email="reviewer@stjude.org", hashed_password=default_pwd, full_name="Dr. Ross Geller (St. Jude Reviewer)", role=RoleEnum.CLINICAL_REVIEWER)
        ]
        db.add_all(users)
        await db.flush()

        print("Seeding Protocols & Knowledge Resources...")
        proto_metro = Protocol(
            id="proto-metro-cardiac-1",
            hospital_id="hosp-metro-1",
            name="Post-Discharge Cardiac Protocol v2.1",
            version="2.1.0",
            category="Cardiology",
            target_conditions=["Heart Failure", "Myocardial Infarction", "Coronary Stent"],
            red_flags=["chest pain", "shortness of breath", "sudden weight gain", "dizziness", "leg swelling"],
            follow_up_questions=[
                "Have you experienced any chest tightness or discomfort since returning home?",
                "Are you having any shortness of breath while resting or lying flat?",
                "Have you weighed yourself this morning as instructed?",
                "Are you taking your prescribed blood thinners and beta blockers as directed?"
            ],
            escalation_contacts=["Cardiology On-Call Triage Nurse (Ext 4091)", "Dr. Vance Direct"],
            is_active=True
        )
        db.add(proto_metro)
        
        rag_metro = ProtocolRAGService(db, "hosp-metro-1")
        await rag_metro.ingest_protocol_document(
            title="MetroHealth Cardiac Outreach Care Standard",
            category="Clinical Guidelines",
            content="MetroHealth Post-Discharge Guidelines:\n\nPatients discharged following Acute Myocardial Infarction or Heart Failure exacerbation require mandatory outreach within 48 hours of discharge.\n\nRed Flag Criteria: Any report of new or worsening angina, dyspnea at rest, lower extremity edema (>2+), or weight gain > 3 lbs in 24 hours MUST be escalated immediately to the Clinical Review Queue.\n\nMedication Adherence: Confirm compliance with antiplatelet therapy (aspirin, clopidogrel) and ACE-i/ARBs.",
            version="2.1.0"
        )
        await db.flush()


        print("Seeding Campaigns...")
        camp_cardiac = Campaign(
            id="camp-cardiac-101",
            hospital_id="hosp-metro-1",
            name="Post-Acute Cardiac Follow-Up Campaign",
            description="Outreach for patients discharged with cardiac diagnoses within the last 72 hours.",
            status=CampaignStatusEnum.RUNNING,
            eligibility_rules={"care_setting": "Inpatient", "follow_up_window_hours": 48},
            follow_up_window_hours=48,
            calling_start_hour=8,
            calling_end_hour=20,
            priority_score=8,
            retry_limit=3,
            max_concurrent_calls=10
        )
        db.add(camp_cardiac)
        await db.flush()

        print("Seeding 300 Synthetic Patients & Encounters across Hospitals...")
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
        conditions_list = ["Congestive Heart Failure", "Acute Myocardial Infarction", "Post-Op Knee Replacement", "COPD Exacerbation", "Pneumonia", "Type 2 Diabetes Exacerbation", "Hypertension", "Coronary Artery Disease"]

        patients_seeded = 0
        now = datetime.utcnow()

        for h in hospitals:
            count_for_hosp = 80 if h.code == "METRO" else 50
            patients_list = []
            encounters_list = []
            discharges_list = []
            
            for i in range(count_for_hosp):
                p_id = f"pat-{h.code.lower()}-{i+1}"
                fn = random.choice(first_names)
                ln = random.choice(last_names)
                is_high_risk = random.random() < 0.25
                
                patient = Patient(
                    id=p_id,
                    hospital_id=h.id,
                    mrn=f"{h.code}-MRN-{10000+i}",
                    first_name=fn,
                    last_name=ln,
                    dob=f"19{random.randint(45, 90)}-0{random.randint(1,9)}-{random.randint(10,28)}",
                    phone=f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}",
                    gender="Male" if i % 2 == 0 else "Female",
                    preferred_language="English" if i % 4 != 0 else "Spanish",
                    communication_preference="phone",
                    high_risk_flag=is_high_risk,
                    created_at=now - timedelta(days=random.randint(1, 10))
                )
                patients_list.append(patient)
                
                # Encounter & Discharge
                enc_id = f"enc-{h.code.lower()}-{i+1}"
                dis_time = now - timedelta(hours=random.randint(2, 40))
                cond = random.choice(conditions_list)
                
                encounter = Encounter(
                    id=enc_id,
                    hospital_id=h.id,
                    patient_id=p_id,
                    encounter_number=f"ENC-{h.code}-{50000+i}",
                    admission_date=dis_time - timedelta(days=random.randint(2, 7)),
                    discharge_date=dis_time,
                    care_setting="Inpatient",
                    attending_physician="Dr. Vance" if h.code == "METRO" else "Dr. Smith",
                    primary_diagnosis=cond,
                    discharge_status="Discharged Home"
                )
                encounters_list.append(encounter)
                
                risk_tier = "HIGH" if is_high_risk else ("MEDIUM" if i % 3 == 0 else "LOW")
                discharge = Discharge(
                    id=f"dis-{h.code.lower()}-{i+1}",
                    hospital_id=h.id,
                    patient_id=p_id,
                    encounter_id=enc_id,
                    discharge_timestamp=dis_time,
                    discharge_instructions=f"Take prescribed medications. Monitor for red flags associated with {cond}. Rest and hydrate.",
                    follow_up_window_hours=48,
                    risk_score=3.5 if is_high_risk else 1.5,
                    risk_tier=risk_tier,
                    created_at=dis_time
                )
                discharges_list.append(discharge)
                patients_seeded += 1

            db.add_all(patients_list)
            await db.flush()
            db.add_all(encounters_list)
            await db.flush()
            db.add_all(discharges_list)
            await db.flush()

        print("Seeding Queue Simulation Tasks (25 Mock Patients)...")
        # Seed 25 OutreachTasks with varying priority, deadlines, and queue states for MetroHealth
        simulation_profiles = [
            ("pat-metro-1", TaskStateEnum.PENDING, 85.0, "HIGH", timedelta(hours=2), None, 0),
            ("pat-metro-2", TaskStateEnum.PENDING, 92.5, "URGENT", timedelta(hours=1), None, 0),
            ("pat-metro-3", TaskStateEnum.CALLING, 78.0, "HIGH", timedelta(hours=4), None, 0),
            ("pat-metro-4", TaskStateEnum.RETRY_SCHEDULED, 64.0, "MEDIUM", timedelta(hours=12), None, 1),
            ("pat-metro-5", TaskStateEnum.CALLBACK_SCHEDULED, 95.0, "HIGH", timedelta(hours=6), now + timedelta(minutes=5), 0),
            ("pat-metro-6", TaskStateEnum.COMPLETED, 50.0, "LOW", timedelta(hours=24), None, 1),
            ("pat-metro-7", TaskStateEnum.ESCALATED, 98.0, "URGENT", timedelta(hours=3), None, 1),
            ("pat-metro-8", TaskStateEnum.MANUAL_FOLLOW_UP, 45.0, "MEDIUM", timedelta(hours=8), None, 3),
            ("pat-metro-9", TaskStateEnum.PENDING, 72.0, "HIGH", timedelta(hours=5), None, 0),
            ("pat-metro-10", TaskStateEnum.PENDING, 60.0, "MEDIUM", timedelta(hours=18), None, 0),
            ("pat-metro-11", TaskStateEnum.RETRY_SCHEDULED, 55.0, "LOW", timedelta(hours=20), None, 2),
            ("pat-metro-12", TaskStateEnum.PENDING, 88.0, "URGENT", timedelta(hours=2), None, 0),
            ("pat-metro-13", TaskStateEnum.PENDING, 40.0, "LOW", timedelta(hours=30), None, 0),
            ("pat-metro-14", TaskStateEnum.PENDING, 65.0, "MEDIUM", timedelta(hours=15), None, 0),
            ("pat-metro-15", TaskStateEnum.PENDING, 81.0, "HIGH", timedelta(hours=4), None, 0)
        ]
        
        for idx, (p_id, state, prio, risk, cutoff_offset, cb_time, attempts) in enumerate(simulation_profiles):
            task_id = f"task-metro-sim-{idx+1}"
            task = OutreachTask(
                id=task_id,
                hospital_id="hosp-metro-1",
                campaign_id="camp-cardiac-101",
                patient_id=p_id,
                state=state,
                priority_score=prio,
                attempt_count=attempts,
                max_attempts=3,
                next_attempt_at=now if state in [TaskStateEnum.PENDING, TaskStateEnum.RETRY_SCHEDULED] else cb_time,
                scheduled_callback_at=cb_time,
                clinical_cutoff_at=now + cutoff_offset,
                partial_context={"initial_note": "Post-discharge outreach task initialized."},
                worker_id="worker-1" if state == TaskStateEnum.CALLING else None,
                locked_at=now if state == TaskStateEnum.CALLING else None,
                created_at=now - timedelta(hours=random.randint(1, 10))
            )
            db.add(task)
            
            # Eligibility entry
            el = CampaignEligibility(
                id=f"el-{task_id}",
                hospital_id="hosp-metro-1",
                campaign_id="camp-cardiac-101",
                patient_id=p_id,
                is_eligible=True,
                reason="Discharged 24h ago; within 48h cardiac campaign window; consent verified.",
                evaluated_at=now
            )
            db.add(el)

        await db.flush()

        print("Seeding Initial Escalation & Call Record...")
        call_id = "call-metro-urgent-1"
        call = Call(
            id=call_id,
            hospital_id="hosp-metro-1",
            task_id="task-metro-sim-7",
            campaign_id="camp-cardiac-101",
            patient_id="pat-metro-7",
            status="COMPLETED",
            started_at=now - timedelta(minutes=45),
            ended_at=now - timedelta(minutes=40),
            duration_seconds=300,
            outcome="ESCALATED",
            recording_url=f"{settings.PUBLIC_BASE_URL.rstrip('/')}/recordings/call-metro-urgent-1.mp3",
            metadata_json={"simulated": True}
        )
        db.add(call)
        await db.flush()

        conv = Conversation(
            id="conv-metro-1",
            call_id=call_id,
            hospital_id="hosp-metro-1",
            transcript_json=[
                {"speaker": "AI Intake", "text": "Hello, this is MetroHealth Outreach checking on your recovery. How are you feeling today?"},
                {"speaker": "Patient (John Smith)", "text": "I'm having worsening chest tightness and I can barely catch my breath when walking across the room."},
                {"speaker": "AI Intake", "text": "Thank you for reporting this. Chest tightness and difficulty breathing are serious symptoms. I am immediately notifying our clinical triage nurse."}
            ],
            collected_data={"reported_symptoms": ["worsening chest tightness", "shortness of breath"]},
            prompt_version="v1.0.0"
        )
        db.add(conv)

        triage = TriageAssessment(
            id="triage-metro-1",
            call_id=call_id,
            hospital_id="hosp-metro-1",
            patient_id="pat-metro-7",
            agent_name="Clinical Triage Agent",
            classification=TriageClassificationEnum.URGENT,
            observations=["Worsening chest tightness", "Shortness of breath on mild exertion"],
            red_flags=["RED_FLAG_CHEST_PAIN_SHORTNESS_OF_BREATH"],
            evidence=["Patient statement: 'worsening chest tightness and I can barely catch my breath'"],
            protocol_references=["Post-Discharge Cardiac Protocol v2.1 Section 4.2"],
            confidence=0.98,
            uncertainty=[],
            prompt_version="v1.0.0"
        )
        db.add(triage)

        dec = ConsensusDecision(
            id="dec-metro-1",
            call_id=call_id,
            hospital_id="hosp-metro-1",
            patient_id="pat-metro-7",
            consensus_classification=TriageClassificationEnum.URGENT,
            is_disagreement=False,
            consensus_policy_used="STRICT_CONSERVATIVE",
            final_escalation_recommendation=True,
            rationale="Unanimous URGENT classification across Assessment A, Assessment B, and Rule Engine.",
            created_at=now - timedelta(minutes=38)
        )
        db.add(dec)

        esc = Escalation(
            id="esc-metro-1",
            hospital_id="hosp-metro-1",
            patient_id="pat-metro-7",
            call_id=call_id,
            campaign_id="camp-cardiac-101",
            priority="URGENT",
            state=EscalationStateEnum.OPEN,
            assigned_reviewer_id=None,
            trigger_reason="Patient reported severe acute chest tightness and dyspnea during outreach call.",
            clinical_indicators=["Worsening chest tightness", "Shortness of breath"],
            evidence=["Transcript line 2: 'worsening chest tightness and I can barely catch my breath'"],
            created_at=now - timedelta(minutes=35)
        )
        db.add(esc)

        print("Seeding Audit Log & System Health...")
        audit = AuditLog(
            id=str(uuid.uuid4()),
            hospital_id="hosp-metro-1",
            user_id="usr-metro-admin",
            action="DATABASE_SEEDED",
            resource_type="System",
            resource_id="ALL",
            details={"seeded_patients": patients_seeded, "seeded_hospitals": len(hospitals)},
            created_at=now
        )
        db.add(audit)

        health = SystemHealth(
            id=str(uuid.uuid4()),
            component="Database",
            status="HEALTHY",
            details={"connection": "OK", "seeded_patients": patients_seeded},
            checked_at=now
        )
        db.add(health)

        await db.commit()
        print("=" * 70)
        print(f"DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print(f"Hospitals: {len(hospitals)}")
        print(f"Users: {len(users)}")
        print(f"Patients: {patients_seeded}")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(seed_database())
