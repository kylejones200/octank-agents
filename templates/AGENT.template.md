---
role_id: ""
agent_name: ""
agent_version: "0.1.0"
skill_file: "./SKILL.md"
workflow_files: []  # paths to WORKFLOW.md this agent may join
---

# Agent runtime: [Agent name] — [Role display name]

## Load order

1. If present, read `learning/batch_context.json` for latest batch artifact paths.
2. Read `ORG_STATE` (relevant sections only if implementation supports scoped read).
3. Check what corpus / ONA / task artifacts the operator attached (`learning/AVAILABLE_DATA.md`).
4. Apply this file + linked `SKILL.md` + active `WORKFLOW.md` for current `workflow_type`.
5. Obey `MESSAGE_SCHEMA`; never send outside envelope rules.

## Participating workflows

| workflow_type | Max concurrent | Notes |
|---|---|---|
| | | |

## Trigger → action

| Trigger (message / state / schedule) | Action | Outbound message_type |
|---|---|---|
| | | |

## Escalation rules

- [When to send `escalation` vs `notification`; deadlines; who receives escalation.]

## Output templates

- [Pointers or inline templates for confirmations, reports, etc.]

## Hard boundaries (non-negotiable)

Enumerable list — if any condition matches, do **not** proceed; create `exception` or route per EXCEPTION_QUEUE:

1. ...
2. ...

## Low-confidence behavior

- [What to do when no workflow matches or ambiguity — aligns with EXCEPTION_QUEUE `novel_situation` / `low_confidence`.]

## Tooling / integrations (optional)

- [APIs, inboxes, calendars — boundary layer may own some of this.]
