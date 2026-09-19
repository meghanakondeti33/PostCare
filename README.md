# Multi-Hospital Post-Discharge Outreach Platform

> Autonomous AI-Powered Patient Follow-Up, Clinical Triage & Hospital Outreach Operations Platform

---

## 1. Project Overview

PostCare is a multi-tenant AI-powered healthcare operations platform designed for hospital systems to automate post-discharge patient outreach, queue management, clinical triage, dual-assessment consensus escalation, and human-in-the-loop review.

The system manages the complete post-discharge journey:
$$\text{Hospital Onboarding} \rightarrow \text{Discharge Feed Ingestion} \rightarrow \text{Eligibility Engine} \rightarrow \text{Intelligent Queue} \rightarrow \text{Capacity-Aware Scheduling} \rightarrow \text{AI Voice Simulator} \rightarrow \text{Structured Triage} \rightarrow \text{Dual Assessment Consensus} \rightarrow \text{Clinical Review Inbox} \rightarrow \text{Mock EHR Sync} \rightarrow \text{Observability \& Audit}$$

---

## 2. Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, React Router DOM, TanStack Query.
- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.x (Async), AsyncPG / SQLite (aiosqlite).
- **Database**: PostgreSQL (with `pgvector` for clinical protocol embeddings; SQLite fallback for local test suite).
- **AI Abstraction**: Multi-provider support (`GeminiProvider`, `OpenAIProvider`, `MockAIProvider`), Semantic Prompt Versioning (`v1.0.0`), Controlled AI Tools Framework.
- **Safety Evaluation**: Fixed 25-case clinical benchmark dataset with 0.00% False Negative Rate reporting.

---

## 3. Key Architecture & Features

1. **Strict Multi-Tenant Isolation**:
   - Every patient record, outreach task, call, protocol, and escalation carries an explicit `hospital_id`. Cross-tenant data retrieval is blocked at the database repository layer.
2. **Intelligent Capacity-Aware Outbound Queue Engine**:
   - Dynamic prioritization formula:
     $$\text{priority} = \text{clinical\_risk} + \text{deadline\_pressure} + \text{callback\_urgency} + \text{campaign\_priority} + \text{waiting\_time\_aging} - \text{retry\_penalty}$$
   - Centralized concurrency control using `SELECT ... FOR UPDATE SKIP LOCKED` guarantees capacity limits (e.g., max 10 concurrent calls) are never exceeded.
   - Exponential backoff retries for `NO_ANSWER`, `BUSY`, `VOICEMAIL`, `DROPPED`.
   - Patient-requested callback scheduling and crashed worker heartbeat recovery.
3. **Dual AI Assessment & Consensus Escalation**:
   - Executes Assessment A (Protocol Focus), Assessment B (Holistic Risk), and Clinical Rule Engine.
   - Applies configurable `STRICT_CONSERVATIVE` policy to force human escalation if any engine flags `URGENT`, `CONCERNING`, or `UNCERTAIN`.
4. **4 Role-Specific Workstations**:
   - **Platform Admin (`/platform`)**: Multi-hospital tenant management, infrastructure health, AI metrics, safety benchmark runner.
   - **Hospital Admin (`/hospital`)**: Hospital settings, discharge feed ingestion, protocols, user management, EHR sync settings.
   - **Campaign Manager (`/campaigns`, `/queue`)**: Campaign lifecycle state machine, capacity meter, live 25-patient queue simulator.
   - **Clinical Reviewer (`/review`)**: Escalation inbox, call transcript inspector, dual assessment consensus viewer, clinical override resolution form.
5. **Reusable Patient Search & Chronological Operational Timeline**:
   - Unified search modal displaying patient demographics, MRN, high-risk flag, and chronological audit journey.

---

## 4. Demo Login Credentials

