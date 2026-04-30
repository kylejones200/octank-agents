# EXCEPTION_QUEUE.md — Human Interface Spec
## Digital Org Architecture · v0.1

---

## Philosophy

The exception queue is the **only** regular touchpoint between humans and
the running org. It is not a help desk or a chat interface — it is a
structured decision inbox where humans resolve specific, bounded questions
that the system has explicitly determined it cannot answer alone.

A well-designed exception queue gets shorter over time. Every resolved
exception is a candidate for encoding as a new rule.

---

## What Belongs in the Exception Queue

The system routes to the exception queue when:

| Trigger | Category | Example |
|---|---|---|
| Constraint violation | `constraint_block` | Deal with unapproved counterparty |
| No matching workflow | `novel_situation` | Request type never seen before |
| Agent confidence below threshold | `low_confidence` | Ambiguous input, multiple plausible workflows |
| Hard authority boundary | `authority_limit` | Contract requires legal signature |
| Escalation unresolved | `escalation_timeout` | Trader didn't respond to breach notice |
| Conflicting rules | `rule_conflict` | Two policies contradict each other |
| Workflow deadline missed | `deadline_breach` | Nomination not sent before pipeline cutoff |
| Human explicitly requested | `human_requested` | Agent flagged "requires human judgment" |

---

## Exception Record Schema

```json
{
  "exception_id":    "exc_<ulid>",
  "created_at":      "2024-11-14T14:23:00Z",
  "priority":        "routine | urgent | critical",
  "sla_deadline":    "2024-11-14T16:00:00Z",

  "category":        "constraint_block | novel_situation | low_confidence | authority_limit | escalation_timeout | rule_conflict | deadline_breach | human_requested",

  "title":           "One-line human-readable description",
  "description":     "What happened, why the system couldn't resolve it, what's at stake",

  "context": {
    "workflow_id":   "wf_<ulid>",
    "workflow_type": "deal_execution",
    "workflow_step": 3,
    "blocked_message_id": "msg_<ulid>",
    "agents_involved": ["agent_trader_01", "agent_risk_01"]
  },

  "evidence": {
    "message_thread": ["msg_001", "msg_002", "msg_003"],
    "relevant_artifacts": ["art_001"],
    "constraint_failures": [
      {
        "rule_id":   "policy.counterparty.approved_list",
        "rule_text": "Deals may only be confirmed with counterparties on the approved list",
        "source":    "internal_policy_v3.2"
      }
    ]
  },

  "options": [
    {
      "option_id":   "opt_1",
      "label":       "Approve this counterparty",
      "description": "Routes to Legal for credit review. Estimated 2–4 hours.",
      "consequence": "Workflow resumes after Legal clears counterparty",
      "risk":        "medium"
    },
    {
      "option_id":   "opt_2",
      "label":       "Reject this deal",
      "description": "Sends rejection to trader. Workflow closes.",
      "consequence": "Deal is cancelled. Counterparty is notified.",
      "risk":        "low"
    },
    {
      "option_id":   "opt_3",
      "label":       "Defer 24 hours",
      "description": "Holds the workflow. No action taken until tomorrow.",
      "consequence": "Nomination deadline may be missed.",
      "risk":        "high"
    }
  ],

  "resolution": null,

  "learning": {
    "encode_as_rule": null,
    "rule_draft":     null,
    "reviewed_by":    null
  },

  "assigned_to":  "human_owner_id | unassigned",
  "status":       "open | in_review | resolved | deferred"
}
```

---

## Resolution Schema

When a human resolves an exception:

```json
{
  "resolved_at":     "2024-11-14T15:10:00Z",
  "resolved_by":     "human_owner_id",
  "chosen_option":   "opt_1",
  "notes":           "FirstEnergy is a known counterparty from our Houston desk. Legal to confirm.",
  "system_action":   "resume_workflow | cancel_workflow | modify_and_resume | defer",
  "resume_from_step": 3
}
```

---

## Learning Loop

After every resolved exception, the system prompts:

```
This exception was resolved as: [chosen option]
[X] Encode this resolution as a new rule so the system handles it automatically next time
[ ] This was a one-off — do not encode

If encoding: draft rule text:
"When [condition], automatically [action] without human review."

Rule scope:
[ ] This workflow type only
[ ] This agent only
[ ] All workflows / system-wide

Confidence required before auto-applying:
[ ] Apply immediately
[ ] Apply after 3 identical cases
[ ] Apply after human review of 5 cases
```

This is how the exception queue shrinks over time. Every resolved exception
is either a one-off or a new rule.

---

## Exception Queue Dashboard (Human Interface)

What the human operator sees:

```
┌─────────────────────────────────────────────────────────────────┐
│  EXCEPTION QUEUE                        11 open · 2 critical    │
├────────────┬───────────────────────────────┬────────┬───────────┤
│  Priority  │  Title                        │  Age   │  SLA      │
├────────────┼───────────────────────────────┼────────┼───────────┤
│  CRITICAL  │  Breach unresolved — Rockies  │  2h15m │  45m left │
│  CRITICAL  │  Pipeline cutoff in 30min     │  4m    │  30m left │
│  urgent    │  New counterparty — FirstEnrg │  1h02m │  3h left  │
│  urgent    │  Rule conflict — ISO vs policy│  3h    │  5h left  │
│  routine   │  Novel request type — vendor  │  6h    │  tomorrow │
│  ...       │  ...                          │  ...   │  ...      │
└────────────┴───────────────────────────────┴────────┴───────────┘
```

Each row expands to show: context, evidence thread, options with consequences.
Human picks an option. System resumes.

---

## SLA Rules

| Priority | Max time to resolve | If breached |
|---|---|---|
| critical | 1 hour | Escalate to org owner; workflow suspended |
| urgent | 4 hours | Notify backup human; flag in daily report |
| routine | 24 hours | Batch for daily review session |

---

## Exception Analytics

Track over time:
- **Volume by category** — which category generates the most exceptions?
- **Volume by workflow type** — which workflow breaks most often?
- **Resolution time by priority** — are SLAs being met?
- **Rule encoding rate** — what % of exceptions become rules?
- **Recurrence rate** — same exception appearing repeatedly = rule needed urgently
- **Queue trend** — is the queue growing or shrinking? (should shrink over time)

A growing queue = the org is encountering more novelty than it can encode.
A shrinking queue = the system is learning faster than new edge cases arrive.
