#!/usr/bin/env python3
"""Synchronize Topic index frontmatter, key outputs, and timeline."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from jarvis.lib import (
    STATUS_DISPLAY,
    add_common_args,
    apply_changes,
    now_date,
    prepare_change,
    print_validation,
    read_text,
    set_frontmatter_status,
    vault_root,
)


def ensure_heading(text: str, heading: str, default_lines: list[str]) -> str:
    if heading in text:
        return text
    suffix = "\n" if text.endswith("\n") else ""
    return text.rstrip() + "\n\n" + heading + "\n\n" + "\n".join(default_lines) + "\n" + suffix


def replace_status_block(text: str, status: str, next_action: str | None) -> str:
    text = ensure_heading(text, "## 当前状态", [f"- **阶段**：{STATUS_DISPLAY[status]}", "- **Next Action**：待补充"])
    text = re.sub(r"(?m)^- \*\*阶段\*\*：.*$", f"- **阶段**：{STATUS_DISPLAY[status]}", text, count=1)
    if next_action:
        if re.search(r"(?m)^- \*\*Next Action\*\*：.*$", text):
            text = re.sub(r"(?m)^- \*\*Next Action\*\*：.*$", f"- **Next Action**：{next_action}", text, count=1)
        else:
            text = text.replace("## 当前状态", f"## 当前状态\n\n- **Next Action**：{next_action}", 1)
    return text


def append_unique_bullets(text: str, heading: str, bullets: list[str]) -> str:
    bullets = [bullet.strip() for bullet in bullets if bullet.strip()]
    if not bullets:
        return text
    text = ensure_heading(text, heading, ["- 暂无。"])
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return text
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if i > start + 1 and lines[i].startswith("## "):
            end = i
            break
    existing = {line.strip()[2:].strip() for line in lines[start + 1:end] if line.strip().startswith("- ")}
    insert_at = end
    if "- 暂无。" in lines[start + 1:end]:
        lines = [line for line in lines if line != "- 暂无。"]
        insert_at = len(lines)
        for i in range(start + 1, len(lines)):
            if i > start + 1 and lines[i].startswith("## "):
                insert_at = i
                break
    for bullet in bullets:
        if bullet not in existing:
            lines.insert(insert_at, f"- {bullet}")
            insert_at += 1
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def append_timeline(text: str, date: str, entries: list[str]) -> str:
    entries = [entry.strip() for entry in entries if entry.strip()]
    if not entries:
        return text
    timeline_bullets = [f"{date} {entry}" for entry in entries]
    return append_unique_bullets(text, "## 时间线", timeline_bullets)


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--topic-dir", required=True)
    parser.add_argument("--status", choices=sorted(STATUS_DISPLAY))
    parser.add_argument("--next-action", default="")
    parser.add_argument("--key-output", action="append", default=[])
    parser.add_argument("--timeline", action="append", default=[])
    parser.add_argument("--date", default=now_date())
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    topic_dir = Path(args.topic_dir)
    if not topic_dir.is_absolute():
        topic_dir = (root / topic_dir).resolve()
    index = topic_dir / "索引.md"
    if not index.exists():
        return print_validation([f"missing index: {index}"])

    text = read_text(index)
    status = args.status or "doing"
    text = set_frontmatter_status(text, status)
    text = replace_status_block(text, status, args.next_action or None)
    text = append_unique_bullets(text, "## 关键产出", args.key_output)
    text = append_timeline(text, args.date, args.timeline)

    change = prepare_change(index, text)
    apply_changes([change], args.write)

    errors: list[str] = []
    if args.write:
        written = read_text(index)
        if f"status: {status}" not in written:
            errors.append("index status not updated")
        if args.next_action and args.next_action not in written:
            errors.append("index next action not updated")
        for item in args.key_output + [f"{args.date} {entry}" for entry in args.timeline]:
            if item and item not in written:
                errors.append(f"index missing expected entry: {item}")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
