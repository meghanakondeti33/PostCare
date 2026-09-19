import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class RoleEnum(str, enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    CAMPAIGN_MANAGER = "CAMPAIGN_MANAGER"
    CLINICAL_REVIEWER = "CLINICAL_REVIEWER"

class CampaignStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TaskStateEnum(str, enum.Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    CALLING = "CALLING"
    CONNECTED = "CONNECTED"
    COMPLETED = "COMPLETED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"
    VOICEMAIL = "VOICEMAIL"
    DROPPED = "DROPPED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    CALLBACK_SCHEDULED = "CALLBACK_SCHEDULED"
    ESCALATED = "ESCALATED"
    MANUAL_FOLLOW_UP = "MANUAL_FOLLOW_UP"
    FAILED = "FAILED"

class EscalationStateEnum(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    WAITING_FOR_INFORMATION = "WAITING_FOR_INFORMATION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class TriageClassificationEnum(str, enum.Enum):
    ROUTINE = "ROUTINE"
    CONCERNING = "CONCERNING"
    URGENT = "URGENT"
    UNCERTAIN = "UNCERTAIN"

# Database Entities

class Hospital(Base):
    __tablename__ = "hospitals"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    timezone = Column(String(50), default="UTC")
    calling_start_hour = Column(Integer, default=8)
    calling_end_hour = Column(Integer, default=20)
    max_concurrent_calls = Column(Integer, default=10)
    retry_rules = Column(JSON, default=dict)
    notification_config = Column(JSON, default=dict)
    ehr_config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=True) # Null for Platform Admin
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    mrn = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)
    preferred_language = Column(String(50), default="English")
    communication_preference = Column(String(50), default="phone")
    high_risk_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (Index("idx_patient_hospital_mrn", "hospital_id", "mrn", unique=True),)

class Encounter(Base):
    __tablename__ = "encounters"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    encounter_number = Column(String(100), nullable=False)
    admission_date = Column(DateTime, nullable=True)
    discharge_date = Column(DateTime, nullable=False)
    care_setting = Column(String(100), default="Inpatient")
    attending_physician = Column(String(100), nullable=True)
    primary_diagnosis = Column(Text, nullable=True)
    discharge_status = Column(String(100), default="Discharged Home")
    created_at = Column(DateTime, default=datetime.utcnow)

class Discharge(Base):
    __tablename__ = "discharges"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String(36), ForeignKey("encounters.id"), nullable=False, index=True)
    discharge_timestamp = Column(DateTime, nullable=False)
    discharge_instructions = Column(Text, nullable=True)
    follow_up_window_hours = Column(Integer, default=48)
    risk_score = Column(Float, default=1.0)
    risk_tier = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, URGENT
    created_at = Column(DateTime, default=datetime.utcnow)

class Condition(Base):
    __tablename__ = "conditions"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    onset_date = Column(String(50), nullable=True)
    status = Column(String(50), default="active")

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String(36), ForeignKey("encounters.id"), nullable=True)
    code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    value = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class Medication(Base):
    __tablename__ = "medications"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    instructions = Column(Text, nullable=True)

class CarePlan(Base):
    __tablename__ = "care_plans"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    goals = Column(JSON, default=list)
    instructions = Column(Text, nullable=True)

class Procedure(Base):
    __tablename__ = "procedures"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    code = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    performed_at = Column(DateTime, nullable=True)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(CampaignStatusEnum), default=CampaignStatusEnum.DRAFT, nullable=False)
    eligibility_rules = Column(JSON, default=dict)
    follow_up_window_hours = Column(Integer, default=48)
    calling_start_hour = Column(Integer, default=8)
    calling_end_hour = Column(Integer, default=20)
    priority_score = Column(Integer, default=5)
    retry_limit = Column(Integer, default=3)
    max_concurrent_calls = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CampaignEligibility(Base):
    __tablename__ = "campaign_eligibility"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    is_eligible = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

