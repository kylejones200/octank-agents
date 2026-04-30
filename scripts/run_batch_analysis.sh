#!/usr/bin/env bash
# Offline batch: validate registry → infer tasks from corpus → manifest → batch_context index.
# Agents should read learning/batch_context.json (and linked files) before relying on corpus/ONA claims.
#
# Optional env:
#   BATCH_MAX_ROWS      — if set and non-zero, pass --max-rows to infer (faster dev runs)
#   BATCH_MAX_THREADS   — if set, pass --max-threads (cap lines in JSONL output)
#   ORGNET_SUMMARY      — relative path to orgnet artifact for write_batch_context.py (optional)
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== 1. Validate registry =="
python3 scripts/validate_registry.py

echo "== 2. Infer tasks from corpus (enron/corpus_config.json) =="
INFER=(python3 scripts/enron_infer_tasks.py --corpus-config enron/corpus_config.json --output enron/inferred_tasks.jsonl)
if [ -n "${BATCH_MAX_ROWS:-}" ] && [ "${BATCH_MAX_ROWS}" != "0" ]; then
  INFER+=(--max-rows "${BATCH_MAX_ROWS}")
fi
if [ -n "${BATCH_MAX_THREADS:-}" ] && [ "${BATCH_MAX_THREADS}" != "0" ]; then
  INFER+=(--max-threads "${BATCH_MAX_THREADS}")
fi
"${INFER[@]}"

echo "== 3. Emit learning manifest =="
python3 scripts/emit_learning_manifest.py \
  --corpus-config enron/corpus_config.json \
  --tasks enron/inferred_tasks.jsonl \
  --output learning/last_run_manifest.json

echo "== 4. Write batch context index for agents =="
ORGNET_ARGS=()
if [ -n "${ORGNET_SUMMARY:-}" ]; then
  ORGNET_ARGS=(--orgnet-summary "${ORGNET_SUMMARY}")
fi
python3 scripts/write_batch_context.py "${ORGNET_ARGS[@]}"

echo "Done. Agents: load learning/batch_context.json then artifacts listed there."
echo "See learning/AVAILABLE_DATA.md (section: Batch analysis, then agent read)."
