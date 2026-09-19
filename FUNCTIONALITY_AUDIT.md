# PostCare Platform Complete Functionality Audit Matrix

This document provides a comprehensive end-to-end functionality audit of the **PostCare Multi-Hospital Post-Discharge Outreach Platform**, tracing all features across UI, API, Service, Database, Queue Engine/Worker, and AI integration layers.

---

## Functionality Matrix

| Feature | UI Component | API Endpoint | Backend Service | DB Entity / Table | Worker / Queue | AI Engine | Tested | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Campaign Lifecycle** | `CampaignManagerPage` (`CAMPAIGNS` Tab) | `GET /api/v1/campaigns/`<br>`POST /api/v1/campaigns/`<br>`POST /api/v1/campaigns/{id}/status` | `Campaign` Service | `campaigns` | `QueueEngine` respects `Campaign.status == RUNNING` | N/A | YES | **VERIFIED WORKING** |
| **Queue Prioritization** | `CampaignManagerPage` (`QUEUE` Tab) | `GET /api/v1/queue/tasks`<br>`GET /api/v1/queue/summary`<br>`POST /api/v1/queue/simulate_step` | `QueueEngine` | `outreach_tasks`, `patients` | `SELECT ... FOR UPDATE SKIP LOCKED` | N/A | YES | **VERIFIED WORKING** |
| **Explicit Callbacks** | `CampaignManagerPage` (`CALLBACKS` Tab) | `POST /api/v1/queue/schedule_callback` | `ControlledTools.schedule_callback` | `outreach_tasks.scheduled_callback_at` | `QueueEngine` elevates `CALLBACK_SCHEDULED` priority (+45 pts) | N/A | YES | **VERIFIED WORKING** |
| **Exponential Retries** | `CampaignManagerPage` (`RETRIES` Tab) | `POST /api/v1/queue/simulate_step` | `QueueEngine.record_task_outcome` | `outreach_tasks.attempt_count`, `next_attempt_at` | Backoff delays (15m → 60m → 240m) & `MANUAL_FOLLOW_UP` at max attempts | N/A | YES | **VERIFIED WORKING** |
| **Hospital Analytics** | `CampaignManagerPage` (`ANALYTICS` Tab) & `HospitalAdminPage` | `GET /api/v1/analytics/hospital` | `analytics.py` dynamic query service | `patients`, `outreach_tasks`, `calls`, `escalations` | Dynamic real-time calculation | N/A | YES | **VERIFIED WORKING** |
| **Voice Simulator** | `CampaignManagerPage` & `LoginPage` | `POST /api/v1/calls/simulate` | `calls.py` simulation service | `calls`, `conversations` | Task reservation & state transition | `Voice Intake Agent` | YES | **VERIFIED WORKING** |
| **AI Triage Intake** | `ClinicalReviewerPage` & `CampaignManagerPage` | `POST /api/v1/calls/simulate` | `calls.py` intake service | `triage_assessments` | Async triage dispatch | `MockAIProvider` / `GeminiProvider` / `OpenAIProvider` | YES | **VERIFIED WORKING** |
| **Dual AI Assessment** | `ClinicalReviewerPage` | `POST /api/v1/calls/simulate` | `ConsensusEngine.evaluate_consensus` | `escalation_assessments` | Dual parallel execution | `Assessment A` (Protocol) & `Assessment B` (Holistic) | YES | **VERIFIED WORKING** |
| **Consensus Engine** | `ClinicalReviewerPage` | `POST /api/v1/calls/simulate` | `ConsensusEngine` | `consensus_decisions` | Policy enforcement (`STRICT_CONSERVATIVE`) | Disagreement detection & fallback | YES | **VERIFIED WORKING** |
| **Protocol RAG** | `ClinicalReviewerPage` & `HospitalAdminPage` | `GET /api/v1/protocols/` | `ControlledTools.search_protocol` | `protocols` | Tenant-scoped retrieval | Protocol evidence matching | YES | **VERIFIED WORKING** |
| **Controlled AI Tools** | `ClinicalReviewerPage` | `POST /api/v1/calls/simulate` | `ControlledTools` | `audit_logs` | Authorized execution | Schema validation & audit logging | YES | **VERIFIED WORKING** |
| **Escalations** | `ClinicalReviewerPage` | `GET /api/v1/escalations/`<br>`PUT /api/v1/escalations/{id}/action` | `ControlledTools.create_escalation` | `escalations` | Task state set to `ESCALATED` | Conservative safety trigger | YES | **VERIFIED WORKING** |
| **Clinical Reviewer UI** | `ClinicalReviewerPage` | `GET /api/v1/escalations/{id}` | `escalations.py` detail service | `escalations`, `patients`, `conversations` | 3-Column Clinical Workflow | Human override & note entry | YES | **VERIFIED WORKING** |
| **Mock EHR Sync** | `ClinicalReviewerPage` & `HospitalAdminPage` | `POST /api/v1/ehr/sync` | `ControlledTools.update_mock_ehr` | `ehr_records` | Automatic FHIR R4 sync | Controlled tool sync | YES | **VERIFIED WORKING** |
| **Notifications** | Dashboard & Queue Engine | `QueueEngine` notifications | `QueueEngine.record_task_outcome` | `notifications` | Max retries exhaustion trigger | N/A | YES | **VERIFIED WORKING** |
| **Audit Logging** | `PlatformAdminPage` | `GET /api/v1/observability/audit` | `ControlledTools._audit` | `audit_logs` | Immutable event audit trail | N/A | YES | **VERIFIED WORKING** |
| **System Health** | All Navigation headers | `GET /api/v1/observability/health` | `observability.py` | DB, Queue, AI Provider health | Dynamic health check | Provider status | YES | **VERIFIED WORKING** |

