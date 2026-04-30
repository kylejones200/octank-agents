---
workflow_type: counterparty_onboarding
workflow_version: "0.1.0"
---

# Workflow: Counterparty onboarding (credit / KYC)

## Purpose

Take a prospective trading counterparty from first intent to approved status
in org state, with documentation suitable for audit and deal gating.

## Trigger

- `trader` flags new entity, or inbound inquiry from unknown LEI / DUNS, or
  compliance watchlist hit on screening.

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1 | trader | Commercial rationale, expected volumes, products |
| 2 | legal | KYC / AML pack, master agreement, credit memo |
| 2–3 | compliance_officer | Sanctions / policy alignment with legal |
| 3 | accounting | Billing, tax, and settlement instructions |

## Steps

1. **Commercial intake** — `trader` opens workflow with entity name, jurisdiction,
   expected deal types, and references.
2. **Credit and legal** — `legal` drives checklist (beneficial owners, guarantees,
   ISDAs); may spawn human-only signatures.
3. **Operationalize** — `accounting` adds remittance and invoice preferences;
   when all gates clear, `legal` sets `counterparties[id].approved` via controlled
   write (human-attested in production).

## Handoff map

```
trader → legal ⇄ accounting → (org state update + notify desk)
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| entity_id | string | Internal normalized id |
| kyc_status | string | enum-like lifecycle |
| credit_limit_proposed | number | Pending committee |
| approved | bool | Final gate |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| Watchlist hit | screening | Hard stop; compliance exception |
| Incomplete docs | checklist | Block approval; timed reminders |

## Time expectations

- SLAs vary by entity risk tier; critical path tracked in exception analytics.

## Constraint highlights

- No `deal_execution` confirmation to entity until list membership passes.
