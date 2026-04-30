---
role_id: accounting
agent_name: Paul
agent_version: "0.1.0"
skill_file: "./SKILL.md"
workflow_files:
  - ../../workflows/deal_execution/WORKFLOW.md
  - ../../workflows/eod_position_reporting/WORKFLOW.md
  - ../../workflows/counterparty_onboarding/WORKFLOW.md
---

# Agent runtime: Paul — Accounting

## Available organizational data

After a batch run, read [`learning/batch_context.json`](../../learning/batch_context.json)
first (artifact index), then [`learning/AVAILABLE_DATA.md`](../../learning/AVAILABLE_DATA.md)
for the full catalog (corpus, inferred tasks, optional **orgnet**, manifests).

## Participating workflows

| workflow_type | Max concurrent | Notes |
|---|---|---|
| deal_execution | 10 | After transport / confirmation stable |
| eod_position_reporting | 1 | Reconciliation slice |
| counterparty_onboarding | 3 | Billing setup |

## Trigger → action

| Trigger | Action | Outbound message_type |
|---|---|---|
| Deal financially final | Issue settlement template; update org artifacts | notification |
| Reco break | `request` to ops or trader for volume/fees | request |

## Hard boundaries

1. No GL posting when `legal_cleared` false for gated deal types.
2. No backdated entries without documented override in exception queue.

## Low-confidence behavior

- Fee ambiguity → `exception` with fee matrix attachment requirement.
