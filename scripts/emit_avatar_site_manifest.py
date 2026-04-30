#!/usr/bin/env python3
"""
Write assets/avatars/site-manifest.json for a separate website or CDN consumer.

Includes registry agents (role_id, display_name, path, pixel size) and pool tiles
(optional labels from pool/manifest.json). Run after splitting avatars.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError as e:  # pragma: no cover
    print("Install Pillow: pip install Pillow", file=sys.stderr)
    raise SystemExit(1) from e


def repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return Path(out)
    except Exception:
        return Path(__file__).resolve().parent.parent


def size_of(root: Path, rel: str) -> tuple[int, int] | None:
    p = root / rel
    if not p.is_file():
        return None
    with Image.open(p) as im:
        return im.size


def main() -> int:
    root = repo_root()
    reg_path = root / "registry" / "registry.json"
    out_path = root / "assets" / "avatars" / "site-manifest.json"
    pool_manifest_path = root / "assets" / "avatars" / "pool" / "manifest.json"

    if not reg_path.is_file():
        print(f"Missing {reg_path}", file=sys.stderr)
        return 1

    data = json.loads(reg_path.read_text(encoding="utf-8"))
    agents_out: list[dict] = []
    for a in data.get("agents", []):
        if not isinstance(a, dict):
            continue
        rid = a.get("role_id")
        if not isinstance(rid, str):
            continue
        rel = a.get("avatar_path")
        if not isinstance(rel, str) or not rel.strip():
            rel = f"assets/avatars/{rid}.png"
        rel = rel.strip()
        sz = size_of(root, rel)
        agents_out.append(
            {
                "role_id": rid,
                "display_name": a.get("agent_name"),
                "path": rel.replace("\\", "/"),
                "width": sz[0] if sz else None,
                "height": sz[1] if sz else None,
            }
        )

    pool_out: list[dict] = []
    if pool_manifest_path.is_file():
        pm = json.loads(pool_manifest_path.read_text(encoding="utf-8"))
        for t in pm.get("tiles", []):
            if not isinstance(t, dict):
                continue
            fn = t.get("file")
            if not isinstance(fn, str):
                continue
            rel = fn.replace("\\", "/")
            if "/" not in rel:
                rel = f"assets/avatars/pool/{fn}"
            sz = size_of(root, rel)
            pool_out.append(
                {
                    "id": Path(fn).stem,
                    "path": rel,
                    "width": sz[0] if sz else None,
                    "height": sz[1] if sz else None,
                    "portrait_label": t.get("portrait_label"),
                    "hint_title": t.get("hint_title"),
                }
            )

    doc = {
        "schema_version": "1",
        "registry_version": data.get("registry_version"),
        "description": "Static headshot index for web apps; paths are repo-relative from site root.",
        "agents": agents_out,
        "pool": pool_out,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(agents_out)} agents, {len(pool_out)} pool)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