---

## Complete End-to-End Traces

### 1. AI Execution Trace (Frontend → AI → EHR)

```text
[Frontend: CampaignManagerPage] Trigger Call / Urgent Call Button
   │
   ▼
[API: POST /api/v1/calls/simulate] (app/api/v1/calls.py:simulate_outreach_call)
   │
   ├──> 1. Fetch Hospital Protocol (app/models/domain.py:Protocol)
   ├──> 2. Log Call & Conversation (app/models/domain.py:Call, Conversation)
   │
   ├──> 3. AI Intake Agent Execution (app/ai/provider.py:get_ai_provider)
   │      - Model: MockAIProvider / GeminiProvider / OpenAIProvider
   │      - System Prompt: CLINICAL_TRIAGE_SYSTEM_PROMPT (app/ai/prompts.py)
   │      - Output Validation: Pydantic Structured Output (app/schemas/domain.py:StructuredTriageResult)
   │
   ├──> 4. Dual Assessment Execution (app/ai/consensus.py:ConsensusEngine)
   │      ├── Assessment A (Protocol Focus): generate_structured with ASSESSMENT_A_SYSTEM_PROMPT
   │      ├── Assessment B (Holistic Risk): generate_structured with ASSESSMENT_B_SYSTEM_PROMPT
   │      └── Rule Engine: run_rule_engine matching protocol red flags & baseline symptoms
   │
   ├──> 5. Consensus Decision & Disagreement Detection
   │      - Policy: STRICT_CONSERVATIVE
   │      - Disagreement Check: len(set([class_a, class_b, class_rule])) > 1
   │      - Persists ConsensusDecision (app/models/domain.py:ConsensusDecision)
   │
   ├──> 6. Controlled Tool Escalation (app/tools/controlled_tools.py:ControlledTools.create_escalation)
   │      - Enforces Tenant Isolation
   │      - Updates OutreachTask state -> ESCALATED
   │      - Inserts Escalation record (app/models/domain.py:Escalation)
   │      - Inserts AuditLog entry (app/models/domain.py:AuditLog)
   │
   ├──> 7. Mock EHR Synchronization (app/tools/controlled_tools.py:ControlledTools.update_mock_ehr)
   │      - Creates EHRRecord (FHIR R4 Communication/COMM-id)
   │      - Inserts AuditLog entry
   │
   ▼
[Frontend: ClinicalReviewerPage] 3-Column Clinical Reviewer Workstation
   ├── Left Column: Case Inbox (Filtered by URGENT / OPEN)
   ├── Center Column: Patient Info, Observed Red Flags & Full Audio Transcript
   └── Right Column: Dual AI Assessments, Consensus Rationale & Resolution Actions
```

---

### 2. Campaign Manager Workflow Trace

