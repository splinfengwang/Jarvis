#!/usr/bin/env python3
"""Shared helpers for Jarvis v1.0 scripts."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


STATUS_DISPLAY = {
    "doing": "[🟢 Doing]",
    "paused": "[🟡 Paused]",
    "blocked": "[🔴 Blocked]",
    "pending_extraction": "[📋 待萃取]",
    "done": "[⚪ Done]",
}

DISPLAY_TO_STATUS = {v: k for k, v in STATUS_DISPLAY.items()}

# Default paths — used as fallback when jarvis.yaml is missing
_DEFAULT_PATHS: dict[str, str] = {
    "knowledge_base": "知识库",
    "wiki_index": "知识库/wiki索引.md",
    "terms_dir": "知识库/术语",
    "terms_index": "知识库/术语/术语索引.md",
    "business_dir": "业务",
    "ops_dir": "platform-ops",
    "dashboard": "platform-ops/仪表盘.md",
    "log": "platform-ops/log.md",
    "topics": "platform-ops/topics",
}

_config_cache: dict[str, dict] = {}


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for jarvis.yaml — no PyYAML dependency.

    Handles top-level scalars, lists, and one-level-deep mappings (paths section).
    """
    result: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        # Nested mapping (indented key: value) — paths section
        if line.startswith('  ') and ':' in stripped and not stripped.startswith('-'):
            i += 1
            continue  # handled by section parsers below
        # List item
        if stripped.startswith('- '):
            i += 1
            continue  # handled by section parsers below
        # Top-level key: value
        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value == '':
                # Could be start of a mapping section or list
                result[key] = _parse_section(lines, i)
            else:
                result[key] = value
        i += 1
    return result


def _parse_section(lines: list[str], start: int) -> dict | list:
    """Parse an indented mapping or list section starting at start+1."""
    section: dict = {}
    section_list: list = []
    is_list = False
    i = start + 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            i += 1
            continue
        if not line.startswith('  '):
            break
        if stripped.startswith('- '):
            is_list = True
            section_list.append(stripped[2:].strip().strip('"').strip("'"))
        elif ':' in stripped:
            k, _, v = stripped.partition(':')
            section[k.strip()] = v.strip().strip('"').strip("'")
        i += 1
    if is_list:
        return section_list
    return section


def load_jarvis_config(root: Path) -> dict:
    """Load jarvis.yaml from project root. Returns parsed config dict.

    Result is cached per root path so repeated calls are cheap.
    """
    root_key = str(root.resolve())
    if root_key in _config_cache:
        return _config_cache[root_key]
    config_path = root / "jarvis.yaml"
    if config_path.is_file():
        try:
            _config_cache[root_key] = _parse_simple_yaml(config_path.read_text(encoding="utf-8"))
        except Exception:
            _config_cache[root_key] = {}
    else:
        _config_cache[root_key] = {}
    return _config_cache[root_key]


def get_path(key: str, root: Path | None = None) -> Path:
    """Get a configured path. Falls back to default if jarvis.yaml missing or key absent.

    Args:
        key: Path key (e.g. 'dashboard', 'wiki_index', 'topics')
        root: Project root. Defaults to current working directory.
    """
    if root is None:
        root = Path.cwd()
    config = load_jarvis_config(root)
    paths = config.get("paths", {})
    if isinstance(paths, dict) and key in paths:
        return root / paths[key]
    return root / _DEFAULT_PATHS.get(key, key)


SESSION_TABLE_HEADER = "| 工具 | 会话标识 | JSONL 路径 | 工作区路径 | 日期 |"
SESSION_TABLE_SEPARATOR = "|------|------|------|------|------|"
DASHBOARD_TOPIC_HEADER = "| 状态 | Topic | 上次更新 | 下一步 | |"
DASHBOARD_TOPIC_SEPARATOR = "|---|---|---|---|---|"


@dataclass
class Change:
    path: Path
    before: str
    after: str

    def diff(self) -> str:
        before_lines = self.before.splitlines(keepends=True)
        after_lines = self.after.splitlines(keepends=True)
        return "".join(
            difflib.unified_diff(
                before_lines,
                after_lines,
                fromfile=f"{self.path} (before)",
                tofile=f"{self.path} (after)",
                lineterm="",
            )
        )


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--vault-root",
        default=".",
        help="Vault/repo root. Defaults to current working directory.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Actually write changes. Default is dry-run.",
    )


