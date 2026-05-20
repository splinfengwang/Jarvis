#!/usr/bin/env python3
"""Jarvis CLI — lifecycle management commands."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

JARVIS_VERSION = "1.0.0"


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


def load_project_config(project_root: Path) -> dict | None:
    """Load jarvis.yaml from a project. Returns None if not initialized."""
    config_path = project_root / "jarvis.yaml"
    if not config_path.is_file():
        return None
    try:
        from jarvis.lib import load_jarvis_config
        return load_jarvis_config(project_root)
    except Exception:
        return None


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new Jarvis project."""
    target = Path(args.target).resolve()
    jarvis_home = find_jarvis_home()

    print(f"Jarvis v{JARVIS_VERSION} — init")
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
        ".claude/settings.json": resolve_template("settings.json.tmpl"),
        "知识库/wiki索引.md": resolve_template("wiki索引.md.tmpl"),
        "知识库/术语/术语索引.md": resolve_template("术语索引.md.tmpl"),
        "platform-ops/仪表盘.md": resolve_template("仪表盘.md.tmpl"),
        "platform-ops/log.md": f"# 操作日志\n\n> append-only 操作记录。\n\n---\n\n## [{date}] install | Jarvis v{JARVIS_VERSION} 安装\n",
    }
    for rel_path, content in files.items():
        file_path = target / rel_path
        if file_path.exists():
            print(f"  [skip] {rel_path}")
            continue
        content = content.replace("{{DATE}}", date)
        content = content.replace("{{PROJECT_NAME}}", target.name)
        content = content.replace("{{JARVIS_VERSION}}", "1.0.0")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"  [file] {rel_path}")

    # Handle CLAUDE.md — interactive if already exists
    claude_path = target / "CLAUDE.md"
    jarvis_ref = (
        "\n\n---\n"
        f"## Jarvis 行为框架 (v{JARVIS_VERSION})\n\n"
        "本项目启用 Jarvis 行为框架。Core（铁律、写入裁决、Topic 生命周期等）由 SessionStart hook 自动注入。\n"
        "你的**角色和身份**由本文件定义，Jarvis 只约束你的工作方式。\n"
        "配置见 `jarvis.yaml`。\n"
    )
    if claude_path.exists():
        existing = claude_path.read_text(encoding="utf-8")
        # Show what's there
        preview = "\n".join(existing.splitlines()[:8])
        if len(existing.splitlines()) > 8:
            preview += f"\n... (共 {len(existing.splitlines())} 行)"
        print(f"\n  检测到已有 CLAUDE.md ({len(existing.splitlines())} 行):")
        for line in preview.splitlines():
            print(f"    | {line[:100]}")
        print()

        if "jarvis" in existing.lower() and "behavior" in existing.lower():
            print("  [skip] CLAUDE.md (已有 Jarvis 引用)")
        else:
            # Interactive: ask what to do
            answer = input("  如何处理? [A]追加引用 / [S]跳过 / [R]替换(备份旧文件) (默认=A): ").strip().lower()
            if answer == "r":
                backup = target / "CLAUDE.md.bak"
                claude_path.rename(backup)
                print(f"  旧文件已备份为 CLAUDE.md.bak")
                content = resolve_template("CLAUDE.md.tmpl")
                content = content.replace("{{DATE}}", date).replace("{{PROJECT_NAME}}", target.name).replace("{{JARVIS_VERSION}}", "1.0.0")
                claude_path.write_text(content, encoding="utf-8")
                print(f"  [file] CLAUDE.md (新生成)")
            elif answer == "s":
                print("  [skip] CLAUDE.md (保留原文件)")
            else:
                claude_path.write_text(existing.rstrip() + jarvis_ref)
                print("  [update] CLAUDE.md (已追加 Jarvis 引用)")
    else:
        content = resolve_template("CLAUDE.md.tmpl")
        content = content.replace("{{DATE}}", date).replace("{{PROJECT_NAME}}", target.name).replace("{{JARVIS_VERSION}}", "1.0.0")
        claude_path.write_text(content, encoding="utf-8")
        print(f"  [file] CLAUDE.md")

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

    print(f"Jarvis v{JARVIS_VERSION} — doctor")
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
            from jarvis.lib import load_jarvis_config
            be = load_jarvis_config(target).get("backend", "file")
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


