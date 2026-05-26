#!/usr/bin/env python3
"""Locate Codex Desktop or Claude Code JSONL session transcripts."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import print_validation, write_json_result


def candidate_roots(tool: str, home: Path) -> list[Path]:
    if tool == "codex":
        return [home / ".codex" / "sessions", home / ".Codex" / "projects"]
    if tool == "claude-code":
        return [home / ".claude" / "projects", home / ".claude" / "sessions"]
    raise ValueError(tool)


def matches_date(path: Path, date: str | None) -> bool:
    if not date:
        return True
    compact = date.replace("-", "/")
    return date in path.as_posix() or compact in path.as_posix()


def contains_cwd(path: Path, cwd: str) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if cwd in line:
                    return True
    except OSError:
        return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True, choices=["codex", "claude-code"])
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--date", default="")
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()

    home = Path(args.home).expanduser().resolve()
    files: list[Path] = []
    for root in candidate_roots(args.tool, home):
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*.jsonl") if matches_date(path, args.date or None))

    matched = [path for path in files if contains_cwd(path, args.cwd)]
    matched.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    payload = {
        "tool": args.tool,
        "cwd": args.cwd,
        "date": args.date or None,
        "match_count": len(matched),
        "matches": [
            {
                "path": str(path),
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            }
            for path in matched[:20]
        ],
    }
    print("plan:")
    print(f"- locate {args.tool} session transcripts under {home}")
    print("\ndiff preview:")
    print("(read-only)")
    write_json_result(payload)
    errors = [] if matched else ["no matching session transcript found"]
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
