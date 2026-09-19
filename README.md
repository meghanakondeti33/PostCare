# PostCare: Multi-Hospital Post-Discharge Outreach & Clinical Escalation Platform

> Autonomous AI-Powered Patient Follow-Up, Intelligent Queue Management, Dual-Assessment Clinical Triage & Human-in-the-Loop Review Platform

---

## 1. Executive Overview

**PostCare** is a production-ready, multi-tenant AI-assisted healthcare outreach and clinical escalation platform. It enables hospital systems to automate post-discharge patient outreach, queue management, AI voice intake and triage, dual-model consensus escalation, and human clinical review with automated Mock EHR (FHIR R4) synchronization.

```
Hospital Onboarding ──► Discharge Feed ──► Eligibility Engine ──► Intelligent Queue (FOR UPDATE SKIP LOCKED)
  ──► Capacity-Aware Scheduling ──► AI Voice Intake ──► Dual Triage Assessment (Model A & B)
    ──► Strict Conservative Consensus ──► Clinical Reviewer Inbox ──► Mock EHR Sync ──► Observability & Audit
```

---

## 2. Complete Submission Documentation

The complete, authoritative documentation package is located in `/docs/final/`:

| Document | Link | Description |
| :--- | :--- | :--- |
| **Documentation Index** | [`docs/final/INDEX.md`](./docs/final/INDEX.md) | Complete index and roadmap for evaluators. |
| **System Architecture** | [`docs/final/ARCHITECTURE.md`](./docs/final/ARCHITECTURE.md) | Component architecture, data flow, tenant boundaries, and security model. |
| **Intelligent Queue Design** | [`docs/final/QUEUE_DESIGN.md`](./docs/final/QUEUE_DESIGN.md) | Multi-factor priority formula, capacity limiting, `SKIP LOCKED`, retries, backoff. |
| **Safety Evaluation Report** | [`docs/final/SAFETY_EVALUATION.md`](./docs/final/SAFETY_EVALUATION.md) | 25-case benchmark, 0% false-negative rate metrics, confusion matrix. |
| **AI System & Guardrails** | [`docs/final/AI_USAGE.md`](./docs/final/AI_USAGE.md) | Dual assessment models, system prompts, protocol RAG grounding, tool guardrails. |
| **Development AI History** | [`docs/final/DEVELOPMENT_AI_USAGE.md`](./docs/final/DEVELOPMENT_AI_USAGE.md) | Transparent accounting of Google Antigravity & Gemini assistance during development. |
| **Limitations & Tradeoffs** | [`docs/final/LIMITATIONS_AND_TRADEOFFS.md`](./docs/final/LIMITATIONS_AND_TRADEOFFS.md) | Simulated components, prototype security vs HIPAA roadmap, evaluation scope. |
| **Evaluator Demo Guide** | [`docs/final/DEMO_GUIDE.md`](./docs/final/DEMO_GUIDE.md) | Step-by-step evaluator walkthrough across all 4 role workstations. |
| **Deployment Guide** | [`docs/final/DEPLOYMENT.md`](./docs/final/DEPLOYMENT.md) | Cloud infrastructure guide for Render, Neon PostgreSQL (SSL), Upstash Redis, and Vercel. |

---

## 3. Technology Stack & Key Verification Metrics

- **Frontend**: React 18, TypeScript, Vite, Vanilla CSS + Tailwind CSS, Lucide Icons, React Router DOM (`Vite Build Exit Code 0`).
- **Backend**: Python 3.11.9, FastAPI, Pydantic v2, AsyncSQLAlchemy 2.0, Asyncpg / Aiosqlite (`40/40 Pytest Passed`).
- **Database**: Neon PostgreSQL (with SSL/TLS URL parser; SQLite fallback for local test suite).
- **Cache & Queue**: Upstash Redis / Memory cache.
- **AI Triage**: Google Gemini 3.5 Flash (`gemini-3.5-flash`) via `google-genai` SDK + `MockAIProvider` fallback.
- **Clinical Safety Benchmark**: 25-case synthetic benchmark achieving **0.00% False Negative Rate** (18 True Positives, 7 True Negatives).

---

## 4. Pre-Configured Demo Credentials

| Role | Email | Password | Primary Dashboard | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Hospital Admin** | `admin@metrohealth.org` | `admin123` | `/hospital` | MetroHealth System (`hosp-metro-1`) |
| **Campaign Manager** | `campaign@metrohealth.org` | `campaign123` | `/campaigns` | MetroHealth System (`hosp-metro-1`) |
| **Clinical Reviewer** | `reviewer@metrohealth.org` | `reviewer123` | `/review` | MetroHealth System (`hosp-metro-1`) |
| **Platform Admin** | `admin@postcare.health` | `platform123` | `/admin` | Multi-Hospital Global (`ALL`) |

---

## 5. Local Setup & Quick Start

```bash
# 1. Clone & Navigate to Backend
cd backend

# 2. Virtual Environment Setup
python -m venv venv
# On Windows: .\venv\Scripts\activate | On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# 3. Non-Destructive Schema Initialization & Safe Demo Seed
python -m app.scripts.init_prod_db
python -m app.scripts.seed_prod_demo

# 4. Run Backend Tests (40 Passed)
$env:PYTHONPATH="."
.\venv\Scripts\pytest -q

# 5. Run Safety Evaluation Benchmark
python -m app.evaluation.run_safety_eval

# 6. Start Backend Server
python -m app.main

# 7. In a second terminal, start Frontend (Vite)
cd ../frontend
npm install
npm run dev
```

- Frontend Dev Server: `http://localhost:5173`
- Backend API & Docs: `http://localhost:8000/api/v1/docs`
