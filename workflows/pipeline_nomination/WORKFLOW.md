---
workflow_type: pipeline_nomination
workflow_version: "0.1.0"
---

# Workflow: Pipeline nomination (gas day)

## Purpose

Submit accurate nominations to interstate or LDC pipelines for a defined gas
day or month, with operator confirmation and imbalance visibility.

## Trigger

- Confirmed transport need from `deal_execution`, or recurring daily cycle from
  calendar (scheduler-initiated).

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1 | trader | Nomination details: receipt/delivery, rank, volumes |
| 2 | scheduler | Format and transmit per operator protocol |
| 3 | ops | Confirm flow orders, OFOs, actualizations |

## Steps

1. **Build nomination** — `trader` provides structured path, rank, MDQ usage,
   and linked `deal_id` / `workflow_id`.
2. **Transmit** — `scheduler` validates cutoff, sends request, captures
   confirmation number in artifacts.
3. **Physical follow-through** — `ops` monitors confirmations; if curtailed,
   notify `trader` and `scheduler` with revised volumes.

## Handoff map

```
trader → scheduler → ops → (notifications back to trader)
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| pipeline_id | string | Operator identifier |
| gas_day | date | Flow date |
| nomination_id | string | External confirmation ref |
| cutoff_applied | string | Which cutoff rule fired |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| Past cutoff | time_window | Block or urgent exception |
| Partial confirm | operator payload | Update positions provisional flag |

## Time expectations

- Same-day nominations must beat hub-specific cutoffs in `ORG_STATE`.

## Constraint highlights

- `ops.nomination.pipeline_cutoff`, list membership for approved paths where configured.
