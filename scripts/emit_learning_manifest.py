#!/usr/bin/env python3
"""
Emit learning/run_manifest JSON: which data + which agents supported skill learning.

Usage:
  python3 scripts/emit_learning_manifest.py --corpus-config enron/corpus_config.json \\
      --registry registry/registry.json --output learning/last_run_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_uri(p: Path) -> str:
    return p.as_uri()


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parquet_row_count(path: Path) -> int | None:
    try:
        import pyarrow.dataset as ds
    except ImportError:
        return None
    try:
        return int(ds.dataset(str(path), format="parquet").count_rows())
    except Exception:
        return None


def workflow_histogram(tasks_path: Path | None, limit_lines: int = 500_000) -> list[str]:
    if not tasks_path or not tasks_path.is_file():
        return []
    ctr: Counter[str] = Counter()
    n = 0
    with tasks_path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            n += 1
            if n > limit_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            wf = o.get("inferred_workflow_type")
            if isinstance(wf, str):
                ctr[wf] += 1
    return [w for w, _ in ctr.most_common(50)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit learning run manifest JSON")
    ap.add_argument("--corpus-config", type=Path, required=True)
    ap.add_argument("--registry", type=Path, help="Default: registry/registry.json")
    ap.add_argument("--tasks", type=Path, help="Optional inferred_tasks.jsonl")
    ap.add_argument("--output", type=Path, default=Path("learning/last_run_manifest.json"))
    ap.add_argument(
        "--hash-parquet",
        action="store_true",
        help="Compute sha256 of parquet (can be slow for huge files)",
    )
    ap.add_argument("--app-name", type=str, default="Digital org desk")
    ap.add_argument("--app-version", type=str, default="0.1.0")
    args = ap.parse_args()

    root = repo_root()
    cfg = load_json(args.corpus_config)
    reg_path = args.registry or (root / "registry" / "registry.json")
    reg = load_json(reg_path)

    parquet_s = cfg.get("parquet")
    maildir_s = cfg.get("maildir_root")
    parquet_p = Path(parquet_s) if parquet_s else None
    maildir_p = Path(maildir_s) if maildir_s else None

    data_sources: list[dict[str, Any]] = []
    if parquet_p and parquet_p.is_file():
        ds_entry: dict[str, Any] = {
            "kind": "parquet",
            "uri": file_uri(parquet_p.resolve()),
            "description": "Email table (file + message columns)",
            "role_in_learning": "primary_corpus",
        }
        rc = parquet_row_count(parquet_p)
        if rc is not None:
            ds_entry["record_count"] = rc
        if args.hash_parquet:
            ds_entry["content_sha256"] = sha256_file(parquet_p)
        data_sources.append(ds_entry)
    if maildir_p and maildir_p.is_dir():
        data_sources.append(
            {
                "kind": "maildir",
                "uri": file_uri(maildir_p.resolve()),
                "description": "On-disk messages referenced by parquet paths",
                "role_in_learning": "evidence_paths",
            }
        )

    if not data_sources:
        print("No valid data sources from corpus config.", file=sys.stderr)
        return 1

    agents_used: list[dict[str, Any]] = []
    for a in reg.get("agents", []):
        rid = a.get("role_id")
        if not isinstance(rid, str):
            continue
        agents_used.append(
            {
                "role_id": rid,
                "agent_name": str(a.get("agent_name", "")),
                "registry_paths": {
                    "skill_path": str(a.get("skill_path", "")),
                    "agent_path": str(a.get("agent_path", "")),
                },
                "participation": "behavioral_template",
            }
        )

    learning_outputs: list[dict[str, Any]] = []
    if args.tasks and args.tasks.is_file():
        learning_outputs.append(
            {
                "kind": "inferred_tasks",
                "uri": file_uri(args.tasks.resolve()),
                "description": "Inferred tasks (JSONL) aligned to registry workflows",
            }
        )

    learning_outputs.append(
        {
            "kind": "report",
            "uri": file_uri((root / "learning" / "ATTESTATION.md").resolve()),
            "description": "How to describe data + agent + skill lineage in product copy",
        }
    )

    wf_obs = workflow_histogram(args.tasks)

    manifest: dict[str, Any] = {
        "$schema": "./run_manifest.schema.json",
        "manifest_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "application": {
            "name": args.app_name,
            "version": args.app_version,
            "repository": file_uri(root.resolve()),
        },
        "data_sources": data_sources,
        "agents_used": agents_used,
        "workflow_types_observed": wf_obs,
        "learning_outputs": learning_outputs,
        "skills_learned_or_updated": [],
        "method_summary": (
            "Corpus-backed task inference (scripts/enron_infer_tasks.py) and/or "
            "LLM synthesis (PROMPT_TEMPLATES.md) over registry agents; human review "
            "before treating outputs as production skills."
        ),
        "public_claims": [
            "This application used the data listed under data_sources and the agent definitions listed under agents_used in learning/last_run_manifest.json to drive skill learning from that data.",
            "When a run produces concrete SKILL updates, they are recorded under skills_learned_or_updated with versions and optional task id samples.",
        ],
    }

    out = args.output
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
