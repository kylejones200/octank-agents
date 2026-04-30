---
workflow_type: deal_execution
workflow_version: "0.1.0"
---

# Workflow: Physical deal execution (gas / power)

## Purpose

Move a verbal or RFQ-tied commercial agreement to a transportable, financially
controlled trade: risk-approved, legally cleared when required, nominated, and
ready for settlement.

## Trigger

- Inbound counterparty inquiry marked commercial intent, or trader `request`
  opening `workflow_type: deal_execution` with deal skeleton in `state_data`.

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1–2 | trader | Terms, counterparty entity, volume / tenor |
| 2–3 | risk_analyst | Post-trade limits, reporting flags |
| 3–4 | legal | Conditional: new CP, large notional, non-standard docs |
| 3–4 | compliance_officer | Conditional: regulated product / policy gate |
| 4–5 | corporate_treasury | Conditional: material settlement / facility |
| 4–5 | scheduler | Nomination window and path |
| 5–6 | ops | Physical confirmation / OFO handling |
| 5–6 | it_platform | Conditional: system or feed dependency on critical path |
| 6–7 | accounting | Settlement mapping; desk_manager / executive_office on conflict or capital |

## Steps

1. **Commercial capture** — `trader` records counterparty, hub, price, volume,
   period, and deal_id in `state_data`.
2. **Risk gate** — `risk_analyst` validates utilization and flags; sets
   `risk_acknowledged` and any reporting artifacts required.
3. **Legal / credit branch** — If `legal_cleared` required, `legal` sets clearance
   or blocks; else skip with `legal_cleared: true` system note.
4. **Transport** — `scheduler` requests nominations against pipeline cutoffs;
   `ops` tracks operator responses.
5. **Confirmation** — `trader` sends external confirmation only after
   `risk_acknowledged` and transport path viable (per constraint engine).
6. **Financial close** — `accounting` attaches settlement template; workflow
   completes when artifacts and state keys satisfied.

## Handoff map

```
trader → risk_analyst → (legal) → scheduler ⇄ ops → trader (external) → accounting
                    ↘ desk_manager (only on conflict / authority)
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| deal_id | string | Stable id across bus messages |
| counterparty_id | string | Key into org state counterparties |
| counterparty_approved | bool | Credit + legal lists |
| terms_confirmed | bool | Commercial final |
| risk_acknowledged | bool | Risk sign-off |
| legal_cleared | bool \| null | null = not needed |
| nomination_sent | bool | Scheduler submitted |
| physical_confirmed | bool | Ops / operator ok |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| Limit breach | risk check | Block confirm; open `risk_escalation` if persistent |
| Missed cutoff | time_window rule | Warn / block; exception option set |
| Operator reject | ops response | Hold workflow; trader/legal options |

## Time expectations

- Risk gate: same-day for liquid hubs unless desk policy says otherwise.
- Nominations: before `ORG_STATE.calendar.pipeline_cutoffs[hub]`.

## Constraint highlights

- Counterparty list membership, position limits, reporting thresholds, pipeline
  cutoffs ([`docs/specs/CONSTRAINT_ENGINE.md`](../../docs/specs/CONSTRAINT_ENGINE.md)).