def cmd_version(args: argparse.Namespace) -> int:
    """Print Jarvis version."""
    print(f"Jarvis v{JARVIS_VERSION}")
    jarvis_home = find_jarvis_home()
    print(f"  install: {jarvis_home}")
    # Check git for latest
    git_dir = jarvis_home.parent / ".git"
    if git_dir.is_dir():
        try:
            result = subprocess.run(
                ["git", "-C", str(jarvis_home.parent), "log", "--oneline", "-1"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                print(f"  commit:  {result.stdout.strip()}")
        except Exception:
            pass
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show Jarvis installation status for a project."""
    target = Path(args.target or ".").resolve()
    config = load_project_config(target)

    if not config:
        print(f"Jarvis not initialized in {target}")
        print("Run 'jarvis init' first.")
        return 1

    print(f"Jarvis v{JARVIS_VERSION} — status")
    print(f"  Project: {target}")
    print()

    # Version
    proj_ver = config.get("jarvis_version", "unknown")
    print(f"  Version:  {proj_ver}" + (" (current)" if proj_ver == JARVIS_VERSION else f" (latest: {JARVIS_VERSION})"))

    # Plugins
    plugins = config.get("plugins", [])
    if isinstance(plugins, str):
        plugins = [plugins]
    print(f"  Plugins:  {', '.join(plugins) if plugins else '(none)'}")

    # Backend
    backend = config.get("backend", "file")
    print(f"  Backend:  {backend}")

    # Paths
    paths = config.get("paths", {})
    if isinstance(paths, dict) and paths:
        print(f"  Paths:")
        for k, v in paths.items():
            exists = "✓" if (target / v).exists() else "✗"
            print(f"    {k}: {v} {exists}")

    # Skills count
    skills_dir = target / ".claude" / "skills"
    if skills_dir.is_dir():
        skill_count = len([s for s in skills_dir.iterdir() if s.is_symlink() or s.is_dir()])
        print(f"  Skills:   {skill_count} installed")

    # Hooks
    hooks_dir = target / ".claude" / "hooks"
    if hooks_dir.is_dir():
        hook_count = len([h for h in hooks_dir.iterdir() if h.suffix == ".sh"])
        print(f"  Hooks:    {hook_count} installed")

    return 0


def cmd_upgrade(args: argparse.Namespace) -> int:
    """Upgrade Jarvis to the latest version."""
    jarvis_home = find_jarvis_home()
    repo_root = jarvis_home.parent  # jarvis repo root (parent of package dir)

    print(f"Jarvis v{JARVIS_VERSION} — upgrade")
    print()

    # Step 1: git pull
    if (repo_root / ".git").is_dir():
        print("[1/3] git pull...")
        result = subprocess.run(
            ["git", "-C", str(repo_root), "pull"],
            capture_output=True, text=True, timeout=30,
        )
        print(f"  {result.stdout.strip() or 'Already up to date.'}")
        if result.returncode != 0:
            print(f"  [ERROR] {result.stderr.strip()}")
            return 1
    else:
        print("[1/3] Not a git repo — skipping git pull")
        if not args.force:
            print("  Use --force to upgrade without git")
            return 1

    # Step 2: pipx upgrade or pip install
    print("[2/3] Reinstalling package...")
    # Try pipx first
    try:
        result = subprocess.run(
            ["pipx", "upgrade", "jarvis-agent"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            print(f"  {result.stdout.strip().split(chr(10))[-1] if result.stdout.strip() else 'upgraded'}")
        else:
            # Fallback: pipx install --force
            result = subprocess.run(
                ["pipx", "install", "--force", "-e", str(repo_root)],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                print("  reinstalled via pipx")
            else:
                raise RuntimeError(result.stderr)
    except Exception:
        # Fallback to pip
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--break-system-packages", "-e", str(repo_root)],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                print(f"  [ERROR] pip install failed: {result.stderr.strip()}")
                return 1
            print("  reinstalled via pip")
        except Exception as e:
            print(f"  [ERROR] {e}")
            return 1

    # Step 3: doctor on target
    print("[3/3] Running doctor...")
    target = Path(args.target or ".").resolve()
    return cmd_doctor(argparse.Namespace(target=str(target)))

    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Remove Jarvis from a project."""
    target = Path(args.target or ".").resolve()
    config = load_project_config(target)

    if not config:
        print(f"Jarvis is not initialized in {target}")
        return 1

    print(f"Jarvis v{JARVIS_VERSION} — uninstall")
    print(f"  Target: {target}")
    print()

    if not args.yes:
        answer = input("  This will remove Jarvis symlinks and configuration. Continue? [y/N]: ").strip().lower()
        if answer != "y":
            print("  Cancelled.")
            return 0

    removed = []
    kept = []

    # Remove skill symlinks
    skills_dir = target / ".claude" / "skills"
    if skills_dir.is_dir():
        for item in list(skills_dir.iterdir()):
            if item.is_symlink() and "jarvis" in str(item.resolve()):
                item.unlink()
                removed.append(f".claude/skills/{item.name}")

    # Remove hook symlinks
    hooks_dir = target / ".claude" / "hooks"
    if hooks_dir.is_dir():
        for item in list(hooks_dir.iterdir()):
            if item.is_symlink() and "jarvis" in str(item.resolve()):
                item.unlink()
                removed.append(f".claude/hooks/{item.name}")

    # Remove jarvis.yaml
    config_path = target / "jarvis.yaml"
    if config_path.is_file():
        if args.keep_config:
            kept.append("jarvis.yaml")
        else:
            config_path.unlink()
            removed.append("jarvis.yaml")

    # Remove CLAUDE.md jarvis reference (strip the appended block)
    claude_path = target / "CLAUDE.md"
    if claude_path.is_file() and not args.keep_claude:
        content = claude_path.read_text(encoding="utf-8")
        marker = "\n\n---\n## Jarvis 行为框架"
        if marker in content:
            new_content = content[:content.index(marker)]
            claude_path.write_text(new_content, encoding="utf-8")
            print(f"  [clean] CLAUDE.md (removed Jarvis reference)")
        else:
            kept.append("CLAUDE.md (no Jarvis reference found)")
    elif claude_path.is_file():
        kept.append("CLAUDE.md (--keep-claude)")

    # Keep knowledge base and platform-ops by default (user data)
    kb = target / "知识库"
    ops = target / "platform-ops"
    business = target / "业务"
    for d, label in [(kb, "知识库/"), (ops, "platform-ops/"), (business, "业务/")]:
        if d.is_dir() and not args.purge:
            kept.append(f"{label} (user data, use --purge to remove)")

    # Purge if requested
    if args.purge:
        for d in [kb, ops, business]:
            if d.is_dir():
                shutil.rmtree(d)
                removed.append(f"{d.relative_to(target)}/")

    print()
    for r in removed:
        print(f"  [removed] {r}")
    for k in kept:
        print(f"  [kept]   {k}")

    print()
    print("Done. Jarvis has been uninstalled from this project.")
    if not args.purge:
        print("Knowledge base and platform-ops were kept. Use --purge to remove everything.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="jarvis", description="Jarvis CLI — LLM-native agent framework")
    parser.add_argument("--version", "-V", action="store_true", help="Print version and exit")
    sub = parser.add_subparsers(dest="command", help="Commands")

    init_p = sub.add_parser("init", help="Initialize a new Jarvis project")
    init_p.add_argument("target", nargs="?", default=".", help="Target project directory (default: current)")
    init_p.set_defaults(func=cmd_init)

    doctor_p = sub.add_parser("doctor", help="Verify Jarvis installation")
    doctor_p.add_argument("target", nargs="?", default=".", help="Project directory to check (default: current)")
    doctor_p.set_defaults(func=cmd_doctor)

    status_p = sub.add_parser("status", help="Show Jarvis installation status")
    status_p.add_argument("target", nargs="?", default=".", help="Project directory (default: current)")
    status_p.set_defaults(func=cmd_status)

    upgrade_p = sub.add_parser("upgrade", help="Upgrade Jarvis to the latest version")
    upgrade_p.add_argument("target", nargs="?", default=".", help="Project to verify after upgrade (default: current)")
    upgrade_p.add_argument("--force", action="store_true", help="Skip git pull check")
    upgrade_p.set_defaults(func=cmd_upgrade)

    uninstall_p = sub.add_parser("uninstall", help="Remove Jarvis from a project")
    uninstall_p.add_argument("target", nargs="?", default=".", help="Project directory (default: current)")
    uninstall_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    uninstall_p.add_argument("--purge", action="store_true", help="Also remove knowledge base and platform-ops")
    uninstall_p.add_argument("--keep-config", action="store_true", help="Keep jarvis.yaml")
    uninstall_p.add_argument("--keep-claude", action="store_true", help="Keep CLAUDE.md unchanged")
    uninstall_p.set_defaults(func=cmd_uninstall)

    version_p = sub.add_parser("version", help="Print Jarvis version")
    version_p.set_defaults(func=cmd_version)

    args = parser.parse_args()
    if args.version:
        return cmd_version(args)
    if not args.command:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
