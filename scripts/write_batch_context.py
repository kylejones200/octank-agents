#!/usr/bin/env python3
"""
Write learning/batch_context.json — index of batch outputs for agents to read first.

Paths are relative to repository root. Intended to be run after batch analysis
(see scripts/run_batch_analysis.sh).
"""

from __future__ import annotations

import argparse
import json
import subprocess
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


def rel_exists(root: Path, rel: str) -> str | None:
    p = root / rel
    return rel if p.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Write learning/batch_context.json")
    ap.add_argument(
        "--tasks",
        default="enron/inferred_tasks.jsonl",
        help="Relative path to inferred tasks JSONL",
    )
    ap.add_argument(
        "--manifest",
        default="learning/last_run_manifest.json",
        help="Relative path to learning manifest JSON",
    )
    ap.add_argument(
        "--orgnet-summary",
        default=None,
        help="Optional relative path to orgnet summary JSON or report",
    )
    ap.add_argument(
        "--output",
        default="learning/batch_context.json",
        help="Relative path to write batch context index",
    )
    args = ap.parse_args()

    root = repo_root()
    tasks = rel_exists(root, args.tasks)
    manifest = rel_exists(root, args.manifest)
    orgnet = rel_exists(root, args.orgnet_summary) if args.orgnet_summary else None

    doc: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "artifacts": {
            "available_data_catalog": "learning/AVAILABLE_DATA.md",
            "inferred_tasks": tasks,
            "learning_manifest": manifest,
            "orgnet_summary": orgnet,
        },
        "agent_load_order": [
            "learning/batch_context.json (this file)",
            "learning/AVAILABLE_DATA.md",
            "Each path in artifacts that is non-null (open and cite; do not invent metrics)",
            "roles/<role>/SKILL.md and AGENT.md for the active agent",
            "workflows/<type>/WORKFLOW.md for the active workflow_type",
        ],
        "notes": "Batch analysis writes heavy artifacts; agents consume read-only copies or excerpts in context.",
    }

    out = root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
