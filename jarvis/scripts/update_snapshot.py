#!/usr/bin/env python3
"""Append factual updates to a Topic snapshot without rewriting the whole Topic."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import (
    add_common_args,
    add_session_args,
    append_session_row,
    apply_changes,
    build_session_row,
    normalize_table_row,
    now_date,
    prepare_change,
    print_validation,
    read_text,
    vault_root,
)


def append_under_heading(text: str, heading: str, bullet: str) -> str:
    if not bullet:
        return text
    line = f"- {bullet}"
    if line in text:
        return text
    if heading in text:
        return text.replace(heading, heading + "\n\n" + line, 1)
    return text.rstrip() + f"\n\n{heading}\n\n{line}\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    add_session_args(parser)
    parser.add_argument("--topic-dir", required=True)
    parser.add_argument("--last-action", default="")
    parser.add_argument("--next-action", default="")
    parser.add_argument("--unresolved", default="")
    parser.add_argument("--session", default="")
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    topic_dir = Path(args.topic_dir)
    if not topic_dir.is_absolute():
        topic_dir = (root / topic_dir).resolve()
    snapshot = topic_dir / "_上下文快照.md"
    if not snapshot.exists():
        return print_validation([f"missing snapshot: {snapshot}"])

    text = read_text(snapshot)
    text = re.sub(r"(?m)^> \*\*快照时间\*\*: .*$", f"> **快照时间**: {now_date()}", text, count=1)
    text = append_under_heading(text, "## 1. 最后动作", args.last_action)
    text = append_under_heading(text, "## 5. 下一步动作", args.next_action)
    text = append_under_heading(text, "## 4. 待拍板", args.unresolved)
    expected_session = ""
    if args.session:
        expected_session = args.session
        text = append_session_row(text, args.session)
    elif any([args.session_tool != "待确认", args.session_id != "待确认", args.session_jsonl != "待确认", args.session_cwd, args.session_date]):
        session_row = build_session_row(
            args.session_tool,
            args.session_id,
            args.session_jsonl,
            args.session_cwd or str(root),
            args.session_date or now_date(),
        )
        expected_session = session_row
        text = append_session_row(text, session_row)

    change = prepare_change(snapshot, text)
    apply_changes([change], args.write)

    errors: list[str] = []
    if args.write:
        written = read_text(snapshot)
        for expected in [args.last_action, args.next_action, args.unresolved, expected_session]:
            if expected and expected_session and expected == expected_session:
                if normalize_table_row(expected) not in [normalize_table_row(line) for line in written.splitlines()]:
                    errors.append(f"snapshot missing expected text: {expected}")
            elif expected and expected not in written:
                errors.append(f"snapshot missing expected text: {expected}")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
