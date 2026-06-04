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
            v_stripped = value.strip()
            # Block scalar at top level
            if v_stripped in ("|", ">", "|-", ">-"):
                block_lines: list[str] = []
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if not nxt.strip():
                        block_lines.append("")
                        i += 1
                        continue
                    ni = len(nxt) - len(nxt.lstrip())
                    if ni < 2:
                        break
                    block_lines.append(nxt[2:])
                    i += 1
                result[key] = "\n".join(block_lines)
                continue
            value = v_stripped.strip('"').strip("'")
            if value == '':
                # Could be start of a mapping section or list
                result[key] = _parse_section_start(lines, i)
            else:
                result[key] = value
        i += 1
    return result


def _to_bool(v: object) -> bool:
    """Convert YAML string booleans to Python bool."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "yes", "1", "on")
    return bool(v)


def _parse_section_start(lines: list[str], start: int, indent: int = 2) -> dict | list:
    """Entry point for parsing an indented section. Uses a mutable counter internally."""
    i = [start + 1]
    return _parse_section(lines, i, indent)


def _parse_section(lines: list[str], i: list[int], indent: int) -> dict | list:
    """Parse an indented mapping or list, mutating i[0] as we consume lines.

    Supports nested sub-mappings (e.g. catalogs → name → {writable, description}).
    """
    section: dict = {}
    section_list: list = []
    is_list = False
    while i[0] < len(lines):
        line = lines[i[0]]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i[0] += 1
            continue
        cur_indent = len(line) - len(line.lstrip())
        if cur_indent < indent:
            break
        if stripped.startswith("- "):
            is_list = True
            section_list.append(stripped[2:].strip().strip('"').strip("'"))
            i[0] += 1
        elif ":" in stripped:
            k, _, v = stripped.partition(":")
            k = k.strip()
            v_stripped = v.strip()
            # Block scalar (| or >): read all following indented lines as one string
            if v_stripped in ("|", ">", "|-", ">-"):
                block_indent = cur_indent + 2
                block_lines: list[str] = []
                i[0] += 1
                while i[0] < len(lines):
                    nxt = lines[i[0]]
                    if not nxt.strip():
                        block_lines.append("")
                        i[0] += 1
                        continue
                    ni = len(nxt) - len(nxt.lstrip())
                    if ni < block_indent:
                        break
                    block_lines.append(nxt[block_indent:])
                    i[0] += 1
                section[k] = "\n".join(block_lines)
            else:
                v = v_stripped.strip('"').strip("'")
                if v == "":
                    # This key opens a sub-mapping
                    i[0] += 1
                    sub = _parse_section(lines, i, indent + 2)
                    section[k] = sub
                else:
                    section[k] = v
                    i[0] += 1
        else:
            i[0] += 1
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


def get_core_path(key: str, root: Path | None = None) -> Path:
    """Get a core semantic path from jarvis.yaml or defaults.

    Core paths are the 5 well-known files/dirs: dashboard, log, wiki_index,
    terms_index, topics. Use this when the path has fixed semantics that
    scripts depend on.
    """
    if root is None:
        root = Path.cwd()
    config = load_jarvis_config(root)
    core = config.get("core", {})
    if isinstance(core, dict) and key in core:
        return root / core[key]
    return root / _CORE_DEFAULTS.get(key, key)


def terms_dir(root: Path | None = None) -> Path:
    """Get the terms directory (derived from terms_index)."""
    if root is None:
        root = Path.cwd()
    rk = str(root.resolve())
    if rk in _term_dir_resolved:
        return _term_dir_resolved[rk]
    ti = get_core_path("terms_index", root)
    d = ti.parent
    _term_dir_resolved[rk] = d
    return d


def discover_catalogs(root: Path) -> dict[str, Catalog]:
    """Auto-discover all top-level non-hidden directories as catalogs."""
    catalogs: dict[str, Catalog] = {}
    try:
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            name = entry.name
            if name.startswith(".") or name in _AUTO_DISCOVER_IGNORE:
                continue
            catalogs[name] = Catalog(
                name=name,
                path=f"{name}/",
                writable=False,
                auto_discovered=True,
            )
    except OSError:
        pass
    return catalogs


def load_catalogs(root: Path | None = None) -> dict[str, Catalog]:
    """Return all catalogs: auto-discovered merged with user config from jarvis.yaml.

    User catalog config (writable, description) overrides auto-discovered defaults.
    Catalogs explicitly listed in jarvis.yaml keep their configured path.
    """
    if root is None:
        root = Path.cwd()
    rk = str(root.resolve())
    if rk in _catalog_cache:
        return _catalog_cache[rk]

    # Start with auto-discovered
    catalogs = discover_catalogs(root)

    # Overlay user config from jarvis.yaml
    config = load_jarvis_config(root)
    user_catalogs = config.get("catalogs", {})
    if isinstance(user_catalogs, dict):
        for name, cfg in user_catalogs.items():
            if isinstance(cfg, dict):
                cat_path = cfg.get("path", f"{name}/")
                catalogs[name] = Catalog(
                    name=name,
                    path=cat_path,
                    writable=_to_bool(cfg.get("writable", False)),
                    description=cfg.get("description", ""),
                    auto_discovered=(name not in catalogs),
                )

    _catalog_cache[rk] = catalogs
    return catalogs


def resolve_catalog(name: str, root: Path | None = None) -> Path | None:
    """Resolve a catalog name to its absolute path. Returns None if not found."""
    if root is None:
        root = Path.cwd()
    catalogs = load_catalogs(root)
    cat = catalogs.get(name)
    return cat.abs_path(root) if cat else None


def get_path(key: str, root: Path | None = None) -> Path:
    """Universal path resolver: core-path → catalog → defaults.

    Use this when you need a path by name. It resolves in order:
    1. core paths (dashboard, log, wiki_index, terms_index, topics)
    2. registered catalogs (auto-discovered + user-configured)
    3. fallback to raw key as relative path
    """
    if root is None:
        root = Path.cwd()
    config = load_jarvis_config(root)

    # 1. Try core paths
    core = config.get("core", {})
    if isinstance(core, dict) and key in core:
        return root / core[key]
    if key in _CORE_DEFAULTS:
        return root / _CORE_DEFAULTS[key]

    # 2. Try catalogs (auto-discovered + user-configured)
    cat = resolve_catalog(key, root)
    if cat is not None:
        return cat

    # 3. Fallback
    return root / key


def get_path_str(key: str, root: Path | None = None) -> str:
    """Like get_path but returns a string relative to root (for message display)."""
    if root is None:
        root = Path.cwd()
    p = get_path(key, root)
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def unregistered_catalogs(root: Path | None = None) -> list[Catalog]:
    """Return auto-discovered catalogs that are NOT in jarvis.yaml."""
    if root is None:
        root = Path.cwd()
    config = load_jarvis_config(root)
    user_catalogs = config.get("catalogs", {})
    if isinstance(user_catalogs, dict):
        registered = set(user_catalogs.keys())
    else:
        registered = set()
    discovered = discover_catalogs(root)
    return [c for name, c in discovered.items() if name not in registered]


def register_catalog(
    root: Path,
    name: str,
    *,
    writable: bool = False,
    description: str = "",
    catalog_path: str = "",
) -> bool:
    """Add or update a catalog entry in jarvis.yaml.

    Uses line-based editing to preserve comments, blank lines, and formatting.
    Returns True on success, False if jarvis.yaml is missing or write fails.

    Args:
        root: Project root directory.
        name: Catalog name (also used as default path).
        writable: Whether Jarvis may create/update files in this catalog.
        description: Human-readable purpose of the directory.
        catalog_path: Relative dir path (defaults to ``name/``).
    """
    config_path = root / "jarvis.yaml"
    if not config_path.is_file():
        return False
    if not catalog_path:
        catalog_path = f"{name}/"

    lines = config_path.read_text(encoding="utf-8").splitlines()

    # ── Build the entry block ──
    entry_lines = [f"  {name}:"]
    entry_lines.append(f"    writable: {'true' if writable else 'false'}")
    if description:
        entry_lines.append(f'    description: "{description}"')

    # ── Find existing entry and replace ──
    existing_start: int | None = None
    existing_end: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"{name}:") and line.startswith("  "):
            existing_start = i
            # Find end: next line at same indent or less
            for j in range(i + 1, len(lines)):
                nxt = lines[j]
                if nxt.strip() and not nxt.startswith("    "):
                    existing_end = j
                    break
            if existing_end is None:
                existing_end = len(lines)
            break

    if existing_start is not None:
        # Replace existing
        new_lines = lines[:existing_start] + entry_lines + lines[existing_end:]
    else:
        # ── Insert new: find the catalogs section end ──
        catalogs_idx: int | None = None
        for i, line in enumerate(lines):
            if line.strip() == "catalogs:":
                catalogs_idx = i
                break

        if catalogs_idx is None:
            # catalogs section doesn't exist — add it before plugins/backend
            insert_at = len(lines)
            for marker in ("plugins:", "backend:"):
                for i, line in enumerate(lines):
                    if line.strip() == marker:
                        insert_at = i
                        break
                if insert_at < len(lines):
                    break
            # Add blank line + catalogs section + entry
            section = ["", "catalogs:"] + entry_lines
            new_lines = lines[:insert_at] + section + ([""] + lines[insert_at:] if insert_at < len(lines) else [])
        else:
            # Find where catalog entries end (next unindented or less-indented section)
            insert_at = catalogs_idx + 1
            while insert_at < len(lines):
                nxt = lines[insert_at].strip()
                if not nxt:
                    insert_at += 1
                    continue
                if lines[insert_at].startswith("  ") and ':' in nxt and not nxt.startswith('- '):
                    # Still inside catalogs section
                    insert_at += 1
                    # Skip the property lines
                    while insert_at < len(lines) and lines[insert_at].startswith("    "):
                        insert_at += 1
                else:
                    break
            # Trim trailing blank lines before the insert point
            while insert_at > catalogs_idx + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            new_lines = lines[:insert_at] + [""] + entry_lines + ([""] + lines[insert_at:] if insert_at < len(lines) and lines[insert_at].strip() else [""] + lines[insert_at:])

    new_content = "\n".join(new_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"

    try:
        config_path.write_text(new_content, encoding="utf-8")
    except OSError:
        return False

    # Clear caches
    rk = str(root.resolve())
    _config_cache.pop(rk, None)
    _catalog_cache.pop(rk, None)
    return True


def register_persona(
    root: Path,
    name: str,
    *,
    title: str = "",
    icon: str = "",
    role: str = "",
    identity: str = "",
    principles: list[str] | None = None,
    analysis_lens: str = "",
    output_format: str = "",
) -> bool:
    """Add or update a persona entry in jarvis.yaml personas: section.

    Uses line-based editing, same approach as register_catalog().
    Returns True on success, False if jarvis.yaml is missing or write fails.
    """
    config_path = root / "jarvis.yaml"
    if not config_path.is_file():
        return False

    if principles is None:
        principles = []

    lines = config_path.read_text(encoding="utf-8").splitlines()

    # Build the entry block (compact YAML — inline for 1-line fields, block for multi-line)
    entry_lines = [f"  {name}:"]
    if title:
        entry_lines.append(f'    title: "{title}"')
    if icon:
        entry_lines.append(f'    icon: "{icon}"')
    if role:
        entry_lines.append(f'    role: "{role}"')
    if identity:
        entry_lines.append("    identity: |")
        for line in identity.strip().split("\n"):
            entry_lines.append(f"      {line}")
    if principles:
        entry_lines.append("    principles:")
        for p in principles:
            entry_lines.append(f'      - "{p}"')
    if analysis_lens:
        entry_lines.append("    analysis_lens: |")
        for line in analysis_lens.strip().split("\n"):
            entry_lines.append(f"      {line}")
    if output_format:
        entry_lines.append("    output_format: |")
        for line in output_format.strip().split("\n"):
            entry_lines.append(f"      {line}")

    # ── Find existing persona: entry and replace ──
    existing_start: int | None = None
    existing_end: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"{name}:") and line.startswith("  "):
            existing_start = i
            for j in range(i + 1, len(lines)):
                nxt = lines[j]
                if nxt.strip() and not nxt.startswith("    "):
                    existing_end = j
                    break
            if existing_end is None:
                existing_end = len(lines)
            break

    if existing_start is not None:
        new_lines = lines[:existing_start] + entry_lines + lines[existing_end:]
    else:
        # Find personas section or create it
        personas_idx: int | None = None
        for i, line in enumerate(lines):
            if line.strip() == "personas:":
                personas_idx = i
                break

        if personas_idx is None:
            # Insert before plugins/backend, or at end
            insert_at = len(lines)
            for marker in ("plugins:", "backend:"):
                for i, line in enumerate(lines):
                    if line.strip() == marker:
                        insert_at = i
                        break
                if insert_at < len(lines):
                    break
            section = ["", "personas:"] + entry_lines
            new_lines = lines[:insert_at] + section + ([""] + lines[insert_at:] if insert_at < len(lines) else [])
        else:
            # Find end of current personas entries
            insert_at = personas_idx + 1
            while insert_at < len(lines):
                nxt = lines[insert_at].strip()
                if not nxt:
                    insert_at += 1
                    continue
                if lines[insert_at].startswith("  "):
                    insert_at += 1
                    while insert_at < len(lines) and lines[insert_at].startswith("    "):
                        insert_at += 1
                else:
                    break
            while insert_at > personas_idx + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            new_lines = lines[:insert_at] + [""] + entry_lines + ([""] + lines[insert_at:] if insert_at < len(lines) and lines[insert_at].strip() else [""] + lines[insert_at:])

    new_content = "\n".join(new_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"

    try:
        config_path.write_text(new_content, encoding="utf-8")
    except OSError:
        return False

    rk = str(root.resolve())
    _config_cache.pop(rk, None)
    _persona_cache.pop(rk, None)
    return True



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


# ── Persona system ────────────────────────────────────────────────────

@dataclass
class Persona:
    """A review/audit role that can be used in Roundtable discussions."""
    name: str
    title: str = ""
    icon: str = ""
    role: str = ""
    identity: str = ""
    principles: list[str] = None       # type: ignore
    analysis_lens: str = ""
    output_format: str = ""
    source: str = "builtin"            # "builtin" or "project"

    def __post_init__(self):
        if self.principles is None:
            self.principles = []


_persona_cache: dict[str, dict[str, Persona]] = {}


def _load_persona_yaml(path: Path) -> Persona | None:
    """Load a single persona from a YAML file."""
    try:
        cfg = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    def _str(v: object) -> str:
        if isinstance(v, list):
            return "\n".join(str(x) for x in v)
        return str(v) if v else ""

    return Persona(
        name=cfg.get("name", ""),
        title=cfg.get("title", ""),
        icon=cfg.get("icon", ""),
        role=cfg.get("role", ""),
        identity=_str(cfg.get("identity")),
        principles=cfg.get("principles", []) if isinstance(cfg.get("principles"), list) else [],
        analysis_lens=_str(cfg.get("analysis_lens")),
        output_format=_str(cfg.get("output_format")),
        source="builtin",
    )


def _persona_from_config(name: str, cfg: dict) -> Persona:
    """Build a Persona from a jarvis.yaml personas: sub-entry."""

    def _str(v: object) -> str:
        if isinstance(v, list):
            return "\n".join(str(x) for x in v)
        return str(v) if v else ""

    return Persona(
        name=name,
        title=cfg.get("title", name),
        icon=cfg.get("icon", ""),
        role=cfg.get("role", ""),
        identity=_str(cfg.get("identity")),
        principles=cfg.get("principles", []) if isinstance(cfg.get("principles"), list) else [],
        analysis_lens=_str(cfg.get("analysis_lens")),
        output_format=_str(cfg.get("output_format")),
        source="project",
    )


def list_personas(jarvis_home: Path | None = None, root: Path | None = None) -> dict[str, Persona]:
    """Return all available personas (builtin + project-level).

    Builtin personas are loaded from jarvis/personas/.
    Project personas are loaded from jarvis.yaml's ``personas:`` section.
    Project entries with the same name override builtin ones.
    """
    if jarvis_home is None:
        jarvis_home = Path(__file__).resolve().parent
    if root is None:
        root = Path.cwd()

    ck = str(jarvis_home.resolve()) + "::" + str(root.resolve())
    if ck in _persona_cache:
        return _persona_cache[ck]

    personas: dict[str, Persona] = {}

    # 1. Builtin from jarvis/personas/*.yaml
    builtin_dir = jarvis_home / "personas"
    if builtin_dir.is_dir():
        for f in sorted(builtin_dir.glob("*.yaml")):
            p = _load_persona_yaml(f)
            if p and p.name:
                personas[p.name] = p

    # 2. Project-level from jarvis.yaml personas: section
    config = load_jarvis_config(root)
    proj_personas = config.get("personas", {})
    if isinstance(proj_personas, dict):
        for name, cfg in proj_personas.items():
            if isinstance(cfg, dict):
                personas[name] = _persona_from_config(name, cfg)

    _persona_cache[ck] = personas
    return personas


def load_persona(name: str, jarvis_home: Path | None = None, root: Path | None = None) -> Persona | None:
    """Load a single persona by name. Returns None if not found."""
    return list_personas(jarvis_home, root).get(name)


def resolve_persona_prompt(persona: Persona, topic_summary: str = "") -> str:
    """Render a persona into a complete sub-agent prompt.

    The resulting prompt is intended to be passed to a ``task`` sub-agent
    as its instruction. It includes the persona's identity, analysis lens,
    and output format.
    """
    lines = [
        f"你是 {persona.title}（{persona.role}）。",
        "",
        persona.identity,
        "",
        "## 判断原则",
    ]
    for p in persona.principles:
        lines.append(f"- {p}")

    if persona.analysis_lens:
        lines.append("")
        lines.append("## 分析维度")
        lines.append(persona.analysis_lens)

    if persona.output_format:
        lines.append("")
        lines.append("## 输出格式")
        lines.append("严格按照以下格式输出你的分析结果：")
        lines.append(persona.output_format)

    if topic_summary:
        lines.append("")
        lines.append("## 待分析内容")
        lines.append(topic_summary)

    lines.append("")
    lines.append("重要：只分析和输出结论，不要执行任何写入操作（不创建、不修改文件）。")

    return "\n".join(lines)




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

    # Fallback A: gio trash (Linux GNOME/kde — supports Trash)
    try:
        import subprocess
        result = subprocess.run(
            ["gio", "trash", str(target)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and not target.exists():
            return True
    except Exception:
        pass

    # Fallback B: mv to ~/.local/share/Trash/files (Linux XDG)
    xdg_trash = Path.home() / ".local" / "share" / "Trash" / "files"
    if xdg_trash.is_dir():
        dest = xdg_trash / target.name
        if dest.exists():
            from datetime import datetime
            ts = datetime.now().strftime("%H%M%S")
            dest = xdg_trash / f"{target.stem}_{ts}{target.suffix}"
        try:
            target.rename(dest)
            return True
        except OSError:
            pass

    # Fallback C: mv to ~/.Trash (macOS — no Put Back, but still recoverable)
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
