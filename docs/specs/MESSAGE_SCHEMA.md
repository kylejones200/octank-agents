# MESSAGE_SCHEMA.md — Inter-Agent Communication Spec
## Digital Org Architecture · v0.1

---

## Philosophy

Agents do not communicate in freeform prose. Every message between agents
is a typed, structured envelope. This makes the system:
- **Auditable** — every communication is machine-readable
- **Constrainable** — the constraint engine can inspect any message
- **Replayable** — any workflow can be reconstructed from logs
- **Debuggable** — failures have a precise location in a message chain

Freeform prose lives only inside `payload.content` — the human-readable
body of the message. Everything around it is structured.

---

## Base Message Envelope

Every message in the system, regardless of type, conforms to this schema.

```json
{
  "message_id":     "msg_<ulid>",
  "workflow_id":    "wf_<ulid>",
  "workflow_type":  "deal_execution | risk_escalation | recurring_report | ...",
  "step":           3,

  "from": {
    "role":         "trader",
    "agent_id":     "agent_trader_01",
    "display_name": "Natural Gas Desk — Trader"
  },

  "to": {
    "role":         "scheduler",
    "agent_id":     "agent_scheduler_01",
    "display_name": "Pipeline Scheduling"
  },

  "cc": [
    { "role": "risk_analyst", "agent_id": "agent_risk_01" }
  ],

  "message_type":   "request | response | notification | escalation | exception",
  "priority":       "routine | urgent | critical",

  "requires_action": true,
  "action_deadline": "2024-11-14T17:00:00Z",

  "in_reply_to":    "msg_<ulid>",

  "payload": {
    "summary":      "One sentence machine-readable description of this message",
    "content":      "Human-readable body. Free prose or structured text.",
    "structured":   {}
  },

  "artifacts": [],

  "constraint_check": {
    "status":       "passed | failed | bypassed",
    "checked_at":   "2024-11-14T14:23:01Z",
    "rules_checked": ["policy.position_limit", "reg.mifid2.reporting"],
    "failures":     []
  },

  "metadata": {
    "created_at":   "2024-11-14T14:23:00Z",
    "schema_version": "0.1",
    "source":       "agent | human | system"
  }
}
```

---

## Message Types

### `request`
An agent asks another agent to do something. Requires a response.

```json
{
  "message_type": "request",
  "requires_action": true,
  "payload": {
    "summary": "Nomination request for SoCal Feb deal",
    "content": "Please nominate 50,000 MMBtu/day at SoCal Citygate for February. Counterparty is confirmed.",
    "structured": {
      "request_type":  "nomination",
      "deal_id":       "deal_20241114_001",
      "volume":        50000,
      "unit":          "MMBtu/day",
      "hub":           "SoCal Citygate",
      "period_start":  "2024-02-01",
      "period_end":    "2024-02-29"
    }
  }
}
```

---

### `response`
An agent replies to a request. Closes the request loop.

```json
{
  "message_type": "response",
  "in_reply_to":  "msg_<request_id>",
  "requires_action": false,
  "payload": {
    "summary": "Nomination confirmed by pipeline operator",
    "content": "Nominated and confirmed. Pipeline confirmation number: SCC-2024-0089.",
    "structured": {
      "response_status":     "confirmed | rejected | partial | pending",
      "confirmation_number": "SCC-2024-0089",
      "confirmed_volume":    50000,
      "confirmed_by":        "SoCal Gas Transmission"
    }
  }
}
```

---

### `notification`
An agent informs another agent of something. No response required.

```json
{
  "message_type": "notification",
  "requires_action": false,
  "payload": {
    "summary": "EOD position update — all desks within limits",
    "content": "End of day positions as of 17:00 PST. All desks within approved limits.",
    "structured": {
      "notification_type": "eod_report",
      "report_date":       "2024-11-14",
      "positions": [
        { "hub": "SoCal", "net": 120000, "limit": 145000, "utilization": 0.83 },
        { "hub": "Rockies", "net": -80000, "limit": 125000, "utilization": 0.64 }
      ],
      "breach_count": 0
    }
  }
}
```

---

### `escalation`
An agent cannot proceed and routes upward. Always `requires_action: true`.

