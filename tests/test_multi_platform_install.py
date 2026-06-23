from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.cli import cmd_init
from jarvis.cli import _sync_project
from jarvis.platform_support import _parse_toml_fallback, detect_platform, detect_platforms, merge_reasonix_config_text


REPO = Path(__file__).resolve().parents[1]
JARVIS_HOME = REPO / "jarvis"


class MultiPlatformInstallTests(unittest.TestCase):
    def test_platform_support_import_does_not_require_tomllib(self) -> None:
        code = """
import importlib.abc
import sys

class BlockToml(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in ("tomllib", "tomli"):
            raise ModuleNotFoundError(fullname)
        return None

sys.meta_path.insert(0, BlockToml())
import jarvis.platform_support as ps
print(ps.DEFAULT_SEMANTIC_PATHS["wiki_index"])
"""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO)
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(REPO),
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("知识库/wiki索引.md", result.stdout)

    def test_detect_platforms_reports_all_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reasonix.toml").write_text('config_version = 3\n', encoding="utf-8")
            (root / ".codex").mkdir()
            (root / "CLAUDE.md").write_text("# test\n", encoding="utf-8")
            self.assertEqual(detect_platforms(str(root)), ["reasonix", "codex", "claude"])

    def test_detect_platform_recognizes_reasonix_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reasonix.toml").write_text('config_version = 3\n', encoding="utf-8")
            self.assertEqual(detect_platform(str(root)), "reasonix")

    def test_detect_platform_returns_all_for_multiple_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".reasonix").mkdir()
            (root / ".codex").mkdir()
            (root / ".claude").mkdir()
            self.assertEqual(detect_platform(str(root)), "all")

    def test_cmd_init_creates_agents_md_and_reasonix_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reasonix.toml").write_text('config_version = 3\n', encoding="utf-8")
            with patch.dict(os.environ, {"HOME": str(root / "home")}):
                rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="auto"))
            self.assertEqual(rc, 0)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("JARVIS_BOOTSTRAP.md", agents)
            self.assertIn("JARVIS_CORE_BRIEF.md", agents)
            config = (root / "jarvis.yaml").read_text(encoding="utf-8")
            self.assertIn("platform: reasonix", config)
            reasonix = (root / "reasonix.toml").read_text(encoding="utf-8")
            self.assertIn('system_prompt_file = "REASONIX.md"', reasonix)
            self.assertIn(f'paths = ["{JARVIS_HOME / "skills"}"]', reasonix)
            self.assertIn('excluded_paths = [".claude/skills", "~/.claude/skills"]', reasonix)
            self.assertTrue((root / "REASONIX.md").exists())
            self.assertFalse((root / ".claude" / "settings.json").exists())
            self.assertFalse((root / "CLAUDE.md").exists())

    def test_cmd_init_all_profile_creates_cross_platform_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(os.environ, {"HOME": str(root / "home")}):
                rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="all"))
            self.assertEqual(rc, 0)
            self.assertTrue((root / ".claude" / "settings.json").exists())
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / "REASONIX.md").exists())
            hook = root / ".claude" / "hooks" / "jarvis-core-inject.sh"
            self.assertEqual(
                hook.resolve(),
                REPO / "adapters" / "claude" / "hooks" / "jarvis-core-inject.sh",
            )
            reasonix = (root / "reasonix.toml").read_text(encoding="utf-8")
            self.assertIn('system_prompt_file = "REASONIX.md"', reasonix)
            self.assertIn(f'paths = ["{JARVIS_HOME / "skills"}"]', reasonix)
            config = (root / "jarvis.yaml").read_text(encoding="utf-8")
            self.assertIn("platform: all", config)

    def test_cmd_init_all_skips_project_claude_adapter_when_global_hooks_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            (claude_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {
                                    "match": "startup",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": 'bash "/tmp/jarvis-core-inject.sh"',
                                        }
                                    ],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"HOME": str(home)}):
                rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="all"))
            self.assertEqual(rc, 0)
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertFalse((root / ".claude" / "settings.json").exists())
            self.assertFalse((root / ".claude" / "hooks").exists())

    def test_cmd_init_codex_profile_skips_claude_and_reasonix_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(os.environ, {"HOME": str(root / "home")}):
                rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="codex"))
            self.assertEqual(rc, 0)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertFalse((root / "reasonix.toml").exists())
            self.assertFalse((root / "CLAUDE.md").exists())
            self.assertFalse((root / ".claude").exists())

    def test_sync_project_refreshes_reasonix_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(os.environ, {"HOME": str(root / "home")}):
                rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="reasonix"))
            self.assertEqual(rc, 0)
            (root / "AGENTS.md").write_text("# custom\n", encoding="utf-8")
            (root / "REASONIX.md").write_text("# old\n", encoding="utf-8")
            (root / "jarvis.yaml").write_text(
                (root / "jarvis.yaml").read_text(encoding="utf-8").replace('jarvis_version: "2.0.0"', 'jarvis_version: "1.9.0"'),
                encoding="utf-8",
            )
            sync_rc = _sync_project(root)
            self.assertEqual(sync_rc, 0)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            reasonix_md = (root / "REASONIX.md").read_text(encoding="utf-8")
            self.assertIn("JARVIS_CORE_BRIEF.md", agents)
            self.assertIn("JARVIS_CORE_BRIEF.md", reasonix_md)
            self.assertIn("框架内结论", agents)
            self.assertIn("框架内结论", reasonix_md)
            self.assertIn('system_prompt_file = "REASONIX.md"', (root / "reasonix.toml").read_text(encoding="utf-8"))

    def test_sync_project_repairs_legacy_multi_platform_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".reasonix").mkdir()
            (root / ".codex").mkdir()
            claude = root / ".claude"
            claude.mkdir()
            (root / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
            (root / "jarvis.yaml").write_text(
                '# Jarvis project configuration\n'
                'jarvis_version: "1.9.0"\n'
                'jarvis_home: "/tmp/old-jarvis"\n\n'
                'paths:\n'
                '  knowledge_base: 知识库\n'
                '  wiki_index: 知识库/wiki索引.md\n'
                '  terms_dir: 知识库/术语\n'
                '  terms_index: 知识库/术语/术语索引.md\n'
                '  business_dir: 业务\n'
                '  ops_dir: platform-ops\n'
                '  dashboard: platform-ops/仪表盘.md\n'
                '  log: platform-ops/log.md\n'
                '  topics: platform-ops/topics\n\n'
                'plugins: []\n\n'
                'backend: file\n',
                encoding="utf-8",
            )
            (claude / "settings.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "",
                                    "hooks": [
                                        {"type": "command", "command": ".claude/hooks/jarvis-write-guard.sh"},
                                        {"type": "command", "command": "echo graphify"},
                                    ],
                                }
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            sync_rc = _sync_project(root)
            self.assertEqual(sync_rc, 0)
            config = (root / "jarvis.yaml").read_text(encoding="utf-8")
            self.assertIn('jarvis_version: "2.0.0"', config)
            self.assertIn(f'jarvis_home: "{JARVIS_HOME}"', config)
            self.assertIn("platform: all", config)
            self.assertTrue((root / "REASONIX.md").is_file())
            self.assertTrue((root / "reasonix.toml").is_file())
            self.assertIn("框架内结论", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("框架内结论", (root / "REASONIX.md").read_text(encoding="utf-8"))
            settings = json.loads((claude / "settings.json").read_text(encoding="utf-8"))
            commands = [
                hook["command"]
                for entries in settings.get("hooks", {}).values()
                for entry in entries
                for hook in entry.get("hooks", [])
            ]
            self.assertEqual(commands, ["echo graphify"])

    def test_merge_reasonix_config_preserves_existing_paths(self) -> None:
        updated, prompt_managed, existing_prompt = merge_reasonix_config_text(
            """
[agent]
temperature = 0.0

[skills]
paths = ["/tmp/existing"]
""",
            skills_path="/tmp/jarvis/skills",
            prompt_path="/tmp/jarvis-system.md",
        )
        self.assertTrue(prompt_managed)
        self.assertIsNone(existing_prompt)
        self.assertIn('system_prompt_file = "/tmp/jarvis-system.md"', updated)
        self.assertIn('paths = ["/tmp/existing", "/tmp/jarvis/skills"]', updated)
        self.assertIn('excluded_paths = [".claude/skills", "~/.claude/skills"]', updated)

    def test_toml_fallback_parses_reasonix_keys(self) -> None:
        parsed = _parse_toml_fallback(
            """
[agent]
system_prompt_file = "/tmp/prompt.md"

[[providers]]
name = "deepseek"

[skills]
paths = ["/tmp/existing", "/tmp/other"]
excluded_paths = [".claude/skills"]
"""
        )
        self.assertEqual(parsed["agent"]["system_prompt_file"], "/tmp/prompt.md")
        self.assertEqual(parsed["skills"]["paths"], ["/tmp/existing", "/tmp/other"])
        self.assertEqual(parsed["skills"]["excluded_paths"], [".claude/skills"])

    def test_merge_reasonix_config_handles_array_tables(self) -> None:
        updated, prompt_managed, _ = merge_reasonix_config_text(
            """
[agent]
temperature = 0.0

[[providers]]
name = "deepseek"

[skills]
paths = ["/tmp/existing"]
""",
            skills_path="/tmp/jarvis/skills",
            prompt_path="/tmp/jarvis-system.md",
        )
        self.assertTrue(prompt_managed)
        self.assertRegex(
            updated,
            r"\[agent\][\s\S]*system_prompt_file = \"/tmp/jarvis-system.md\"[\s\S]*\[\[providers\]\]",
        )

    def test_reasonix_installer_writes_native_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".reasonix"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.toml").write_text(
                "[agent]\ntemperature = 0.0\n\n[skills]\npaths = [\"/tmp/existing\"]\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["JARVIS_HOME"] = str(JARVIS_HOME)
            env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO), env.get("PYTHONPATH", "")]))
            subprocess.run(
                ["bash", str(JARVIS_HOME / "installers" / "reasonix.sh")],
                check=True,
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
            )

            prompt_path = config_dir / "prompts" / "jarvis-system.md"
            skills_path = JARVIS_HOME / "skills"
            self.assertTrue(prompt_path.is_file())
            config = (config_dir / "config.toml").read_text(encoding="utf-8")
            self.assertIn(f'system_prompt_file = "{prompt_path}"', config)
            self.assertIn(f'paths = ["/tmp/existing", "{skills_path}"]', config)
            self.assertIn('excluded_paths = [".claude/skills", "~/.claude/skills"]', config)
            self.assertFalse((config_dir / "settings.json").exists())

    def test_reasonix_installer_cleans_legacy_settings_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".reasonix"
            config_dir.mkdir(parents=True, exist_ok=True)
            legacy = config_dir / "settings.json"
            legacy.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {
                                    "command": 'bash "/old/jarvis-core-inject.sh"',
                                    "description": "old jarvis",
                                },
                                {
                                    "command": "echo keep",
                                    "description": "custom",
                                },
                            ],
                            "PreToolUse": [
                                {
                                    "match": "Write",
                                    "command": 'bash "/old/jarvis-write-guard.sh"',
                                }
                            ],
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["JARVIS_HOME"] = str(JARVIS_HOME)
            env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO), env.get("PYTHONPATH", "")]))
            subprocess.run(
                ["bash", str(JARVIS_HOME / "installers" / "reasonix.sh")],
                check=True,
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
            )

            updated = json.loads(legacy.read_text(encoding="utf-8"))
            commands = [
                entry.get("command")
                for entries in updated.get("hooks", {}).values()
                for entry in entries
            ]
            self.assertEqual(commands, ["echo keep"])
            self.assertTrue(list(config_dir.glob("settings.json.bak-*")))

    def test_claude_installer_merges_sessionstart_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True, exist_ok=True)
            settings_path = claude_dir / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {
                                    "match": "startup",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "bash \"/tmp/existing-hook.sh\"",
                                            "timeout": 1000,
                                        }
                                    ],
                                }
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["JARVIS_HOME"] = str(JARVIS_HOME)
            env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(REPO), env.get("PYTHONPATH", "")]))
            subprocess.run(
                ["bash", str(JARVIS_HOME / "installers" / "claude.sh")],
                check=True,
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
            )

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            session_start = settings["hooks"]["SessionStart"]
            commands = [
                hook["command"]
                for entry in session_start
                for hook in entry.get("hooks", [])
            ]
            self.assertIn('bash "/tmp/existing-hook.sh"', commands)
            self.assertIn(f'bash "{home / ".claude" / "hooks" / "jarvis-core-inject.sh"}"', commands)
            self.assertIn("deny", settings["permissions"])
            self.assertIn("Read(.env)", settings["permissions"]["deny"])

    def test_claude_installer_uses_adapter_hooks_when_jarvis_hooks_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            fake_jarvis = root / "pkg" / "jarvis"
            fake_hooks = root / "pkg" / "adapters" / "claude" / "hooks"
            fake_skill = fake_jarvis / "skills" / "jarvis-test"
            fake_skill.mkdir(parents=True)
            fake_hooks.mkdir(parents=True)
            (fake_skill / "SKILL.md").write_text("# test\n", encoding="utf-8")
            for name in ("jarvis-core-inject.sh", "jarvis-write-guard.sh", "jarvis-compact-save.sh"):
                hook = fake_hooks / name
                hook.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
                hook.chmod(hook.stat().st_mode | stat.S_IXUSR)

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["JARVIS_HOME"] = str(fake_jarvis)
            subprocess.run(
                ["bash", str(JARVIS_HOME / "installers" / "claude.sh")],
                check=True,
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
            )

            linked_hook = home / ".claude" / "hooks" / "jarvis-core-inject.sh"
            self.assertTrue(linked_hook.is_symlink())
            self.assertEqual(linked_hook.resolve(), (fake_hooks / "jarvis-core-inject.sh").resolve())

    def test_claude_installer_relinks_legacy_symlinks_and_replaces_old_settings_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            fake_jarvis = root / "pkg" / "jarvis"
            fake_hooks = root / "pkg" / "adapters" / "claude" / "hooks"
            fake_skill = fake_jarvis / "skills" / "jarvis-test"
            old_root = root / "old"
            old_hooks = old_root / "hooks"
            old_skill = old_root / "skills" / "jarvis-test"
            fake_skill.mkdir(parents=True)
            fake_hooks.mkdir(parents=True)
            old_hooks.mkdir(parents=True)
            old_skill.mkdir(parents=True)
            (fake_skill / "SKILL.md").write_text("# new\n", encoding="utf-8")
            for name in ("jarvis-core-inject.sh", "jarvis-write-guard.sh", "jarvis-compact-save.sh"):
                hook = fake_hooks / name
                hook.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
                hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
                old_hook = old_hooks / name
                old_hook.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
                old_hook.chmod(old_hook.stat().st_mode | stat.S_IXUSR)

            claude_dir = home / ".claude"
            (claude_dir / "hooks").mkdir(parents=True)
            (claude_dir / "skills").mkdir(parents=True)
            (claude_dir / "hooks" / "jarvis-write-guard.sh").symlink_to(old_hooks / "jarvis-write-guard.sh")
            (claude_dir / "skills" / "jarvis-test").symlink_to(old_skill)
            (claude_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "",
                                    "hooks": [
                                        {"type": "command", "command": ".claude/hooks/jarvis-write-guard.sh"},
                                        {"type": "command", "command": "echo graphify"},
                                    ],
                                }
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["JARVIS_HOME"] = str(fake_jarvis)
            subprocess.run(
                ["bash", str(JARVIS_HOME / "installers" / "claude.sh")],
                check=True,
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual((claude_dir / "hooks" / "jarvis-write-guard.sh").resolve(), (fake_hooks / "jarvis-write-guard.sh").resolve())
            self.assertEqual((claude_dir / "skills" / "jarvis-test").resolve(), fake_skill.resolve())
            settings = json.loads((claude_dir / "settings.json").read_text(encoding="utf-8"))
            commands = [
                hook["command"]
                for entries in settings.get("hooks", {}).values()
                for entry in entries
                for hook in entry.get("hooks", [])
            ]
            self.assertIn("echo graphify", commands)
            self.assertIn(f'bash "{claude_dir / "hooks" / "jarvis-write-guard.sh"}"', commands)
            self.assertNotIn(".claude/hooks/jarvis-write-guard.sh", commands)

    def test_write_guard_honors_bypass_permissions_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transcript = root / "transcript.jsonl"
            transcript.write_text(
                '{"type":"user","permissionMode":"bypassPermissions"}\n',
                encoding="utf-8",
            )
            hook_input = {
                "tool_name": "Write",
                "tool_input": {"file_path": "知识库/术语/新术语.md", "content": "test"},
                "transcript_path": str(transcript),
            }
            script = REPO / "adapters" / "claude" / "hooks" / "jarvis-write-guard.sh"
            script.chmod(script.stat().st_mode | stat.S_IXUSR)
            result = subprocess.run(
                ["bash", str(script)],
                input=json.dumps(hook_input, ensure_ascii=False),
                text=True,
                capture_output=True,
                cwd=str(REPO),
                check=True,
            )
            self.assertIn('"permissionDecision":"allow"', result.stdout)
            self.assertNotIn('"permissionDecision":"ask"', result.stdout)


if __name__ == "__main__":
    unittest.main()
