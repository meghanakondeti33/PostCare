# PostCare AI System & Dual Assessment Architecture

*(For the complete submission documentation index, visit [`docs/final/INDEX.md`](./docs/final/INDEX.md) and [`docs/final/AI_USAGE.md`](./docs/final/AI_USAGE.md))*

## Overview

PostCare uses a dual-model, protocol-grounded AI triage system designed to evaluate post-discharge patient outreach conversations. To ensure clinical safety, AI models operate within strict architectural boundaries: they generate structured JSON predictions which are validated by backend Pydantic schemas and evaluated by a deterministic consensus engine.

## Core Features
1. **Multi-Provider Factory**: Supports Google Gemini 3.5 Flash (`GeminiAIProvider`) and offline deterministic mock (`MockAIProvider`).
2. **Dual Triage Pipeline**: Model A (Protocol-Focused) + Model B (Holistic-Focused).
3. **Strict Conservative Consensus**: Automatically escalates on disagreement, red flags, or uncertainty.
4. **Tenant-Scoped Protocol RAG**: Grounded in hospital-specific clinical protocols (`KnowledgeChunk`).
5. **Controlled Tool Guardrails**: Pydantic validation -> Rule Audit -> Execution -> `AIUsage` logging.
