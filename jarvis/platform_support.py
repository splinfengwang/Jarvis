"""Helpers for platform-specific Jarvis integration."""

from __future__ import annotations

import json
import re
from pathlib import Path

VALID_PLATFORMS = ("claude", "reasonix", "codex", "all")
JARVIS_RUNTIME_START = "<!-- JARVIS_RUNTIME_START -->"
JARVIS_RUNTIME_END = "<!-- JARVIS_RUNTIME_END -->"

DEFAULT_SEMANTIC_PATHS: dict[str, str] = {
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


def detect_platforms(project_root: str = ".") -> list[str]:
    """Detect all platform markers present in a project directory."""
    root = Path(project_root)
    detected: list[str] = []
    if (root / "reasonix.toml").is_file() or (root / ".reasonix").exists() or (root / "REASONIX.md").is_file():
        detected.append("reasonix")
    if (root / ".codex").exists():
        detected.append("codex")
    if (root / "CLAUDE.md").is_file() or (root / ".claude").exists():
        detected.append("claude")
    return detected


def detect_platform(project_root: str = ".") -> str:
    """Detect the agent platform used by a project directory."""
    detected = detect_platforms(project_root)
    if len(detected) > 1:
        return "all"
    if "reasonix" in detected:
        return "reasonix"
    if "codex" in detected:
        return "codex"
    return "claude"


def extract_semantic_paths(config: dict | None) -> dict[str, str]:
    """Extract semantic paths from either `paths:` or current `core:` schema."""
    result = dict(DEFAULT_SEMANTIC_PATHS)
    if not config:
        return result

    paths = config.get("paths")
    if isinstance(paths, dict):
        for key, value in paths.items():
            if isinstance(value, str) and value:
                result[key] = value

    core = config.get("core")
    if isinstance(core, dict):
        for key in ("dashboard", "log", "wiki_index", "terms_index", "topics"):
            value = core.get(key)
            if isinstance(value, str) and value:
                result[key] = value
        result["knowledge_base"] = str(Path(result["wiki_index"]).parent)
        result["terms_dir"] = str(Path(result["terms_index"]).parent)
        result["ops_dir"] = str(Path(result["dashboard"]).parent)

    catalogs = config.get("catalogs")
    if isinstance(catalogs, dict) and "业务" in catalogs:
        result["business_dir"] = "业务"

    return result


def build_path_config_block(paths: dict[str, str], jarvis_home: str | Path) -> str:
    """Build semantic-to-actual path mapping block."""
    label_map = {
        "dashboard": "仪表盘",
        "log": "操作日志",
        "topics": "Topic目录",
        "wiki_index": "wiki索引",
        "terms_index": "术语索引",
        "terms_dir": "术语目录",
        "knowledge_base": "知识库",
        "business_dir": "业务目录",
        "ops_dir": "平台运维",
    }
    lines = ["[Jarvis Path Config — semantic to actual file mapping]"]
    lines.append("Use these paths when skills reference files by name:")
    for key in (
        "knowledge_base",
        "wiki_index",
        "terms_dir",
        "terms_index",
        "business_dir",
        "ops_dir",
        "dashboard",
        "log",
        "topics",
    ):
        value = paths.get(key)
        if not value:
            continue
        lines.append(f"- {label_map.get(key, key)} -> {value}")
    lines.append(f"- jarvis -> {jarvis_home}")
    return "\n".join(lines)


def _core_brief_body(jarvis_home: str | Path) -> str:
    brief_path = Path(jarvis_home) / "core" / "JARVIS_CORE_BRIEF.md"
    return brief_path.read_text(encoding="utf-8").strip()


def build_runtime_block(
    version: str,
    jarvis_home: str | Path,
    config: dict | None,
    *,
    runtime: str,
) -> str:
    """Build the managed Jarvis runtime block for non-hook runtimes."""
    paths = extract_semantic_paths(config)
    path_block = build_path_config_block(paths, jarvis_home)
    runtime_note = (
        "本区块是 Reasonix / Codex 等无 SessionStart hook 运行时的直接行为基线。"
        if runtime == "agents"
        else "本文件是 Reasonix 的 cache-stable system prompt 入口。"
    )
    foreign_note = (
        "若 `CLAUDE.md` 或 `.claude/` 中存在仅适用于 Claude Code 的启动机制描述，"
        "在 Reasonix / Codex 中以本区块为准。"
    )
    return (
        f"{JARVIS_RUNTIME_START}\n"
        f"## Jarvis Runtime Core (v{version})\n\n"
        f"{runtime_note}\n"
        f"{foreign_note}\n\n"
        "Treat the following Core as already active in this session.\n\n"
        f"{_core_brief_body(jarvis_home)}\n\n"
        f"{path_block}\n"
        f"{JARVIS_RUNTIME_END}"
    )


def build_agents_reference(version: str, jarvis_home: str | Path, config: dict | None) -> str:
    """Build a Jarvis managed block for AGENTS.md."""
    return build_runtime_block(version, jarvis_home, config, runtime="agents")


def build_reasonix_reference(version: str, jarvis_home: str | Path, config: dict | None) -> str:
    """Build a Jarvis managed block for REASONIX.md."""
    return build_runtime_block(version, jarvis_home, config, runtime="reasonix")


def build_claude_reference(version: str) -> str:
    """Build a Jarvis reference block for CLAUDE.md append mode."""
    return (
        "\n\n---\n"
        f"## Jarvis 行为框架 (v{version})\n\n"
        "本项目启用 Jarvis 行为框架。Core（铁律、写入裁决、Topic 生命周期等）"
        "由 Claude SessionStart hook 自动注入。\n"
        "若当前会话未看到 `[JARVIS_CORE]` 或 `[JARVIS_KNOWLEDGE_SNAPSHOT]`，"
        "请读取 `jarvis.yaml`，再按其中 `jarvis_home` 指向的 "
        "`core/JARVIS_BOOTSTRAP.md` 手动完成启动。\n"
        "你的角色和身份由本文件定义，Jarvis 只约束你的工作方式。\n"
        "配置见 `jarvis.yaml`。\n"
    )


def reasonix_prompt_text() -> str:
    """Render the global Reasonix bridge prompt."""
    return """# Jarvis Bridge for Reasonix

Apply this file only when the current workspace contains `jarvis.yaml`.

Startup contract:
1. Prefer `REASONIX.md` as the runtime prompt when present. `AGENTS.md` is the fallback.
2. If neither file embeds Jarvis Core yet, read `jarvis.yaml`, resolve `jarvis_home`, then read `<jarvis_home>/core/JARVIS_BOOTSTRAP.md`.
3. Treat `CLAUDE.md` as project context only, not as the active Reasonix runtime contract.
4. Skill visibility alone does not mean Jarvis is active. If Jarvis Core is not already present in the prompt, read it first.

If `jarvis.yaml` is absent, ignore this file and use normal Reasonix behavior.
"""


def merge_reasonix_config_text(
    content: str,
    *,
    skills_path: str,
    prompt_path: str,
) -> tuple[str, bool, str | None]:
    """
    Merge Jarvis settings into a Reasonix TOML config string.

    Returns: (updated_text, prompt_managed, existing_prompt)
    """
    raw = content or ""
    parsed = _loads_toml(raw) if raw.strip() else {}

    existing_prompt = None
    agent_cfg = parsed.get("agent")
    if isinstance(agent_cfg, dict):
        existing_prompt = agent_cfg.get("system_prompt_file")

    prompt_managed = existing_prompt in (None, "", prompt_path, "AGENTS.md")
    updated = raw
    if prompt_managed:
        updated = _remove_toml_key_lines(updated, "system_prompt_file")
        updated = upsert_toml_key(updated, "agent", "system_prompt_file", json.dumps(prompt_path, ensure_ascii=False))

    skills_cfg = parsed.get("skills")
    paths: list[str] = []
    if isinstance(skills_cfg, dict):
        current_paths = skills_cfg.get("paths", [])
        if isinstance(current_paths, list):
            for item in current_paths:
                if not isinstance(item, str):
                    continue
                lower = item.lower()
                if prompt_managed and (lower.endswith("/jarvis/skills") or lower.endswith("\\jarvis\\skills")):
                    continue
                if item not in paths:
                    paths.append(item)
    if skills_path not in paths:
        paths.append(skills_path)
    updated = upsert_toml_key(updated, "skills", "paths", json.dumps(paths, ensure_ascii=False))

    excluded_paths: list[str] = []
    if isinstance(skills_cfg, dict):
        current_excluded = skills_cfg.get("excluded_paths", [])
        if isinstance(current_excluded, list):
            for item in current_excluded:
                if isinstance(item, str) and item not in excluded_paths:
                    excluded_paths.append(item)
    for item in (".claude/skills", "~/.claude/skills"):
        if item not in excluded_paths:
            excluded_paths.append(item)
    updated = upsert_toml_key(updated, "skills", "excluded_paths", json.dumps(excluded_paths, ensure_ascii=False))
    return updated, prompt_managed, existing_prompt


def _loads_toml(raw: str) -> dict:
    """Parse TOML when a parser is available; hooks must import on Python 3.10 too."""
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            return _parse_toml_fallback(raw)
    try:
        return tomllib.loads(raw)
    except Exception:
        return _parse_toml_fallback(raw)


def _parse_toml_fallback(raw: str) -> dict:
    """Minimal TOML fallback for Jarvis-managed Reasonix keys."""
    result: dict[str, dict] = {}
    for section in ("agent", "skills"):
        block = _extract_toml_section(raw, section)
        if not block:
            continue
        section_data: dict[str, object] = {}
        prompt = re.search(r'(?m)^\s*system_prompt_file\s*=\s*"([^"]*)"', block)
        if prompt:
            section_data["system_prompt_file"] = prompt.group(1)
        for key in ("paths", "excluded_paths"):
            match = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*\[(.*?)\]', block, re.S)
            if match:
                section_data[key] = re.findall(r'"([^"]*)"', match.group(1))
        if section_data:
            result[section] = section_data
    return result


def _extract_toml_section(raw: str, section: str) -> str:
    start = _find_section_start(raw, section)
    if start < 0:
        return ""
    end = _find_section_end(raw, start)
    return raw[start:end]


def upsert_marked_block(text: str, block: str) -> str:
    """Insert or replace a managed Jarvis runtime block in a markdown document."""
    if JARVIS_RUNTIME_START in text and JARVIS_RUNTIME_END in text:
        pattern = re.compile(
            rf"{re.escape(JARVIS_RUNTIME_START)}[\s\S]*?{re.escape(JARVIS_RUNTIME_END)}",
            re.MULTILINE,
        )
        updated = pattern.sub(block, text, count=1)
        return updated.rstrip() + "\n"

    base = text.rstrip()
    if not base:
        return block.rstrip() + "\n"
    return base + "\n\n" + block.rstrip() + "\n"


def upsert_toml_key(text: str, section: str, key: str, rendered_value: str) -> str:
    """Upsert a simple `key = value` line inside a top-level TOML section."""
    section_header = f"[{section}]"
    line = f'{key} = {rendered_value}'
    raw = text.rstrip()

    if not raw:
        return f"{section_header}\n{line}\n"

    start = _find_section_start(raw, section)
    if start < 0:
        return raw + f"\n\n{section_header}\n{line}\n"

    end = _find_section_end(raw, start)
    block = raw[start:end]
    key_pattern = re.compile(rf"(?m)^(?P<prefix>\s*){re.escape(key)}\s*=.*$")
    if key_pattern.search(block):
        replaced = key_pattern.sub(lambda m: f"{m.group('prefix')}{line}", block, count=1)
    else:
        suffix = "" if block.endswith("\n") else "\n"
        replaced = block + f"{suffix}{line}\n"
    return raw[:start] + replaced + raw[end:] + ("\n" if not raw.endswith("\n") else "")


def _find_section_start(text: str, section: str) -> int:
    pattern = re.compile(rf"(?m)^\[{re.escape(section)}\]\s*$")
    match = pattern.search(text)
    return match.start() if match else -1


def _find_section_end(text: str, start: int) -> int:
    next_header = re.compile(r"(?m)^\[{1,2}[^\]]+\]{1,2}\s*$").search(text, start + 1)
    return next_header.start() if next_header else len(text)


def _remove_toml_key_lines(text: str, key: str) -> str:
    pattern = re.compile(rf"(?m)^\s*{re.escape(key)}\s*=.*\n?")
    return pattern.sub("", text)
