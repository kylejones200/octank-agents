# ARCHITECTURE.md — Digital Org System Design
## v0.2 (see `registry/registry.json` → `registry_version` for agent pack version)

---

## What This Is

A runtime architecture for an organization staffed entirely by AI agents.
Humans exist only at two boundaries: **policy** (setting limits and rules)
and **exception** (resolving what the system cannot handle alone).

Everything in between — receiving inputs, executing workflows, enforcing
compliance, producing artifacts, communicating with the outside world —
is handled by agents operating against a shared org state.

---

## System Layers

```
┌──────────────────────────────────────────────────────────────────────┐
│  EXTERNAL WORLD                                                       │
│  Customers · Counterparties · Regulators · Markets · Vendors          │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ inbound / outbound
┌───────────────────────────▼──────────────────────────────────────────┐
│  BOUNDARY LAYER                                                       │
│  · Parses inbound communications into typed messages                  │
│  · Routes to correct workflow / agent                                 │
│  · Signs / sends outbound on behalf of org                            │
│  · Surfaces human exception queue                                     │
│  · Human override console                                             │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  AGENT WORKFORCE                                                      │
│                                                                       │
│   Trader ◄──────────────────────────────────► Risk Analyst            │
│     │                                              │                  │
│     ▼                                              ▼                  │
│   Scheduler ◄──────────────────────────────► Legal / Compliance       │
│     │                                              │                  │
│     ▼                                              ▼                  │
│   Accounting ◄─────────────────────────────► Operations               │
│                                                                       │
│  Each agent: SKILL.md + WORKFLOW.md + AGENT.md + org state access     │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ all messages pass through
┌───────────────────────────▼──────────────────────────────────────────┐
│  MESSAGE BUS                                                          │
│  · Receives all agent outputs                                         │
│  · Routes to constraint engine before delivery                        │
│  · Logs every message to audit trail                                  │
│  · Enforces message schema                                            │
│  · Manages workflow state transitions                                 │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  CONSTRAINT ENGINE                                                    │
│  · Evaluates every message against all applicable rules               │
│  · Sources: internal policy · ISO standards · regulations             │
│  · Pass → deliver. Fail → block + exception.                          │
│  · All checks logged immutably                                        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────────┐
│  ORG STATE                                                            │
│  · Positions · Limits · Counterparties · Active workflows             │
│  · Agent registry · Calendar · Snapshots                              │
│  · Single source of truth for all agents                              │
│  · Versioned, append-only history                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Spec Index

| Spec | File | What it defines |
|---|---|---|
| Message Schema | [`docs/specs/MESSAGE_SCHEMA.md`](../specs/MESSAGE_SCHEMA.md) | Structure of all inter-agent communication |
| Exception Queue | [`docs/specs/EXCEPTION_QUEUE.md`](../specs/EXCEPTION_QUEUE.md) | Human touchpoint — what routes there, how it's resolved |
| Constraint Engine | [`docs/specs/CONSTRAINT_ENGINE.md`](../specs/CONSTRAINT_ENGINE.md) | Rule types, evaluation, override, audit log |
| Org State | [`docs/specs/ORG_STATE.md`](../specs/ORG_STATE.md) | Live memory — positions, limits, counterparties, workflows |
| Agent Registry | [`docs/AGENT_REGISTRY.md`](../AGENT_REGISTRY.md) | Human-readable catalog; canonical JSON is `registry/registry.json` |
| Bootstrap Prompts | [`docs/specs/PROMPT_TEMPLATES.md`](../specs/PROMPT_TEMPLATES.md) | LLM prompts to generate SKILL / WORKFLOW / AGENT / rules from data |
| Agent Definition | `AGENT.md` (per role) | Trigger→action map, escalation rules, output formats |
| Skill Definition | `SKILL.md` (per role) | Role identity, inputs, outputs, decision patterns |
| Workflow Definition | `WORKFLOW.md` (per type) | Step-by-step process, handoffs, failure modes |
| File templates | `templates/*.template.md` | Empty structures for new roles and workflows |
| Data catalog | `learning/AVAILABLE_DATA.md` | What agents may assume exists (corpus, tasks, orgnet ONA, manifests) |
| Batch → read | `scripts/run_batch_analysis.sh` | Offline corpus + manifest; writes `learning/batch_context.json` for agents |

---

## Data Flows

### Inbound (external → org)
```
External message arrives
  → Boundary layer parses → typed message envelope
  → Workflow classifier: which workflow type does this trigger?
  → Workflow instance created in org state
  → First agent in workflow receives message
  → Workflow executes step by step via message bus
  → Final output sent via boundary layer to external world
```

### Agent → Agent (internal)
```
Agent produces output (message or artifact)
  → Message bus receives
  → Constraint engine evaluates
  → Pass: logged + delivered to recipient agent
  → Fail: blocked, exception created, routed to human queue
  → Recipient agent processes, produces next output
  → Repeat until workflow complete
```

### Exception (human touchpoint)
```
Exception created (constraint fail / novel situation / escalation timeout)
  → Routed to human exception queue with priority
  → Human reviews evidence, selects resolution option
  → System applies resolution (resume / cancel / modify)
  → Resolution logged
  → Learning loop: encode as rule? (→ constraint engine)
```

---

## What Makes This Different From a Task Bot System

| Task Bot System | This Architecture |
|---|---|
| One bot, one job | Multiple agents with defined relationships |
| Stateless | Persistent org state shared across all agents |
| Ad hoc rules | Formal constraint engine with versioned rules |
| No audit trail | Immutable log of every action and check |
| Human in the loop | Human at the boundary only |
| Can't learn | Exception → rule encoding loop |
| Can't be inspected | Full replay from message + state log |
| Breaks silently | Explicit failure modes with exception routing |

---

## Bootstrap Path

### Phase 0 — Build the spine
Message schema · Org state schema · Message bus · Constraint engine (empty)
Result: A working plumbing system with no agents yet

### Phase 1 — Seed from Enron corpus
Run Stages 1–3 of the extraction pipeline
Result: SKILL.md + WORKFLOW.md + AGENT.md for ~8 roles + ~10 workflows

### Phase 2 — Seed constraints from standards
Extract rules from ISO 9001 / relevant regulations
Result: Constraint engine with ~50 rules from authoritative sources

### Phase 3 — Shadow mode
Agents run alongside real operations
All agent decisions logged but not executed
Human executes, compares to agent recommendation
Result: Calibration data, confidence baselines

### Phase 4 — Narrow autonomy
Agents execute on routine cases with high confidence
Everything else → exception queue
Result: First real autonomous org behavior

### Phase 5 — Expanding autonomy
Exception queue shrinks as rules are encoded
Authority boundary moves outward
Result: Org runs with minimal human intervention on known patterns

---

## What Humans Do in the Mature System

| Role | Frequency | What they do |
|---|---|---|
| Policy Owner | Monthly | Set/change limits, approve new rule additions |
| Exception Reviewer | Daily | Clear exception queue, encode resolutions as rules |
| Audit Reviewer | Weekly | Review constraint check logs, verify compliance |
| Architect | Quarterly | Add new agent roles, new workflow types, new constraint sources |

The org runs continuously. Humans check in, not the reverse.