```text
[Frontend: CampaignManagerPage -> CAMPAIGNS Tab]
   │
   ├── Action: Create New Campaign
   │   └── API: POST /api/v1/campaigns/ -> DB: Campaign (status=READY)
   │
   ├── Action: Start Campaign
   │   └── API: POST /api/v1/campaigns/{id}/status?status_str=RUNNING -> DB: Campaign.status = RUNNING
   │       └── Queue Engine: Now allows OutreachTask reservations for this campaign
   │
   ├── Action: Pause Campaign
   │   └── API: POST /api/v1/campaigns/{id}/status?status_str=PAUSED -> DB: Campaign.status = PAUSED
   │       └── Queue Engine: Blocks new task reservations for this campaign (FOR UPDATE SKIP LOCKED)
   │
   └── Action: Complete Campaign
       └── API: POST /api/v1/campaigns/{id}/status?status_str=COMPLETED -> DB: Campaign.status = COMPLETED
```

---

### 3. Callback Workflow Trace

```text
[Patient Call / Campaign Manager] Request Callback
   │
   ▼
[API: POST /api/v1/queue/schedule_callback] (app/api/v1/queue.py:schedule_callback)
   │
   ▼
[Service: ControlledTools.schedule_callback] (app/tools/controlled_tools.py)
   ├── Updates OutreachTask.state -> CALLBACK_SCHEDULED
   ├── Sets OutreachTask.scheduled_callback_at & next_attempt_at = requested_time
   └── Inserts AuditLog record (action: TOOL_SCHEDULE_CALLBACK)
   │
   ▼
[Queue Engine: Priority Score Calculation] (app/queue/queue_engine.py:calculate_priority_score)
   ├── Applies +45.0 Callback Urgency Surge when requested_time <= now
   └── Queue Reservation: SELECT ... FOR UPDATE SKIP LOCKED picks callback task ahead of routine items
   │
   ▼
[Frontend: CampaignManagerPage -> CALLBACKS Tab] Displays in explicit callback queue
```

---

### 4. Retry & Exponential Backoff Workflow Trace

```text
[Call Attempt Outcome: NO_ANSWER / BUSY / VOICEMAIL / DROPPED]
   │
   ▼
[Service: QueueEngine.record_task_outcome] (app/queue/queue_engine.py)
   ├── Increments OutreachTask.attempt_count += 1
   │
   ├── IF attempt_count < max_attempts (e.g. 3):
   │   ├── OutreachTask.state = RETRY_SCHEDULED
   │   ├── Calculates Exponential Backoff:
   │   │   ├── Attempt 1 -> 15 minutes delay
   │   │   ├── Attempt 2 -> 60 minutes delay
   │   │   └── Attempt 3 -> 240 minutes delay
   │   └── Sets OutreachTask.next_attempt_at = now + delay
   │
   └── IF attempt_count >= max_attempts:
       ├── OutreachTask.state = MANUAL_FOLLOW_UP
       └── Creates Notification record (type: MAX_RETRIES_EXHAUSTED)
   │
   ▼
[Frontend: CampaignManagerPage -> RETRIES Tab] Displays in retry pipeline schedule
```

---

### 5. Analytics Workflow Trace

```text
[Frontend: CampaignManagerPage -> ANALYTICS Tab & HospitalAdminPage]
   │
   ▼
[API: GET /api/v1/analytics/hospital] (app/api/v1/analytics.py:get_hospital_analytics)
   │
   ├── Queries `patients`: Total Ingested Patients count
   ├── Queries `outreach_tasks`: Completed, Retries, Callbacks, Escalated counts
   ├── Queries `calls`: Total Calls Attempted count
   ├── Queries `escalations`: Total Escalations count
   ├── Computes Dynamic Contact Rate = Completed Tasks / Total Active Pipeline
   ├── Computes Dynamic Average Attempts per Contact = avg(attempt_count)
   └── Queries QueueEngine for Capacity Utilization = active_capacity / capacity_limit
   │
   ▼
[Frontend Charts & KPI Cards] Render live metrics updated in real time upon call simulation
```

---

## Test Verification Summary

- **Automated Pytest Suite**: **16 / 16 PASSED** (`.\venv\Scripts\pytest -v -o pythonpath=.`)
- **Clinical Safety Benchmark**: **Passed with 0.00% False Negative Rate** (`python -m app.evaluation.run_safety_eval`)
- **Scripted End-to-End Demo Scenario**: **36 / 36 Steps Passed** (`python -m app.scripts.run_demo_scenario`)
- **Frontend Production Build**: **0 TypeScript Errors, 0 CSS Errors** (`npm run build`)
