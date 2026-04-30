# Data available to desk agents

Agents should assume these sources **may** be present in the environment. When
making recommendations, **prefer citing paths or artifact ids** over inventing
network metrics or email quotes.

## Batch analysis, then agent read (recommended)

1. **Offline** — Run heavy work in batch (corpus scan, optional orgnet, exports).
   Use **`./scripts/run_batch_analysis.sh`** (optional: `BATCH_MAX_ROWS=50000`
   for a shorter dev run; omit for full parquet scan).
2. **Index** — The script writes **`learning/batch_context.json`**, a small
   manifest listing which artifact paths exist right now (`inferred_tasks`,
   `last_run_manifest`, optional `orgnet_summary`).
3. **Online / agent session** — Load **`learning/batch_context.json` first**,
   then **`learning/AVAILABLE_DATA.md`**, then only the non-null files under
   `artifacts` (excerpts or full files, per your context budget). Agents **do
   not** re-run orgnet or full-corpus inference inside each turn unless you
   explicitly give them a tool that does so.

See also `learning/batch_context.example.json` for the JSON shape.

## 1. Email corpus (primary behavioral signal)

- **Parquet table:** configured in `enron/corpus_config.json` (typically
  `emails.parquet` with `file` + `message` columns).
- **Maildir tree:** same config’s `maildir_root` — on-disk messages for
  resolvable paths and audits.

Use for: thread evidence, task inference, vocabulary, escalation patterns.

## 2. Inferred tasks (corpus → registry workflows)

- **JSONL:** `enron/inferred_tasks.jsonl` (or smoke output `enron/_smoke_tasks.jsonl`)
  produced by `scripts/enron_infer_tasks.py`.
- Each line links threads to `workflow_type`, `role_id`, and `agent_bindings`
  aligned with `registry/registry.json`.

Use for: which workflow to open, suggested steps, participant lists.

## 3. Organizational network analysis (ONA) — orgnet

- **Library:** [orgnet](https://pypi.org/project/orgnet/) — graphs, centralities,
  communities, temporal and NLP-style signals over digital exhaust (including
  optional **email** extras per package metadata).
- **Artifacts:** not committed by default. When a batch job has run, expect
  summaries or reports under a path your operator documents (e.g.
  `learning/orgnet_output/` or your orgnet `config.yaml` output path).

Use for: who collaborates with whom, bottlenecks, peer suggestions for
`typical_peers` or escalation design — **only** when those artifacts exist and
you reference them explicitly.

## 4. Lineage / attestation

- **`learning/last_run_manifest.json`** — which data and agent definitions were
  used for a learning or synthesis run (`scripts/emit_learning_manifest.py`).
- **`learning/ATTESTATION.md`** — how to describe data + agents + skills in
  product or compliance language.

## 5. Live runtime state (when executing, not training)

- **[`docs/specs/ORG_STATE.md`](../docs/specs/ORG_STATE.md)** — positions, limits, workflows in flight (simulation or
  production). Distinct from historical corpus and ONA snapshots.

---

**Rule of thumb:** Historical email + ONA **describe the past org**; org state
and the message bus **describe the now**. Do not confuse them in outputs.
