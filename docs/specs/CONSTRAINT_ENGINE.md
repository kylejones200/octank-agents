# CONSTRAINT_ENGINE.md — Rule Enforcement Spec
## Digital Org Architecture · v0.1

---

## Philosophy

The constraint engine sits between every agent and every action. No message
is delivered, no artifact is produced, and no workflow step advances without
passing through it. It is not advisory — it is a hard gate.

This is what makes the system structurally safer than a human org. In a
human org, a trader *could* route around a compliance check. In this
architecture, they literally cannot — the message bus won't deliver the
message until the constraint engine passes it.

---

## Architecture Position

```
Agent produces output
        ↓
  MESSAGE BUS receives it
        ↓
  CONSTRAINT ENGINE intercepts
        ↓
  ┌─────────────┐    ┌──────────────────┐
  │   PASSED    │    │     FAILED       │
  │             │    │                  │
  │  Deliver    │    │  Block message   │
  │  message    │    │  Create exception│
  │  Log check  │    │  Route to queue  │
  └─────────────┘    └──────────────────┘
```

Every check is logged regardless of pass/fail.

---

## Rule Schema

Each rule in the constraint engine has this structure:

```json
{
  "rule_id":       "policy.position_limit.hard_cap",
  "rule_version":  "2.1",
  "source": {
    "type":        "internal_policy | iso_standard | regulation | encoded_exception",
    "document":    "Trading Risk Policy v3.2",
    "clause":      "Section 4.2 — Position Limits",
    "enacted_at":  "2024-01-15",
    "enacted_by":  "Risk Committee"
  },

  "scope": {
    "applies_to_roles":          ["trader"],
    "applies_to_message_types":  ["request", "response"],
    "applies_to_workflow_types": ["deal_execution", "position_update"],
    "applies_to_artifacts":      ["deal_confirmation", "nomination"]
  },

  "condition": {
    "description": "Human-readable condition being checked",
    "check_type":  "threshold | list_membership | field_presence | cross_reference | time_window | compound",
    "expression":  "payload.structured.volume + org_state.positions[payload.structured.hub].net > org_state.limits[payload.structured.hub]"
  },

  "action_on_fail": {
    "type":           "block | warn | require_approval | log_only",
    "exception_category": "constraint_block",
    "exception_priority": "critical",
    "message_to_agent":   "Deal would exceed position limit for {hub}. Current: {current}, Limit: {limit}, This deal: {volume}.",
    "resolution_options": ["reduce_volume", "request_limit_exception", "cancel_deal"]
  },

  "override": {
    "allowed":       true,
    "allowed_by_roles": ["desk_manager", "risk_officer"],
    "requires_reason": true,
    "logged_as":     "approved_exception"
  },

  "active":    true,
  "test_mode": false
}
```

---

## Rule Types

### Threshold Rules
Numeric values checked against limits.

```json
{
  "rule_id":    "policy.position_limit.hard_cap",
  "condition": {
    "check_type":  "threshold",
    "expression":  "post_trade_position > approved_limit",
    "variables": {
      "post_trade_position": "org_state.positions[hub].net + message.volume",
      "approved_limit":      "org_state.limits[hub]"
    }
  },
  "action_on_fail": { "type": "block" }
}
```

---

### List Membership Rules
Check whether an entity is on an approved/blocked list.

```json
{
  "rule_id":    "policy.counterparty.approved_list",
  "condition": {
    "check_type":  "list_membership",
    "field":       "payload.structured.counterparty_id",
    "list":        "org_state.approved_counterparties",
    "must_be_in":  true
  },
  "action_on_fail": { "type": "block" }
}
```

---

### Field Presence Rules
Ensure required fields / artifacts exist before proceeding.

```json
{
  "rule_id":    "policy.deal.legal_clearance_required",
  "condition": {
    "check_type":  "field_presence",
    "when":        "payload.structured.deal_size > 5000000 OR payload.structured.counterparty_type == 'new'",
    "required_field": "workflow_state.state_data.legal_cleared",
    "required_value":  true
  },
  "action_on_fail": {
    "type": "block",
    "message_to_agent": "Deals over $5M or with new counterparties require Legal clearance before confirmation."
  }
}
```

