# PostCare AI System & Dual Assessment Architecture

## 1. AI Architecture Overview

PostCare uses a dual-model, protocol-grounded AI triage system designed to evaluate post-discharge patient outreach conversations. To ensure clinical safety, AI models operate within strict architectural boundaries: they generate structured JSON predictions which are validated by backend Pydantic schemas and evaluated by a deterministic consensus engine.

---

## 2. AI Provider Abstraction

The AI layer ([`backend/app/ai/provider.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/ai/provider.py)) defines a factory interface (`BaseAIProvider`) supporting multiple implementations:

1. **`GeminiAIProvider`**: Connects to Google Gemini API (`gemini-3.5-flash`) using the official `google-genai` SDK. Supports structured outputs via system instructions and schema definitions.
2. **`MockAIProvider`**: Deterministic, offline provider used for automated testing, offline evaluation benchmarking, and automatic fallback when live API quota is exceeded.

```python
# Provider Selection Logic (app/ai/provider.py)
def get_ai_provider() -> BaseAIProvider:
    provider_name = settings.AI_PROVIDER.lower()
    if provider_name == "gemini":
        try:
            return GeminiAIProvider()
        except AIProviderConfigError:
            if settings.AI_FALLBACK_TO_MOCK:
                return MockAIProvider()
            raise
    return MockAIProvider()
```

---

## 3. Specialized AI Agents & System Prompts

| Agent / Model Role | System Prompt Focus | Primary Responsibilities |
| :--- | :--- | :--- |
| **Voice Intake Agent** | Telephony Conversation Context | Simulates conversational post-discharge patient Q&A, asking targeted questions about pain, wound care, fever, and medications. |
| **Assessment A (Protocol Focus)** | `CLINICAL_TRIAGE_SYSTEM_PROMPT` (Protocol Mode) | Evaluates strict clinical protocol rules, numeric thresholds (e.g. fever > 101.0°F), and explicit red flag keywords. |
| **Assessment B (Holistic Focus)** | `CLINICAL_TRIAGE_SYSTEM_PROMPT` (Holistic Mode) | Evaluates overall patient recovery trajectory, symptom progression, confusion, and psychosocial context. |
| **Documentation Agent** | Clinical Summary Generation | Formats clinical findings into concise SBAR (Situation, Background, Assessment, Recommendation) notes for reviewer documentation. |

---

## 4. Dual Assessment & Consensus Engine

Every completed outreach call triggers two independent triage assessments to mitigate single-model bias and hallucinations:

```
                  ┌─────────────────────────────────────────┐
                  │          Outreach Call Transcript       │
                  └────────────────────┬────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
   ▼                                                          ▼
┌───────────────────────────────────┐      ┌───────────────────────────────────┐
│       Assessment A (Gemini)       │      │       Assessment B (Gemini)       │
│      Protocol-Focused Triage      │      │       Holistic-Focused Triage     │
└─────────────────┬─────────────────┘      └─────────────────┬─────────────────┘
                  │                                          │
                  └────────────────────┬─────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Consensus Engine             │
                       │  (STRICT_CONSERVATIVE Policy) │
                       └───────────────┬───────────────┘
                                       │
                      ┌────────────────┴────────────────┐
                      │                                 │
           If Disagreement or Urgent          If Both Models Agree Routine
                      ▼                                 ▼
           ┌─────────────────────┐           ┌─────────────────────┐
           │ Create Escalation   │           │ Close Routine Task  │
           │ & Alert Nurse       │           │ Log Audit Record    │
           └─────────────────────┘           └─────────────────────┘
```

### Consensus Policy (`STRICT_CONSERVATIVE`)
- **Agreement on Routine**: If Assessment A and Assessment B both classify the call as `ROUTINE`, consensus is `ROUTINE`.
- **Model Disagreement / Red Flags**: If one model identifies `URGENT` or `CONCERNING` while the other outputs `ROUTINE`, or if either model expresses `UNCERTAIN`, the consensus engine forces an automatic escalation to `URGENT` / `CONCERNING` and flags `"MODEL_DISAGREEMENT"` in the clinical rationale.

---

## 5. Protocol RAG Grounding Engine

PostCare uses a tenant-scoped Retrieval-Augmented Generation (RAG) engine ([`backend/app/rag/protocol_rag.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/rag/protocol_rag.py)) to ground AI triage predictions in verified hospital clinical protocols:

