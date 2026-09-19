# PostCare Architectural Limitations, Prototype Scope & Healthcare Roadmap

*(For the complete submission documentation index, visit [`docs/final/INDEX.md`](./docs/final/INDEX.md) and [`docs/final/LIMITATIONS_AND_TRADEOFFS.md`](./docs/final/LIMITATIONS_AND_TRADEOFFS.md))*

## Overview & Prototype Boundaries

PostCare is an engineering proof-of-concept for AI-assisted healthcare outreach. It operates under the following explicit prototype tradeoffs:

1. **Simulated Telephony**: Outreach calls are simulated via API (`/api/v1/calls/simulate`); no PSTN carrier is attached.
2. **Mock EHR**: FHIR R4 JSON records are created and synced locally; no live Epic/Cerner connection.
3. **Synthetic Data**: All patient names, MRNs, and discharge summaries are synthetic test data.
4. **Synthetic Safety Benchmark**: The 25-case safety benchmark achieves a **0% false-negative rate** on synthetic data, but does not constitute real-world clinical certification.
5. **HIPAA Notice**: PostCare is **not** HIPAA or SOC 2 certified. It is a prototype software project.
