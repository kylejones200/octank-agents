# From Enron corpus to agent-performable tasks

## Goal

Turn historical email threads into **structured tasks** your registry agents can
execute: each task names a `workflow_type`, a primary `role_id`, evidence from
the thread, and suggested steps aligned with `workflows/*/WORKFLOW.md`.

The corpus does not know about Morgan or Claire — it knows mailboxes and
language. You bridge that with **hints** (`enron_to_registry_hints.json`) and
optional **mailbox → role** maps you build from org charts or sampling.

## Pipeline (offline)

1. **Ingest** — Maildir (common Enron distribution) or mbox; normalize headers.
2. **Thread** — Group by `References` root / `In-Reply-To` chain; keep
   `Message-ID`, `Date`, `From`, `To`, `Cc`, `Subject`, body snippet.
3. **Score** — Match subjects + bodies against keyword sets → candidate
   `workflow_type` with confidence (weighted keyword hits / thread length).
4. **Assign role** — `email_localpart_to_role` wins when present; else rank
   senders by volume in thread + `body_keyword_to_role`.
5. **Emit** — JSONL lines: one record per thread (or per sub-thread if you split
   later). Store paths to raw messages for audit, not full bodies in git.

## Quality levers

- **Calibration** — Hand-label 50 threads → tune keywords and mailbox map.
- **Min thread size** — `--min-messages 2` reduces noise; raise for “real” workflows.
- **Shadow mode** — Agents propose next message; you compare to archived human mail.

## Your corpus (`~/Documents/email`)

This desk repo is wired to your parquet + maildir layout via `enron/corpus_config.json`:

- `emails.parquet` — columns `file` (relative to `maildir/`) and `message` (full RFC822)
- `maildir/` — on-disk files for resolvable paths in task output

Install the optional reader once:

```bash
pip install -r requirements-corpus.txt
```

End-to-end smoke (registry → 25k-row task sample → manifest):

```bash
./scripts/smoke_pipeline.sh
```

Full **batch → agent-read** pipeline (writes `enron/inferred_tasks.jsonl`,
`learning/last_run_manifest.json`, `learning/batch_context.json`):

```bash
./scripts/run_batch_analysis.sh
# Dev-sized run:
# BATCH_MAX_ROWS=50000 BATCH_MAX_THREADS=2000 ./scripts/run_batch_analysis.sh
```

## Run

```bash
# Default paths from enron/corpus_config.json (edit if you move the corpus)
python3 scripts/enron_infer_tasks.py --corpus-config enron/corpus_config.json --output enron/inferred_tasks.jsonl

# Quick test (first N rows only)
python3 scripts/enron_infer_tasks.py --corpus-config enron/corpus_config.json --max-rows 50000 --max-threads 500 --output enron/inferred_tasks.jsonl

# Full pass (275k+ rows; may take several minutes, high memory for thread index)
python3 scripts/enron_infer_tasks.py --corpus-config enron/corpus_config.json --output enron/inferred_tasks.jsonl

# Prefer multi-message “threads” when References are sparse (PST-style exports)
python3 scripts/enron_infer_tasks.py --corpus-config enron/corpus_config.json --bucket-mailbox-subject-day --min-messages 2 --output enron/inferred_tasks.jsonl

# Raw Maildir only (cur/new style trees)
python3 scripts/enron_infer_tasks.py --maildir /path/to/maildir --output enron/inferred_tasks.jsonl

python3 scripts/enron_infer_tasks.py --demo   # no corpus; shows output shape
```

Default `--min-messages` is **1** so each email can become an atomic task when
Message-IDs do not chain. Raise to `2` for strict RFC threading only.

Edit `enron/enron_to_registry_hints.json` as you learn which mailboxes and
phrases map to your registry roles and workflows.

## Stating what the app used (data + agents → skills)

After inference or a synthesis batch, emit **`learning/last_run_manifest.json`**
(see `learning/ATTESTATION.md` and `scripts/emit_learning_manifest.py`). Your app
can link to that file and reuse the `public_claims` strings so the sentence
“this app used this data and these agents to learn new skills” stays tied to
verifiable paths and versions.