def add_session_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--session-tool", default="待确认", help="Session tool name, e.g. Codex Desktop or Claude Code.")
    parser.add_argument("--session-id", default="待确认", help="Session/thread identifier when known.")
    parser.add_argument("--session-jsonl", default="待确认", help="Resolved JSONL path, or 待确认 when not resolved.")
    parser.add_argument("--session-cwd", default="", help="Workspace path for the session. Defaults to vault root.")
    parser.add_argument("--session-date", default="", help="Session date. Defaults to today.")


def vault_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_compact_date() -> str:
    return datetime.now().strftime("%Y%m%d")


def table_cell(value: str) -> str:
    value = str(value or "待确认").replace("\n", " ").strip()
    return value.replace("|", "\\|") or "待确认"


def build_session_row(tool: str, session_id: str, jsonl_path: str, cwd: str, date: str) -> str:
    return (
        f"| {table_cell(tool)} | {table_cell(session_id)} | {table_cell(jsonl_path)} | "
        f"{table_cell(cwd)} | {table_cell(date)} |"
    )


def normalize_table_row(row: str) -> str:
    return row.replace("`", "").replace("\\|", "|").strip()


def append_session_row(text: str, session_row: str) -> str:
    if not session_row:
        return text
    if session_row in text:
        return text
    normalized_session_row = normalize_table_row(session_row)
    for line in text.splitlines():
        if normalize_table_row(line) == normalized_session_row:
            return text
    lines = text.splitlines()
    heading_index = None
    for i, line in enumerate(lines):
        if line.strip() == "## 6. 关联会话":
            heading_index = i
            break
    if heading_index is None:
        suffix = "\n" if text.endswith("\n") else ""
        return (
            text.rstrip()
            + "\n\n## 6. 关联会话\n\n"
            + SESSION_TABLE_HEADER
            + "\n"
            + SESSION_TABLE_SEPARATOR
            + "\n"
            + session_row
            + "\n"
            + suffix
        )
    insert_at = heading_index + 1
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1
    if insert_at >= len(lines) or lines[insert_at].strip() != SESSION_TABLE_HEADER:
        lines.insert(insert_at, SESSION_TABLE_SEPARATOR)
        lines.insert(insert_at, SESSION_TABLE_HEADER)
        insert_at += 2
    elif insert_at + 1 >= len(lines) or not lines[insert_at + 1].strip().startswith("|---"):
        lines.insert(insert_at + 1, SESSION_TABLE_SEPARATOR)
        insert_at += 1
    else:
        insert_at += 1
    table_end = insert_at + 1
    while table_end < len(lines) and lines[table_end].strip().startswith("|"):
        table_end += 1
    lines.insert(table_end, session_row)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def safe_topic_slug(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|#\[\]\n\r\t]+", "", title).strip()
    cleaned = re.sub(r"\s+", "", cleaned)
    if not cleaned:
        raise SystemExit("validation result: failed - empty topic title after sanitizing")
    return cleaned


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def ensure_not_agent(path: Path) -> None:
    if path.name == "AGENT.md" or "/AGENT.md" in path.as_posix():
        raise SystemExit(f"refuse to modify high-risk file: {path}")


def prepare_change(path: Path, after: str) -> Change:
    ensure_not_agent(path)
    before = read_text(path)
    return Change(path=path, before=before, after=after)


def apply_changes(changes: Iterable[Change], write: bool) -> None:
    changes = list(changes)
    print("mode:", "write" if write else "dry-run")
    print("plan:")
    for change in changes:
        action = "update" if change.path.exists() else "create"
        print(f"- {action}: {change.path}")
    print("\ndiff preview:")
    for change in changes:
        diff = change.diff()
        print(diff if diff else f"(no content change) {change.path}\n")
    if write:
        for change in changes:
            ensure_not_agent(change.path)
            change.path.parent.mkdir(parents=True, exist_ok=True)
            change.path.write_text(change.after, encoding="utf-8")


def ensure_single_line_insert(before: str, after: str, label: str) -> None:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    if len(after_lines) != len(before_lines) + 1:
        raise SystemExit(f"validation result: failed - {label} must insert exactly one line")
    i = 0
    j = 0
    skipped = 0
    while i < len(before_lines) and j < len(after_lines):
        if before_lines[i] == after_lines[j]:
            i += 1
            j += 1
            continue
        skipped += 1
        j += 1
        if skipped > 1:
            raise SystemExit(f"validation result: failed - {label} changes more than one inserted line")
    if skipped > 1:
        raise SystemExit(f"validation result: failed - {label} changes more than one inserted line")


def ensure_single_line_update(before: str, after: str, label: str) -> None:
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    if len(before_lines) != len(after_lines):
        raise SystemExit(f"validation result: failed - {label} must not add or remove lines")
    changed = sum(1 for before_line, after_line in zip(before_lines, after_lines) if before_line != after_line)
    if changed > 1:
        raise SystemExit(f"validation result: failed - {label} changes {changed} lines; expected at most one")


def trash_path(path: str | Path) -> bool:
    """Move a file or directory to the macOS Trash.

    Uses AppleScript (Finder) so the item can be Put Back.  On non-macOS
    or when AppleScript is unavailable, falls back to a rename into
    ``~/.Trash`` (no Put Back support).

    Returns True if the item was successfully moved to Trash.
    """
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return False

    # Primary: AppleScript Finder (supports Put Back)
    try:
        import subprocess

        script = (
            'tell application "Finder" to delete '
            f'(POSIX file "{target}" as alias)'
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and not target.exists():
            return True
    except Exception:
        pass

    # Fallback: mv to ~/.Trash (no Put Back, but still recoverable)
    trash_dir = Path.home() / ".Trash"
    if trash_dir.is_dir():
        dest = trash_dir / target.name
        # Avoid overwriting: append timestamp
        if dest.exists():
            from datetime import datetime
            ts = datetime.now().strftime("%H%M%S")
            dest = trash_dir / f"{target.stem}_{ts}{target.suffix}"
        try:
            target.rename(dest)
            return True
        except OSError:
            pass

    return False


def print_validation(errors: list[str], warnings: list[str] | None = None) -> int:
    warnings = warnings or []
    print("\nvalidation result:")
    for warning in warnings:
        print(f"- warning: {warning}")
    if errors:
        for error in errors:
            print(f"- failed: {error}")
        return 1
    print("- passed")
    return 0


def dashboard_path(root: Path) -> Path:
    return get_path("dashboard", root)


def topics_root(root: Path) -> Path:
    return get_path("topics", root)


def escape_wikilink_pipe(text: str) -> str:
    return text.replace("|", "\\|")


def obsidian_link_for_topic(topic_dir: Path, title: str, root: Path) -> str:
    index_path = topic_dir / "索引.md"
    rel = index_path.relative_to(root).as_posix()
    return f"[[{escape_wikilink_pipe(rel)}\\|{escape_wikilink_pipe(title)}]]"


def split_markdown_table_row(row: str) -> list[str]:
    stripped = row.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    parts: list[str] = []
    current = []
    escaped = False
    for char in stripped[1:-1]:
        if char == "\\" and not escaped:
            escaped = True
            current.append(char)
            continue
        if char == "|" and not escaped:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        escaped = False
    parts.append("".join(current).strip())
    return parts


def dashboard_table_bounds(text: str, heading: str, required: bool = True) -> tuple[int, int] | None:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i
            break
    if start is None:
        if required:
            raise SystemExit(f"validation result: failed - missing {heading} section")
        return None
    table_start = None
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            break
        if lines[i].strip().startswith("|"):
            table_start = i
            break
    if table_start is None:
        if required:
            raise SystemExit(f"validation result: failed - missing table under {heading}")
        return None
    table_end = table_start
    for i in range(table_start, len(lines)):
        if not lines[i].strip().startswith("|"):
            break
        table_end = i
    return table_start, table_end


def active_topic_table_bounds(text: str) -> tuple[int, int]:
    bounds = dashboard_table_bounds(text, "## 活跃 Topic", required=True)
    assert bounds is not None
    return bounds


def ensure_dashboard_section(text: str, heading: str, before_heading: str) -> str:
    if f"\n{heading}\n" in f"\n{text}":
        return text
    lines = text.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == before_heading:
            insert_at = i
            break
    section = [
        heading,
        "",
        DASHBOARD_TOPIC_HEADER,
        DASHBOARD_TOPIC_SEPARATOR,
    ]
    if insert_at > 0 and lines[insert_at - 1].strip():
        section.insert(0, "")
    if insert_at < len(lines) and lines[insert_at].strip():
        section.append("")
    lines[insert_at:insert_at] = section
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def append_active_topic_row(dashboard: str, row: str) -> str:
    lines = dashboard.splitlines()
    _, table_end = active_topic_table_bounds(dashboard)
    lines.insert(table_end + 1, row)
    return "\n".join(lines) + ("\n" if dashboard.endswith("\n") else "")


def topic_rel_variants(topic_rel: str) -> set[str]:
    variants = {topic_rel}
    if topic_rel.endswith(".md"):
        variants.add(topic_rel[:-3])
    else:
        variants.add(topic_rel + ".md")
    return variants


def row_matches_topic(row: str, topic_rel: str) -> bool:
    return any(variant in row for variant in topic_rel_variants(topic_rel))


def format_dashboard_row(cells: list[str]) -> str:
    while len(cells) < 5:
        cells.append("")
    return "| " + " | ".join(cells[:5]) + " |"


def update_dashboard_row_text(row: str, status_display: str, update_date: str, next_action: str) -> str | None:
    cells = split_markdown_table_row(row)
    if len(cells) < 4:
        return None
    while len(cells) < 5:
        cells.append("")
    cells[0] = status_display
    cells[2] = update_date
    cells[3] = next_action
    return format_dashboard_row(cells)


def find_dashboard_row(lines: list[str], bounds: tuple[int, int] | None, topic_rel: str) -> int | None:
    if bounds is None:
        return None
    table_start, table_end = bounds
    for i in range(table_start + 2, table_end + 1):
        if row_matches_topic(lines[i], topic_rel):
            return i
    return None


def insert_dashboard_row(lines: list[str], bounds: tuple[int, int], row: str) -> None:
    _, table_end = bounds
    lines.insert(table_end + 1, row)


def update_dashboard_topic_row(
    dashboard: str,
    topic_rel: str,
    status_display: str,
    update_date: str,
    next_action: str,
) -> tuple[str, bool]:
    lines = dashboard.splitlines()
    table_start, table_end = active_topic_table_bounds(dashboard)
    changed = False
    for i in range(table_start + 2, table_end + 1):
        if row_matches_topic(lines[i], topic_rel):
            updated = update_dashboard_row_text(lines[i], status_display, update_date, next_action)
            if updated is None:
                continue
            lines[i] = updated
            changed = True
            break
    return "\n".join(lines) + ("\n" if dashboard.endswith("\n") else ""), changed


def sync_dashboard_topic_status(
    dashboard: str,
    topic_rel: str,
    status_display: str,
    update_date: str,
    next_action: str,
) -> tuple[str, bool]:
    if status_display == STATUS_DISPLAY["pending_extraction"]:
        dashboard = ensure_dashboard_section(dashboard, "## 待萃取", "## 已归档")
    lines = dashboard.splitlines()
    active_bounds = dashboard_table_bounds(dashboard, "## 活跃 Topic", required=True)
    pending_bounds = dashboard_table_bounds(dashboard, "## 待萃取", required=False)
    target_bounds = pending_bounds if status_display == STATUS_DISPLAY["pending_extraction"] else active_bounds
    source_bounds = active_bounds if status_display == STATUS_DISPLAY["pending_extraction"] else pending_bounds

    target_index = find_dashboard_row(lines, target_bounds, topic_rel)
    if target_index is not None:
        updated = update_dashboard_row_text(lines[target_index], status_display, update_date, next_action)
        if updated is None:
            return dashboard, False
        lines[target_index] = updated
        return "\n".join(lines) + ("\n" if dashboard.endswith("\n") else ""), True

    source_index = find_dashboard_row(lines, source_bounds, topic_rel)
    if source_index is None:
        return dashboard, False
    updated = update_dashboard_row_text(lines[source_index], status_display, update_date, next_action)
    if updated is None or target_bounds is None:
        return dashboard, False
    del lines[source_index]
    dashboard_after_delete = "\n".join(lines) + ("\n" if dashboard.endswith("\n") else "")
    target_bounds = dashboard_table_bounds(
        dashboard_after_delete,
        "## 待萃取" if status_display == STATUS_DISPLAY["pending_extraction"] else "## 活跃 Topic",
        required=True,
    )
    assert target_bounds is not None
    lines = dashboard_after_delete.splitlines()
    insert_dashboard_row(lines, target_bounds, updated)
    return "\n".join(lines) + ("\n" if dashboard.endswith("\n") else ""), True


def read_frontmatter_status(text: str) -> str | None:
    match = re.search(r"(?m)^status:\s*([A-Za-z0-9_-]+)\s*$", text)
    return match.group(1) if match else None


def set_frontmatter_status(text: str, status: str) -> str:
    if re.search(r"(?m)^status:\s*[A-Za-z0-9_-]+\s*$", text):
        return re.sub(r"(?m)^status:\s*[A-Za-z0-9_-]+\s*$", f"status: {status}", text, count=1)
    if text.startswith("---\n"):
        return text.replace("---\n", f"---\nstatus: {status}\n", 1)
    return f"---\nstatus: {status}\n---\n\n{text}"


def write_json_result(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def list_markdown_files(root: Path) -> list[Path]:
    ignored = {".git", "node_modules", ".obsidian", ".trash"}
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignored]
        for filename in filenames:
            if filename.endswith(".md"):
                files.append(Path(dirpath) / filename)
    return files
