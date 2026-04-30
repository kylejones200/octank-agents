# Constraint rule packs (stub)

This directory holds **machine-readable rules** referenced by [`docs/specs/CONSTRAINT_ENGINE.md`](../docs/specs/CONSTRAINT_ENGINE.md).

| Path | Purpose |
|---|---|
| `rules/` | JSON or YAML rule packs (`rule_id`, `applies_to_roles`, checks, severity). Empty until you add packs. |
| `sources/` | Traceability artifacts (pointers to policy PDFs, ISO clauses, ticket ids). |

Optional human-facing checklists can live here as `COMPLIANCE.md`, `DECISION_TREES.md`, etc., per [`docs/AGENT_REGISTRY.md`](../docs/AGENT_REGISTRY.md) file layout.