1. **Protocol Ingestion**: Clinical guidelines (e.g. *Post-Discharge Cardiac Surgery Protocol v2.1*) are uploaded by Hospital Admins and chunked into `KnowledgeChunk` records.
2. **Tenant Isolation**: Search queries strictly filter by `where(KnowledgeChunk.hospital_id == hospital_id)`.
3. **Relevance Ranking**: Chunks are scored against patient symptoms using keyword and TF-IDF similarity.
4. **Prompt Context Injection**: Relevant protocol sections are formatted into the system prompt context:
   ```python
   prompt_context = format_rag_prompt_context(matched_chunks)
   ```

---

## 6. Controlled AI Tool Boundary & Security Guardrails

AI models in PostCare **do not** have direct database or execution privileges.

```
AI Model Prediction (JSON)
  ──► Schema Validation (Pydantic)
    ──► Clinical Rule Engine Audit
      ──► Authorized Service Execution (Database Write)
        ──► Immutable AuditLog Record
```

- **Pydantic Validation**: All raw JSON responses are parsed against schema models (`TriageAssessmentSchema`). Malformed outputs raise schema validation errors and trigger retry handling.
- **Audit Logging**: Every AI invocation creates an `AIUsage` record tracking prompt tokens, completion tokens, execution time, model provider, prompt version, and estimated cost.

---

## 7. Prototype Tradeoffs & Security Scope

- **AI Token Tracking**: Token counts and execution latency are tracked in `AIUsage`. Financial cost is calculated using static tier estimations ($0.00015 / 1K tokens).
- **Prompt Injection Defense**: Adversarial inputs (e.g. *"Ignore previous instructions"*) are safely neutralized because the triage engine evaluates raw patient statements strictly against Pydantic schema enums (`URGENT`, `CONCERNING`, `ROUTINE`).

---

## 8. Client-Side Rate Limiting & Gemini Free-Tier Hardening

Under the Google Gemini Free Tier, model request limits enforce approximately **5 Requests Per Minute (RPM)**. Because a single simulated post-discharge outreach workflow requires 4 sequential Gemini API calls (Voice Intake Agent, Clinical Triage Agent, Assessment A, and Assessment B), PostCare implements application-side rate limiting to remain safe:

1. **Async Sliding-Window Rate Limiter**: Configured via `GEMINI_RPM_SAFETY_LIMIT=4` (default target: 4 RPM, below Google's 5 RPM hard cap). Every API call passes through `GeminiRateLimiter.acquire()`, which waits asynchronously (`asyncio.sleep`) without blocking the FastAPI event loop if the limit is reached.
2. **HTTP 429 Handling**:
   - **Temporary RPM Limits**: Evaluates `Retry-After` headers or uses bounded exponential backoff with jitter (`min(0.5 * 2^attempt + jitter, 5.0)`).
   - **Daily Quota Exhaustion (`RPD` Limit)**: Detects non-retryable project quota exhaustion (`RESOURCE_EXHAUSTED` / `GenerateRequestsPerDayPerProject-FreeTier`) and fails fast with an explicit `AIProviderUnavailableError` without creating retry storms.
3. **Sequential Assessment Execution**: Assessment A (Protocol Focus) and Assessment B (Holistic Focus) are executed sequentially through the rate limiter to maintain independent reasoning while controlling request timing.
4. **Clarification**: Client-side rate limiting does not increase Google's quota or guarantee unlimited throughput; it provides deterministic application-side protection against exceeding configured project limits.
