from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.domain import RoleEnum, CampaignStatusEnum, TaskStateEnum, EscalationStateEnum, TriageClassificationEnum

# Auth & User Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: RoleEnum
    hospital_id: Optional[str] = None

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: str
    full_name: str
    role: RoleEnum
    hospital_id: Optional[str] = None
    is_active: bool
    created_at: datetime

# Hospital Schemas
class HospitalCreate(BaseModel):
    name: str
    code: str
    timezone: str = "UTC"
    calling_start_hour: int = 8
    calling_end_hour: int = 20
    max_concurrent_calls: int = 10
    retry_rules: Optional[Dict[str, Any]] = None
    notification_config: Optional[Dict[str, Any]] = None
    ehr_config: Optional[Dict[str, Any]] = None

class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    code: str
    timezone: str
    calling_start_hour: int
    calling_end_hour: int
    max_concurrent_calls: int
    retry_rules: Dict[str, Any]
    notification_config: Dict[str, Any]
    ehr_config: Dict[str, Any]
    is_active: bool
    created_at: datetime

# Patient & Clinical Schemas
class PatientCreate(BaseModel):
    mrn: str
    first_name: str
    last_name: str
    dob: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    preferred_language: str = "English"
    communication_preference: str = "phone"
    high_risk_flag: bool = False

class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    mrn: str
    first_name: str
    last_name: str
    dob: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    preferred_language: str
    communication_preference: str
    high_risk_flag: bool
    created_at: datetime

class EncounterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    patient_id: str
    encounter_number: str
    admission_date: Optional[datetime] = None
    discharge_date: datetime
    care_setting: str
    attending_physician: Optional[str] = None
    primary_diagnosis: Optional[str] = None
    discharge_status: str

class DischargeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    patient_id: str
    encounter_id: str
    discharge_timestamp: datetime
    discharge_instructions: Optional[str] = None
    follow_up_window_hours: int
    risk_score: float
    risk_tier: str

class TimelineEvent(BaseModel):
    event_type: str
    timestamp: datetime
    title: str
    description: str
    metadata: Dict[str, Any] = {}

class PatientTimelineOut(BaseModel):
    patient: PatientOut
    encounters: List[EncounterOut]
    discharges: List[DischargeOut]
    timeline: List[TimelineEvent]

# Campaign Schemas
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    eligibility_rules: Dict[str, Any] = {}
    follow_up_window_hours: int = 48
    calling_start_hour: int = 8
    calling_end_hour: int = 20
    priority_score: int = 5
    retry_limit: int = 3
    max_concurrent_calls: int = 5

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatusEnum] = None
    priority_score: Optional[int] = None
    max_concurrent_calls: Optional[int] = None

class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    name: str
    description: Optional[str] = None
    status: CampaignStatusEnum
    eligibility_rules: Dict[str, Any]
    follow_up_window_hours: int
    calling_start_hour: int
    calling_end_hour: int
    priority_score: int
    retry_limit: int
    max_concurrent_calls: int
    created_at: datetime

class EligibilityOut(BaseModel):
    patient_id: str
    campaign_id: str
    is_eligible: bool
    reason: str
    evaluated_at: datetime

# Queue & Task Schemas
class OutreachTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    campaign_id: str
    patient_id: str
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    state: TaskStateEnum
    priority_score: float
    attempt_count: int
    max_attempts: int
    next_attempt_at: Optional[datetime] = None
    scheduled_callback_at: Optional[datetime] = None
    clinical_cutoff_at: Optional[datetime] = None
    partial_context: Dict[str, Any] = {}
    created_at: datetime

class QueueSummaryOut(BaseModel):
    hospital_id: str
    active_capacity: int
    capacity_limit: int
    queue_depth: int
    oldest_pending_minutes: Optional[int] = None
    cutoff_risk_count: int
    state_breakdown: Dict[str, int]

# Call & Conversation Schemas
class CallCreateSimulation(BaseModel):
    task_id: str
    simulated_outcome: Optional[str] = "COMPLETED"
    patient_responses: Optional[List[str]] = None

class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    task_id: str
    campaign_id: str
    patient_id: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int
    outcome: str
    recording_url: Optional[str] = None

# AI Triage & Assessment Schemas
class StructuredTriageResult(BaseModel):
    classification: TriageClassificationEnum
    observations: List[str] = []
    red_flags: List[str] = []
    evidence: List[str] = []
    protocol_references: List[str] = []
    confidence: float = 1.0
    uncertainty: List[str] = []
    escalation_recommendation: bool = False
    prompt_version: str = "v1.0.0"

class ConsensusDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    call_id: str
    hospital_id: str
    patient_id: str
    consensus_classification: TriageClassificationEnum
    is_disagreement: bool
    consensus_policy_used: str
    final_escalation_recommendation: bool
    rationale: str
    created_at: datetime

# Escalation Schemas
class EscalationUpdate(BaseModel):
    state: Optional[EscalationStateEnum] = None
    assigned_reviewer_id: Optional[str] = None
    resolution_notes: Optional[str] = None

class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    patient_id: str
    patient_name: Optional[str] = None
    call_id: str
    campaign_id: str
    priority: str
    state: EscalationStateEnum
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    trigger_reason: str
    clinical_indicators: List[str]
    evidence: List[str]
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

# Protocol & RAG Schemas
class ProtocolCreate(BaseModel):
    name: str
    category: str = "General"
    target_conditions: List[str] = []
    red_flags: List[str] = []
    follow_up_questions: List[str] = []
    escalation_contacts: List[str] = []

class ProtocolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: str
    name: str
    version: str
    category: str
    target_conditions: List[str]
    red_flags: List[str]
    follow_up_questions: List[str]
    escalation_contacts: List[str]
    is_active: bool
    created_at: datetime

# Observability & Audit Schemas
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    hospital_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any]
    created_at: datetime

class SystemHealthOut(BaseModel):
    status: str
    components: Dict[str, Dict[str, Any]]
    queue_health: Dict[str, Any]
    checked_at: datetime
