# PostCare Architecture & System Design Document

*(For the complete submission documentation index, visit [`docs/final/INDEX.md`](./docs/final/INDEX.md) and [`docs/final/ARCHITECTURE.md`](./docs/final/ARCHITECTURE.md))*

## 1. System Overview

**PostCare** is a production-ready, multi-tenant AI-assisted healthcare outreach and clinical escalation platform. It enables hospital systems to manage post-discharge patient outreach campaigns, automate AI voice intake and triage, apply strict multi-model consensus to clinical assessments, and escalate concerning patient cases to human clinical reviewers with automated Mock EHR (FHIR R4) synchronization.

---

## 2. Master System Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Layer (Vercel Frontend)"]
        User["User / Healthcare Staff"] -->|HTTPS / JWT| Frontend["React 18 + Vite SPA\n(Hospital Admin, Campaign Mgr,\nClinical Reviewer, Platform Admin)"]
    end

    subgraph APILayer ["API & Control Layer (Render Python Backend)"]
        Frontend -->|REST API / JSON| FastAPI["FastAPI Application (Python 3.11.9)\n- JWT Auth & RBAC Middleware\n- X-Hospital-Id Tenant Isolator"]
    end

    subgraph ApplicationServices ["Core Application Services"]
        FastAPI --> QueueEngine["Intelligent Queue Engine\n- Multi-factor Priority Formula\n- Capacity Concurrency Limiter\n- FOR UPDATE SKIP LOCKED"]
        FastAPI --> TriagePipeline["Dual AI Triage Engine\n- Model A: Protocol Focus\n- Model B: Holistic Focus\n- Dynamic Conservative Consensus"]
        FastAPI --> EHRGateway["Mock EHR Gateway\n- FHIR R4 Record Creator\n- Resolution Auto-Sync"]
        FastAPI --> AuditObs["Observability & Audit Service\n- AuditLog & SystemHealth\n- AI Usage & Token Tracking"]
    end

    subgraph DataStorage ["Data & Cache Storage Layer"]
        QueueEngine -->|Asyncpg Connection| NeonDB[(Neon PostgreSQL\n- Encrypted TLS/SSL\n- 26+ Domain Schema)]
        FastAPI -->|Asyncpg Connection| NeonDB
        QueueEngine -->|Redis Protocol| UpstashRedis[(Upstash Redis\n- Task Cache & Locks)]
    end

    subgraph AIServices ["AI & RAG Grounding Layer"]
        TriagePipeline -->|Google GenAI SDK| GeminiAPI["Google Gemini 3.5 Flash API\n(Or MockAIProvider Fallback)"]
        TriagePipeline --> ProtocolRAG["Protocol RAG Engine\n- Tenant-Scoped Chunks\n- Keyword / Vector Relevance"]
    end

    subgraph GuardrailBoundary ["Controlled AI Tool & Execution Boundary"]
        GeminiAPI -->|Structured Output| Validation["Pydantic Schema Validation"]
        Validation -->|Business Rule Audit| RuleEngine["Clinical Rule Engine\n(Strict Conservative Fallback)"]
        RuleEngine -->|Authorized Actions Only| NeonDB
        RuleEngine -->|Audit Trail| AuditObs
    end
```

---

## 3. Core Architectural Principles

1. **Multi-Tenancy**: Every data entity and query is strictly isolated by `hospital_id`.
2. **Deterministic Guardrails**: AI models generate structured JSON predictions, which are validated by Pydantic schemas and evaluated by a strict conservative rule engine.
3. **Capacity & Concurrency**: Outreach task allocation uses `FOR UPDATE SKIP LOCKED` and respects hospital capacity limits.
4. **Resilience & Recovery**: Automatic stale task recovery for worker failures, exponential backoff retries, and fallback to Mock AI on quota exhaustion.
