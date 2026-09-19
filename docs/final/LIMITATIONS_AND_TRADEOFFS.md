# PostCare Architectural Limitations, Prototype Scope & Healthcare Roadmap

## 1. Prototype Scope Statement

**PostCare** is designed as a production-grade engineering prototype and architectural demonstration for AI-assisted healthcare outreach. While the system adheres to strict software engineering standards—including multi-tenant data isolation, dynamic consensus rules, capacity-aware queue locking, and cloud deployment—it operates within specific prototype boundaries.

---

## 2. Technical Limitations & Simulated Components

### 1. Simulated Telephony & Audio Call Gateway
- **Current Implementation**: Outreach calls are simulated via API (`POST /api/v1/calls/simulate`). Transcripts and patient responses are passed as JSON payloads. Recording URLs are simulated metadata endpoints.
- **Production Requirement**: Real-world deployment requires integration with a WebRTC / PSTN voice carrier (e.g. Twilio Voice API, Plivo, or SignalWire) with live streaming Speech-to-Text (STT) and Text-to-Speech (TTS).

### 2. Mock EHR Gateway (FHIR R4)
- **Current Implementation**: Patient discharge records and escalation resolution syncs generate FHIR R4 JSON payloads stored in the PostgreSQL database.
- **Production Requirement**: Live healthcare deployment requires integration with hospital Electronic Health Record systems (Epic, Cerner, SMART-on-FHIR) via HL7/FHIR APIs with mutual TLS (mTLS) authentication.

### 3. Synthetic Patient & Clinical Dataset
- **Current Implementation**: All patient names (e.g. *Jennifer Johnson*, *Charles Hernandez*, *William Miller*), MRNs, and clinical discharge records are synthetic test data generated for evaluation.
- **Production Requirement**: No real Protected Health Information (PHI) is present in the codebase or repository.

### 4. Protocol RAG & Retrieval Engine
- **Current Implementation**: Clinical guidelines are chunked into `KnowledgeChunk` records and retrieved using keyword and TF-IDF similarity scoring.
- **Production Requirement**: Enterprise clinical RAG requires a dedicated vector database (e.g. `pgvector`, Pinecone, or Qdrant) with domain-specific medical embeddings (e.g. BioBERT / MedCPT).

### 5. Synthetic Safety Evaluation Benchmark Scope
- **Current Implementation**: The 25-scenario safety benchmark ([`app/evaluation/run_safety_eval.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/evaluation/run_safety_eval.py)) evaluates prompt adherence and consensus fallback.
- **Production Requirement**: The **0% false-negative rate** applies strictly to this 25-case synthetic benchmark. It does **not** constitute clinical certification or real-world medical safety validation.

---

## 3. Security Boundary vs. Healthcare Compliance

| Security Dimension | Current Prototype Status | Production Healthcare Requirement |
| :--- | :--- | :--- |
| **Authentication & RBAC** | Implemented (JWT HS256, 4 User Roles) | OAuth2 + OIDC with SAML/SSO integration |
| **Tenant Isolation** | Implemented (`hospital_id` SQL filtering) | Enforced multi-tenant schema / VPC isolation |
| **Data Encryption** | Implemented (PostgreSQL TLS/SSL) | Encrypted storage at rest (AES-256) & in transit |
| **HIPAA Compliance** | **NOT CERTIFIED (Prototype Scope)** | Signed Business Associate Agreement (BAA) with Cloud Providers |
| **Audit Logging** | Implemented (`AuditLog` DB records) | WORM (Write Once Read Many) immutable audit trail |

> [!CAUTION]
> **HIPAA Caveat**: PostCare is a software prototype. It is **not** HIPAA certified, SOC 2 certified, or approved for processing live Protected Health Information (PHI).

---

## 4. Production Healthcare Roadmap

To transition PostCare from prototype to live clinical deployment:

1. **HIPAA & Infrastructure**: Execute Business Associate Agreements (BAAs) with Render, Neon, Upstash, and Google Cloud.
2. **EHR Interoperability**: Implement OAuth2 SMART-on-FHIR launch flows for Epic Hyperspace and Cerner PowerChart.
3. **PSTN Telephony**: Integrate Twilio Media Streams for live bi-directional audio streaming.
4. **Clinical Validation**: Conduct IRB-approved retrospective clinical studies with human nurse review oversight.
