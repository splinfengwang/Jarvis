#!/usr/bin/env python3
"""Jarvis CLI — init and doctor commands."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def find_jarvis_home() -> Path:
    """Resolve jarvis installation directory (parent of this script's directory)."""
    return Path(__file__).resolve().parent


def resolve_template(name: str) -> str:
    """Read template file from jarvis/templates/."""
    tmpl_path = find_jarvis_home() / "templates" / name
    if tmpl_path.is_file():
        return tmpl_path.read_text(encoding="utf-8")
    return ""


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new Jarvis project."""
    target = Path(args.target).resolve()
    jarvis_home = find_jarvis_home()

    print(f"Jarvis v1.0 — init")
    print(f"  Target: {target}")
    print(f"  Jarvis: {jarvis_home}")
    print()

    # Create directories
    dirs = [
        ".claude/skills",
        ".claude/hooks",
        "知识库/术语",
        "业务",
        "platform-ops/topics",
    ]
    for d in dirs:
        (target / d).mkdir(parents=True, exist_ok=True)
        print(f"  [dir]  {d}")

    # Symlink skills
    skills_dir = jarvis_home / "skills"
    if skills_dir.is_dir():
        for skill_path in sorted(skills_dir.iterdir()):
            if skill_path.is_dir():
                link = target / ".claude" / "skills" / skill_path.name
                if not link.exists():
                    os.symlink(skill_path, link)
                    print(f"  [link] .claude/skills/{skill_path.name}")

    # Symlink hooks
    hooks_dir = jarvis_home / "hooks"
    if hooks_dir.is_dir():
        for hook_path in sorted(hooks_dir.iterdir()):
            if hook_path.suffix == ".sh":
                link = target / ".claude" / "hooks" / hook_path.name
                if not link.exists():
                    os.symlink(hook_path, link)
                    print(f"  [link] .claude/hooks/{hook_path.name}")

    # Generate files from templates
    date = now_date()
    files = {
        "CLAUDE.md": resolve_template("CLAUDE.md.tmpl"),
        ".claude/settings.json": resolve_template("settings.json.tmpl"),
        "知识库/wiki索引.md": resolve_template("wiki索引.md.tmpl"),
        "知识库/术语/术语索引.md": resolve_template("术语索引.md.tmpl"),
        "platform-ops/仪表盘.md": resolve_template("仪表盘.md.tmpl"),
        "platform-ops/log.md": f"# 操作日志\n\n> append-only 操作记录。\n\n---\n\n## [{date}] install | Jarvis v1.0 安装\n",
    }
    for rel_path, content in files.items():
        file_path = target / rel_path
        if file_path.exists():
            print(f"  [skip] {rel_path}")
            continue
        # Variable substitution
        content = content.replace("{{DATE}}", date)
        content = content.replace("{{PROJECT_NAME}}", target.name)
        content = content.replace("{{JARVIS_VERSION}}", "1.0.0")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"  [file] {rel_path}")

    # Write jarvis.yaml
    config_path = target / "jarvis.yaml"
    if not config_path.exists():
        config_content = f"""# Jarvis project configuration
jarvis_version: "1.0.0"
jarvis_home: "{jarvis_home}"

paths:
  knowledge_base: 知识库
  wiki_index: 知识库/wiki索引.md
  terms_dir: 知识库/术语
  terms_index: 知识库/术语/术语索引.md
  business_dir: 业务
  ops_dir: platform-ops
  dashboard: platform-ops/仪表盘.md
  log: platform-ops/log.md
  topics: platform-ops/topics

plugins: []

backend: file
"""
        config_path.write_text(config_content, encoding="utf-8")
        print(f"  [file] jarvis.yaml")

    print()
    print("Done. Start a new Claude Code session — Core will auto-inject.")
    print("Run 'jarvis doctor' to verify.")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Verify Jarvis installation integrity."""
    target = Path(args.target or ".").resolve()
    jarvis_home = find_jarvis_home()
    errors: list[str] = []
    warnings: list[str] = []

    print(f"Jarvis v1.0 — doctor")
    print(f"  Target: {target}")
    print(f"  Jarvis: {jarvis_home}")
    print()

    # Check jarvis.yaml
    config = target / "jarvis.yaml"
    if config.is_file():
        print(f"  [OK]   jarvis.yaml")
    else:
        errors.append("jarvis.yaml not found — run 'jarvis init' first")

    # Check CLAUDE.md
    claude = target / "CLAUDE.md"
    if claude.is_file():
        print(f"  [OK]   CLAUDE.md")
    else:
        warnings.append("CLAUDE.md not found")

    # Check Core
    core = jarvis_home / "core" / "JARVIS_CORE.md"
    if core.is_file():
        print(f"  [OK]   core/JARVIS_CORE.md")
    else:
        errors.append(f"Core not found: {core}")

    # Check skills symlinks
    skills_dir = target / ".claude" / "skills"
    if skills_dir.is_dir():
        skill_count = 0
        for item in skills_dir.iterdir():
            if item.is_symlink() or item.is_dir():
                skill_count += 1
        if skill_count >= 10:
            print(f"  [OK]   .claude/skills/ ({skill_count} skills)")
        else:
            warnings.append(f"Only {skill_count} skills found in .claude/skills/")
    else:
        errors.append(".claude/skills/ not found")

    # Check hooks
    hooks_dir = target / ".claude" / "hooks"
    if hooks_dir.is_dir():
        hook_count = len([f for f in hooks_dir.iterdir() if f.suffix == ".sh"])
        if hook_count >= 3:
            print(f"  [OK]   .claude/hooks/ ({hook_count} hooks)")
        else:
            warnings.append(f"Only {hook_count} hooks found")
    else:
        errors.append(".claude/hooks/ not found")

    # Check settings.json
    settings = target / ".claude" / "settings.json"
    if settings.is_file():
        print(f"  [OK]   .claude/settings.json")
    else:
        warnings.append(".claude/settings.json not found — hooks won't fire")

    # Check knowledge base structure
    for path_key, label in [
        ("知识库/wiki索引.md", "wiki索引"),
        ("知识库/术语/术语索引.md", "术语索引"),
        ("platform-ops/仪表盘.md", "仪表盘"),
        ("platform-ops/log.md", "操作日志"),
        ("platform-ops/topics", "Topic目录"),
    ]:
        p = target / path_key
        if p.exists():
            print(f"  [OK]   {label}")
        else:
            warnings.append(f"{label} not found: {path_key}")

    # Check backend availability
    if config.is_file():
        import subprocess
        try:
            import jarvis.lib
            be = jarvis_lib.load_jarvis_config(target).get("backend", "file")
            print(f"  [OK]   backend: {be}")
        except Exception:
            pass

    print()

    if errors:
        for e in errors:
            print(f"  [ERROR] {e}")
    if warnings:
        for w in warnings:
            print(f"  [WARN]  {w}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) — fix errors first.")
        return 1

    if warnings:
        print(f"\n{len(warnings)} warning(s) — consider fixing.")
    else:
        print("All checks passed.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="Jarvis CLI — LLM-native agent framework")
    sub = parser.add_subparsers(dest="command", help="Commands")

    init_p = sub.add_parser("init", help="Initialize a new Jarvis project")
    init_p.add_argument("target", nargs="?", default=".", help="Target project directory (default: current)")
    init_p.set_defaults(func=cmd_init)

    doctor_p = sub.add_parser("doctor", help="Verify Jarvis installation")
    doctor_p.add_argument("target", nargs="?", default=".", help="Project directory to check (default: current)")
    doctor_p.set_defaults(func=cmd_doctor)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
