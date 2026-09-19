# PostCare Evaluator Walkthrough & End-to-End Demo Guide

## 1. Demo Overview & Evaluator Credentials

This guide provides a step-by-step walkthrough for evaluating the **PostCare** platform. It covers all 4 role-based dashboards, campaign creation, intelligent queue execution, live AI call simulation, dual-model triage disagreement, clinical escalation resolution, and runnable safety benchmarking.

### Pre-Configured Demo Credentials

| Role | Email | Password | Primary Dashboard | Key Features Demonstrated |
| :--- | :--- | :--- | :--- | :--- |
| **Hospital Admin** | `admin@metrohealth.org` | `admin123` | `/hospital` | Hospital overview, patient list, discharge records, protocol RAG management. |
| **Campaign Manager** | `campaign@metrohealth.org` | `campaign123` | `/campaigns` | Campaign creation, queue capacity monitoring, step simulation, manual callback triggers. |
| **Clinical Reviewer** | `reviewer@metrohealth.org` | `reviewer123` | `/review` | Escalation inbox, dual AI assessment comparison, consensus rationale, EHR resolution. |
| **Platform Admin** | `admin@postcare.health` | `platform123` | `/admin` | Multi-hospital platform analytics, audit log timeline, system health, Safety Evaluation trigger. |

---

## 2. End-to-End Step-by-Step Evaluator Walkthrough

### Step 1: Authentication & Role Selection
1. Navigate to the application root (`/`).
2. Click **"Demo Access / Auto-Login"** or enter `admin@metrohealth.org` / `admin123`.
3. **What to Observe**: Successful JWT authentication token issue and automatic redirection to the Hospital Admin overview dashboard (`/hospital`).

### Step 2: Hospital Overview & Protocol Configuration (`/hospital`)
1. Click the **PROTOCOLS** tab in the Hospital Admin header.
2. View existing protocols (e.g. *Post-Discharge Cardiac Surgery Protocol v2.1*).
3. **What to Observe**: Hospital-scoped clinical guidelines ingested and chunked into `KnowledgeChunk` records for RAG context retrieval.

### Step 3: Campaign Creation & Eligibility (`/campaigns`)
1. Log in or switch to **Campaign Manager** (`campaign@metrohealth.org`).
2. Click **Create New Campaign**.
3. Enter campaign name (e.g. *"Post-Op Cardiac Outreach Q3"*), select protocol, and set daily calling capacity limit.
4. **What to Observe**: Campaign status updates to `RUNNING`. Eligible patients are automatically assigned `OutreachTask` records with dynamic priority scores.

### Step 4: Intelligent Queue & Concurrency Control (`/campaigns` -> Callbacks / Queue)
1. In Campaign Manager, view the **Queue Breakdown** summary.
2. Note the **Capacity Limit** (e.g. 10 max concurrent calls) and **Queue Depth**.
3. Click **"Simulate Queue Step"**.
4. **What to Observe**: The backend executes `QueueEngine.reserve_next_task()` using `FOR UPDATE SKIP LOCKED`, locking the highest priority candidate task into `CALLING` state without race conditions.

### Step 5: Live AI Call Simulation & Dual Assessment
1. Click **"Trigger Call Simulation"** for patient *William Miller* or *Jennifer Johnson*.
2. **What to Observe**:
   - The backend executes `simulate_outreach_call`.
   - The Voice Intake Agent simulates conversation transcript generation.
   - Dual AI models execute in parallel:
     - **Model A**: Protocol-Focused Triage.
     - **Model B**: Holistic-Focused Triage.

### Step 6: Clinical Reviewer Escalation Triage (`/review`)
1. Log in or switch to **Clinical Reviewer** (`reviewer@metrohealth.org`).
2. Select **Jennifer Johnson** (Status: `URGENT`, `OPEN`).
3. **What to Observe**:
   - **Dual Badges**: Assessment A (Gemini 3.5 Flash - Protocol) vs Assessment B (Gemini 3.5 Flash - Holistic).
   - **Consensus Rationale**: Displays `STRICT_CONSERVATIVE` policy enforcement.
   - **RAG Evidence Tab**: Shows exact protocol references (e.g. *Section 4.2: Chest pain / shortness of breath red flags*).

### Step 7: Clinical Action & Mock EHR Auto-Sync (`/review`)
1. In Jennifer Johnson's detail view, enter resolution notes: *"Contacted patient; advised immediate ED presentation."*
2. Click **"Resolve & Sync EHR"**.
3. **What to Observe**:
   - Escalation state updates to `RESOLVED` with `resolved_at` timestamp.
   - Linked outreach task transitions to `COMPLETED`.
   - Mock EHR Gateway automatically generates a FHIR R4 `EscalationResolution` record (`EHRRecord`).

### Step 8: Platform Admin & Runnable Safety Evaluation (`/admin`)
1. Log in or switch to **Platform Admin** (`admin@postcare.health`).
2. Click **"Run Safety Evaluation"**.
3. **What to Observe**:
   - The backend runs `run_safety_evaluation()` over the 25 fixed clinical test cases.
   - Evaluator displays real-time metrics: **0% False Negative Rate**, 100% Precision, 100% Recall, 100% Accuracy.
   - Audit Log timeline displays the immutable `SAFETY_EVALUATION_EXECUTED` log entry.
