# PostCare Intelligent Queue & Scheduling Architecture

*(For the complete submission documentation index, visit [`docs/final/INDEX.md`](./docs/final/INDEX.md) and [`docs/final/QUEUE_DESIGN.md`](./docs/final/QUEUE_DESIGN.md))*

## 1. Queue Purpose & Overview

The **PostCare Intelligent Queue Engine** ([`backend/app/queue/queue_engine.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/queue/queue_engine.py)) is a capacity-aware, multi-factor prioritization engine for automated post-discharge patient outreach. It ensures that high-risk cardiac and surgical patients are contacted promptly, clinical cutoffs are met, explicit callbacks are prioritized, starvation of lower-priority cases is prevented, and hospital concurrency limits are respected without race conditions.

---

## 2. Priority Calculation Formula

$$\text{Priority Score} = \text{BaseRisk} + \text{DeadlinePressure} + \text{CallbackUrgency} + (\text{CampaignPriority} \times 5) + \text{Aging} - \text{RetryPenalty}$$

- **Base Risk**: URGENT (40.0), HIGH (30.0), MEDIUM (15.0), LOW (5.0).
- **Deadline Pressure**: Overdue (+50.0), <=6h (+40.0), <=12h (+25.0), <=24h (+10.0).
- **Callback Urgency**: Due or overdue (+45.0).
- **Campaign Priority**: Weight factor $\times 5.0$.
- **Waiting-Time Aging**: $+2.0$ points per waiting hour (capped at +30.0).
- **Retry Penalty**: $-5.0$ points per failed attempt.

---

## 3. Concurrency Control

- **Capacity Check**: `active_calling_count < hospital.max_concurrent_calls`.
- **Row Locking**: PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` prevents race conditions.
- **Worker Crash Recovery**: Automatically resets stale `CALLING` locks (> 5 min).
