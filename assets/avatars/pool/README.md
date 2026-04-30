# Extra avatar pool

PNG files **`tile_00.png` … `tile_09.png`** are neutral crops from a second 2×5
composite (not tied to `registry.json` `role_id` files in the parent folder).

Use them for:

- A second trader / analyst instance (`agent_trader_2` → pick a `tile_XX.png`),
- Human approvers or exception-queue personas in UI,
- Placeholders until you assign a dedicated `assets/avatars/<role_id>.png`.

**Catalog:** see [`manifest.json`](manifest.json) for the illustrated names and
titles on the source sheet (hints only — your runtime may rename freely).

**Regenerate tiles** (e.g. after replacing the source artwork):

```bash
python3 scripts/split_avatar_sheet.py \
  --preset labeled_headshot \
  --input "/path/to/new-composite.png" \
  --pool-dir assets/avatars/pool

python3 scripts/emit_avatar_site_manifest.py
```

Then update `manifest.json` if the people or order on the sheet changed. If faces
are still clipped, raise `--portrait-top-pct` toward `82` or lower `--cell-pad-pct`.
