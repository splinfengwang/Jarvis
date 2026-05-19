#!/usr/bin/env python3
"""Synchronize Topic status across index, snapshot, and dashboard."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from jarvis.lib import (
    STATUS_DISPLAY,
    add_common_args,
    apply_changes,
    dashboard_path,
    ensure_single_line_update,
    prepare_change,
    print_validation,
    read_text,
    set_frontmatter_status,
    sync_dashboard_topic_status,
    vault_root,
    now_date,
)


def update_snapshot_status(text: str, status: str, note: str) -> str:
    display = STATUS_DISPLAY[status]
    if "> **状态**:" in text:
        text = __import__("re").sub(r"(?m)^> \*\*状态\*\*: .*$", f"> **状态**: {display}", text, count=1)
    else:
        text = text.rstrip() + f"\n\n> **状态**: {display}\n"
    if note:
        marker = "## 5. 下一步动作"
        bullet = f"- {note}"
        if marker in text and bullet not in text:
            return text.replace(marker, marker + "\n\n" + bullet, 1)
    return text


def update_index_status(text: str, status: str, note: str) -> str:
    display = STATUS_DISPLAY[status]
    if "## 当前状态" not in text:
        text = text.rstrip() + f"\n\n## 当前状态\n\n- **阶段**：{display}\n- **Next Action**：{note or '待补充'}\n"
        return text
    text = re.sub(r"(?m)^- \*\*阶段\*\*：.*$", f"- **阶段**：{display}", text, count=1)
    if note and re.search(r"(?m)^- \*\*Next Action\*\*：.*$", text):
        text = re.sub(r"(?m)^- \*\*Next Action\*\*：.*$", f"- **Next Action**：{note}", text, count=1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--topic-dir", required=True)
    parser.add_argument("--status", required=True, choices=sorted(STATUS_DISPLAY))
    parser.add_argument("--note", default="")
    parser.add_argument("--blocker", default="")
    parser.add_argument("--recovery", default="")
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    topic_dir = Path(args.topic_dir)
    if not topic_dir.is_absolute():
        topic_dir = (root / topic_dir).resolve()
    index = topic_dir / "索引.md"
    snapshot = topic_dir / "_上下文快照.md"
    dash = dashboard_path(root)

    errors: list[str] = []
    if args.status == "blocked" and (not args.blocker or not args.recovery):
        errors.append("blocked status requires --blocker and --recovery")
    for path in [index, snapshot, dash]:
        if not path.exists():
            errors.append(f"missing file: {path}")
    if errors:
        return print_validation(errors)

    note = args.note
    if args.status == "blocked":
        note = note or f"阻塞物：{args.blocker}；恢复条件：{args.recovery}"

    index_after = update_index_status(set_frontmatter_status(read_text(index), args.status), args.status, note)
    snapshot_after = update_snapshot_status(read_text(snapshot), args.status, note)
    topic_rel = (topic_dir / "索引.md").relative_to(root).as_posix()
    dashboard_before = read_text(dash)
    dashboard_after, changed = sync_dashboard_topic_status(
        dashboard_before,
        topic_rel,
        STATUS_DISPLAY[args.status],
        now_date(),
        note or "待补充",
    )
    if not changed:
        errors.append(f"topic row not found in dashboard: {topic_rel}")
        return print_validation(errors)
    if len(dashboard_before.splitlines()) == len(dashboard_after.splitlines()):
        try:
            ensure_single_line_update(dashboard_before, dashboard_after, "dashboard topic status update")
        except SystemExit:
            # Row moves between sections change two lines; still permitted for status lifecycle transitions.
            pass

    changes = [
        prepare_change(index, index_after),
        prepare_change(snapshot, snapshot_after),
        prepare_change(dash, dashboard_after),
    ]
    apply_changes(changes, args.write)

    if args.write:
        if f"status: {args.status}" not in read_text(index):
            errors.append("index frontmatter status not updated")
        if STATUS_DISPLAY[args.status] not in read_text(snapshot):
            errors.append("snapshot display status not updated")
        if STATUS_DISPLAY[args.status] not in read_text(dash):
            errors.append("dashboard display status not updated")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
