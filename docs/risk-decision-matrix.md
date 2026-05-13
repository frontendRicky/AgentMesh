# Risk Decision Matrix

| Severity | Default Behavior | Allowed Human Actions |
|---|---|---|
| `P0_BLOCKER` | Blocks progress. | `send_to_pm`, `send_to_architect`, `send_to_developer`, `send_to_qa`, `convert_to_blocker`, `cancel_task`. |
| `P1_HIGH` | Blocks by default. | `accept_risk_and_continue` only with explicit reason; replan/send/blocker/cancel options are preferred. |
| `P2_MEDIUM` | If `requires_human_decision == true`, unresolved risk blocks final-delivery. If `requires_human_decision == false`, it does not block but remains visible in report / known risks. | A legal RiskDecision allows final-delivery to proceed and must be referenced when accepted. |
| `P3_LOW` | Warning. | Record and continue unless it compounds with other risks. |
| `INFO` | Informational. | Record only. |

Runtime never accepts P0/P1 risk automatically.
