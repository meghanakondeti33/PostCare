# Architecture Documentation (ARCHITECTURE.md)

## System Overview & Component Diagram

The **Multi-Hospital Post-Discharge Outreach Platform** is built as a production-oriented modular monolith designed for multi-tenant isolation, capacity-aware concurrency queueing, dual AI consensus triage, and clinical human-in-the-loop escalation.

```mermaid
graph TD
    Client["React + TypeScript + Vite Frontend<br/>(4 Workstations)"]
    
    subgraph FastAPI_Backend ["FastAPI Backend (Modular Monolith)"]
        AuthModule["JWT Auth & RBAC Dependencies"]
        TenantGuard["Tenant Isolation Guard (hospital_id)"]
        
        APILayer["API Routers<br/>(Patients, Queue, Campaigns, Calls, Escalations)"]
        
        QueueEngine["Queue & Scheduling Engine<br/>(Priority Formula + Concurrency Lock)"]
        
        AIProvider["AI Provider Abstraction<br/>(GeminiProvider / OpenAIProvider / MockAIProvider)"]
        PromptRepo["Versioned Prompt Repo (v1.0.0)"]
        
        RAGModule["Tenant-Isolated Protocol RAG Service"]
        ConsensusModule["Multi-Assessment & Consensus Engine<br/>(Assessment A + Assessment B + Rule Engine)"]
        
        ControlledTools["Controlled AI Tools Framework"]
        EHRModule["Mock EHR Integration (FHIR R4)"]
        
        AuditObs["Observability & Audit Logger"]
    end
    
    Database[(PostgreSQL Database<br/>SQLAlchemy 2.x + pgvector)]
    RedisQueue[(Redis / Celery Worker Queue)]
    
    Client -->|HTTPS / JWT| AuthModule
    AuthModule --> TenantGuard
    TenantGuard --> APILayer
    
    APILayer --> QueueEngine
    QueueEngine -->|SELECT FOR UPDATE SKIP LOCKED| Database
    QueueEngine --> RedisQueue
    
    APILayer --> AIProvider
    AIProvider --> PromptRepo
    AIProvider --> RAGModule
    RAGModule --> Database
    
    AIProvider --> ConsensusModule
    ConsensusModule --> ControlledTools
    ControlledTools --> Database
    ControlledTools --> EHRModule
    
    APILayer --> AuditObs
    AuditObs --> Database
```

## Architectural Boundaries

1. **Multi-Tenancy & Authorization Boundary**:
   - Every database query and background worker task carries an explicit `hospital_id` filter.
   - Frontend passes `X-Hospital-Id` header (or reads from JWT user context).
   - Zero cross-tenant data retrieval across hospitals.

2. **Queue Concurrency Boundary**:
   - Outbound calling capacity is strictly limited per hospital tenant (e.g. 10 concurrent calls).
   - Database level `SELECT ... FOR UPDATE SKIP LOCKED` guarantees two workers never reserve the same slot or exceed capacity.

3. **AI Control Boundary**:
   - AI models NEVER directly touch database tables.
   - All side effects (escalation creation, callback scheduling, EHR sync) execute via `ControlledTools` with schema validation, business rule checks, and audit logging.

4. **Clinical Safety Consensus Boundary**:
   - Dual AI assessments (Assessment A & B) plus a clinical Rule Engine operate independently.
   - Under `STRICT_CONSERVATIVE` consensus policy, any indication of `URGENT`, `CONCERNING`, or `UNCERTAIN` triggers mandatory human escalation.
