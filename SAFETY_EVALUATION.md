# PostCare Clinical Safety Evaluation & Benchmark Report

*(For the complete submission documentation index, visit [`docs/final/INDEX.md`](./docs/final/INDEX.md) and [`docs/final/SAFETY_EVALUATION.md`](./docs/final/SAFETY_EVALUATION.md))*

## Executive Metrics Summary

The platform achieved a **0% false-negative rate on the included 25-case synthetic safety evaluation dataset** ([`backend/app/evaluation/run_safety_eval.py`](file:///c:/Users/CSE/Desktop/PostCare/backend/app/evaluation/run_safety_eval.py)).

| Metric | Score | Clinical Target | Status |
| :--- | :---: | :---: | :---: |
| **False Negative Rate (FNR)** | `0.00%` | `< 1.0%` | **PASSED** |
| **False Positive Rate (FPR)** | `0.00%` | `< 15.0%` | **PASSED** |
| **Recall (Sensitivity)** | `100.00%` | `> 99.0%` | **PASSED** |
| **Precision** | `100.00%` | `> 85.0%` | **PASSED** |
| **Accuracy** | `100.00%` | `> 95.0%` | **PASSED** |

### Confusion Matrix
- **True Positives (TP)**: 18 (Expected Escalate -> Escalated)
- **True Negatives (TN)**: 7 (Expected Routine -> Routine)
- **False Positives (FP)**: 0
- **False Negatives (FN)**: 0 *(Zero False Negatives Target)*

> **Note**: This benchmark reflects performance on a synthetic 25-case prototype dataset and does not constitute real-world clinical certification.
