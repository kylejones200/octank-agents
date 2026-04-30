#!/usr/bin/env bash
# Quick end-to-end check: registry → corpus tasks → learning manifest.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "== validate registry =="
python3 scripts/validate_registry.py
echo "== infer tasks (25k rows, 150 tasks cap) =="
python3 scripts/enron_infer_tasks.py \
  --corpus-config enron/corpus_config.json \
  --max-rows 25000 \
  --max-threads 150 \
  --output enron/_smoke_tasks.jsonl
echo "== lines =="
wc -l enron/_smoke_tasks.jsonl
echo "== emit manifest =="
python3 scripts/emit_learning_manifest.py \
  --corpus-config enron/corpus_config.json \
  --tasks enron/_smoke_tasks.jsonl \
  --output learning/_smoke_manifest.json
echo "== batch context index (smoke paths) =="
python3 scripts/write_batch_context.py \
  --tasks enron/_smoke_tasks.jsonl \
  --manifest learning/_smoke_manifest.json \
  --output learning/_smoke_batch_context.json
echo "== sample task =="
head -1 enron/_smoke_tasks.jsonl | python3 -m json.tool | head -20
echo "OK smoke_pipeline"
