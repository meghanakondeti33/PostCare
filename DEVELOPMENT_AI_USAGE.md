# Development AI Usage Documentation (DEVELOPMENT_AI_USAGE.md)

## AI-Assisted Engineering Workflows

During the design and construction of the PostCare platform, AI development tools were utilized for architecture planning, schema design, queue modeling, prompt engineering, and test suite generation.

### Key Engineering Prompts & AI Contributions

1. **Multi-Tenant Architecture & Concurrency Locking**:
   - *Prompt Goal*: Design a database-backed concurrency reservation engine for FastAPI and SQLAlchemy 2.x that prevents worker race conditions without requiring external microservices.
   - *Outcome*: Implemented `SELECT ... FOR UPDATE SKIP LOCKED` inside [`backend/app/queue/queue_engine.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/queue/queue_engine.py).

2. **Dual AI Assessment & Consensus Policy**:
   - *Prompt Goal*: Implement dual independent LLM evaluation paths (Protocol Matching vs Holistic Deterioration Risk) and a conservative consensus engine.
   - *Outcome*: Built [`backend/app/ai/consensus.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/ai/consensus.py) with configurable policies (`STRICT_CONSERVATIVE`, `MAJORITY_VOTE`, `RULE_OVERRIDE_ONLY`).

3. **Clinical Safety Benchmark Dataset**:
   - *Prompt Goal*: Construct a 25-case clinical evaluation dataset covering urgent red flags, post-op complications, ambiguous statements, and prompt injection attacks.
   - *Outcome*: Created [`backend/app/evaluation/run_safety_eval.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/evaluation/run_safety_eval.py) achieving 0.00% False Negative Rate.
