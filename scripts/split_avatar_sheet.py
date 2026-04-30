#!/usr/bin/env python3
"""
Split a uniform rows×cols sprite sheet into PNG tiles.

**Registry mode (default):** one file per `role_id` from `registry.json` agent order
(`--out`, default `assets/avatars/`). When there are more agents than cells, the
last cell is duplicated for trailing roles.

**Pool mode (`--pool-dir`):** write `tile_00.png` … for generic / extra personas not
yet bound to a `role_id` — use for additional `agent_id` instances, humans-in-loop,
or future registry rows.

**Better crops:** ChatGPT-style sheets often have (1) outer whitespace, (2) text
under each portrait, (3) tight spacing between cells. Use `--preset labeled_sheet`
or tune `--edge-trim-pct`, `--cell-pad-pct`, and `--portrait-top-pct`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError as e:  # pragma: no cover
    print("Install Pillow: pip install Pillow", file=sys.stderr)
    raise SystemExit(1) from e


PRESETS: dict[str, dict[str, float]] = {
    # Tuned for 2×5 “portrait + name + job title under oval” composites
    "labeled_sheet": {
        "edge_trim_pct": 1.25,
        "cell_pad_pct": 4.5,
        "portrait_top_pct": 76.0,
    },
}


def edge_trim(img: Image.Image, trim_pct: float) -> Image.Image:
    """Remove trim_pct% width from left and right, same for top/bottom, before gridding."""
    if trim_pct <= 0:
        return img
    w, h = img.size
    dx = int(round(w * trim_pct / 100.0))
    dy = int(round(h * trim_pct / 100.0))
    l, t, r, b = dx, dy, w - dx, h - dy
    if r <= l + 8 or b <= t + 8:
        return img
    return img.crop((l, t, r, b))


def cell_crop_rect(
    w: int,
    h: int,
    rows: int,
    cols: int,
    cell_idx: int,
    *,
    cell_pad_pct: float,
    portrait_top_pct: float,
) -> tuple[int, int, int, int]:
    cw = w // cols
    ch = h // rows
    if cw < 4 or ch < 4:
        raise ValueError("Image too small for grid")
    rr = cell_idx // cols
    cc = cell_idx % cols
    left = cc * cw
    top = rr * ch
    right = left + cw
    bottom = top + ch

    if cell_pad_pct > 0:
        pw = cw * (cell_pad_pct / 100.0)
        ph = ch * (cell_pad_pct / 100.0)
        left += pw / 2.0
        top += ph / 2.0
        right -= pw / 2.0
        bottom -= ph / 2.0

    if portrait_top_pct < 100.0:
        height = bottom - top
        bottom = top + height * (portrait_top_pct / 100.0)

    l, t, r, b = int(round(left)), int(round(top)), int(round(right)), int(round(bottom))
    r = max(l + 1, min(w, r))
    b = max(t + 1, min(h, b))
    return l, t, r, b


def crop_cell(
    img: Image.Image,
    rows: int,
    cols: int,
    cell_idx: int,
    *,
    cell_pad_pct: float,
    portrait_top_pct: float,
) -> Image.Image:
    w, h = img.size
    box = cell_crop_rect(w, h, rows, cols, cell_idx, cell_pad_pct=cell_pad_pct, portrait_top_pct=portrait_top_pct)
    return img.crop(box)


def apply_preset(args: argparse.Namespace) -> None:
    if not args.preset:
        return
    key = args.preset.strip().lower()
    if key not in PRESETS:
        print(f"Unknown --preset {args.preset!r}; choose from {list(PRESETS)}", file=sys.stderr)
        raise SystemExit(1)
    p = PRESETS[key]
    args.edge_trim_pct = p["edge_trim_pct"]
    args.cell_pad_pct = p["cell_pad_pct"]
    args.portrait_top_pct = p["portrait_top_pct"]


def run_pool(args: argparse.Namespace, img: Image.Image) -> int:
    img = edge_trim(img, args.edge_trim_pct)
    rows, cols = args.rows, args.cols
    ncells = rows * cols
    args.pool_dir.mkdir(parents=True, exist_ok=True)
    for cell_idx in range(ncells):
        tile = crop_cell(
            img,
            rows,
            cols,
            cell_idx,
            cell_pad_pct=args.cell_pad_pct,
            portrait_top_pct=args.portrait_top_pct,
        )
        out_path = args.pool_dir / f"tile_{cell_idx:02d}.png"
        tile.save(out_path)
        print(f"Wrote {out_path}", file=sys.stderr)
    return 0


def run_registry(args: argparse.Namespace, img: Image.Image) -> int:
    img = edge_trim(img, args.edge_trim_pct)
    reg = json.loads(args.registry.read_text(encoding="utf-8"))
    agents = reg.get("agents")
    if not isinstance(agents, list) or not agents:
        print("registry.json has no agents array", file=sys.stderr)
        return 1

    role_ids: list[str] = []
    for a in agents:
        if isinstance(a, dict) and isinstance(a.get("role_id"), str):
            role_ids.append(a["role_id"])

    rows, cols = args.rows, args.cols
    ncells = rows * cols
    args.out.mkdir(parents=True, exist_ok=True)
    for i, rid in enumerate(role_ids):
        cell_idx = min(i, ncells - 1)
        tile = crop_cell(
            img,
            rows,
            cols,
            cell_idx,
            cell_pad_pct=args.cell_pad_pct,
            portrait_top_pct=args.portrait_top_pct,
        )
        out_path = args.out / f"{rid}.png"
        tile.save(out_path)
        dup = " (duplicate of last tile)" if i >= ncells else ""
        print(f"Wrote {out_path}{dup}", file=sys.stderr)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="Combined PNG/JPEG")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("assets/avatars"),
        help="Registry mode: output directory for {role_id}.png",
    )
    ap.add_argument(
        "--pool-dir",
        type=Path,
        default=None,
        help="If set, pool mode: write tile_00.png … here (ignores registry)",
    )
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument(
        "--registry",
        type=Path,
        default=Path("registry/registry.json"),
        help="Registry JSON (registry mode only)",
    )
    ap.add_argument(
        "--preset",
        type=str,
        default="",
        help=f"Apply crop tuning preset ({', '.join(PRESETS)})",
    )
    ap.add_argument(
        "--edge-trim-pct",
        type=float,
        default=0.0,
        help="Shrink full sheet by this %% from each edge before gridding (default 0)",
    )
    ap.add_argument(
        "--cell-pad-pct",
        type=float,
        default=0.0,
        help="Shrink each cell inward by this %% of cell width/height (reduces neighbor bleed)",
    )
    ap.add_argument(
        "--portrait-top-pct",
        type=float,
        default=100.0,
        help="Keep only top N%% of each cell height (drops captions under portraits; default 100)",
    )
    args = ap.parse_args()

    if args.preset:
        apply_preset(args)

    if not args.input.is_file():
        print(f"Missing input: {args.input}", file=sys.stderr)
        return 1

    img = Image.open(args.input).convert("RGBA")

    if args.pool_dir is not None:
        return run_pool(args, img)
    return run_registry(args, img)


if __name__ == "__main__":
    raise SystemExit(main())
