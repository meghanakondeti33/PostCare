# Intelligent Capacity-Aware Outbound Queue Design (QUEUE_DESIGN.md)

## 1. Dynamic Prioritization Algorithm

The outbound queue optimizes outreach timing within each patient's clinical follow-up window rather than processing in FIFO insertion order.

### Priority Formula:
$$ \text{priority} = \text{clinical\_risk} + \text{deadline\_pressure} + \text{callback\_urgency} + \text{campaign\_priority} + \text{waiting\_time\_aging} - \text{retry\_penalty} $$

| Component | Calculation Logic | Range |
| :--- | :--- | :--- |
| **Clinical Risk** | `URGENT`: +40, `HIGH`: +30, `MEDIUM`: +15, `LOW`: +5 | 5.0 – 40.0 |
| **Deadline Pressure** | `< 6h remaining`: +40, `< 12h`: +25, `< 24h`: +10 | 0.0 – 50.0 |
| **Callback Urgency** | Patient requested time reached or overdue: +45 | 0.0 – 45.0 |
| **Campaign Priority** | `campaign.priority_score * 5` | 0.0 – 50.0 |
| **Waiting Time Aging** | `+2.0 points per hour waiting` (Starvation Prevention) | 0.0 – 30.0 |
| **Retry Penalty** | `-5.0 points per failed attempt` (Prioritizes fresh calls) | -15.0 – 0.0 |

---

## 2. Centralized Concurrency Control

When multiple background workers compete to make calls:
- The system queries active calls in state `CALLING` for the hospital tenant.
- If `active_calls >= max_concurrent_calls` (e.g. 10/10), the worker yields and waits.
- Capacity reservation uses database-level transactional locking:
  ```sql
  SELECT * FROM outreach_tasks
  WHERE hospital_id = :hospital_id
    AND state IN ('PENDING', 'RETRY_SCHEDULED', 'CALLBACK_SCHEDULED')
    AND (next_attempt_at IS NULL OR next_attempt_at <= NOW())
  ORDER BY priority_score DESC
  FOR UPDATE SKIP LOCKED
  LIMIT 1;
  ```

---

## 3. Retry Strategy & Exponential Backoff

When a call outcome is non-terminal (`NO_ANSWER`, `BUSY`, `VOICEMAIL`, `DROPPED`):
- **Attempt 1 Failure**: Backoff 15 minutes (`next_attempt_at = now + 15m`).
- **Attempt 2 Failure**: Backoff 60 minutes (`next_attempt_at = now + 60m`).
- **Attempt 3 Failure**: Maximum attempts (3) reached -> Task transitions to `MANUAL_FOLLOW_UP` and notifies clinical staff.

---

## 4. Dropped Call Context Recovery

If a call drops mid-conversation:
- Partial conversation transcript and answered questions are persisted in `partial_context`.
- Upon retry, the Voice Intake Agent resumes with the recorded context rather than repeating questions.

---

## 5. Crashed Worker Recovery (Heartbeat Timeout)

- Tasks reserved by workers are stamped with `worker_id` and `locked_at`.
- If a worker crashes while holding capacity, a heartbeat detector identifies tasks stuck in `CALLING` for > 5 minutes, releases the lock, increments `attempt_count`, and resets the state to `RETRY_SCHEDULED`.
