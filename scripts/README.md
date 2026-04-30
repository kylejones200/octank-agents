# Scripts

| Command | Purpose |
|---|---|
| `python3 scripts/validate_registry.py` | Check `registry/registry.json` vs `roles/` and `workflows/` (paths, front matter, participation rules, optional `avatar_path`). Exit non-zero on error. |
| `python3 scripts/split_avatar_sheet.py --input <sheet.png>` | Crop a uniform `rows×cols` sprite sheet (default 2×5) into `assets/avatars/<role_id>.png` in registry order; duplicates the last tile if there are more agents than cells. |
| `./scripts/smoke_pipeline.sh` | Registry validate → small corpus task infer → smoke manifest → smoke `batch_context` (writes under `corpus/_smoke_*`, `learning/_smoke_*`). |
| `./scripts/run_batch_analysis.sh` | Full batch: infer tasks, emit `learning/last_run_manifest.json`, write `learning/batch_context.json` (requires corpus; manifest is gitignored). |
| `./scripts/install-git-hooks.sh` | Install repo `pre-commit` hook that runs the registry validator. |

### Learning manifest

```bash
python3 scripts/emit_learning_manifest.py \
  --corpus-config corpus/corpus_config.json \
  --registry registry/registry.json \
  --output learning/last_run_manifest.json
```

Do not commit `learning/last_run_manifest.json` (local URIs). See [`learning/ATTESTATION.md`](../learning/ATTESTATION.md).
