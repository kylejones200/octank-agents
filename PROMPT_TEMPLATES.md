# PROMPT_TEMPLATES.md — Bootstrap LLM Prompts
## Digital Org Architecture · v0.1

Use these prompts **offline** against redacted samples (email threads, SOPs,
standard clauses). Outputs feed `roles/*/SKILL.md`, `workflows/*/WORKFLOW.md`,
`roles/*/AGENT.md`, and constraint rule drafts — not live runtime.

---

## Prompt A — Role cluster → SKILL.md

**Input bundle:** (1) list of representative senders or cluster id, (2) 20–50
redacted threads where they are primary actor, (3) optional job description.

**System / instructions:**

You are extracting a **role skill definition** for an organizational digital twin.
Output a single markdown document following the structure in SKILL.template.md.
Use only evidence from the provided corpus; where evidence is thin, mark
`[INFERRED — low evidence]`. Do not invent compliance rules; note "needs
standards pass" where compliance matters.

**User message:**

[Paste structured bundle: threads, metadata, glossary of acronyms from org.]

---

## Prompt B — Thread shape cluster → WORKFLOW.md

**Input bundle:** (1) workflow name hypothesis, (2) 10–20 threaded examples with
timestamps and roles, (3) known failure cases if any.

**System / instructions:**

You are reconstructing one **workflow type** as a directed handoff graph.
Output markdown following WORKFLOW.template.md. Identify steps, roles, typical
`state_data` keys, and failure modes visible in the data. If threads disagree,
document variants as "Branch A / Branch B" rather than merging silently.

---

## Prompt C — SKILL + WORKFLOW + registry row → AGENT.md

**Input bundle:** (1) draft SKILL.md, (2) draft WORKFLOW.md files this role uses,
(3) one row of policy: "never autonomous on X".

**System / instructions:**

Produce **AGENT.md** following AGENT.template.md. Triggers must be enumerable.
Hard boundaries must be a numbered list suitable for exception routing. Include
a short "shadow mode metrics" subsection: what to log to compare later to humans.

---

## Prompt D — Standard clause batch → constraint rules (JSON)

**Input bundle:** (1) numbered clauses with shall/should text, (2) org role names
for mapping, (3) priority hint (regulation vs policy).

**System / instructions:**

Emit a **JSON array** of rule objects compatible with CONSTRAINT_ENGINE.md rule
schema. Each shall → `block` or `require_approval` as appropriate. Each should →
`warn` or `log_only`. Include `source.document` and `source.clause`. If text is
ambiguous, emit a rule with `test_mode: true` and `description` explaining the
ambiguity. Do not duplicate rules; merge identical shalls.

---

## Hygiene (all prompts)

- Strip PII; use placeholders in examples.
- Keep one workflow per Prompt B invocation; one role skill per Prompt A.
- Version outputs in front matter (`*_version`) and store with git.
