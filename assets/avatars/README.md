# Agent headshots (`avatar_path`)

Each file is **`{role_id}.png`**, referenced from [`registry/registry.json`](../../registry/registry.json) as `avatar_path` (repo-relative).

## Source sheet

The current PNGs were split from a single **2 rows × 5 columns** composite using:

```bash
# Recommended for “portrait + caption under oval” sheets (trims edges, pads cells,
# keeps only the top ~76% of each cell so names/job titles are dropped):
python3 scripts/split_avatar_sheet.py \
  --preset labeled_sheet \
  --input "/path/to/combined-sheet.png" \
  --out assets/avatars
```

Tune manually if needed: `--edge-trim-pct 1.5` (shrink full image before gridding),
`--cell-pad-pct 5` (inset each cell to avoid neighbor bleed), `--portrait-top-pct 78`
(keep only the top 78% of each cell’s height for the face).

Agent order follows the **`agents` array order** in `registry.json` (row-major assignment: left-to-right, top row then bottom row).

## Eleven agents, ten cells

This registry has **11** roles; a 2×5 sheet has **10** portraits. The **last grid cell** is duplicated for **`executive_office`** so every role has a file. Replace `executive_office.png` with a dedicated crop when you have one.

## Art vs registry names

Generated artwork may show different printed names than `agent_name` in the registry; the **mapping is positional** (registry order ↔ grid order). Re-run the splitter after reordering `agents` in JSON, or swap individual PNG files manually.

## Extra faces (other people / instances)

Additional 2×5 sheets can be split into **`assets/avatars/pool/`** as `tile_00.png` …
for personas not mapped to a canonical `role_id` yet (extra desk seats, humans,
placeholders). See [`pool/README.md`](pool/README.md) and [`pool/manifest.json`](pool/manifest.json).

```bash
python3 scripts/split_avatar_sheet.py \
  --preset labeled_sheet \
  --input "/path/to/second-sheet.png" \
  --pool-dir assets/avatars/pool
```
