export type Role = "PLATFORM_ADMIN" | "HOSPITAL_ADMIN" | "CAMPAIGN_MANAGER" | "CLINICAL_REVIEWER";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  hospital_id?: string;
  is_active: boolean;
  created_at: string;
}

export interface Hospital {
  id: string;
  name: string;
  code: string;
  timezone: string;
  calling_start_hour: number;
  calling_end_hour: number;
  max_concurrent_calls: number;
  retry_rules: Record<string, any>;
  notification_config: Record<string, any>;
  ehr_config: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

export interface Patient {
  id: string;
  hospital_id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  dob?: string;
  phone?: string;
  gender?: string;
  preferred_language: string;
  communication_preference: string;
  high_risk_flag: boolean;
  created_at: string;
}

export interface TimelineEvent {
  event_type: string;
  timestamp: string;
  title: string;
  description: string;
  metadata: Record<string, any>;
}

export interface PatientTimeline {
  patient: Patient;
  encounters: any[];
  discharges: any[];
  timeline: TimelineEvent[];
}

export interface Campaign {
  id: string;
  hospital_id: string;
  name: string;
  description?: string;
  status: "DRAFT" | "READY" | "SCHEDULED" | "RUNNING" | "PAUSED" | "COMPLETED" | "CANCELLED";
  eligibility_rules: Record<string, any>;
  follow_up_window_hours: number;
  calling_start_hour: number;
  calling_end_hour: number;
  priority_score: number;
  retry_limit: number;
  max_concurrent_calls: number;
  created_at: string;
}

export interface OutreachTask {
  id: string;
  hospital_id: string;
  campaign_id: string;
  patient_id: string;
  patient_name?: string;
  patient_mrn?: string;
  state: string;
  priority_score: number;
  attempt_count: number;
  max_attempts: number;
  next_attempt_at?: string;
  scheduled_callback_at?: string;
  clinical_cutoff_at?: string;
  partial_context: Record<string, any>;
  created_at: string;
}

export interface QueueSummary {
  hospital_id: string;
  active_capacity: number;
  capacity_limit: number;
  queue_depth: number;
  oldest_pending_minutes?: number;
  cutoff_risk_count: number;
  state_breakdown: Record<string, number>;
}

export interface Escalation {
  id: string;
  hospital_id: string;
  patient_id: string;
  patient_name?: string;
  call_id: string;
  campaign_id: string;
  priority: string;
  state: "OPEN" | "ASSIGNED" | "IN_REVIEW" | "WAITING_FOR_INFORMATION" | "RESOLVED" | "CLOSED";
  assigned_reviewer_id?: string;
  assigned_reviewer_name?: string;
  trigger_reason: string;
  clinical_indicators: string[];
  evidence: string[];
  resolution_notes?: string;
  resolved_at?: string;
  created_at: string;
}

export interface Protocol {
  id: string;
  hospital_id: string;
  name: string;
  version: string;
  category: string;
  target_conditions: string[];
  red_flags: string[];
  follow_up_questions: string[];
  escalation_contacts: string[];
  is_active: boolean;
  created_at: string;
}

export interface EHRRecord {
  id: string;
  hospital_id: string;
  patient_id: string;
  encounter_id?: string;
  resource_type: string;
  resource_id: string;
  data: Record<string, any>;
  synced_at: string;
}
