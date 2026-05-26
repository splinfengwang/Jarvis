#!/usr/bin/env python3
"""Append application feedback to a knowledge file and optionally update status."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import add_common_args, apply_changes, prepare_change, print_validation, read_text, set_frontmatter_status, vault_root


def ensure_feedback_section(text: str) -> str:
    if "## 应用反馈" in text:
        return text
    suffix = "\n" if text.endswith("\n") else ""
    return text.rstrip() + "\n\n## 应用反馈\n\n- 暂无。\n" + suffix


def append_feedback(text: str, feedback: str, date: str) -> str:
    text = ensure_feedback_section(text)
    line = f"- {date} {feedback}"
    if line in text:
        return text
    text = text.replace("- 暂无。", "", 1)
    lines = text.splitlines()
    try:
        idx = lines.index("## 应用反馈")
    except ValueError:
        return text.rstrip() + "\n\n## 应用反馈\n\n" + line + "\n"
    insert_at = idx + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    lines.insert(insert_at, line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def update_index_status(text: str, title: str, status: str) -> str:
    lines = text.splitlines()
    changed = False
    for i, line in enumerate(lines):
        if title in line and line.strip().startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                cells[2] = status
                lines[i] = "| " + " | ".join(cells[:3]) + " |"
                changed = True
    return ("\n".join(lines) + ("\n" if text.endswith("\n") else "")) if changed else text


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--path", required=True)
    parser.add_argument("--feedback", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--status", default="")
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    path = Path(args.path)
    if not path.is_absolute():
        path = (root / path).resolve()
    if not path.exists():
        return print_validation([f"knowledge file not found: {path}"])

    text = read_text(path)
    title = path.stem
    if args.status:
        text = set_frontmatter_status(text, args.status)
    text = append_feedback(text, args.feedback, args.date)

    changes = [prepare_change(path, text)]
    if args.status:
        for index_path in [
            root / "知识库" / "wiki索引.md",
            root / "知识库" / "术语" / "术语索引.md",
        ]:
            if index_path.exists():
                changes.append(prepare_change(index_path, update_index_status(read_text(index_path), title, args.status)))
    apply_changes(changes, args.write)

    errors: list[str] = []
    if args.write:
        written = read_text(path)
        if args.feedback not in written:
            errors.append("knowledge feedback not written")
        if args.status and f"status: {args.status}" not in written:
            errors.append("knowledge status not updated")
        if args.status:
            for index_path in [
                root / "知识库" / "wiki索引.md",
                root / "知识库" / "术语" / "术语索引.md",
            ]:
                if index_path.exists() and args.status not in read_text(index_path):
                    errors.append(f"index status not updated: {index_path}")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
