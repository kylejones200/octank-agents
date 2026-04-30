# What you can truthfully say

Use a **learning run manifest** (`learning/last_run_manifest.json`) as the single source of truth.
Agents are instructed to consult **`learning/batch_context.json`** (after each
batch) and **`learning/AVAILABLE_DATA.md`** for what data exists and how to use
it honestly (cite artifacts; do not invent metrics). Your app, README, or compliance appendix can point at it and quote the `public_claims` strings verbatim if they still match the files on disk.

**Repository hygiene:** `learning/last_run_manifest.json` is **gitignored** — generated manifests include local file URIs and should not be committed. Keep [`learning/run_manifest.example.json`](run_manifest.example.json) (and the schema) in git as documentation of the shape only.

## Suggested wording (after you generate a manifest)

1. **Data** — “This application used the datasets listed under `data_sources` in `learning/last_run_manifest.json`, including paths and (when recorded) record counts.”

2. **Agents** — “Operational behavior was grounded in the agent pack under `agents_used` in that manifest (registry-backed `SKILL.md` / `AGENT.md` for each named role).”

3. **Skills** — “New or revised skills appear in `skills_learned_or_updated` with bumped `skill_version` and provenance you attach (e.g. `sources` in front matter pointing to this manifest or task ids).”

4. **Method** — “Inference and synthesis steps are summarized in `method_summary`; raw email bodies are not required to ship with the app if the manifest references file URIs on your side.”

## Generate or refresh the manifest

```bash
python3 scripts/emit_learning_manifest.py \
  --corpus-config corpus/corpus_config.json \
  --registry registry/registry.json \
  --output learning/last_run_manifest.json
```

Optional: attach inferred tasks and optional SHA-256 of the parquet file:

```bash
python3 scripts/emit_learning_manifest.py \
  --corpus-config corpus/corpus_config.json \
  --registry registry/registry.json \
  --tasks corpus/inferred_tasks.jsonl \
  --hash-parquet \
  --output learning/last_run_manifest.json
```

Edit `public_claims` in the emitted JSON if your legal/comms team needs different phrasing; keep them consistent with what is actually listed in the same file.