---

### Cross-Reference Rules
Validate consistency between message content and org state.

```json
{
  "rule_id":    "reg.cftc.position_reporting",
  "condition": {
    "check_type":    "cross_reference",
    "description":   "Any deal over reporting threshold must have a CFTC report artifact attached",
    "when":          "payload.structured.notional > 10000000",
    "must_have_artifact": "cftc_position_report"
  },
  "action_on_fail": {
    "type": "block",
    "message_to_agent": "CFTC reporting required for deals over $10M. Generate report before confirming."
  }
}
```

---

### Time Window Rules
Enforce deadlines and blackout periods.

```json
{
  "rule_id":    "ops.nomination.pipeline_cutoff",
  "condition": {
    "check_type":   "time_window",
    "description":  "Nominations must be sent before pipeline cutoff",
    "field":        "message_type == 'request' AND payload.structured.request_type == 'nomination'",
    "cutoff_time":  "org_state.pipeline_cutoffs[payload.structured.hub]",
    "current_time": "now()"
  },
  "action_on_fail": {
    "type": "warn",
    "message_to_agent": "Pipeline cutoff for {hub} has passed. Nomination may be rejected by operator.",
    "exception_priority": "urgent"
  }
}
```

---

### Compound Rules
Boolean combinations of other rules.

```json
{
  "rule_id":    "policy.large_deal.full_clearance",
  "condition": {
    "check_type":  "compound",
    "operator":    "AND",
    "rules": [
      "policy.counterparty.approved_list",
      "policy.deal.legal_clearance_required",
      "reg.cftc.position_reporting"
    ]
  },
  "applies_when": "payload.structured.notional > 5000000",
  "action_on_fail": { "type": "block" }
}
```

---

## Rule Sources and Priority

Rules come from multiple sources. When rules conflict, priority order:

```
1. Regulation (highest — cannot be overridden by anyone in the org)
2. ISO / External Standard
3. Internal Policy
4. Workflow SOP
5. Encoded Exception (lowest — was a human judgment, not a formal rule)
```

Rule conflicts themselves generate an exception routed to human queue.

---

## Check Log Schema

Every constraint check — pass or fail — is logged immutably:

```json
{
  "check_id":      "chk_<ulid>",
  "checked_at":    "2024-11-14T14:23:01.042Z",
  "message_id":    "msg_<ulid>",
  "workflow_id":   "wf_<ulid>",
  "rule_id":       "policy.position_limit.hard_cap",
  "rule_version":  "2.1",
  "result":        "passed | failed | overridden",
  "values_checked": {
    "post_trade_position": 147000,
    "approved_limit":      145000
  },
  "override": {
    "applied":    false,
    "by_role":    null,
    "reason":     null
  }
}
```

This log is the audit trail. It proves, for any action the system ever took,
exactly which rules were checked, what values were evaluated, and what the outcome was.

---

## Rule Lifecycle

```
Draft → Review → Active → Deprecated
```

| State | Meaning |
|---|---|
| `draft` | Being authored, not yet enforced |
| `test_mode` | Enforced in shadow mode only — logs failures but doesn't block |
| `active` | Fully enforced |
| `deprecated` | No longer enforced, retained for audit history |

New rules from encoded exceptions start in `test_mode` until they've
been validated against 20+ real cases without false positives.

---

## Override Protocol

Some rules allow override by authorized roles. Overrides are:
- Always logged with reason
- Always time-limited (default: single workflow instance)
- Never retroactive
- Reviewed in daily exception analytics

```json
{
  "override_id":   "ovr_<ulid>",
  "rule_id":       "policy.position_limit.hard_cap",
  "approved_by":   "human_risk_officer_id",
  "reason":        "Strategic hedge position — pre-approved by Risk Committee ref RC-2024-089",
  "applies_to_workflow": "wf_<ulid>",
  "expires_at":    "2024-11-14T23:59:59Z"
}
```
