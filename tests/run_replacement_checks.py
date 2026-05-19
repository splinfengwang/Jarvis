#!/usr/bin/env python3
"""Replacement checks for Jarvis Runtime v0.1.

The checks are intentionally deterministic. They verify the runtime package can
operate in a fixture vault without AGENT.md and that required artifacts exist.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


RUNTIME = Path(__file__).resolve().parents[1]
REPO = RUNTIME.parents[2]
FIXTURE = RUNTIME / "tests" / "fixtures" / "replacement-vault"

RESEARCH_FIELDS = [
    "source_project",
    "source_url",
    "source_paths",
    "mechanism_summary",
    "jarvis_mapping",
    "adopted_parts",
    "rejected_parts",
    "usable_rule",
    "test_case",
    "failure_trigger_for_research",
]

SKILL_FIELDS = [
    "trigger",
    "non_trigger",
    "inputs",
    "outputs",
    "required_references",
    "allowed_scripts",
    "write_level",
    "confirmation_rules",
    "fallback_rules",
    "acceptance_cases",
]

SKILLS = [
    "jarvis-analysis-thread",
    "jarvis-confluence-read",
    "jarvis-file-process",
    "jarvis-fragment-triage",
    "jarvis-help",
    "jarvis-knowledge-feedback",
    "jarvis-status",
    "jarvis-followup-sync",
    "jarvis-topic-create",
    "jarvis-topic-resume",
    "jarvis-topic-freeze",
    "jarvis-topic-close",
    "jarvis-knowledge-extract",
    "jarvis-knowledge-ingest",
]

REQUIRED_SCRIPTS = [
    "create_topic.py",
    "update_topic_status.py",
    "update_snapshot.py",
    "validate_dashboard.py",
    "validate_links.py",
    "locate_session_jsonl.py",
    "knowledge_link_stats.py",
    "append_operation_log.py",
    "extract_evidence_pack.py",
    "ingest_evidence_pack.py",
    "sync_followup.py",
    "sync_topic_index.py",
    "confluence_query.py",
    "record_knowledge_feedback.py",
    "record_file_process.py",
    "term_health_check.py",
    "memcommit_adapter.py",
]


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(cmd, cwd=cwd or REPO, env=env, text=True, capture_output=True)


def fail(message: str, details: str = "") -> None:
    print(f"FAIL: {message}")
    if details:
        print(details)
    raise SystemExit(1)


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        fail(f"{path} missing required text", "\n".join(missing))


def assert_text(label: str, text: str, needles: list[str]) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        fail(f"{label} missing required text", "\n".join(missing))


def build_fixture() -> None:
    if FIXTURE.exists():
        from jarvis_lib import trash_path
        trash_path(FIXTURE)
    topic = FIXTURE / "platform-ops" / "topics" / "20260516_贾维斯运行时架构迭代"
    topic.mkdir(parents=True)
    (FIXTURE / "platform-ops" / "仪表盘.md").write_text(
        """# 工作启动仪表盘（贾维斯）

## 活跃 Topic

| 状态 | Topic | 上次更新 | 下一步 | |
|---|---|---|---|---|
| [🟢 Doing] | [[platform-ops/topics/20260516_贾维斯运行时架构迭代/索引\\|贾维斯运行时架构迭代]] | 2026-05-16 | 继续替换验收 | |

## 待萃取

| 状态 | Topic | 上次更新 | 下一步 | |
|---|---|---|---|---|

## 待拍板

- 无
""",
        encoding="utf-8",
    )
    (FIXTURE / "platform-ops" / "log.md").write_text(
        "# 操作日志\n\n> append-only 操作记录。格式：`## [YYYY-MM-DD] 操作类型 | 简述`\n\n---\n",
        encoding="utf-8",
    )
    (FIXTURE / "platform-ops" / ".confluence-cookie").write_text("JSESSIONID=fake-cookie", encoding="utf-8")
    (topic / "索引.md").write_text(
        """---
topic: 贾维斯运行时架构迭代
status: doing
---

# 贾维斯运行时架构迭代

## 当前状态

- **Next Action**：继续替换验收
""",
        encoding="utf-8",
    )
    (topic / "_上下文快照.md").write_text(
        """# 上下文快照: 贾维斯运行时架构迭代

> **快照时间**: 2026-05-16
> **状态**: [🟢 Doing]

## 1. 最后动作

- runtime-v0.1 fixture 已建立。

## 4. 待拍板

- 无。

## 5. 下一步动作

- 跑替换验收。
""",
        encoding="utf-8",
    )
    (topic / "_准入检查单.md").write_text("# Topic 准入检查单\n", encoding="utf-8")
    (topic / "讨论记录.md").write_text(
        """# 讨论记录

## 2026-05-16 提炼输入

### 关键判断

- Claude Code 优先，Codex 保持结构兼容。

### 风险

