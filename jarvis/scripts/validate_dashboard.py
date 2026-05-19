#!/usr/bin/env python3
"""Validate Jarvis dashboard table shape, status values, and Topic links."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from jarvis.lib import STATUS_DISPLAY, dashboard_path, dashboard_table_bounds, print_validation, read_text, split_markdown_table_row, vault_root


def validate_topic_table(root: Path, lines: list[str], table_start: int, table_end: int, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    header_cells = split_markdown_table_row(lines[table_start])
    expected = len(header_cells)
    if expected < 4:
        errors.append(f"{label} table has fewer than 4 columns")
    allowed_statuses = set(STATUS_DISPLAY.values())
    for line_no in range(table_start + 2, table_end + 1):
        row = lines[line_no]
        cells = split_markdown_table_row(row)
        if len(cells) != expected:
            if len(cells) == expected - 1 and header_cells[-1] == "":
                warnings.append(f"line {line_no + 1}: missing trailing empty column")
            else:
                errors.append(f"line {line_no + 1}: expected {expected} columns, got {len(cells)}")
        if cells and cells[0] not in allowed_statuses:
            errors.append(f"line {line_no + 1}: invalid status {cells[0]}")
        for link in re.findall(r"\[\[([^|\\\]]+)(?:\\?\|[^\]]+)?\]\]", row):
            if link.startswith("http"):
                continue
            target = root / link
            if not target.exists() and not target.with_suffix(".md").exists():
                warnings.append(f"line {line_no + 1}: topic link target not found: {link}")
    return errors, warnings


def validate_followup_table(lines: list[str], table_start: int, table_end: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    header_cells = split_markdown_table_row(lines[table_start])
    expected = len(header_cells)
    for line_no in range(table_start + 2, table_end + 1):
        row = lines[line_no]
        cells = split_markdown_table_row(row)
        if len(cells) != expected:
            errors.append(f"line {line_no + 1}: follow-up row expected {expected} columns, got {len(cells)}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", default=".")
    args = parser.parse_args()
    root = vault_root(args.vault_root)
    dash = dashboard_path(root)
    if not dash.exists():
        return print_validation([f"dashboard not found: {dash}"])
    text = read_text(dash)
    errors: list[str] = []
    warnings: list[str] = []
    lines = text.splitlines()
    for heading, label, required in [
        ("## 活跃 Topic", "active topic", True),
        ("## 待萃取", "pending extraction", True),
    ]:
        try:
            bounds = dashboard_table_bounds(text, heading, required=required)
        except SystemExit as exc:
            return print_validation([str(exc)])
        if bounds is None:
            continue
        table_errors, table_warnings = validate_topic_table(root, lines, bounds[0], bounds[1], label)
        errors.extend(table_errors)
        warnings.extend(table_warnings)
    followup_bounds = dashboard_table_bounds(text, "## 跟进事项", required=False)
    if followup_bounds is not None:
        table_errors, table_warnings = validate_followup_table(lines, followup_bounds[0], followup_bounds[1])
        errors.extend(table_errors)
        warnings.extend(table_warnings)
    print("plan:")
    print(f"- validate dashboard: {dash}")
    print("\ndiff preview:")
    print("(read-only)")
    return print_validation(errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