class OutreachTask(Base):
    __tablename__ = "outreach_tasks"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    state = Column(SQLEnum(TaskStateEnum), default=TaskStateEnum.PENDING, nullable=False, index=True)
    priority_score = Column(Float, default=0.0, index=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    scheduled_callback_at = Column(DateTime, nullable=True)
    clinical_cutoff_at = Column(DateTime, nullable=True, index=True)
    partial_context = Column(JSON, default=dict)
    worker_id = Column(String(100), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("outreach_tasks.id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    outcome = Column(String(50), nullable=False) # COMPLETED, NO_ANSWER, BUSY, VOICEMAIL, DROPPED, CALLBACK_REQUESTED
    recording_url = Column(String(500), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    transcript_json = Column(JSON, default=list)
    collected_data = Column(JSON, default=dict)
    prompt_version = Column(String(50), default="v1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)

class Protocol(Base):
    __tablename__ = "protocols"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0.0")
    category = Column(String(100), default="General")
    target_conditions = Column(JSON, default=list)
    red_flags = Column(JSON, default=list)
    follow_up_questions = Column(JSON, default=list)
    escalation_contacts = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="Protocol Guidance")
    content = Column(Text, nullable=False)
    version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding_vector = Column(JSON, nullable=True) # Vector stored as array or JSON for cross-DB compatibility
    metadata_json = Column(JSON, default=dict)

    document = relationship("KnowledgeDocument", back_populates="chunks")

class TriageAssessment(Base):
    __tablename__ = "triage_assessments"
    
    id = Column(String(36), primary_key=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    classification = Column(SQLEnum(TriageClassificationEnum), nullable=False)
    observations = Column(JSON, default=list)
    red_flags = Column(JSON, default=list)
    evidence = Column(JSON, default=list)
    protocol_references = Column(JSON, default=list)
    confidence = Column(Float, default=1.0)
    uncertainty = Column(JSON, default=list)
    prompt_version = Column(String(50), default="v1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)

class EscalationAssessment(Base):
    __tablename__ = "escalation_assessments"
    
    id = Column(String(36), primary_key=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    assessment_a = Column(JSON, nullable=False)
    assessment_b = Column(JSON, nullable=False)
    rule_engine_result = Column(JSON, nullable=False)
    prompt_version = Column(String(50), default="v1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)

class ConsensusDecision(Base):
    __tablename__ = "consensus_decisions"
    
    id = Column(String(36), primary_key=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    consensus_classification = Column(SQLEnum(TriageClassificationEnum), nullable=False)
    is_disagreement = Column(Boolean, default=False)
    consensus_policy_used = Column(String(50), default="STRICT_CONSERVATIVE")
    final_escalation_recommendation = Column(Boolean, default=False)
    rationale = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id"), nullable=False, index=True)
    priority = Column(String(20), default="URGENT", index=True) # ROUTINE, CONCERNING, URGENT
    state = Column(SQLEnum(EscalationStateEnum), default=EscalationStateEnum.OPEN, nullable=False, index=True)
    assigned_reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    trigger_reason = Column(Text, nullable=False)
    clinical_indicators = Column(JSON, default=list)
    evidence = Column(JSON, default=list)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Documentation(Base):
    __tablename__ = "documentations"
    
    id = Column(String(36), primary_key=True)
    call_id = Column(String(36), ForeignKey("calls.id"), nullable=False, index=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    patient_reported_symptoms = Column(JSON, default=list)
    triage_result = Column(String(50), nullable=False)
    ehr_synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class EHRRecord(Base):
    __tablename__ = "ehr_records"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String(36), ForeignKey("encounters.id"), nullable=True)
    resource_type = Column(String(50), nullable=False) # Patient, Observation, Communication, Task, Encounter
    resource_id = Column(String(100), nullable=False)
    data = Column(JSON, nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    type = Column(String(50), nullable=False) # ESCALATION_CREATED, CALLBACK_DUE, RETRY_EXHAUSTED
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), default="dashboard") # dashboard, email
    status = Column(String(50), default="SENT")
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class AIUsage(Base):
    __tablename__ = "ai_usage"
    
    id = Column(String(36), primary_key=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=True, index=True)
    agent_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_version = Column(String(50), default="v1.0.0")
    latency_ms = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class SystemHealth(Base):
    __tablename__ = "system_health"
    
    id = Column(String(36), primary_key=True)
    component = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), default="HEALTHY")
    details = Column(JSON, default=dict)
    checked_at = Column(DateTime, default=datetime.utcnow)