- 血氧下限仍待医学验证。
""",
        encoding="utf-8",
    )
    term_dir = FIXTURE / "知识库" / "术语"
    term_dir.mkdir(parents=True)
    (term_dir / "测试术语.md").write_text("# 测试术语\n", encoding="utf-8")
    biz_dir = FIXTURE / "业务" / "测试"
    biz_dir.mkdir(parents=True)
    (biz_dir / "引用页.md").write_text(
        "# 引用页\n\n- 关联 [[知识库/术语/测试术语|测试术语]]。\n",
        encoding="utf-8",
    )
    (biz_dir / "测试替换知识.md").write_text(
        """# 测试替换知识

## 术语定义

- 测试替换术语：用于验证 Jarvis Runtime 入库边界的业务术语。

## 决策记录

- 这个判断类条目不应被 A 组确认带入库。

## 风险与待验证

- 血氧下限仍待医学验证。
""",
        encoding="utf-8",
    )
    (FIXTURE / "sources").mkdir(parents=True)
    (FIXTURE / "sources" / "宣传页-ocr.txt").write_text(
        "产品型号：K-S100Pro\n核心卖点：双水平无创通气支持\n适用场景：院内与居家延续管理\n",
        encoding="utf-8",
    )
    (FIXTURE / "sources" / "宣传页.pdf").write_text("fake pdf placeholder", encoding="utf-8")
    (topic / "evidence-pack-doc.fixture.json").write_text(
        """{
  "items": [
    {
      "id": "B9",
      "group": "B",
      "title": "运行时阶段结论",
      "claim": "Jarvis Runtime 的阶段结论应回写到业务文档中统一沉淀。",
      "knowledge_type": "decision",
      "knowledge_layer": "L3",
      "memory_type": "episodic",
      "source_type": "topic",
      "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
      "source_excerpt": "阶段结论需要归档到业务文档。",
      "evidence_level": "primary",
      "confidence": "high",
      "verification_status": "confirmed",
      "usage_scope": "knowledge_base",
      "can_ingest": "after_confirmation",
      "linked_topic": "贾维斯运行时架构迭代",
      "related_entries": [],
      "target_path": "业务/测试/运行时知识汇总.md",
      "requires_separate_confirmation": false
    }
  ]
}
""",
        encoding="utf-8",
    )
    # Multi-layer fixture evidence pack
    multi_layer_pack = topic / "multi-layer.fixture.json"
    multi_layer_pack.write_text(
        """{
  "items": [
    {
      "id": "T2-1",
      "group": "T",
      "title": "L2测试规则条目",
      "claim": "这是一条L2层级的关系/规则测试条目，用于验证业务文档自动创建。",
      "knowledge_type": "procedure",
      "knowledge_layer": "L2",
      "memory_type": "semantic",
      "source_type": "topic",
      "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
      "source_excerpt": "L2规则测试",
      "evidence_level": "primary",
      "confidence": "high",
      "verification_status": "verified",
      "usage_scope": "测试",
      "can_ingest": "after_confirmation",
      "linked_topic": "贾维斯运行时架构迭代",
      "target_path": "业务/测试/L2测试规则条目.md",
      "requires_separate_confirmation": false
    },
    {
      "id": "T3-1",
      "group": "T",
      "title": "L3测试决策条目",
      "claim": "这是一条L3层级的判断/决策测试条目，应生成人工入库计划而非自动写入。",
      "knowledge_type": "decision",
      "knowledge_layer": "L3",
      "memory_type": "episodic",
      "source_type": "topic",
      "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
      "source_excerpt": "L3决策测试",
      "evidence_level": "primary",
      "confidence": "high",
      "verification_status": "verified",
      "usage_scope": "测试",
      "can_ingest": "after_confirmation",
      "linked_topic": "贾维斯运行时架构迭代",
      "target_path": "业务/测试/L3测试决策条目.md",
      "requires_separate_confirmation": false
    },
    {
      "id": "T4-1",
      "group": "T",
      "title": "L4测试待验证条目",
      "claim": "这是一条L4层级的待验证问题测试条目，应注册到待验证问题追踪文件。",
      "knowledge_type": "procedure",
      "knowledge_layer": "L4",
      "memory_type": "semantic",
      "source_type": "topic",
      "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
      "source_excerpt": "L4待验证测试",
      "evidence_level": "primary",
      "confidence": "low",
      "verification_status": "needs_confirmation",
      "usage_scope": "测试",
      "can_ingest": "after_confirmation",
      "linked_topic": "贾维斯运行时架构迭代",
      "target_path": null,
      "requires_separate_confirmation": false
    },
    {
      "id": "TS-1",
      "group": "T",
      "title": "安全白名单测试安全收缩条目",
      "claim": "这条条目包含安全收缩关键词但因白名单不应被拦截。安全收缩是实施范围描述，非医学安全参数。",
      "knowledge_type": "fact",
      "knowledge_layer": "L1",
      "memory_type": "semantic",
      "source_type": "topic",
      "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
      "source_excerpt": "安全白名单测试",
      "evidence_level": "primary",
      "confidence": "high",
      "verification_status": "verified",
      "usage_scope": "测试",
      "can_ingest": "after_confirmation",
      "linked_topic": "贾维斯运行时架构迭代",
      "target_path": "知识库/术语/安全白名单测试术语.md",
      "requires_separate_confirmation": false
    }
  ]
}
""",
        encoding="utf-8",
    )
    (FIXTURE / "CLAUDE.md").write_text((REPO / "CLAUDE.md").read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copytree(REPO / ".claude" / "skills", FIXTURE / ".claude" / "skills")
    runtime_dst = FIXTURE / "智能体" / "贾维斯" / "runtime-v0.1"
    runtime_dst.mkdir(parents=True)
    for filename in ["JARVIS_BOOTSTRAP.md", "JARVIS_CORE.md"]:
        shutil.copy2(RUNTIME / filename, runtime_dst / filename)
    for dirname in ["references", "research-cards", "scripts", "skills"]:
        shutil.copytree(RUNTIME / dirname, runtime_dst / dirname)
    fake_sessions = FIXTURE / "home" / ".codex" / "sessions" / "2026" / "05" / "16"
    fake_sessions.mkdir(parents=True)
    (fake_sessions / "fixture-session.jsonl").write_text(
        '{"cwd":"' + str(FIXTURE) + '","message":"萃取一下这个 Topic"}\n',
        encoding="utf-8",
    )


def check_artifacts() -> None:
    assert_contains(REPO / "CLAUDE.md", ["JARVIS_BOOTSTRAP.md", "AGENT.md", "fallback"])
    if (FIXTURE / "智能体" / "贾维斯" / "AGENT.md").exists():
        fail("fixture must not contain AGENT.md")
    for card in (RUNTIME / "research-cards").glob("*.md"):
        assert_contains(card, [*RESEARCH_FIELDS, "source_revision"])
        if "/tmp/jarvis-runtime-research" in card.read_text(encoding="utf-8"):
            fail(f"{card} must not use non-durable /tmp source paths")
    if len(list((RUNTIME / "research-cards").glob("*.md"))) < 7:
        fail("expected at least 7 research cards")
    for script in REQUIRED_SCRIPTS:
        if not (RUNTIME / "scripts" / script).exists():
            fail(f"missing required script: {script}")
    pyc_files = list(RUNTIME.rglob("*.pyc"))
    if pyc_files:
        fail("runtime candidate contains generated bytecode", "\n".join(str(p) for p in pyc_files))
    # No direct rm/rmtree/unlink in scripts — must use jarvis_lib.trash_path
    for script in (RUNTIME / "scripts").glob("*.py"):
        text = script.read_text(encoding="utf-8")
        for banned in ("shutil.rmtree", "os.remove(", "os.unlink(", ".unlink()"):
            if banned in text:
                fail(f"{script.name}: banned direct delete '{banned}' — use trash_path() instead")
    bootstrap = (RUNTIME / "JARVIS_BOOTSTRAP.md").read_text(encoding="utf-8")
    required_section = bootstrap.split("## 按需读取", 1)[0]
    if "研究卡" in required_section:
        fail("research cards must not be in bootstrap required-read path")
    assert_text("bootstrap on-demand section", bootstrap, ["## 按需读取", "研究卡", "Re-Research Loop"])
    memory_reference = (RUNTIME / "references" / "memory-and-sources.md").read_text(encoding="utf-8")
    assert_text(
        "memory adapter boundary",
        memory_reference,
        ["记忆写入 adapter", "memory_commit: skipped_or_failed", "不得声称已写入 OpenViking"],
    )
    for spec in ["router-spec.md", "context-pack-spec.md", "evidence-pack-spec.md"]:
        text = (RUNTIME / "references" / spec).read_text(encoding="utf-8")
        if text.count("### ") < 10:
            fail(f"{spec} must contain at least 10 examples")
    for skill in SKILLS:
        path = REPO / ".claude" / "skills" / skill / "SKILL.md"
        if not path.exists():
            fail(f"missing skill: {skill}")
        assert_contains(path, SKILL_FIELDS)
    settings = (REPO / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert_text(
        ".claude/settings.json permissions",
        settings,
        ["Read(.claude/claudian-settings.json)", "Edit(智能体/贾维斯/AGENT.md)", "disableBypassPermissionsMode"],
    )


def check_scripts() -> None:
    scripts = RUNTIME / "scripts"
    for script in scripts.glob("*.py"):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            fail("python script compile failed", f"{script}: {exc}")
    commands = [
        [sys.executable, str(scripts / "validate_dashboard.py"), "--vault-root", str(FIXTURE)],
        [
            sys.executable,
            str(scripts / "create_topic.py"),
            "--vault-root",
            str(FIXTURE),
            "--title",
            "测试替换验收",
            "--scope",
            "测试 Jarvis Runtime 替换",
            "--date",
            "20260516",
            "--session-tool",
            "Codex Desktop",
            "--session-id",
            "fixture-create-session",
            "--session-jsonl",
            "/tmp/fixture-create-session.jsonl",
            "--session-cwd",
            str(FIXTURE),
            "--session-date",
            "2026-05-16",
        ],
        [
            sys.executable,
            str(scripts / "create_topic.py"),
            "--vault-root",
            str(FIXTURE),
            "--title",
            "测试替换验收",
            "--scope",
            "测试 Jarvis Runtime 替换",
            "--date",
            "20260516",
            "--session-tool",
            "Codex Desktop",
            "--session-id",
            "fixture-create-session",
            "--session-jsonl",
            "/tmp/fixture-create-session.jsonl",
            "--session-cwd",
            str(FIXTURE),
            "--session-date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "update_snapshot.py"),
            "--vault-root",
            str(FIXTURE),
            "--topic-dir",
            "platform-ops/topics/20260516_测试替换验收",
            "--last-action",
            "完成替换验收脚本测试",
            "--next-action",
            "生成 acceptance report",
            "--unresolved",
            "无",
            "--session-tool",
            "Codex Desktop",
            "--session-id",
            "fixture-freeze-session",
            "--session-jsonl",
            "/tmp/fixture-freeze-session.jsonl",
            "--session-cwd",
            str(FIXTURE),
            "--session-date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "update_snapshot.py"),
            "--vault-root",
            str(FIXTURE),
            "--topic-dir",
            "platform-ops/topics/20260516_测试替换验收",
            "--last-action",
            "关闭前最终会话同步",
            "--next-action",
            "等待林峰主动触发知识萃取",
            "--unresolved",
            "待萃取",
            "--session-tool",
            "Codex Desktop",
            "--session-id",
            "fixture-close-session",
            "--session-jsonl",
            "/tmp/fixture-close-session.jsonl",
            "--session-cwd",
            str(FIXTURE),
            "--session-date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "sync_topic_index.py"),
            "--vault-root",
            str(FIXTURE),
            "--topic-dir",
            "platform-ops/topics/20260516_测试替换验收",
            "--status",
            "paused",
            "--next-action",
            "等待反馈后继续",
            "--key-output",
            "替换验收脚本测试通过",
            "--timeline",
            "阶段冻结",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "update_topic_status.py"),
            "--vault-root",
            str(FIXTURE),
            "--topic-dir",
            "platform-ops/topics/20260516_测试替换验收",
            "--status",
            "paused",
            "--note",
            "替换验收脚本测试通过",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "update_topic_status.py"),
            "--vault-root",
            str(FIXTURE),
            "--topic-dir",
            "platform-ops/topics/20260516_测试替换验收",
            "--status",
            "pending_extraction",
            "--note",
            "关闭后进入待萃取，不自动入库",
            "--write",
        ],
        [sys.executable, str(scripts / "validate_links.py"), "--vault-root", str(FIXTURE), "--scope", "platform-ops/topics/20260516_测试替换验收"],
        [
            sys.executable,
            str(scripts / "locate_session_jsonl.py"),
            "--tool",
            "codex",
            "--cwd",
            str(FIXTURE),
            "--date",
            "2026-05-16",
            "--home",
            str(FIXTURE / "home"),
        ],
        [
            sys.executable,
            str(scripts / "knowledge_link_stats.py"),
            "--vault-root",
            str(FIXTURE),
            "--scope",
            "知识库",
            "--scope",
            "业务",
        ],
        [
            sys.executable,
            str(scripts / "append_operation_log.py"),
            "--vault-root",
            str(FIXTURE),
            "--type",
            "topic",
            "--summary",
            "创建 Topic: 测试替换验收",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "record_file_process.py"),
            "--vault-root",
            str(FIXTURE),
            "--source-file",
            "sources/宣传页.pdf",
            "--domain",
            "测试",
            "--title",
            "宣传页OCR整理",
            "--quality",
            "描述级",
            "--processed-in",
            "[[platform-ops/topics/20260516_贾维斯运行时架构迭代/索引|贾维斯运行时架构迭代]]",
            "--content-file",
            "sources/宣传页-ocr.txt",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "append_operation_log.py"),
            "--vault-root",
            str(FIXTURE),
            "--type",
            "other",
            "--summary",
            "文件处理产物: 宣传页OCR整理",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "sync_followup.py"),
            "--vault-root",
            str(FIXTURE),
            "--item",
            "等待王涛经理盲审反馈",
            "--window",
            "2026-05-20 前",
            "--status",
            "进行中",
            "--action",
            "收到反馈后汇总三方评分",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "append_operation_log.py"),
            "--vault-root",
            str(FIXTURE),
            "--type",
            "other",
            "--summary",
            "跟进事项: 等待王涛经理盲审反馈",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "confluence_query.py"),
            "--mode",
            "validate-config",
            "--cookie-file",
            str(FIXTURE / "platform-ops" / ".confluence-cookie"),
            "--base-url",
            "https://www.kf580.com/kd",
        ],
        [
            sys.executable,
            str(scripts / "extract_evidence_pack.py"),
            "--vault-root",
            str(FIXTURE),
            "--topic-dir",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代",
            "--source",
            "业务/测试/测试替换知识.md",
            "--session-jsonl",
            str(FIXTURE / "home" / ".codex" / "sessions" / "2026" / "05" / "16" / "fixture-session.jsonl"),
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "ingest_evidence_pack.py"),
            "--vault-root",
            str(FIXTURE),
            "--evidence-pack",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代/_evidence-pack.json",
            "--confirm-scope",
            "A",
            "--topic-dir",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "ingest_evidence_pack.py"),
            "--vault-root",
            str(FIXTURE),
            "--evidence-pack",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代/evidence-pack-doc.fixture.json",
            "--confirm-scope",
            "B",
            "--topic-dir",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [sys.executable, str(scripts / "validate_links.py"), "--vault-root", str(FIXTURE), "--scope", "知识库"],
        [sys.executable, str(scripts / "validate_links.py"), "--vault-root", str(FIXTURE), "--scope", "业务"],
        [
            sys.executable,
            str(scripts / "knowledge_link_stats.py"),
            "--vault-root",
            str(FIXTURE),
            "--scope",
            "知识库",
            "--scope",
            "业务",
        ],
        [
            sys.executable,
            str(scripts / "append_operation_log.py"),
            "--vault-root",
            str(FIXTURE),
            "--type",
            "ingest",
            "--summary",
            "知识入库: 测试替换术语",
            "--date",
            "2026-05-16",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "record_knowledge_feedback.py"),
            "--vault-root",
            str(FIXTURE),
            "--path",
            "知识库/术语/测试替换术语.md",
            "--feedback",
            "应用中发现语境过窄，先标存疑。",
            "--date",
            "2026-05-16",
            "--status",
            "存疑",
            "--write",
        ],
        [
            sys.executable,
            str(scripts / "append_operation_log.py"),
            "--vault-root",
            str(FIXTURE),
            "--type",
            "other",
            "--summary",
            "知识反馈: 测试替换术语 -> 存疑",
            "--date",
            "2026-05-16",
            "--write",
        ],
        # Phase A: multi-layer ingest
        [
            sys.executable,
            str(scripts / "ingest_evidence_pack.py"),
            "--vault-root",
            str(FIXTURE),
            "--evidence-pack",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代/multi-layer.fixture.json",
            "--confirm-scope",
            "T",
            "--topic-dir",
            "platform-ops/topics/20260516_贾维斯运行时架构迭代",
            "--date",
            "2026-05-16",
            "--skip-safety-check",
            "--write",
        ],
        [sys.executable, str(scripts / "validate_links.py"), "--vault-root", str(FIXTURE), "--scope", "知识库"],
        [sys.executable, str(scripts / "validate_links.py"), "--vault-root", str(FIXTURE), "--scope", "业务"],
        # Phase C: memcommit adapter syntax + payload validation (dry-run only)
        [
            sys.executable,
            str(scripts / "memcommit_adapter.py"),
            "--repo-root",
            str(FIXTURE),
            "--kind", "test",
            "--topic", "fixture-test",
            "--summary", "Test payload generation without writing.",
            "--fact", "Fixture-only test, no external service required.",
            "--decision", "Dry-run mode is default.",
        ],
    ]
    for command in commands:
        result = run(command)
        if result.returncode != 0:
            fail("script command failed", " ".join(command) + "\n" + result.stdout + result.stderr)
        if "validation result:" not in result.stdout:
            fail("script did not print validation result", " ".join(command))


def check_acceptance_cases() -> None:
    router = (RUNTIME / "references" / "router-spec.md").read_text(encoding="utf-8")
    context = (RUNTIME / "references" / "context-pack-spec.md").read_text(encoding="utf-8")
    evidence = (RUNTIME / "references" / "evidence-pack-spec.md").read_text(encoding="utf-8")
    extraction_reference = (RUNTIME / "references" / "knowledge-extraction.md").read_text(encoding="utf-8")
    core_text = (RUNTIME / "JARVIS_CORE.md").read_text(encoding="utf-8")
    memcommit_ref = (RUNTIME / "references" / "memory-and-sources.md").read_text(encoding="utf-8")
    help_skill = (REPO / ".claude" / "skills" / "jarvis-help" / "SKILL.md").read_text(encoding="utf-8")
    confluence_skill = (REPO / ".claude" / "skills" / "jarvis-confluence-read" / "SKILL.md").read_text(encoding="utf-8")
    file_process_skill = (REPO / ".claude" / "skills" / "jarvis-file-process" / "SKILL.md").read_text(encoding="utf-8")
    triage_skill = (REPO / ".claude" / "skills" / "jarvis-fragment-triage" / "SKILL.md").read_text(encoding="utf-8")
    followup_skill = (REPO / ".claude" / "skills" / "jarvis-followup-sync" / "SKILL.md").read_text(encoding="utf-8")
    feedback_skill = (REPO / ".claude" / "skills" / "jarvis-knowledge-feedback" / "SKILL.md").read_text(encoding="utf-8")
    close_skill = (REPO / ".claude" / "skills" / "jarvis-topic-close" / "SKILL.md").read_text(encoding="utf-8")
    extract_skill = (REPO / ".claude" / "skills" / "jarvis-knowledge-extract" / "SKILL.md").read_text(encoding="utf-8")
    ingest_skill = (REPO / ".claude" / "skills" / "jarvis-knowledge-ingest" / "SKILL.md").read_text(encoding="utf-8")
    status_skill = (REPO / ".claude" / "skills" / "jarvis-status" / "SKILL.md").read_text(encoding="utf-8")
    extracted_pack = (FIXTURE / "platform-ops" / "topics" / "20260516_贾维斯运行时架构迭代" / "_evidence-pack.json").read_text(encoding="utf-8")
    extracted_checklist = (FIXTURE / "platform-ops" / "topics" / "20260516_贾维斯运行时架构迭代" / "_萃取确认清单.md").read_text(encoding="utf-8")

    cases = {
        "近况查询": [
            (router, ["input: `最近怎么样`", "intent: status_query", "side_effect: read_only", "write_level: none"]),
            (context, ["task_type: status_query", "platform-ops/仪表盘.md"]),
            (status_skill, ["待萃取 Topic 列表", "跟进事项"]),
        ],
        "Confluence 读取": [
            (confluence_skill, ["只读，不写入本地文件", "Cookie 缺失 -> 直接报配置缺失"]),
            ((FIXTURE / "platform-ops" / ".confluence-cookie").read_text(encoding="utf-8"), ["JSESSIONID=fake-cookie"]),
        ],
        "文件处理产物": [
            (file_process_skill, ["先落可复核文档", "evidence_level=OCR文档解析"]),
            ((FIXTURE / "业务" / "测试" / "2026-05-16 测试-宣传页OCR整理.md").read_text(encoding="utf-8"), ["核心卖点：双水平无创通气支持", "## 人工复核", "evidence_level: OCR文档解析"]),
            ((FIXTURE / "知识库" / "wiki索引.md").read_text(encoding="utf-8"), ["宣传页OCR整理", "OCR / 文档解析产物"]),
            ((FIXTURE / "platform-ops" / "log.md").read_text(encoding="utf-8"), ["文件处理产物: 宣传页OCR整理"]),
        ],
        "碎片分流": [
            (triage_skill, ["fragment_type", "recommended_action", "needs_followup"]),
            ((RUNTIME / "references" / "conversation-governance.md").read_text(encoding="utf-8"), ["followup", "topic_switch", "quick_context"]),
        ],
        "Topic 恢复": [
            (router, ["input: `继续贾维斯运行时架构`", "intent: topic_resume", "write_level: none"]),
            (context, ["task_type: topic_resume", "_上下文快照.md", "讨论记录.md"]),
        ],
        "Topic 创建": [
            (router, ["intent: topic_create", "write_level: write_after_confirmation", "recommended_script: create_topic.py"]),
            ((FIXTURE / "platform-ops" / "topics" / "20260516_测试替换验收" / "索引.md").read_text(encoding="utf-8"), ["topic: 测试替换验收"]),
            ((FIXTURE / "platform-ops" / "仪表盘.md").read_text(encoding="utf-8"), ["测试替换验收"]),
            ((FIXTURE / "platform-ops" / "topics" / "20260516_测试替换验收" / "_上下文快照.md").read_text(encoding="utf-8"), ["fixture-create-session", "/tmp/fixture-create-session.jsonl"]),
            ((FIXTURE / "platform-ops" / "log.md").read_text(encoding="utf-8"), ["创建 Topic: 测试替换验收"]),
        ],
        "跟进事项": [
            (followup_skill, ["跟进事项写入计划", "validation result"]),
            ((FIXTURE / "platform-ops" / "仪表盘.md").read_text(encoding="utf-8"), ["等待王涛经理盲审反馈", "2026-05-20 前", "收到反馈后汇总三方评分"]),
            ((FIXTURE / "platform-ops" / "log.md").read_text(encoding="utf-8"), ["跟进事项: 等待王涛经理盲审反馈"]),
        ],
        "明确边界": [
            (router, ["input: `不要动原文件，只给方案`", "intent: analysis_only", "write_level: none"]),
        ],
        "高风险边界": [
            (router, ["input: `直接改 AGENT.md`", "intent: high_risk_edit_request", "high_risk_explicit_confirmation"]),
        ],
        "Topic 冻结": [
            ((FIXTURE / "platform-ops" / "topics" / "20260516_测试替换验收" / "_上下文快照.md").read_text(encoding="utf-8"), ["完成替换验收脚本测试", "fixture-freeze-session", "/tmp/fixture-freeze-session.jsonl"]),
            ((FIXTURE / "platform-ops" / "topics" / "20260516_测试替换验收" / "索引.md").read_text(encoding="utf-8"), ["替换验收脚本测试通过", "2026-05-16 阶段冻结"]),
        ],
        "Topic 关闭": [
            (router, ["input: `这个 Topic 收一下`", "intent: topic_close", "recommended_skill: jarvis-topic-close"]),
            (close_skill, ["pending_extraction", "不自动萃取", "不生成知识库条目"]),
            (extraction_reference, ["明确不触发萃取", "这些请求应先走 `jarvis-topic-close`"]),
            ((FIXTURE / "platform-ops" / "topics" / "20260516_测试替换验收" / "索引.md").read_text(encoding="utf-8"), ["status: pending_extraction", "[📋 待萃取]"]),
            ((FIXTURE / "platform-ops" / "仪表盘.md").read_text(encoding="utf-8"), ["## 待萃取", "[📋 待萃取]", "测试替换验收"]),
            ((FIXTURE / "platform-ops" / "topics" / "20260516_测试替换验收" / "_上下文快照.md").read_text(encoding="utf-8"), ["fixture-close-session", "/tmp/fixture-close-session.jsonl"]),
        ],
        "知识萃取": [
            (extract_skill, ["Evidence Pack", "确认清单", "只生成候选，不写知识库"]),
            (evidence, ["source_type: session_jsonl", "verification_status: needs_source", "can_ingest: false", "knowledge_layer:"]),
            (extracted_pack, ["测试替换术语", "\"knowledge_layer\": \"L1\"", "\"group\": \"A\"", "\"source_type\": \"session_jsonl\""]),
            (extracted_checklist, ["# 萃取确认清单", "## A. 可快速确认", "## B. 需要林峰拍板", "## C. 需要验证"]),
        ],
        "知识入库": [
            (ingest_skill, ["只处理林峰明确确认的组或条目", "knowledge_link_stats.py", "不能把 `candidate_only` 或 `needs_source` 条目写入正式知识库", "人工入库计划"]),
            ((FIXTURE / "知识库" / "术语" / "测试替换术语.md").read_text(encoding="utf-8"), ["测试替换术语是用于验证 Jarvis Runtime 入库边界的业务术语"]),
            ((FIXTURE / "知识库" / "wiki索引.md").read_text(encoding="utf-8"), ["测试替换术语"]),
            ((FIXTURE / "知识库" / "术语" / "术语索引.md").read_text(encoding="utf-8"), ["测试替换术语"]),
            ((FIXTURE / "业务" / "测试" / "运行时知识汇总.md").read_text(encoding="utf-8"), ["## 萃取补充", "Jarvis Runtime 的阶段结论应回写到业务文档中统一沉淀。"]),
            ((FIXTURE / "知识库" / "wiki索引.md").read_text(encoding="utf-8"), ["运行时阶段结论"]),
            ((FIXTURE / "platform-ops" / "log.md").read_text(encoding="utf-8"), ["知识入库: 测试替换术语"]),
        ],
        "知识反馈": [
            (feedback_skill, ["应用反馈", "存疑", "建议进入跟进事项"]),
            ((FIXTURE / "知识库" / "术语" / "测试替换术语.md").read_text(encoding="utf-8"), ["status: 存疑", "## 应用反馈", "应用中发现语境过窄，先标存疑。"]),
            ((FIXTURE / "知识库" / "wiki索引.md").read_text(encoding="utf-8"), ["测试替换术语", "存疑"]),
            ((FIXTURE / "知识库" / "术语" / "术语索引.md").read_text(encoding="utf-8"), ["测试替换术语", "存疑"]),
            ((FIXTURE / "platform-ops" / "log.md").read_text(encoding="utf-8"), ["知识反馈: 测试替换术语 -> 存疑"]),
        ],
        "源码借鉴体现": [
            (help_skill, ["为什么 Context Pack 这样设计", "研究卡"]),
            (context, ["为什么 Context Pack 这样设计", "Obsidian-Copilot.md", "Khoj.md"]),
        ],
        "L2业务文档创建": [
            ((FIXTURE / "业务" / "测试" / "L2测试规则条目.md").read_text(encoding="utf-8"), ["L2测试规则条目", "L2层级的关系/规则测试"]),
            ((FIXTURE / "知识库" / "wiki索引.md").read_text(encoding="utf-8"), ["L2测试规则条目"]),
        ],
        "L3人工入库计划": [
            ((FIXTURE / "platform-ops" / "topics" / "20260516_贾维斯运行时架构迭代" / "_人工入库计划.md").read_text(encoding="utf-8"), ["L3测试决策条目", "人工入库计划", "建议落点"]),
        ],
        "L4待验证问题": [
            ((FIXTURE / "知识库" / "待验证问题.md").read_text(encoding="utf-8"), ["L4测试待验证条目", "待验证"]),
        ],
        "安全白名单不误拦": [
            ((FIXTURE / "知识库" / "术语" / "安全白名单测试术语.md").read_text(encoding="utf-8"), ["安全收缩关键词但因白名单不应被拦截"]),
        ],
        "术语索引列表格式": [
            ((FIXTURE / "知识库" / "术语" / "术语索引.md").read_text(encoding="utf-8"), ["- [[知识库/术语/安全白名单测试术语|安全白名单测试术语]]"]),
        ],
        "memcommit集成验证": [
            ((REPO / ".claude" / "skills" / "jarvis-topic-freeze" / "SKILL.md").read_text(encoding="utf-8"), ["memcommit_adapter.py"]),
            ((REPO / ".claude" / "skills" / "jarvis-topic-close" / "SKILL.md").read_text(encoding="utf-8"), ["memcommit_adapter.py"]),
            (memcommit_ref, ["memory_commit: skipped_or_failed", "不得声称已写入 OpenViking"]),
            ((REPO / ".claude" / "skills" / "jarvis-topic-freeze" / "SKILL.md").read_text(encoding="utf-8"), ["memcommit_adapter.py --write", "git commit -m"]),
            ((REPO / ".claude" / "skills" / "jarvis-topic-close" / "SKILL.md").read_text(encoding="utf-8"), ["memcommit_adapter.py --write", "git commit -m"]),
        ],
        "memcommit spec一致性": [
            (core_text, ["DeepSeek adapter 是否影响现有 Topic 状态同步"]),
        ],
    }

    for case_name, checks in cases.items():
        for i, (text, needles) in enumerate(checks, start=1):
            assert_text(f"acceptance case {case_name} check {i}", text, needles)
    for forbidden in [
        FIXTURE / "知识库" / "术语" / "不应入库判断.md",
        FIXTURE / "知识库" / "术语" / "缺来源术语.md",
    ]:
        if forbidden.exists():
            fail(f"forbidden ingest file exists: {forbidden}")

    result = run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from pathlib import Path; from jarvis_lib import prepare_change; "
            "prepare_change(Path('智能体/贾维斯/AGENT.md'), 'x')",
            str(RUNTIME / "scripts"),
        ]
    )
    if result.returncode == 0 or "refuse to modify high-risk file" not in (result.stdout + result.stderr):
        fail("AGENT.md high-risk write guard did not fire")

    report = (RUNTIME / "acceptance-report.md").read_text(encoding="utf-8")
    assert_text(
        "acceptance report replacement status",
        report,
        ["Gate 5 真实项目试点 | Pass", "日常入口试点通过"],
    )

    # L3 items should NOT create business doc files (plan only)
    for forbidden in [
        FIXTURE / "业务" / "测试" / "L3测试决策条目.md",
    ]:
        if forbidden.exists():
            fail(f"L3 item should not auto-create doc file: {forbidden}")

    # Cross-file consistency: acceptance-report ↔ pilot-report
    pilot = (RUNTIME / "pilot-report.md").read_text(encoding="utf-8")
    # Semantic contradiction: pilot says unfinished but report says passed
    if ("Gate 5 未完成" in pilot or "需重新执行" in pilot) and "Gate 5 真实项目试点 | Pass" in report:
        fail("pilot-report says Gate 5 unfinished but acceptance-report says Pass — cross-file contradiction")
    # Semantic contradiction: pilot says 0/5 but report says 5/5
    if "Passed tasks | 0" in pilot and "5/5" in report:
        fail("pilot-report says 0 tasks passed but acceptance-report claims 5/5 — cross-file contradiction")
    # Semantic contradiction: pilot says full-replacement but report says pilot-pass only
    if "达到签字级完全替代" in pilot and "日常入口试点通过" in report:
        fail("pilot-report claims 签字级完全替代 but acceptance-report says 日常试点 — cross-file contradiction")


def main() -> int:
    build_fixture()
    check_artifacts()
    check_scripts()
    check_acceptance_cases()
    print("PASS: Jarvis Runtime v0.1 replacement checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
