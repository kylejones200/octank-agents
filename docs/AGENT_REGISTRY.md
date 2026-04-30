# AGENT_REGISTRY.md — Who Exists and What They Load
## Digital Org Architecture · v0.2

---

## Purpose

This document is the **human-readable catalog** of roles in the twin. The
**canonical machine source** is [`registry/registry.json`](../registry/registry.json) — validated on every
commit if you run `scripts/install-git-hooks.sh` or use the `pre-commit` config
in the repo root. Spec index: [`docs/README.md`](README.md).

Runtime systems should read `registry.json`; humans can start here, then open
linked `SKILL.md` / `AGENT.md` / `WORKFLOW.md` files.

Each row is one **logical role**. Multiple `agent_id` instances of the same role
are allowed (e.g. two traders on different desks).

---

## Registry Schema (per role)

| Field | Meaning |
|---|---|
| `role_id` | Stable slug for message `from.role` / `to.role` |
| `agent_name` | Human display name (canonical in `registry.json`); use as `display_name` in envelopes |
| `agent_id` pattern | e.g. `agent_trader_{desk}` |
| `skill_file` | Path to `SKILL.md` — identity, inputs, outputs |
| `workflow_files` | Paths to `WORKFLOW.md` types this role may participate in |
| `agent_file` | Path to `AGENT.md` — triggers, boundaries, templates |
| `avatar_path` | Optional repo-relative image (e.g. `assets/avatars/<role_id>.png`) for UI or manifests |
| `constraint_scope` | Subset of rule scopes that apply (see CONSTRAINT_ENGINE) |
| `typical_peers` | Roles on the message bus this role most often addresses |
| `hard_boundaries` | What must always route to exception queue (summary) |

---

## Example registry (energy trading desk)

| role_id (agent_name) | skill_file | agent_file | typical_peers | hard_boundaries |
|---|---|---|---|---|
| `trader` (Morgan) | `roles/trader/SKILL.md` | `roles/trader/AGENT.md` | scheduler, risk_analyst, legal | New counterparty without credit; deal over signing authority |
| `risk_analyst` (Claire) | `roles/risk_analyst/SKILL.md` | `roles/risk_analyst/AGENT.md` | trader, desk_manager | Waiving regulatory report requirement |
| `scheduler` (Henry) | `roles/scheduler/SKILL.md` | `roles/scheduler/AGENT.md` | trader, ops | Nomination after cutoff without documented override |
| `legal` (Anne) | `roles/legal/SKILL.md` | `roles/legal/AGENT.md` | trader, accounting | Binding legal commitment without human signatory |
| `accounting` (Paul) | `roles/accounting/SKILL.md` | `roles/accounting/AGENT.md` | trader, ops | Posting outside reconciliation window |
| `ops` (Sam) | `roles/ops/SKILL.md` | `roles/ops/AGENT.md` | scheduler, accounting | Physical ops exception without supervisor |
| `desk_manager` (Diane) | `roles/desk_manager/SKILL.md` | `roles/desk_manager/AGENT.md` | trader, risk_analyst | Permanent limit changes (may need committee) |

## Corporate / platform agents (beyond the desk line)

| role_id (agent_name) | skill_file | agent_file | typical_peers | hard_boundaries |
|---|---|---|---|---|
| `compliance_officer` (Ruth) | `roles/compliance_officer/SKILL.md` | `roles/compliance_officer/AGENT.md` | legal, executive_office, trader | Unsourced regulatory claims; overriding counsel |
| `corporate_treasury` (Victor) | `roles/corporate_treasury/SKILL.md` | `roles/corporate_treasury/AGENT.md` | accounting, trader, legal | Wire instructions without dual-control policy |
| `it_platform` (Nina) | `roles/it_platform/SKILL.md` | `roles/it_platform/AGENT.md` | ops, risk_analyst, scheduler | Production change outside approved window |
| `executive_office` (Grace) | `roles/executive_office/SKILL.md` | `roles/executive_office/AGENT.md` | desk_manager, compliance_officer, legal | Legal filings without full chain |

New org-wide workflows: `regulatory_inquiry`, `systems_change_request` (see `workflows/`).

Workflow types each role may touch are listed in that role’s `AGENT.md` under
**Participating workflows**; the bus enforces `MESSAGE_SCHEMA` rule 6 (participant only).

---

## File layout convention

```
roles/
  <role_id>/
    SKILL.md      # what the role is
    AGENT.md      # how it runs (triggers, boundaries, prompts)
workflows/
  <workflow_type>/
    WORKFLOW.md   # steps, handoffs, failure modes
constraints/
  README.md       # layout + how rule packs map to CONSTRAINT_ENGINE
  rules/          # JSON or YAML rule packs (see docs/specs/CONSTRAINT_ENGINE.md)
  sources/        # traceability to ISO / policy PDFs
```

Standards-derived artifacts (optional per deployment):

```
constraints/
  COMPLIANCE.md   # human-readable checklist derived from clauses
  DECISION_TREES.md
```

See [`constraints/README.md`](../constraints/README.md) for the live stub layout.

---

## Relationship to other specs

| Spec | How registry uses it |
|---|---|
| [`docs/specs/MESSAGE_SCHEMA.md`](specs/MESSAGE_SCHEMA.md) | `role_id` must match envelope `from.role` / `to.role` |
| [`docs/specs/ORG_STATE.md`](specs/ORG_STATE.md) | `agents` map keys = `agent_id`; `skill_version` points at skill file version |
| [`docs/specs/CONSTRAINT_ENGINE.md`](specs/CONSTRAINT_ENGINE.md) | `constraint_scope` filters which `rule_id`s run for this role’s messages |
| [`docs/specs/EXCEPTION_QUEUE.md`](specs/EXCEPTION_QUEUE.md) | `hard_boundaries` should align with categories that create exceptions |

---

## Versioning

- Bump `skill_file` / `agent_file` **version** in front matter when behavior changes.
- `ORG_STATE` records `skill_version` per agent for replay and audit.
- Breaking message `payload.structured` shape changes require `schema_version` bump
  in [`docs/specs/MESSAGE_SCHEMA.md`](specs/MESSAGE_SCHEMA.md) and coordinated registry update.

---

## Next steps for a real org

1. Edit **`registry/registry.json`** when adding a role or workflow, then run
   `python3 scripts/validate_registry.py`. Optional headshots: place PNGs under
   `assets/avatars/` and set `avatar_path`, or regenerate from a sprite sheet via
   `python3 scripts/split_avatar_sheet.py --input <combined.png>`.
2. Keep `SKILL.md` / `AGENT.md` / `WORKFLOW.md` front matter `role_id` /
   `workflow_type` aligned with the registry (the validator enforces this).
3. Add rules to the constraint engine with explicit `applies_to_roles`.
4. Run shadow mode ([`docs/architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md) bootstrap Phase 3) before any autonomous execution.
