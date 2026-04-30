---
workflow_type: regulatory_inquiry
workflow_version: "0.1.0"
---

# Workflow: Regulatory inquiry (desk + compliance)

## Purpose

Route a trading or operations question that has **regulatory or policy interpretation**
risk through compliance and legal before the desk commits language or filings.

## Trigger

- Regulator letter, audit question, internal compliance review, or desk request
  tagged `workflow_type: regulatory_inquiry`.

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| 1–2 | trader | Business facts, positions, what was done in market |
| 2–4 | compliance_officer | Interpretation, control mapping, filing posture |
| 3 | legal | Binding legal view when required |
| 4 | risk_analyst | Quantitative impact, limit and reporting implications |
| 3–5 | corporate_treasury | When inquiry touches funding, reporting, or bank controls |
| 5 | executive_office | Attestation or firm-level decision when required |

## Steps

1. **Intake** — `trader` or `risk_analyst` opens workflow with facts, dates, hubs, and copies of relevant messages.
2. **Compliance assessment** — `compliance_officer` maps to rulesets, identifies gaps, requests evidence.
3. **Legal sign-off branch** — If needed, `legal` provides opinion; else documented waiver path.
4. **Desk response** — Structured reply to regulator or internal stakeholder; artifacts archived.

## Handoff map

```
trader / risk_analyst → compliance_officer ⇄ legal → (back to desk or external)
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| inquiry_id | string | Stable id |
| regulator_ref | string \| null | External reference |
| compliance_position | string | draft / final |
| legal_required | bool | |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| Incomplete facts | compliance checklist | Block external send |
| Conflicting legal vs compliance | dual review | Escalate to executive_office |

## Constraint highlights

- No outbound regulatory language without compliance_officer path complete.
