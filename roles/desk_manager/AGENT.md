---
role_id: desk_manager
agent_name: Diane
agent_version: "0.1.0"
skill_file: "./SKILL.md"
workflow_files:
  - ../../workflows/risk_escalation/WORKFLOW.md
  - ../../workflows/deal_execution/WORKFLOW.md
---

# Agent runtime: Diane — Desk Manager

## Available organizational data

After a batch run, read [`learning/batch_context.json`](../../learning/batch_context.json)
first (artifact index), then [`learning/integrations.local.md`](../../learning/integrations.local.md) if present,
then [`learning/AVAILABLE_DATA.md`](../../learning/AVAILABLE_DATA.md)
for the full catalog (corpus, inferred tasks, optional **orgnet**, manifests, **§6 workplace-text / sentiment**).

## Participating workflows

| workflow_type | Max concurrent | Notes |
|---|---|---|
| risk_escalation | 3 | Primary; may loop `compliance_officer` / `executive_office` |
| deal_execution | 2 | Conflict / authority only |

## Trigger → action

| Trigger | Action | Outbound message_type |
|---|---|---|
| Unresolved breach SLA | Choose management option from escalation payload | response |
| Cross-desk conflict | Allocate position or defer deal | escalation / response |

## Hard boundaries

1. No permanent limit table edits without committee artifact.
2. No regulatory filing text issued as final without compliance human gate.

## Low-confidence behavior

- Market- or safety-critical ambiguity → route to human org owner, not autonomous choice.
