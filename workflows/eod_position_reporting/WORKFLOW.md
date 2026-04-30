---
workflow_type: eod_position_reporting
workflow_version: "0.1.0"
---

# Workflow: End-of-day position reporting

## Purpose

Publish authoritative desk positions by hub and book after market close,
drive limit utilization reporting, and feed accounting reconciliation.

## Trigger

- Scheduled EOD event in boundary layer, or `risk_analyst` manual open with
  `workflow_type: eod_position_reporting`.

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1 | risk_analyst | Compile positions, utilization, breaches |
| 2 | trader | Acknowledge or dispute with evidence |
| 3 | corporate_treasury | Liquidity / facility utilization vs positions (conditional) |
| 4 | accounting | Reconciliation hooks, accrual triggers |

## Steps

1. **Position compile** — `risk_analyst` aggregates from org state and
   in-flight deals; emits `notification` with structured positions array.
2. **Desk acknowledgment** — `trader` confirms or disputes within window;
   disputes become `exception` or sub-workflow per policy.
3. **Treasury slice** — `corporate_treasury` adds liquidity and headroom view when material.
4. **Accounting handoff** — `accounting` consumes snapshot id for GL and
   invoice accrual markers.

## Handoff map

```
risk_analyst → trader → corporate_treasury → accounting
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| report_date | date | As-of |
| snapshot_id | string | Links to `ORG_STATE` snapshot |
| dispute_open | bool | Accounting hold flag |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| Source disagreement | trader vs risk numbers | Freeze subset; human exception |
| Late deal | deal after snapshot | Versioned re-run EOD+1 |

## Time expectations

- Complete acknowledgment window per desk policy (e.g. T+0 19:00 local).

## Constraint highlights

- Regulatory position reports if thresholds exceeded — artifact requirements.
