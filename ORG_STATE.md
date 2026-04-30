# ORG_STATE.md — Live Organizational Memory Spec
## Digital Org Architecture · v0.1

---

## Philosophy

A human org carries memory in people's heads, inboxes, and spreadsheets.
When someone leaves, that memory walks out the door. This system externalizes
all organizational memory into a queryable, versioned state object that every
agent reads from and writes to.

Org state is the answer to: *"What does the org know right now?"*

---

## Top-Level Structure

```json
{
  "org_id":       "org_<ulid>",
  "org_name":     "Natural Gas Trading Desk",
  "state_version": 4821,
  "last_updated":  "2024-11-14T14:23:00Z",

  "positions":     {},
  "limits":        {},
  "counterparties": {},
  "workflows":     {},
  "agents":        {},
  "rules":         {},
  "exceptions":    {},
  "calendar":      {}
}
```

---

## Positions

Current open positions by location and commodity. Updated after every confirmed deal.

```json
{
  "positions": {
    "SoCal_Gas": {
      "net":          120000,
      "unit":         "MMBtu/day",
      "long":         170000,
      "short":        50000,
      "last_updated": "2024-11-14T14:00:00Z",
      "updated_by_workflow": "wf_<ulid>"
    },
    "Rockies_Gas": {
      "net":          -80000,
      "unit":         "MMBtu/day",
      "long":         20000,
      "short":        100000,
      "last_updated": "2024-11-14T13:45:00Z",
      "updated_by_workflow": "wf_<ulid>"
    }
  }
}
```

---

## Limits

Approved position limits by location. Changed only by authorized humans or Risk Committee.

```json
{
  "limits": {
    "SoCal_Gas": {
      "long_limit":    145000,
      "short_limit":   145000,
      "warn_at":       0.80,
      "breach_at":     1.00,
      "approved_by":   "risk_committee",
      "approved_at":   "2024-10-01",
      "expires_at":    "2024-12-31"
    }
  }
}
```

---

## Counterparties

Approved trading counterparties with credit status and terms.

```json
{
  "counterparties": {
    "pacific_gas_trading_llc": {
      "approved":          true,
      "credit_limit":      50000000,
      "credit_used":       12000000,
      "legal_entity":      "Pacific Gas Trading LLC",
      "isda_master":       true,
      "approved_at":       "2024-03-15",
      "approved_by":       "legal_credit_team",
      "contact": {
        "name":  "John Smith",
        "email": "j.smith@pgt.com"
      }
    },
    "firstenergy_corp": {
      "approved":   false,
      "status":     "pending_credit_review",
      "applied_at": "2024-11-14",
      "blocker":    "exc_<ulid>"
    }
  }
}
```

---

## Active Workflows

All in-flight workflows and their current state.

```json
{
  "workflows": {
    "wf_<ulid>": {
      "type":         "deal_execution",
      "status":       "in_progress",
      "current_step": 3,
      "started_at":   "2024-11-14T13:00:00Z",
      "deadline":     "2024-11-14T17:00:00Z",
      "blocking_on":  null,
      "state_data": {
        "deal_id":              "deal_20241114_001",
        "counterparty_id":     "pacific_gas_trading_llc",
        "counterparty_approved": true,
        "terms_confirmed":      true,
        "legal_cleared":        null,
        "nomination_sent":      false,
        "risk_acknowledged":    true
      }
    }
  }
}
```

---

## Agent Registry

Which agents exist, their current status and task queue.

```json
{
  "agents": {
    "agent_trader_01": {
      "role":          "trader",
      "status":        "active | busy | offline",
      "current_workflow": "wf_<ulid>",
      "queue_depth":   2,
      "skill_version": "skill_trader_v1.2",
      "last_heartbeat": "2024-11-14T14:22:50Z"
    }
  }
}
```

---

## Pipeline Cutoffs

Operational deadlines that time-window rules reference.

```json
{
  "calendar": {
    "pipeline_cutoffs": {
      "SoCal_Gas":  "14:00",
      "Rockies_Gas": "13:00",
      "PGE_Gas":    "14:30"
    },
    "trading_hours": {
      "start": "06:00",
      "end":   "17:00",
      "timezone": "America/Los_Angeles"
    },
    "holidays": ["2024-11-28", "2024-12-25"],
    "eod_report_time": "17:15"
  }
}
```

---

## State Write Rules

Agents cannot write freely to org state. Writes are controlled:

| State Section | Who can write | How |
|---|---|---|
| `positions` | Any agent, after confirmed deal | Via workflow completion event |
| `limits` | Human only | Via admin interface |
| `counterparties.approved` | Legal agent + human approval | Via exception resolution |
| `workflows` | Message bus (automatic) | After each message delivered |
| `agents` | System (heartbeat) | Automatic |
| `calendar.pipeline_cutoffs` | Human only | Via admin interface |

All writes are versioned. `state_version` increments on every write.
Previous versions are retained for audit replay.

---

## State Read Rules

Any agent can read any part of org state at any time. Reads are:
- Free (no permission required)
- Logged only in aggregate (not per-read)
- Always consistent (agents see the same state within a single workflow step)

---

## State Snapshot

At EOD, a full state snapshot is saved:

```json
{
  "snapshot_id":   "snap_20241114_eod",
  "captured_at":   "2024-11-14T17:30:00Z",
  "trigger":       "scheduled_eod",
  "state":         { ... full org state ... },
  "workflows_completed_today": 47,
  "workflows_in_progress":      3,
  "exceptions_resolved_today": 11,
  "exceptions_pending":         2
}
```

Snapshots are the basis for:
- Daily reports (generated automatically from snapshot diff)
- Audit requests (point-in-time org state reconstruction)
- Simulation (load a historical snapshot and replay)
