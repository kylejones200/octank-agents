# Headshots for websites

All role avatars are **square PNGs** (default **384×384** when built with
`--preset labeled_headshot`). Pool tiles use the same pipeline.

## Machine-readable index

**[`site-manifest.json`](site-manifest.json)** — copy this file (and the `assets/avatars/` tree) into your static site or API repo. Each entry includes:

- `path` — repo-relative path (e.g. `assets/avatars/trader.png`)
- `width` / `height` — actual pixel size after last split
- `display_name` / `role_id` for agents; `portrait_label` / `hint_title` for pool tiles

Your web app can resolve `path` against a CDN base URL or import images from a monorepo path.

## Regenerate headshots + manifest

```bash
python3 scripts/split_avatar_sheet.py --preset labeled_headshot \
  --input "/path/to/registry-sheet.png" --out assets/avatars

python3 scripts/split_avatar_sheet.py --preset labeled_headshot \
  --input "/path/to/pool-sheet.png" --pool-dir assets/avatars/pool

python3 scripts/emit_avatar_site_manifest.py
```

### Options

- **`--headshot-size 512`** — change square output size (use with `--headshot` or extend preset via CLI after `--preset`).
- **`--circle-mask`** — transparent pixels outside a circle (still on a square canvas); use if you do not want square corners in a non-CSS pipeline.

## Raw sheet layout (no headshot)

Use `--preset labeled_sheet` without `--headshot` if you need full cell crops for debugging.