| Role | Email | Password | Scope |
| :--- | :--- | :--- | :--- |
| **Platform Admin** | `admin@platform.gov` | `AdminPass123!` | Multi-Hospital Global |
| **Hospital Admin** | `admin@metrohealth.org` | `MetroAdmin123!` | MetroHealth System (`METRO`) |
| **Campaign Manager** | `manager@metrohealth.org` | `Manager123!` | MetroHealth System (`METRO`) |
| **Clinical Reviewer** | `reviewer@metrohealth.org` | `Reviewer123!` | MetroHealth System (`METRO`) |

---

## 5. Local Setup & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### Quick Start Commands

1. **Setup Backend**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   
   pip install -r requirements.txt
   pip install aiosqlite
   ```

2. **Seed Database (300+ Synthetic Patients across 4 Hospitals)**:
   ```bash
   python -m app.scripts.seed_data
   ```

3. **Run Safety Evaluation Benchmark**:
   ```bash
   python -m app.evaluation.run_safety_eval
   ```

4. **Run Scripted End-to-End Demo Scenario (36 Steps)**:
   ```bash
   python -m app.scripts.run_demo_scenario
   ```

5. **Start FastAPI Backend Server**:
   ```bash
   python -m app.main
   ```
   *Backend API runs at `http://localhost:8000` (Docs: `http://localhost:8000/api/v1/docs`)*

6. **Start React Frontend**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
   *Frontend app runs at `http://localhost:5173`*

---

# MANUAL STEPS FOR YOU

Here are the step-by-step instructions for what you need to do manually to run and evaluate the project on your machine:

- **Step 1: Install Required Software**
  - Ensure you have **Python 3.11 or higher** installed (`python --version`).
  - Ensure you have **Node.js 18 or higher** installed (`node -v`).

- **Step 2: Initialize Backend & Seed Database**
  - Open a terminal and navigate to the project directory: `cd backend`.
  - Activate the Python virtual environment: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/macOS).
  - Run the database seeding script:
    ```bash
    python -m app.scripts.seed_data
    ```
    *This creates the database schema and seeds 4 hospital tenants, 6 users, 230+ synthetic patients, protocols, campaigns, and queue simulation tasks.*

- **Step 3: Run the Clinical Safety Evaluation Benchmark**
  - In the `backend` directory with the virtual environment activated, run:
    ```bash
    python -m app.evaluation.run_safety_eval
    ```
    *This executes the 25-case safety evaluation benchmark and outputs `safety_report.json` and `safety_report.md` reporting a 0.00% False Negative Rate.*

- **Step 4: Run the Scripted End-to-End Demo Scenario**
  - In the `backend` directory, run:
    ```bash
    python -m app.scripts.run_demo_scenario
    ```
    *This automatically executes the 36-step end-to-end workflow from Platform Admin login through Queue simulation, AI intake, Consensus escalation, and EHR update.*

- **Step 5: Start the Backend API Server**
  - In the `backend` directory, run:
    ```bash
    python -m app.main
    ```
    *The FastAPI backend will start listening at `http://localhost:8000`.*

- **Step 6: Start the Frontend Application**
  - Open a second terminal window and navigate to the `frontend` directory: `cd frontend`.
  - Start the Vite development server:
    ```bash
    npm run dev
    ```
  - Open your browser and navigate to `http://localhost:5173`.

- **Step 7: Log in and Explore the 4 Workstations**
  - Click any of the **Quick Demo Persona Login** buttons on the login screen to explore:
    - **Platform Admin**: View aggregate system health, multi-hospital metrics, and trigger safety evaluations.
    - **Hospital Admin**: View ingested discharge feed, hospital settings, and protocols.
    - **Campaign Manager**: Explore the Live Queue Simulator, capacity meter, and click **Simulate Queue Step** or **Simulate Urgent Call**.
    - **Clinical Reviewer**: Open the escalation inbox, inspect patient transcript & dual AI assessments, and click **Resolve Escalation & Sync EHR**.
