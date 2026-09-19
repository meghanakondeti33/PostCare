# AI Architecture & Usage Documentation (AI_USAGE.md)

## 1. Provider Abstraction Layer

The platform abstracts LLM interactions behind `AIProviderInterface` ([`backend/app/ai/provider.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/ai/provider.py)):
- **`MockAIProvider`**: Deterministic provider used for reproducible unit tests and safety evaluation benchmarks without requiring external API keys.
- **`GeminiProvider`**: Direct integration with Google Gemini 2.5/1.5 API using structured JSON schema response modes.
- **`OpenAIProvider`**: OpenAI ChatCompletions compatible interface (`gpt-4o`, `gpt-4o-mini`).

Configured via `.env` variable `AI_PROVIDER=mock` (or `gemini`, `openai`).

---

## 2. Agent Framework & Responsibilities

1. **Voice Intake Agent**:
   - Manages structured patient outreach dialogue.
   - Verifies identity, follows hospital protocols, collects symptom responses.
2. **Clinical Triage Agent**:
   - Parses transcripts into Pydantic structured output (`ROUTINE`, `CONCERNING`, `URGENT`, `UNCERTAIN`).
3. **Escalation Decision System**:
   - Executes Dual AI Assessments (Assessment A & B) plus Rule Engine.
   - Evaluates consensus policy (`STRICT_CONSERVATIVE`).
4. **Documentation Agent**:
   - Generates structured post-discharge clinical notes and syncs to Mock EHR.

---

## 3. Explicit Prompt Versioning & Auditing

All prompt templates are semantically versioned (e.g. `v1.0.0_intake`, `v1.0.0_triage`) in [`backend/app/ai/prompts.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/ai/prompts.py).
Every call assessment records the exact `prompt_version` in `TriageAssessment`, `ConsensusDecision`, and `AuditLog` tables for regulatory auditability.
