#!/usr/bin/env python3
"""Insert or update one follow-up row in platform-ops/仪表盘.md."""

from __future__ import annotations

import argparse

from jarvis.lib import add_common_args, apply_changes, dashboard_path, prepare_change, print_validation, read_text, split_markdown_table_row, vault_root


FOLLOWUP_HEADER = "| 事项 | 截止/窗口 | 状态 | 动作 |"
FOLLOWUP_SEPARATOR = "|---|---|---|---|"
PLACEHOLDER_ROW = "| （暂无活跃跟进事项） | — | — | — |"


def ensure_followup_section(text: str) -> str:
    if "\n## 跟进事项\n" in f"\n{text}":
        return text
    lines = text.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "## 待拍板":
            insert_at = i
            break
    section = ["", "## 跟进事项", "", FOLLOWUP_HEADER, FOLLOWUP_SEPARATOR, PLACEHOLDER_ROW, ""]
    lines[insert_at:insert_at] = section
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def followup_bounds(text: str) -> tuple[int, int]:
    lines = text.splitlines()
    heading = None
    for i, line in enumerate(lines):
        if line.strip() == "## 跟进事项":
            heading = i
            break
    if heading is None:
        raise SystemExit("validation result: failed - missing ## 跟进事项 section")
    start = None
    for i in range(heading + 1, len(lines)):
        if lines[i].strip().startswith("|"):
            start = i
            break
    if start is None:
        raise SystemExit("validation result: failed - missing follow-up table")
    end = start
    for i in range(start, len(lines)):
        if not lines[i].strip().startswith("|"):
            break
        end = i
    return start, end


def format_row(item: str, window: str, status: str, action: str) -> str:
    return f"| {item} | {window} | {status} | {action} |"


def sync_row(text: str, item: str, window: str, status: str, action: str) -> tuple[str, bool]:
    text = ensure_followup_section(text)
    lines = text.splitlines()
    start, end = followup_bounds(text)
    row = format_row(item, window, status, action)
    changed = False
    for i in range(start + 2, end + 1):
        cells = split_markdown_table_row(lines[i])
        if cells and cells[0] == item:
            lines[i] = row
            changed = True
            break
    if not changed:
        if PLACEHOLDER_ROW in lines[start + 2:end + 1]:
            lines = [line for line in lines if line != PLACEHOLDER_ROW]
            text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
            lines = text.splitlines()
            start, end = followup_bounds(text)
        lines.insert(end + 1, row)
        changed = True
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), changed


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--item", required=True)
    parser.add_argument("--window", required=True)
    parser.add_argument("--status", default="进行中")
    parser.add_argument("--action", required=True)
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    dash = dashboard_path(root)
    if not dash.exists():
        return print_validation([f"dashboard not found: {dash}"])
    before = read_text(dash)
    after, changed = sync_row(before, args.item, args.window, args.status, args.action)
    if not changed:
        return print_validation(["follow-up row not changed"])
    change = prepare_change(dash, after)
    apply_changes([change], args.write)

    errors: list[str] = []
    if args.write:
        written = read_text(dash)
        for expected in [args.item, args.window, args.status, args.action]:
            if expected not in written:
                errors.append(f"dashboard missing follow-up field: {expected}")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
