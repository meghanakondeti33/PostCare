# PostCare Development AI Usage & Engineering History

## 1. Overview & Responsible AI Engineering

In accordance with PRD v2.0 requirements, this document transparently records how AI-assisted engineering tools—specifically **Google Antigravity IDE** powered by **Gemini** models—were utilized during the design, implementation, testing, debugging, and deployment of the PostCare platform.

AI assistants served as pair-programming tools under human supervision. Every line of code, database schema model, and priority algorithm generated or refined with AI assistance was validated through empirical testing (`pytest`), static typing (`tsc`), and runtime log verification.

---

## 2. Key Development Phases & AI Prompt Categories

### Phase 1: System Architecture & Data Schema
- **Task**: Designing the multi-hospital database model ([`app/models/domain.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/models/domain.py)).
- **AI Prompting Summary**: Guided the structuring of SQLAlchemy 2.0 async models for 26+ domain entities, enforcing foreign-key tenant isolation (`hospital_id`) across all tables.

### Phase 2: Intelligent Queue & Concurrency Engine
- **Task**: Implementing the multi-factor priority algorithm and row locking in [`app/queue/queue_engine.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/queue/queue_engine.py).
- **AI Prompting Summary**: Collaborated on drafting the priority score formula (combining risk tier, deadline pressure, callback urgency, campaign weight, aging, and retry penalty) and integrating PostgreSQL `SELECT FOR UPDATE SKIP LOCKED`.

### Phase 3: Dual Assessment & Consensus Engine
- **Task**: Developing the dual triage workflow and `STRICT_CONSERVATIVE` consensus policy ([`app/ai/consensus.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/ai/consensus.py)).
- **AI Prompting Summary**: Designed Assessment A (Protocol-Focused) and Assessment B (Holistic-Focused) system prompts, and implemented conservative fallback logic whenever models disagree or report red flags.

### Phase 4: Deterministic Safety Evaluation Benchmark
- **Task**: Building a 25-scenario repeatable safety evaluation benchmark ([`app/evaluation/run_safety_eval.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/evaluation/run_safety_eval.py)).
- **AI Prompting Summary**: Formulated 25 clinical test cases (urgent, concerning, ambiguous, adversarial prompt-injection, and routine) and built an offline evaluator using `MockAIProvider` to guarantee 0% false negatives without consuming live API quota.

### Phase 5: Production Deployment & Neon PostgreSQL Compatibility
- **Task**: Resolving asyncpg driver compatibility issues (`sslmode=require`, `channel_binding=require`) for Neon PostgreSQL deployment.
- **AI Prompting Summary**: Built [`prepare_database_config()`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/core/database.py#L8) to strip libpq query params from DSNs and map SSL configuration to `connect_args["ssl"] = "require"`.

---

## 3. Human Verification & Quality Assurance

- **Verification Process**: No code was accepted without empirical test pass reports.
- **Test Coverage**: 40 unit and integration tests (`pytest -q`) and full Vite production builds (`npm run build`) confirm zero compilation or runtime regressions.
