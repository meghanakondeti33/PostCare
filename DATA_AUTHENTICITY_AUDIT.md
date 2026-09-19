# PostCare Platform Data Authenticity Audit

This document provides a comprehensive **Data Authenticity Audit** of the PostCare platform, verifying that no hardcoded, fake, or mock fallback data is rendered automatically on page loads. All UI components strictly render data from backend database queries or explicit user actions.

---

## Data Authenticity Matrix

| Feature | Current Data Source | Hardcoded Data Found | Removed? | API Endpoint | Database Table | User Action Required | Verified? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Platform Dashboard** | Real DB Aggregates | `total_patients || 230`, `disagreement || 0.084` | YES | `GET /api/v1/analytics/platform` | `hospitals`, `patients`, `calls`, `escalations` | None (reads DB) | **VERIFIED** |
| **Hospital Dashboard** | Real DB Aggregates | `contact_rate || 0.84`, `capacity || 10` | YES | `GET /api/v1/analytics/hospital` | `patients`, `outreach_tasks`, `calls` | None (reads DB) | **VERIFIED** |
| **Patients Feed** | Real DB Records | `dob || '1968-05-14'`, `language || 'English'` | YES | `GET /api/v1/patients/` | `patients` | `[Ingest Discharge Feed]` action or DB seed | **VERIFIED** |
| **Discharges Feed** | Real DB Records | Static fallback patient arrays | YES | `GET /api/v1/patients/` | `discharges`, `encounters` | Ingest CSV or DB seed | **VERIFIED** |
| **Campaigns Register** | Real DB Records | `currentCampaign || { name: 'Metro...' }` | YES | `GET /api/v1/campaigns/`<br>`POST /api/v1/campaigns/` | `campaigns` | `[Create Campaign]` or DB seed | **VERIFIED** |
| **Queue Tasks** | Real DB Records | `active_capacity || 1` meter fallbacks | YES | `GET /api/v1/queue/tasks`<br>`GET /api/v1/queue/summary` | `outreach_tasks` | Campaign activation or `[Simulate Queue Step]` | **VERIFIED** |
| **Scheduled Callbacks** | Real DB Records | Pre-populated fallback callback arrays | YES | `POST /api/v1/queue/schedule_callback` | `outreach_tasks.scheduled_callback_at` | `[Schedule Callback]` action or call outcome | **VERIFIED** |
| **Retry Pipeline** | Real DB Records | Static fallback retry rows | YES | `GET /api/v1/queue/tasks?state=RETRY_SCHEDULED` | `outreach_tasks.attempt_count`, `next_attempt_at` | Call attempt failure (`NO_ANSWER`, `BUSY`) | **VERIFIED** |
| **Analytics Dashboard** | Real DB Aggregates | `84%`, `142 calls`, `1.4 attempts` | YES | `GET /api/v1/analytics/hospital` | `patients`, `calls`, `outreach_tasks` | Operational activity in DB | **VERIFIED** |
| **Call Simulation** | Real API & AI Provider | Hardcoded call outcome triggers | YES | `POST /api/v1/calls/simulate` | `calls`, `conversations` | `[Trigger Call]` or `[Simulate Urgent Call]` | **VERIFIED** |
| **AI Intake & Triage** | Live LLM / Mock Provider | Hardcoded triage output | YES | `POST /api/v1/calls/simulate` | `triage_assessments` | `[Trigger Call]` action | **VERIFIED** |
| **Dual AI Assessment** | Live LLM / Mock Provider | `detail...classification || 'URGENT'` | YES | `POST /api/v1/calls/simulate` | `escalation_assessments` | `[Trigger Call]` action | **VERIFIED** |
| **Protocol RAG** | Real DB Protocols | Hardcoded red flags string | YES | `GET /api/v1/protocols/` | `protocols` | Tenant-scoped protocol matching | **VERIFIED** |
| **Clinical Escalations** | Real DB Escalations | Static "James Wilson" escalation | YES | `GET /api/v1/escalations/` | `escalations` | AI / Rule Engine safety trigger | **VERIFIED** |
| **Clinical Reviewer UI** | Real DB Detail Endpoint | Hardcoded dyspnea symptom quote | YES | `GET /api/v1/escalations/{id}` | `escalations`, `patients`, `conversations` | Escalation selection in inbox | **VERIFIED** |
| **Mock EHR Sync** | Real DB Records | Static FHIR sync badges | YES | `POST /api/v1/ehr/sync` | `ehr_records` | `[Resolve & Sync EHR]` button | **VERIFIED** |
| **Audit Logs** | Real DB Logs | Static "Campaign started 2m ago" | YES | `GET /api/v1/observability/audit` | `audit_logs` | Controlled tools / system operations | **VERIFIED** |
| **System Health** | Real Health Endpoint | Static "HEALTHY" pills | YES | `GET /api/v1/observability/health` | System services health check | Endpoint status check | **VERIFIED** |

---

## Empty State Verification (Fresh Empty Database)

When PostCare is launched on a fresh, unseeded database:

1. **Platform Admin**: Displays `4` Active Hospitals (preserved foundational tenant records), `0` Outreach Volume, `HEALTHY` System Health (derived from live DB ping), and `—` AI Disagreement (*No assessments yet*).
2. **Hospital Admin**: Displays `0` Patients and an empty state card: *"No Patients Ingested Yet. Click 'Ingest Discharge Feed' to load patient records."*
3. **Campaign Manager (`QUEUE` Tab)**: Displays `0` Queue Depth and an empty state card: *"No Outreach Tasks Currently Queued. Create or start an outreach campaign to populate queue tasks."*
4. **Campaign Manager (`CAMPAIGNS` Tab)**: Displays an empty state card: *"No Outreach Campaigns Created. Click 'Create Campaign' to set up an outreach campaign."*
5. **Campaign Manager (`CALLBACKS` Tab)**: Displays `0` Callbacks and an empty state card: *"No Callbacks Scheduled. Patient-requested callbacks will appear here when scheduled."*
6. **Campaign Manager (`RETRIES` Tab)**: Displays `0` Retries and an empty state card: *"No Retry Tasks. Tasks requiring retries due to unanswered calls will appear here."*
7. **Campaign Manager (`ANALYTICS` Tab)**: Displays `0%` Contact Rate, `0` Patients, `0` Calls, and an empty state card: *"Not Enough Operational Data. Analytics will appear as outreach activity is recorded."*
8. **Clinical Reviewer Workstation**: Displays an empty state card: *"All Clear — No Escalations Require Review. Clinical alerts triggered by AI consensus or protocol rules will appear here."*

---

## Data Seeding & Reset Scripts

- **Explicit Seed Command**: `python -m app.scripts.seed_data` (Populates 4 hospitals, 6 users, 230+ patients, cardiac protocols, and campaigns for demo/testing).
- **Explicit Reset Command**: `python -m app.scripts.reset_demo` (Clears all operational database records back to an empty database state).

---

## Causal Execution Chain

The application strictly adheres to the following causal chain:

```text
USER ACTION (or CLI Seed Command)
   │
   ▼
API ENDPOINT
   │
   ▼
BUSINESS LOGIC & CONTROLLED TOOLS
   │
   ▼
DATABASE / AI ENGINE / QUEUE WORKER
   │
   ▼
REAL RESULT STORED IN DB
   │
   ▼
UI COMPONENT RENDERS REAL DB DATA
```