```json
{
  "message_type": "escalation",
  "priority":     "critical",
  "requires_action": true,
  "action_deadline": "2024-11-14T16:00:00Z",
  "payload": {
    "summary": "Position limit breach — Rockies desk — unresolved after 2 hours",
    "content": "Trader acknowledged breach at 13:45 but has not reduced position. Current utilization 108%. Requires senior management instruction.",
    "structured": {
      "escalation_reason":  "limit_breach_unresolved",
      "original_message_id": "msg_<ulid>",
      "time_since_trigger":  "PT2H15M",
      "current_state": {
        "hub":         "Rockies",
        "position":    135000,
        "limit":       125000,
        "utilization": 1.08
      },
      "actions_taken": [
        { "at": "2024-11-14T13:45Z", "action": "Warning sent to trader" },
        { "at": "2024-11-14T14:30Z", "action": "Trader acknowledged, no action" }
      ],
      "options": [
        "Approve temporary limit exception",
        "Instruct immediate position reduction",
        "Suspend trading on Rockies desk"
      ]
    }
  }
}
```

---

### `exception`
A message the constraint engine blocked. Routes to human exception queue.

```json
{
  "message_type": "exception",
  "priority":     "critical",
  "requires_action": true,
  "payload": {
    "summary": "Constraint engine blocked deal — new counterparty without credit approval",
    "content": "Agent attempted to send deal confirmation to FirstEnergy Corp. Counterparty not on approved list. Action blocked pending credit review.",
    "structured": {
      "exception_type":     "constraint_violation",
      "blocked_message_id": "msg_<ulid>",
      "violated_rules": [
        {
          "rule_id":    "policy.counterparty.approved_list",
          "rule_text":  "Deals may only be confirmed with counterparties on the approved list",
          "source":     "internal_policy_v3.2"
        }
      ],
      "resolution_options": [
        "Approve counterparty (routes to Legal for credit review)",
        "Reject deal",
        "Defer pending review"
      ]
    }
  }
}
```

---

## Artifact Schema

Artifacts are outputs attached to messages — reports, confirmations, data files.

```json
{
  "artifact_id":   "art_<ulid>",
  "artifact_type": "deal_confirmation | risk_report | nomination | invoice | contract | audit_record",
  "produced_by":   "agent_trader_01",
  "produced_at":   "2024-11-14T14:23:00Z",
  "workflow_id":   "wf_<ulid>",
  "name":          "Deal Confirmation — SoCal Feb — 20241114",
  "format":        "structured_json | pdf | csv | text",
  "content":       {},
  "retention_policy": {
    "retain_until": "2031-11-14",
    "reason":       "ISO 9001 s7.5 + CFTC 7-year requirement"
  }
}
```

---

## Workflow State Object

The live state of any in-flight workflow. Updated after every message.

```json
{
  "workflow_id":    "wf_<ulid>",
  "workflow_type":  "deal_execution",
  "status":         "in_progress | completed | blocked | failed | escalated",
  "current_step":   3,
  "total_steps":    6,

  "started_at":     "2024-11-14T13:00:00Z",
  "last_updated":   "2024-11-14T14:23:00Z",
  "deadline":       "2024-11-14T17:00:00Z",

  "participants": [
    { "role": "trader",     "agent_id": "agent_trader_01",    "status": "active" },
    { "role": "scheduler",  "agent_id": "agent_scheduler_01", "status": "waiting" },
    { "role": "risk",       "agent_id": "agent_risk_01",      "status": "notified" }
  ],

  "message_log": ["msg_001", "msg_002", "msg_003"],
  "artifact_log": ["art_001"],

  "blocking_on": null,
  "escalated_to": null,

  "state_data": {
    "deal_id":            "deal_20241114_001",
    "counterparty":       "Pacific Gas Trading LLC",
    "counterparty_approved": true,
    "terms_confirmed":    true,
    "legal_cleared":      null,
    "nomination_sent":    false,
    "risk_acknowledged":  true
  }
}
```

---

## Message Flow Rules

These are enforced by the message bus, not by individual agents:

1. Every `request` must receive a `response` or `escalation` within its `action_deadline`
2. A message that fails constraint check becomes an `exception` — the original is never delivered
3. Every message is appended to the workflow's `message_log` before delivery
4. Agents cannot modify sent messages — the log is append-only
5. `cc` recipients receive a read-only copy — they cannot respond on that thread
6. An agent can only send messages for workflows it is a participant in
7. `critical` priority messages interrupt the agent's current task queue
