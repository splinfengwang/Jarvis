#!/usr/bin/env python3
"""Append one entry to the project log (configured in jarvis.yaml)."""

from __future__ import annotations

import argparse

from jarvis.lib import (
    add_common_args,
    apply_changes,
    ensure_single_line_insert,
    get_path,
    now_date,
    prepare_change,
    print_validation,
    read_text,
    vault_root,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--type", required=True, choices=["topic", "status", "freeze", "close", "ingest", "lint", "other"])
    parser.add_argument("--summary", required=True)
    parser.add_argument("--date", default=now_date())
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    log = get_path("log", root)
    before = read_text(log)
    if not before:
        before = "# 操作日志\n\n> append-only 操作记录。格式：`## [YYYY-MM-DD] 操作类型 | 简述`\n\n---\n"
    entry = f"## [{args.date}] {args.type} | {args.summary}"
    if entry in before:
        after = before
    else:
        after = before.rstrip() + "\n" + entry + "\n"
    if after != before:
        ensure_single_line_insert(before, after, "operation log append")

    change = prepare_change(log, after)
    apply_changes([change], args.write)

    errors: list[str] = []
    if args.write and entry not in read_text(log):
        errors.append("operation log entry not found after write")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
