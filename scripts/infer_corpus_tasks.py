#!/usr/bin/env python3
"""
Infer agent-performable tasks from a Maildir or parquet email corpus.

Supports:
  - Maildir: any folder tree containing cur/ or new/ message files
  - Parquet: columns `file` (path relative to maildir_root) + `message` (RFC822)

Outputs JSONL linking threads to registry workflow_type + role_id.

Usage:
  python3 scripts/infer_corpus_tasks.py --corpus-config corpus/corpus_config.json --output corpus/inferred_tasks.jsonl
  python3 scripts/infer_corpus_tasks.py --parquet /path/emails.parquet --maildir-root /path/maildir --max-rows 5000
  python3 scripts/infer_corpus_tasks.py --maildir /path/maildir
  python3 scripts/infer_corpus_tasks.py --demo
"""

from __future__ import annotations

import argparse
import email
import hashlib
import json
import re
import subprocess
import sys
from email.utils import getaddresses, parsedate_to_datetime
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import timezone
from email import policy
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


def load_registry_agents(root: Path) -> dict[str, dict[str, str]]:
    reg = load_json(root / "registry" / "registry.json")
    out: dict[str, dict[str, str]] = {}
    for a in reg.get("agents", []):
        rid = a.get("role_id")
        if isinstance(rid, str):
            out[rid] = {
                "agent_name": str(a.get("agent_name", "")),
                "skill_path": str(a.get("skill_path", "")),
                "agent_path": str(a.get("agent_path", "")),
            }
    return out


def parse_address_list(header_val: str | None) -> list[str]:
    if not header_val:
        return []
    pairs = getaddresses([header_val.replace("\n", " ")])
    return [addr.lower() for _, addr in pairs if addr and "@" in addr]


def local_part(addr: str) -> str:
    return addr.split("@", 1)[0].lower()


