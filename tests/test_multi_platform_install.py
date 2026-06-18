from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from jarvis.cli import cmd_init
from jarvis.cli import _sync_project
from jarvis.platform_support import detect_platform, detect_platforms, merge_reasonix_config_text


REPO = Path(__file__).resolve().parents[1]
JARVIS_HOME = REPO / "jarvis"


class MultiPlatformInstallTests(unittest.TestCase):
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

    def test_cmd_init_creates_agents_md_and_reasonix_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reasonix.toml").write_text('config_version = 3\n', encoding="utf-8")
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
            rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="all"))
            self.assertEqual(rc, 0)
            self.assertTrue((root / ".claude" / "settings.json").exists())
            self.assertTrue((root / "CLAUDE.md").exists())
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertTrue((root / "REASONIX.md").exists())
            reasonix = (root / "reasonix.toml").read_text(encoding="utf-8")
            self.assertIn('system_prompt_file = "REASONIX.md"', reasonix)
            self.assertIn(f'paths = ["{JARVIS_HOME / "skills"}"]', reasonix)
            config = (root / "jarvis.yaml").read_text(encoding="utf-8")
            self.assertIn("platform: all", config)

    def test_cmd_init_codex_profile_skips_claude_and_reasonix_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rc = cmd_init(argparse.Namespace(target=str(root), sync=False, claude_mode="a", platform="codex"))
            self.assertEqual(rc, 0)
            self.assertTrue((root / "AGENTS.md").exists())
            self.assertFalse((root / "reasonix.toml").exists())
            self.assertFalse((root / "CLAUDE.md").exists())
            self.assertFalse((root / ".claude").exists())

    def test_sync_project_refreshes_reasonix_runtime_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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
            self.assertIn("JARVIS_CORE_BRIEF.md", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("JARVIS_CORE_BRIEF.md", (root / "REASONIX.md").read_text(encoding="utf-8"))
            self.assertIn('system_prompt_file = "REASONIX.md"', (root / "reasonix.toml").read_text(encoding="utf-8"))

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
