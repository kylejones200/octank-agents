---
workflow_type: systems_change_request
workflow_version: "0.1.0"
---

# Workflow: Systems change request (IT + desk + ops)

## Purpose

Safely change feeds, ETRM configuration, integrations, or access that affect
trading, scheduling, or risk reporting — with IT ownership and desk sign-off.

## Trigger

- New data feed, version upgrade, cutover window, or access change that touches
  market or operational systems.

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1 | it_platform | Impact analysis, change plan, rollback |
| 2 | ops | Physical / operator-facing impacts |
| 3 | trader or scheduler | Desk confirmation of business acceptance |
| 4 | risk_analyst | Reporting and limit engine checks post-change |

## Steps

1. **Change proposal** — `it_platform` documents scope, window, dependencies, test evidence.
2. **Ops review** — `ops` confirms pipeline / SCADA / operator touchpoints.
3. **Business acceptance** — `trader` or `scheduler` confirms desk-ready (as applicable).
4. **Risk validation** — `risk_analyst` re-runs checks or signs off on reporting continuity.

## Handoff map

```
it_platform → ops → trader|scheduler → risk_analyst → close
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| change_id | string | |
| maintenance_window | string | ISO window |
| rollback_plan_ref | string | artifact id |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| Go-live without risk sign-off | workflow state | Block production flag |

## Constraint highlights

- Segregation of duties: IT does not unilaterally approve risk-impacting cutover.