_MAILDIR_REL = re.compile(
    r"^[a-z][a-z0-9_-]*/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)


def is_plausible_maildir_rel(rel: str | None) -> bool:
    """Parquet `file` column should look like 'allen-p/inbox/123.' — skip junk rows."""
    if not isinstance(rel, str) or not rel or len(rel) > 400:
        return False
    if ".." in rel or "\n" in rel or "\x00" in rel:
        return False
    low = rel.lower()
    if any(
        x in low
        for x in (
            "javascript",
            "function",
            "<script",
            "random",
            "parent.",
            "mailto:",
        )
    ):
        return False
    if rel[0] in ".(/<{[":
        return False
    return bool(_MAILDIR_REL.match(rel))


def parse_email_bytes(raw: bytes, path: str) -> dict[str, Any] | None:
    try:
        msg = email.message_from_bytes(raw, policy=policy.default)
    except Exception:
        return None

    def decode_part(m: email.message.Message) -> str:
        try:
            if m.get_content_maintype() == "multipart":
                chunks: list[str] = []
                for sub in m.iter_parts():
                    if sub.get_content_type() == "text/plain":
                        try:
                            chunks.append(sub.get_content())
                        except Exception:
                            pass
                return "\n".join(chunks)
            return m.get_content()
        except Exception:
            return ""

    body = decode_part(msg) or ""
    body = body[:4000]

    mid = msg.get("Message-ID") or ""
    mid = mid.strip().strip("<>")
    irt = msg.get("In-Reply-To") or ""
    irt = re.sub(r"^<|>$", "", irt.strip())
    refs = msg.get("References") or ""
    ref_ids = [r.strip("<>") for r in refs.split() if r.strip()]

    subj = msg.get("Subject") or ""
    date_hdr = msg.get("Date")
    dt: str | None = None
    if date_hdr:
        try:
            parsed = parsedate_to_datetime(date_hdr)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            dt = parsed.isoformat()
        except Exception:
            dt = None

    froms = parse_address_list(msg.get("From"))
    tos = parse_address_list(msg.get("To"))
    ccs = parse_address_list(msg.get("Cc"))

    fallback_id = mid or path
    return {
        "path": path,
        "message_id": mid or fallback_id,
        "in_reply_to": irt,
        "references": ref_ids,
        "subject": subj,
        "date": dt,
        "from": froms,
        "to": tos,
        "cc": ccs,
        "body": body.lower(),
    }


def maildir_messages(maildir: Path) -> list[Path]:
    paths: list[Path] = []
    for p in maildir.rglob("*"):
        if not p.is_file():
            continue
        if p.parent.name in ("cur", "new"):
            paths.append(p)
    return sorted(set(paths))


def read_message(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    m = parse_email_bytes(raw, str(path))
    if m:
        ps = str(path).replace("\\", "/")
        if "/maildir/" in ps:
            m["rel"] = ps.split("/maildir/", 1)[-1]
    return m


def iter_parquet_messages(
    parquet_path: Path,
    maildir_root: Path | None,
    max_rows: int,
) -> Iterable[dict[str, Any]]:
    try:
        import pyarrow.dataset as ds
    except ImportError as e:
        raise SystemExit(
            "Parquet ingestion requires pyarrow. Install with:\n"
            "  pip install -r requirements-corpus.txt\n"
            f"  ({e})"
        ) from e

    dataset = ds.dataset(str(parquet_path), format="parquet")
    cols = dataset.schema.names
    if "file" not in cols or "message" not in cols:
        raise SystemExit(
            f"Parquet must have columns 'file' and 'message'; got: {cols!r}"
        )

    scanner = dataset.scanner(columns=["file", "message"], batch_size=4096)
    n = 0
    for batch in scanner.to_batches():
        files = batch.column(0)
        msgs = batch.column(1)
        for i in range(batch.num_rows):
            if max_rows and n >= max_rows:
                return
            rel = files[i].as_py()
            if not is_plausible_maildir_rel(rel):
                n += 1
                continue
            body = msgs[i].as_py()
            if body is None:
                n += 1
                continue
            raw = body.encode("utf-8", errors="replace") if isinstance(body, str) else bytes(body)
            if maildir_root and rel:
                disk = maildir_root / rel
                path_str = str(disk) if disk.is_file() else f"{parquet_path}::{rel}"
            else:
                path_str = f"{parquet_path}::{rel}" if rel else str(parquet_path)
            parsed = parse_email_bytes(raw, path_str)
            if parsed:
                parsed["rel"] = rel
                yield parsed
            n += 1


_ws_re = re.compile(r"\s+")


def normalize_subject(subject: str) -> str:
    s = (subject or "").strip()
    while True:
        low = s.lower()
        if low.startswith("re:"):
            s = s[3:].lstrip()
        elif low.startswith("fwd:") or low.startswith("fw:"):
            s = s[4:].lstrip()
        else:
            break
    return _ws_re.sub(" ", s)[:220].lower()


def thread_key(
    m: dict[str, Any],
    *,
    subject_day_bucket: bool = False,
) -> str:
    if m["references"]:
        return m["references"][0]
    if m["in_reply_to"]:
        return m["in_reply_to"]
    mid = (m.get("message_id") or "").strip()
    if mid:
        return mid
    if subject_day_bucket:
        rel = m.get("rel") or ""
        mb = rel.split("/")[0] if rel else "unknown"
        day = (m.get("date") or "")[:10] or "nodate"
        ns = normalize_subject(m.get("subject") or "")
        tail = ns if ns else hashlib.sha256(m.get("path", "").encode()).hexdigest()[:12]
        return f"bucket|{mb}|{day}|{tail}"
    return m.get("path", "unknown")


def score_workflow(text: str, sets: list[dict[str, Any]]) -> tuple[str, float, list[str]]:
    best_wf = "deal_execution"
    best_score = 0.0
    all_hits: list[str] = []
    for spec in sets:
        wf = spec.get("workflow_type")
        kws = spec.get("keywords") or []
        weight = float(spec.get("weight", 1.0))
        if not isinstance(wf, str) or not isinstance(kws, list):
            continue
        hits = [k for k in kws if k.lower() in text]
        if not hits:
            continue
        score = len(hits) * weight
        if score > best_score:
            best_score = score
            best_wf = wf
            all_hits = hits
    if best_score == 0.0:
        return "deal_execution", 0.0, []
    return best_wf, best_score, all_hits


def infer_primary_role(
    participants: list[str],
    counts: Counter[str],
    hints: dict[str, Any],
    combined_text: str,
) -> str:
    local_map = hints.get("email_localpart_to_role") or {}
    if isinstance(local_map, dict):
        for addr in participants:
            lp = local_part(addr)
            r = local_map.get(lp)
            if isinstance(r, str) and r:
                return r

    rsec = hints.get("role_from_participant_rank") or {}
    rules = rsec.get("body_keyword_to_role") if isinstance(rsec, dict) else None
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            kws = rule.get("keywords") or []
            rid = rule.get("role_id")
            if not isinstance(rid, str):
                continue
            if any(str(k).lower() in combined_text for k in kws):
                return rid

    if counts:
        top_addr, _ = counts.most_common(1)[0]
        lp = local_part(top_addr)
        r = local_map.get(lp) if isinstance(local_map, dict) else None
        if isinstance(r, str) and r:
            return r
    return "trader"


def suggested_steps(workflow_type: str) -> list[str]:
    return {
        "deal_execution": [
            "Capture commercial terms and counterparty in org state.",
            "Run risk gate; attach utilization and flags.",
            "If required, request legal clearance before confirmation.",
            "Hand to scheduler for transport; ops for physical confirmation.",
            "Accounting settlement template and close.",
        ],
        "pipeline_nomination": [
            "Validate cutoff vs org state calendar.",
            "Submit nomination with structured path and volumes.",
            "Record operator confirmation; ops monitors curtailments.",
        ],
        "risk_escalation": [
            "Package breach metrics and timeline.",
            "Request trader mitigation within SLA.",
            "Desk manager decision; log override if applicable.",
        ],
        "eod_position_reporting": [
            "Compile positions and utilization by hub/book.",
            "Notify desk; capture acknowledgments or disputes.",
            "Hand snapshot id to accounting for reconciliation.",
        ],
        "counterparty_onboarding": [
            "Intake entity and expected activity from trader.",
            "Legal credit/KYC checklist; accounting billing setup.",
            "Update approved counterparty in org state when gates clear.",
        ],
        "regulatory_inquiry": [
            "Intake facts and message evidence from desk.",
            "Compliance maps to controls and filings; legal branch if binding.",
            "Risk attaches quantitative and reporting impact.",
            "Structured response; archive artifacts.",
        ],
        "systems_change_request": [
            "IT documents impact, window, rollback, and tests.",
            "Ops confirms physical/operator touchpoints.",
            "Desk accepts business impact; risk validates post-change checks.",
        ],
    }.get(
        workflow_type,
        ["Review thread evidence", "Map to workflow in registry", "Execute per WORKFLOW.md"],
    )


def stable_task_id(thread_key: str, wf: str) -> str:
    h = hashlib.sha256(f"{thread_key}|{wf}".encode()).hexdigest()[:16]
    return f"task_corpus_{h}"


def run_demo(registry: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    def bind(rid: str) -> dict[str, str]:
        n = registry.get(rid, {}).get("agent_name", "")
        return {rid: n} if n else {rid: ""}

    a = {
        "task_id": stable_task_id("demo-root-id", "pipeline_nomination"),
        "schema_version": "0.1",
        "source": "demo",
        "thread_key": "demo-root-id",
        "message_count": 3,
        "date_range": {"start": "2000-01-01T12:00:00+00:00", "end": "2000-01-01T15:00:00+00:00"},
        "subjects": ["RE: nomination for Jan 3 at Transwestern"],
        "inferred_workflow_type": "pipeline_nomination",
        "confidence": 0.9,
        "matched_keywords": ["nomination", "pipeline"],
        "inferred_primary_role": "scheduler",
        "participants": [
            {"email": "trader@example.com", "message_count": 1},
            {"email": "scheduling@example.com", "message_count": 2},
        ],
        "agent_bindings": bind("scheduler"),
        "suggested_task_title": "Nominate and confirm transport for flow date",
        "suggested_steps": suggested_steps("pipeline_nomination"),
    }
    b = {
        "task_id": stable_task_id("demo-risk", "risk_escalation"),
        "schema_version": "0.1",
        "source": "demo",
        "thread_key": "demo-risk",
        "message_count": 4,
        "date_range": {"start": "2000-01-02T14:00:00+00:00", "end": "2000-01-02T16:30:00+00:00"},
        "subjects": ["URGENT: Rockies position limit"],
        "inferred_workflow_type": "risk_escalation",
        "confidence": 0.75,
        "matched_keywords": ["limit", "position", "urgent"],
        "inferred_primary_role": "risk_analyst",
        "participants": [{"email": "risk@example.com", "message_count": 3}],
        "agent_bindings": bind("risk_analyst"),
        "suggested_task_title": "Resolve limit breach with escalation path",
        "suggested_steps": suggested_steps("risk_escalation"),
    }
    return [a, b]


def build_tasks_from_messages(
    messages: Iterable[dict[str, Any]],
    hints: dict[str, Any],
    registry: dict[str, dict[str, str]],
    min_messages: int,
    max_threads: int,
    source_label: str,
    *,
    subject_day_bucket: bool = False,
) -> list[dict[str, Any]]:
    kw_sets = hints.get("subject_keyword_sets") or []
    by_thread: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in messages:
        by_thread[thread_key(m, subject_day_bucket=subject_day_bucket)].append(m)

    tasks: list[dict[str, Any]] = []
    items = sorted(
        by_thread.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    emitted = 0
    for tk, msgs in items:
        if len(msgs) < min_messages:
            continue
        msgs.sort(key=lambda x: x.get("date") or "")
        subjects = list({m["subject"] for m in msgs if m.get("subject")})
        combined = " ".join(
            [s.lower() for s in subjects] + [m.get("body", "") for m in msgs],
        )
        wf, score, hits = score_workflow(combined, kw_sets)
        counts: Counter[str] = Counter()
        participants_set: set[str] = set()
        for m in msgs:
            for a in m.get("from", []):
                counts[a] += 1
                participants_set.add(a)
            for a in m.get("to", []) + m.get("cc", []):
                participants_set.add(a)
        participants = sorted(participants_set)
        primary = infer_primary_role(participants, counts, hints, combined)
        dates = [m["date"] for m in msgs if m.get("date")]
        dr: dict[str, str] = {}
        if dates:
            dr = {"start": min(dates), "end": max(dates)}
        conf = min(1.0, 0.15 + 0.1 * len(msgs) + 0.05 * score)
        task = {
            "task_id": stable_task_id(tk, wf),
            "schema_version": "0.1",
            "source": source_label,
            "thread_key": tk,
            "message_count": len(msgs),
            "date_range": dr,
            "subjects": subjects[:12],
            "message_paths": [m["path"] for m in msgs][:50],
            "participants": [{"email": e, "message_count": counts[e]} for e in participants][:40],
            "inferred_workflow_type": wf,
            "confidence": round(conf, 3),
            "matched_keywords": hits[:30],
            "inferred_primary_role": primary,
            "agent_bindings": {
                primary: registry.get(primary, {}).get("agent_name", ""),
            },
            "suggested_task_title": subjects[0][:200] if subjects else wf,
            "suggested_steps": suggested_steps(wf),
        }
        tasks.append(task)
        emitted += 1
        if max_threads and emitted >= max_threads:
            break
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Infer registry-aligned tasks from Maildir or emails.parquet"
    )
    ap.add_argument("--corpus-config", type=Path, help="JSON with parquet + maildir_root paths")
    ap.add_argument("--parquet", type=Path, help="Path to emails.parquet (needs pyarrow)")
    ap.add_argument(
        "--maildir-root",
        type=Path,
        help="Root for relative paths in parquet `file` column (optional)",
    )
    ap.add_argument("--maildir", type=Path, help="Maildir tree with cur/ or new/ folders")
    ap.add_argument("--output", type=Path, help="JSONL output path (default: stdout)")
    ap.add_argument("--hints", type=Path, help="Hints JSON (default: corpus/registry_hints.json)")
    ap.add_argument(
        "--min-messages",
        type=int,
        default=1,
        help="Minimum messages per thread (use 2+ for strict RFC threading only)",
    )
    ap.add_argument(
        "--bucket-mailbox-subject-day",
        action="store_true",
        help="When Message-ID/References are missing, group by mailbox + calendar day + "
        "normalized subject (helps PST-style parquet exports)",
    )
    ap.add_argument("--max-threads", type=int, default=0, help="Cap emitted threads (0 = no cap)")
    ap.add_argument("--max-rows", type=int, default=0, help="Parquet only: max rows to scan (0 = all)")
    ap.add_argument("--demo", action="store_true", help="Example tasks without corpus")
    args = ap.parse_args()

    root = repo_root()
    hints_path = args.hints or (root / "corpus" / "registry_hints.json")
    hints = load_json(hints_path) if hints_path.is_file() else {}
    registry = load_registry_agents(root)

    parquet_path = args.parquet
    maildir_root = args.maildir_root
    if args.corpus_config:
        cfg = load_json(args.corpus_config)
        parquet_path = parquet_path or (
            Path(p) if (p := cfg.get("parquet")) else None
        )
        if maildir_root is None and cfg.get("maildir_root"):
            maildir_root = Path(cfg["maildir_root"])

    tasks: list[dict[str, Any]] = []
    if args.demo:
        tasks = run_demo(registry)
    elif parquet_path:
        if not parquet_path.is_file():
            print(f"Not a file: {parquet_path}", file=sys.stderr)
            return 1
        msgs = iter_parquet_messages(
            parquet_path,
            maildir_root,
            args.max_rows,
        )
        tasks = build_tasks_from_messages(
            msgs,
            hints,
            registry,
            args.min_messages,
            args.max_threads,
            source_label="parquet",
            subject_day_bucket=args.bucket_mailbox_subject_day,
        )
    elif args.maildir:
        if not args.maildir.is_dir():
            print(f"Not a directory: {args.maildir}", file=sys.stderr)
            return 1
        parsed: list[dict[str, Any]] = []
        for p in maildir_messages(args.maildir):
            m = read_message(p)
            if m:
                parsed.append(m)
        tasks = build_tasks_from_messages(
            parsed,
            hints,
            registry,
            args.min_messages,
            args.max_threads,
            source_label="maildir",
            subject_day_bucket=args.bucket_mailbox_subject_day,
        )
    else:
        ap.print_help()
        print(
            "\nProvide --demo, --maildir, --parquet, or --corpus-config "
            "(see corpus/corpus_config.json).",
            file=sys.stderr,
        )
        return 1

    lines = [json.dumps(t, ensure_ascii=False) for t in tasks]
    text = "\n".join(lines) + ("\n" if lines else "")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {len(tasks)} tasks to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
