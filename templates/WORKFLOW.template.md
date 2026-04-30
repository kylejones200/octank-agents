---
workflow_type: ""
workflow_version: "0.1.0"
sources: []  # e.g. thread_cluster:deal_chain, SOP:deal-execution-v2
---

# Workflow: [Human-readable name]

## Purpose

[What business outcome this workflow achieves.]

## Trigger

- [Event or message pattern that starts `workflow_id` in org state.]

## Participants (roles)

| Step range | Role | Responsibility |
|---|---|---|
| | | |

## Steps

1. **[Step name]** — [Owner role]. [Action]. [Outputs / artifacts].
2. ...

## Handoff map

```
[ASCII or short description: who sends request to whom, optional CCs.]
```

## State keys (`workflow.state_data`)

| Key | Type | Meaning |
|---|---|---|
| | | |

## Failure modes

| Failure | Detection | System response |
|---|---|---|
| | | |

## Time expectations

- [SLAs per step; links to pipeline cutoffs in ORG_STATE if relevant.]

## Constraint highlights

- [Which rule families commonly apply — full rules live in constraint engine.]
