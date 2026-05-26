#!/usr/bin/env python3
"""Scan knowledge base for stale 待确认 terms (>14 days without update)."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import get_path, list_markdown_files, print_validation, read_text, vault_root, write_json_result


STALE_DAYS = 14


def extract_status(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("status:") or line.startswith("status："):
            return line.split(":", 1)[-1].split("：", 1)[-1].strip()
    return None


def extract_frontmatter_date(text: str) -> str | None:
    """Extract date from frontmatter fields like created, extracted_at, updated."""
    for key in ("created:", "extracted_at:", "updated:", "date:"):
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(key):
                return line.split(":", 1)[-1].strip()
    return None


def file_mtime_days_ago(path: Path) -> int:
    mtime = path.stat().st_mtime
    mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    return (now - mtime_dt).days


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--stale-days", type=int, default=STALE_DAYS, help=f"Days threshold (default {STALE_DAYS})")
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    term_dir = get_path("terms_dir", root)
    if not term_dir.exists():
        return print_validation([f"term directory not found: {term_dir}"])

    stale_terms: list[dict] = []
    total_terms = 0
    total_pending = 0

    for md in list_markdown_files(term_dir):
        total_terms += 1
        text = read_text(md)
        status = extract_status(text)
        if status != "待确认":
            continue
        total_pending += 1
        age_days = file_mtime_days_ago(md)
        if age_days >= args.stale_days:
            stale_terms.append({
                "path": md.relative_to(root).as_posix(),
                "title": md.stem,
                "status": status,
                "age_days": age_days,
                "last_modified": datetime.fromtimestamp(md.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d"),
                "suggested_action": "林峰确认内容后更新 status 为 已确认，或标记为 已废弃",
            })

    payload = {
        "total_terms": total_terms,
        "pending_terms": total_pending,
        "stale_threshold_days": args.stale_days,
        "stale_count": len(stale_terms),
        "stale_terms": stale_terms,
    }

    print("plan:")
    print(f"- scan term health: {term_dir}")
    print(f"- stale threshold: {args.stale_days} days")
    print(f"\ndiff preview:")
    print("(read-only)")
    write_json_result(payload)

    warnings = [f"{len(stale_terms)} stale 待确认 terms (>{args.stale_days}d)"] if stale_terms else []
    return print_validation([], warnings)


if __name__ == "__main__":
    raise SystemExit(main())