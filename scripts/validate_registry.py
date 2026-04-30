#!/usr/bin/env python3
"""
Validate registry/registry.json against repo layout and cross-references.

Exit 0 if OK; non-zero with stderr messages on failure.
No third-party dependencies.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


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


def parse_front_matter_field(text: str, field: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    prefix = f"{field}:"
    for line in block.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            val = line[len(prefix) :].strip()
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                return val[1:-1]
            return val.strip() or None
    return None


def main() -> int:
    root = repo_root()
    reg_path = root / "registry" / "registry.json"
    if not reg_path.is_file():
        print(f"Missing {reg_path}", file=sys.stderr)
        return 1

    data = json.loads(reg_path.read_text(encoding="utf-8"))

    errors: list[str] = []

    agents = data.get("agents")
    workflows = data.get("workflows")
    if not isinstance(agents, list) or not isinstance(workflows, list):
        errors.append('"agents" and "workflows" must be arrays')
        return 1

    role_ids: list[str] = []
    for a in agents:
        if not isinstance(a, dict):
            errors.append("Each agent must be an object")
            continue
        rid = a.get("role_id")
        if not rid or not isinstance(rid, str):
            errors.append("Agent missing role_id")
            continue
        if rid in role_ids:
            errors.append(f"Duplicate role_id: {rid}")
        role_ids.append(rid)

    role_set = set(role_ids)

    display_names: list[str] = []
    for a in agents:
        if not isinstance(a, dict):
            continue
        rid = a.get("role_id")
        aname_raw = a.get("agent_name")
        if rid and (not isinstance(aname_raw, str) or not aname_raw.strip()):
            errors.append(f"Agent {rid}: agent_name must be a non-empty string")
        elif rid and isinstance(aname_raw, str):
            display_names.append(aname_raw.strip())

    for n, count in Counter(display_names).items():
        if count > 1:
            errors.append(f"Duplicate agent_name: {n!r}")

    for a in agents:
        if not isinstance(a, dict):
            continue
        rid = a.get("role_id")
        skill = a.get("skill_path")
        agentp = a.get("agent_path")
        wts = a.get("workflow_types")
        aname = a.get("agent_name")
        aname_norm = aname.strip() if isinstance(aname, str) else None
        if not rid:
            continue
        if not skill or not agentp:
            errors.append(f"Agent {rid}: skill_path and agent_path required")
            continue
        for label, p in (("skill_path", skill), ("agent_path", agentp)):
            path = root / p
            if not path.is_file():
                errors.append(f"Agent {rid}: {label} not found: {p}")
            else:
                body = path.read_text(encoding="utf-8")
                fm_role = parse_front_matter_field(body, "role_id")
                if fm_role and fm_role != rid:
                    errors.append(
                        f"Agent {rid}: front matter role_id is {fm_role!r} in {p}"
                    )
                fm_aname = parse_front_matter_field(body, "agent_name")
                if aname_norm:
                    if fm_aname is None:
                        errors.append(
                            f"Agent {rid}: missing agent_name in front matter of {p}"
                        )
                    elif fm_aname != aname_norm:
                        errors.append(
                            f"Agent {rid}: front matter agent_name is {fm_aname!r}, "
                            f"registry has {aname_norm!r} in {p}"
                        )
        if not isinstance(wts, list) or not wts:
            errors.append(f"Agent {rid}: workflow_types must be a non-empty array")

    for a in agents:
        if not isinstance(a, dict):
            continue
        rid = a.get("role_id")
        peers = a.get("typical_peers")
        if not rid or not isinstance(peers, list):
            continue
        for p in peers:
            if p not in role_set:
                errors.append(
                    f"Agent {rid}: typical_peers references unknown role {p!r}"
                )

    wf_set: set[str] = set()
    wf_types: list[str] = []
    for w in workflows:
        if not isinstance(w, dict):
            errors.append("Each workflow must be an object")
            continue
        wt = w.get("workflow_type")
        path = w.get("workflow_path")
        parts = w.get("participant_roles")
        if not wt or not path:
            errors.append("Workflow missing workflow_type or workflow_path")
            continue
        if wt in wf_set:
            errors.append(f"Duplicate workflow_type: {wt}")
        wf_set.add(wt)
        wf_types.append(wt)
        fp = root / path
        if not fp.is_file():
            errors.append(f"Workflow {wt}: file not found: {path}")
        else:
            body = fp.read_text(encoding="utf-8")
            fm_wf = parse_front_matter_field(body, "workflow_type")
            if fm_wf and fm_wf != wt:
                errors.append(
                    f"Workflow {wt}: front matter workflow_type is {fm_wf!r} in {path}"
                )
        if not isinstance(parts, list) or not parts:
            errors.append(f"Workflow {wt}: participant_roles must be non-empty array")
            continue
        for pr in parts:
            if pr not in role_set:
                errors.append(
                    f"Workflow {wt}: participant_roles references unknown role {pr!r}"
                )

    agent_by_role: dict[str, dict] = {}
    for a in agents:
        if isinstance(a, dict) and isinstance(a.get("role_id"), str):
            agent_by_role[a["role_id"]] = a

    for a in agents:
        if not isinstance(a, dict):
            continue
        rid = a.get("role_id")
        wts = a.get("workflow_types")
        if not rid or not isinstance(wts, list):
            continue
        for wt in wts:
            if wt not in wf_set:
                errors.append(
                    f"Agent {rid}: workflow_types references unknown workflow {wt!r}"
                )

    for w in workflows:
        if not isinstance(w, dict):
            continue
        wt = w.get("workflow_type")
        parts = w.get("participant_roles")
        if not wt or not isinstance(parts, list):
            continue
        for rid in role_ids:
            a = agent_by_role.get(rid)
            if not isinstance(a, dict):
                continue
            aw = a.get("workflow_types")
            if not isinstance(aw, list):
                continue
            if wt in aw and rid not in parts:
                errors.append(
                    f"Workflow {wt}: role {rid} lists this workflow in registry "
                    "but is missing from participant_roles"
                )
        for pr in parts:
            a = agent_by_role.get(pr)
            if not isinstance(a, dict):
                continue
            aw = a.get("workflow_types")
            if not isinstance(aw, list) or wt not in aw:
                errors.append(
                    f"Workflow {wt}: participant {pr!r} must include {wt!r} "
                    "in agent workflow_types"
                )

    if errors:
        print("Registry validation failed:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(
        f"OK: registry {data.get('registry_version', '?')} "
        f"({len(role_ids)} agents, {len(wf_types)} workflows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
