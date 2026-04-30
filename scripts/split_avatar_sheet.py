#!/usr/bin/env python3
"""
Split a uniform rows×cols sprite sheet into PNG tiles.

**Registry mode (default):** one file per `role_id` from `registry.json` agent order
(`--out`, default `assets/avatars/`). When there are more agents than cells, the
last cell is duplicated for trailing roles.

**Pool mode (`--pool-dir`):** write `tile_00.png` … for generic / extra personas not
yet bound to a `role_id` — use for additional `agent_id` instances, humans-in-loop,
or future registry rows.
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


def crop_grid(
    img: Image.Image, rows: int, cols: int, cell_idx: int
) -> Image.Image:
    w, h = img.size
    cell_w, cell_h = w // cols, h // rows
    if cell_w < 1 or cell_h < 1:
        raise ValueError("Image too small for grid")
    r = cell_idx // cols
    c = cell_idx % cols
    left = c * cell_w
    top = r * cell_h
    return img.crop((left, top, left + cell_w, top + cell_h))


def run_pool(args: argparse.Namespace, img: Image.Image) -> int:
    rows, cols = args.rows, args.cols
    ncells = rows * cols
    args.pool_dir.mkdir(parents=True, exist_ok=True)
    for cell_idx in range(ncells):
        tile = crop_grid(img, rows, cols, cell_idx)
        out_path = args.pool_dir / f"tile_{cell_idx:02d}.png"
        tile.save(out_path)
        print(f"Wrote {out_path}", file=sys.stderr)
    return 0


def run_registry(args: argparse.Namespace, img: Image.Image) -> int:
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
        tile = crop_grid(img, rows, cols, cell_idx)
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
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"Missing input: {args.input}", file=sys.stderr)
        return 1

    img = Image.open(args.input).convert("RGBA")

    if args.pool_dir is not None:
        return run_pool(args, img)
    return run_registry(args, img)


if __name__ == "__main__":
    raise SystemExit(main())
