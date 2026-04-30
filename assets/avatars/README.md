# Agent headshots (`avatar`)

PNG files are **`{role_id}.png`**. Each agent in [`registry/registry.json`](../../registry/registry.json) points at its image with **`avatar.path`** (and optional **`avatar.width` / `avatar.height`** for validation).

## Web / another tool

Outputs are **square headshots** (384×384 when using `labeled_headshot`) plus a JSON index:

- **[`site-manifest.json`](site-manifest.json)** — `role_id`, `display_name`, `path`, `width`, `height` for each agent, plus `pool` entries for extra faces.
- **[`WEB.md`](WEB.md)** — how a separate website or CDN should consume these files.

After any split, refresh the index:

```bash
python3 scripts/emit_avatar_site_manifest.py
```

## Regenerate from a sprite sheet

**Recommended** (trim + top band + **center square headshot** + resize):

```bash
python3 scripts/split_avatar_sheet.py \
  --preset labeled_headshot \
  --input "/path/to/combined-sheet.png" \
  --out assets/avatars

python3 scripts/emit_avatar_site_manifest.py
```

**Custom square size** (preset fixes 384×384): use sheet tuning + explicit headshot flags:

```bash
python3 scripts/split_avatar_sheet.py \
  --preset labeled_sheet \
  --headshot --headshot-size 512 \
  --input "/path/to/combined-sheet.png" \
  --out assets/avatars
```

Optional **`--circle-mask`** with `--headshot` for transparent pixels outside a circle (square canvas).

### Sheet-only tuning (no square crop)

Use **`--preset labeled_sheet`** without `--headshot` if you need full rectangular cell crops.

Agent order follows the **`agents` array order** in `registry.json` (row-major: left-to-right, top row then bottom).

## Eleven agents, ten cells

This registry has **11** roles; a 2×5 sheet has **10** portraits. The **last grid cell** is duplicated for **`executive_office`**. Replace `executive_office.png` when you have an eleventh face.

## Art vs registry names

Artwork labels may not match `agent_name`; **mapping is positional** (registry order ↔ grid order).

## Extra faces (pool)

See [`pool/README.md`](pool/README.md) and [`pool/manifest.json`](pool/manifest.json).

```bash
python3 scripts/split_avatar_sheet.py \
  --preset labeled_headshot \
  --input "/path/to/second-sheet.png" \
  --pool-dir assets/avatars/pool

python3 scripts/emit_avatar_site_manifest.py
```
