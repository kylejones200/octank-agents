#!/usr/bin/env python3
"""
Split a uniform rows×cols sprite sheet into PNG tiles.

**Registry mode (default):** one file per `role_id` from `registry.json` agent order
(`--out`, default `assets/avatars/`). When there are more agents than cells, the
last cell is duplicated for trailing roles.

**Pool mode (`--pool-dir`):** write `tile_00.png` … for generic / extra personas not
yet bound to a `role_id` — use for additional `agent_id` instances, humans-in-loop,
or future registry rows.

**Sheet tuning:** `--preset labeled_sheet` trims edges, pads cells, and keeps the
top band of each cell to drop captions under portraits.

**Web headshots (`--headshot` or `--preset labeled_headshot`):** after the cell
crop, apply a **center square** (face-focused), optional **resize**, optional
**circular alpha** — outputs are easy for another app or static site to consume.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as e:  # pragma: no cover
    print("Install Pillow: pip install Pillow", file=sys.stderr)
    raise SystemExit(1) from e


PRESETS: dict[str, dict[str, float | int | bool]] = {
    "labeled_sheet": {
        "edge_trim_pct": 1.25,
        "cell_pad_pct": 4.5,
        "portrait_top_pct": 72.0,
    },
    # Same sheet tuning + square headshot pipeline for websites / design tools
    "labeled_headshot": {
        "edge_trim_pct": 1.25,
        "cell_pad_pct": 4.5,
        "portrait_top_pct": 72.0,
        "headshot": True,
        "headshot_size": 384,
        "circle_mask": False,
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


def square_center_crop(img: Image.Image) -> Image.Image:
    """Smallest centered square — keeps head mass, drops wide oval margins."""
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    return img.crop((left, top, left + s, top + s))


def resize_square(img: Image.Image, size: int) -> Image.Image:
    if size <= 0:
        return img
    return img.resize((size, size), Image.Resampling.LANCZOS)


def apply_circle_mask(img: Image.Image) -> Image.Image:
    """Square RGBA image → transparent outside inscribed circle."""
    w, h = img.size
    if w != h:
        img = square_center_crop(img)
        w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, w - 1, h - 1), fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    out.paste(img, (0, 0), mask)
    return out


def finalize_tile(img: Image.Image, *, headshot: bool, headshot_size: int, circle_mask: bool) -> Image.Image:
    if headshot:
        img = square_center_crop(img)
        img = resize_square(img, headshot_size)
    if circle_mask:
        img = apply_circle_mask(img)
    return img


def apply_preset(args: argparse.Namespace) -> None:
    if not args.preset:
        return
    key = args.preset.strip().lower()
    if key not in PRESETS:
        print(f"Unknown --preset {args.preset!r}; choose from {list(PRESETS)}", file=sys.stderr)
        raise SystemExit(1)
    p = PRESETS[key]
    args.edge_trim_pct = float(p["edge_trim_pct"])
    args.cell_pad_pct = float(p["cell_pad_pct"])
    args.portrait_top_pct = float(p["portrait_top_pct"])
    if "headshot" in p:
        args.headshot = bool(p["headshot"])
    if "headshot_size" in p:
        args.headshot_size = int(p["headshot_size"])
    if "circle_mask" in p:
        args.circle_mask = bool(p["circle_mask"])


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
        tile = finalize_tile(
            tile,
            headshot=args.headshot,
            headshot_size=args.headshot_size,
            circle_mask=args.circle_mask,
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
        tile = finalize_tile(
            tile,
            headshot=args.headshot,
            headshot_size=args.headshot_size,
            circle_mask=args.circle_mask,
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
        help=f"Apply preset ({', '.join(PRESETS)})",
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
    ap.add_argument(
        "--headshot",
        action="store_true",
        help="After cell crop: center square + optional resize (web headshot)",
    )
    ap.add_argument(
        "--headshot-size",
        type=int,
        default=0,
        metavar="N",
        help="If set with --headshot: resize to N×N pixels (0 = native square size)",
    )
    ap.add_argument(
        "--circle-mask",
        action="store_true",
        help="With --headshot: transparent pixels outside a circle (square canvas)",
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
