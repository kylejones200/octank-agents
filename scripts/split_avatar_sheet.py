#!/usr/bin/env python3
"""
Split a uniform rows×cols sprite sheet into one PNG per role_id (registry order).

When there are more agents than cells, the last cell image is duplicated for
trailing roles (document in assets/avatars/README.md).
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="Combined PNG/JPEG")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("assets/avatars"),
        help="Output directory (created if missing)",
    )
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument(
        "--registry",
        type=Path,
        default=Path("registry/registry.json"),
        help="Registry JSON; agent order = split assignment order",
    )
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"Missing input: {args.input}", file=sys.stderr)
        return 1
    reg = json.loads(args.registry.read_text(encoding="utf-8"))
    agents = reg.get("agents")
    if not isinstance(agents, list) or not agents:
        print("registry.json has no agents array", file=sys.stderr)
        return 1

    role_ids: list[str] = []
    for a in agents:
        if isinstance(a, dict) and isinstance(a.get("role_id"), str):
            role_ids.append(a["role_id"])

    img = Image.open(args.input).convert("RGBA")
    w, h = img.size
    rows, cols = args.rows, args.cols
    cell_w, cell_h = w // cols, h // rows
    if cell_w < 1 or cell_h < 1:
        print("Image too small for grid", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    ncells = rows * cols
    for i, rid in enumerate(role_ids):
        cell_idx = min(i, ncells - 1)
        r = cell_idx // cols
        c = cell_idx % cols
        left = c * cell_w
        top = r * cell_h
        tile = img.crop((left, top, left + cell_w, top + cell_h))
        out_path = args.out / f"{rid}.png"
        tile.save(out_path)
        dup = " (duplicate of last tile)" if i >= ncells else ""
        print(f"Wrote {out_path}{dup}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
