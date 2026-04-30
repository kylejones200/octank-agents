---
workflow_type: risk_escalation
workflow_version: "0.1.0"
---

# Workflow: Risk escalation (limits / policy)

## Purpose

Bounded, time-stamped escalation when risk cannot be cleared automatically:
breach unresolved, ambiguous reporting treatment, or conflicting instructions.

## Trigger

- `risk_analyst` or system raises `escalation` on limit breach, or trader
  requests override path with evidence payload.

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1 | risk_analyst | Package metrics, history, options |
| 2 | trader | Acknowledge, reduce, or provide mitigation plan |
| 3 | desk_manager | Decision within delegated authority |
| 4 | compliance_officer | When regulatory reporting or policy interpretation required |
| 5 | executive_office | Final tier when desk + compliance cannot close within policy |

## Steps

1. **Triage** — `risk_analyst` attaches utilization, hub, limit, proposed trade
   delta, and timer since first breach.
2. **Trader response window** — `trader` must `response` with reduce / hold /
   request temporary exception (routes per constraint).
3. **Management decision** — `desk_manager` selects allowed option; system
   records override id if temporary lift permitted.
4. **Compliance branch (if needed)** — `compliance_officer` confirms reporting and filing posture.
5. **Executive branch (if needed)** — `executive_office` for capital or firm-level exception.

## Handoff map

```
risk_analyst → trader → desk_manager → [compliance_officer] → [executive_office] → (resume deal_execution or close)
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| breach_hub | string | Location / book key |
| utilization | number | At escalation time |
| actions_taken | array | Audit trail of nudges |
| management_option | string | Chosen path |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| SLA missed | escalation timer | Suspend trading on hub per policy |
| Rule conflict | compound rule fail | `rule_conflict` exception queue |

## Time expectations

- Critical SLA per [`docs/specs/EXCEPTION_QUEUE.md`](../../docs/specs/EXCEPTION_QUEUE.md) (example: 1h to management visibility).

## Constraint highlights

- Overrides logged; regulation-sourced rules may forbid override entirely.
