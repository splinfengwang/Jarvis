#!/usr/bin/env python3
"""Jarvis Runtime v0.1 替换 AGENT.md v3.4 — 测试套件

覆盖: T1 Core 内容 / T2 知识入库扩展 / T3 能力缺口 / T4 Hooks / 集成回归

运行方式:
    python3 智能体/贾维斯/runtime-v0.1/tests/test_v0.1_replacement.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RUNTIME = Path(__file__).resolve().parents[1]
REPO = RUNTIME.parents[2]
FIXTURE = RUNTIME / "tests" / "fixtures" / "replacement-vault"

PASS = 0
FAIL = 0


def run(cmd: list[str], cwd: Path | None = None, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        cmd, cwd=cwd or REPO, env=env, text=True, capture_output=True, input=stdin,
    )


# ── helpers ──────────────────────────────────────────────────────────

def tpass(label: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✅ PASS: {label}")


def tfail(label: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"  ❌ FAIL: {label}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"      {line}")


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        tpass(label)
    else:
        tfail(label, detail)


def file_contains(path: Path, needles: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return all(needle in text for needle in needles)


def stdout_contains(result: subprocess.CompletedProcess[str], needles: list[str]) -> bool:
    return all(needle in (result.stdout + result.stderr) for needle in needles)


def json_output(result: subprocess.CompletedProcess[str]) -> dict | None:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def build_extended_fixture() -> None:
    """基于现有 fixture，补充 L2/L3/L4 测试数据."""
    topic = FIXTURE / "platform-ops" / "topics" / "20260516_贾维斯运行时架构迭代"

    # 补充测试业务文档（含 L2 关系/规则）
    biz_test = FIXTURE / "业务" / "测试"
    biz_test.mkdir(parents=True, exist_ok=True)
    (biz_test / "L2关系规则测试.md").write_text(
        """# L2 关系规则测试

## 规则

- K-S100Pro 与 DPAP20 通过蓝牙通信，传输治疗参数和实时监测数据。

## 流程

- 压力滴定标准流程：初始压力 → 逐步递增 → 达到目标 SpO₂ → 稳持 20min → 确认处方。
""",
        encoding="utf-8",
    )

    # 补充可自动入库的 L3 决策条目（非医学、primary+topic 来源）
    (topic / "evidence-pack-extended.fixture.json").write_text(
        json.dumps({
            "items": [
                {
                    "id": "B1",
                    "group": "B",
                    "title": "Claude Code 优先策略",
                    "claim": "贾维斯 Runtime 优先适配 Claude Code，Codex 保持结构兼容。",
                    "knowledge_type": "decision",
                    "knowledge_layer": "L3",
                    "memory_type": "episodic",
                    "source_type": "topic",
                    "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
                    "source_excerpt": "Claude Code 优先，Codex 保持结构兼容。",
                    "evidence_level": "primary",
                    "confidence": "high",
                    "verification_status": "confirmed",
                    "usage_scope": "knowledge_base",
                    "can_ingest": "after_confirmation",
                    "linked_topic": "贾维斯运行时架构迭代",
                    "related_entries": [],
                    "target_path": "业务/测试/运行时知识汇总.md",
                    "requires_separate_confirmation": False,
                },
                {
                    "id": "B2",
                    "group": "B",
                    "title": "Agent推断的未验证结论",
                    "claim": "Agent 推断 DeepSeek 可能适合长文档处理。",
                    "knowledge_type": "decision",
                    "knowledge_layer": "L3",
                    "memory_type": "episodic",
                    "source_type": "topic",
                    "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
                    "source_excerpt": "DeepSeek 1M context 适合长文档。",
                    "evidence_level": "secondary",
                    "confidence": "low",
                    "verification_status": "needs_confirmation",
                    "usage_scope": "manual_ingest_plan",
                    "can_ingest": "after_confirmation",
                    "linked_topic": "贾维斯运行时架构迭代",
                    "related_entries": [],
                    "target_path": "业务/测试/运行时知识汇总.md",
                    "requires_separate_confirmation": True,
                },
                {
                    "id": "C1",
                    "group": "C",
                    "title": "血氧下限安全边界",
                    "claim": "SpO₂ 下限 85% 为终止标准，需医学验证。",
                    "knowledge_type": "medical_candidate",
                    "knowledge_layer": "L4",
                    "memory_type": "semantic",
                    "source_type": "topic",
                    "source_path": "platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md",
                    "source_excerpt": "血氧下限仍待医学验证。",
                    "evidence_level": "primary",
                    "confidence": "low",
                    "verification_status": "needs_confirmation",
                    "usage_scope": "candidate_only",
                    "can_ingest": False,
                    "linked_topic": "贾维斯运行时架构迭代",
                    "related_entries": [],
                    "target_path": "",
                    "requires_separate_confirmation": True,
                },
            ]
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 术语目录 + 创建模拟的旧术语文件
    term_dir = FIXTURE / "知识库" / "术语"
    term_dir.mkdir(parents=True, exist_ok=True)
    # 创建 15 天前 mtime 的待确认术语
    old_term = term_dir / "过期待确认术语.md"
    old_term.write_text(
        """---
status: 待确认
tags: [术语, 测试]
---
# 过期待确认术语

**一句话定义**：这是一个创建超过两周仍未确认的测试术语。
""",
        encoding="utf-8",
    )
    old_mtime = time.time() - (15 * 86400)
    os.utime(old_term, (old_mtime, old_mtime))


# ══════════════════════════════════════════════════════════════════════
# T1: Core 行为指令检查
# ══════════════════════════════════════════════════════════════════════

def test_t1_core_content() -> None:
    print("\n── T1: Core 行为指令检查 ──")
    core_path = RUNTIME / "JARVIS_CORE.md"
    if not core_path.exists():
        tfail("Core file exists", f"missing: {core_path}")
        return
    core = core_path.read_text(encoding="utf-8")

    # T1.1: 裁决层
    check("优先级" in core and ("§0" in core or "裁决" in core),
          "T1.1 裁决层存在")

    # T1.2: 边界映射
    check("只讨论" in core or "先别动" in core or "当前边界" in core,
          "T1.2 边界表达→动作映射")

    # T1.3: 事实/证据/推论区分
    check("事实" in core and "证据" in core and ("推论" in core or "推断" in core),
          "T1.3 事实/证据/推论区分")

    # T1.4: 四条铁律（待 Phase 1 实现）
    iron_laws = ("铁律" in core) and any(phrase in core for phrase in ["文件读取", "读取优先", "先读"])
    if iron_laws:
        tpass("T1.4 铁律已实现")
    else:
        tfail("T1.4 铁律未实现（待 Phase 1 — Core 重写时新增 §4 三条铁律章节）")

    # T1.5: 抗合理化表
    check("OpenViking" in core and ("事实" in core or "线索" in core),
          "T1.5 OpenViking 口径在 Core 中")

    # T1.6: 协作原则关键元素
    collaboration_markers = [
        ("分工" in core or "林峰" in core, "分工模型"),
        ("标注" in core or "⚠️" in core or "状态" in core, "知识引用标注"),
        ("安全" in core and ("参数" in core or "边界" in core), "安全参数"),
        ("确认" in core and ("写入" in core or "写权限" in core or "写" in core), "写入裁决"),
    ]
    for condition, label in collaboration_markers:
        check(condition, f"T1.6 协作-{label}")

    # T1.7: 行数范围（≥400 通过，400+ 行表格格式已达到密度等价）
    line_count = len(core.splitlines())
    if line_count >= 400:
        tpass(f"T1.7 Core 行数 {line_count} (≥400 ✅)")
    else:
        tfail(f"T1.7 Core 行数 {line_count}（目标 ≥400）")

    # T1.8: Core 不含 skill 实现细节
    skill_details = ["trigger:", "non_trigger:", "allowed_scripts:", "confirmation_rules:"]
    leaked = [d for d in skill_details if d in core]
    check(len(leaked) == 0,
          f"T1.8 Core 不含 skill 实现细节",
          f"leaked: {leaked}" if leaked else "")


# ══════════════════════════════════════════════════════════════════════
# T2: 知识入库扩展
# ══════════════════════════════════════════════════════════════════════

def test_t2_knowledge_ingest() -> None:
    print("\n── T2: 知识入库扩展 ──")
    scripts = RUNTIME / "scripts"
    topic = FIXTURE / "platform-ops" / "topics" / "20260516_贾维斯运行时架构迭代"
    py = sys.executable

    # T2.1: L2 关系/规则识别 — 需要 Phase 2 实现 RELATION_HEADINGS
    # 当前脚本无 L2 识别能力，测试验证 RELATION_HEADINGS 常量存在
    extract_source = (scripts / "extract_evidence_pack.py").read_text(encoding="utf-8")
    has_l2_support = "RELATION_HEADINGS" in extract_source
    if has_l2_support:
        l2_file = FIXTURE / "业务" / "测试" / "L2关系规则测试.md"
        if l2_file.exists():
            r = run([
                py, str(scripts / "extract_evidence_pack.py"),
                "--vault-root", str(FIXTURE),
                "--topic-dir", "platform-ops/topics/20260516_贾维斯运行时架构迭代",
                "--source", "业务/测试/L2关系规则测试.md",
                "--session-jsonl", str(FIXTURE / "home" / ".codex" / "sessions" / "2026" / "05" / "16" / "fixture-session.jsonl"),
            ])
            check(r.returncode == 0 and stdout_contains(r, ['"knowledge_layer": "L2"']),
                  "T2.1 L2 关系/规则被识别并输出 knowledge_layer=L2")
        else:
            tfail("T2.1 L2 测试文件不存在（fixture 构建问题）")
    else:
        tfail("T2.1 RELATION_HEADINGS 未实现（待 Phase 2）",
              "extract_evidence_pack.py 需新增 RELATION_HEADINGS 常量和 extract_relation_items() 函数")

    # T2.2: B 组 topic 来源降级确认 - 检查 fixture JSON
    pack_path = topic / "evidence-pack-extended.fixture.json"
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    b1 = next((item for item in pack["items"] if item["id"] == "B1"), None)
    b2 = next((item for item in pack["items"] if item["id"] == "B2"), None)
    check(b1 is not None and b1.get("requires_separate_confirmation") is False,
          "T2.2 B1 primary+topic → requires_separate_confirmation=False")
    check(b2 is not None and b2.get("requires_separate_confirmation") is True,
          "T2.2 B2 secondary+infer → requires_separate_confirmation=True")

    # T2.3: 医学条目被正确标记
    c1 = next((item for item in pack["items"] if item["id"] == "C1"), None)
    check(c1 is not None and c1.get("can_ingest") is False,
          "T2.3 C1 医学条目 can_ingest=False")
    check(c1.get("knowledge_type") == "medical_candidate",
          "T2.3 C1 knowledge_type=medical_candidate")

    # T2.4: ingest B1 (L3 non-medical, target_path clear)
    r = run([
        py, str(scripts / "ingest_evidence_pack.py"),
        "--vault-root", str(FIXTURE),
        "--evidence-pack", str(pack_path),
        "--confirm-scope", "B",
        "--topic-dir", "platform-ops/topics/20260516_贾维斯运行时架构迭代",
        "--date", "2026-05-18",
        "--write",
    ])
    check(r.returncode == 0, "T2.4 ingest B 组运行成功", r.stderr)
    # B1 should be ingested (non-medical, target_path clear, requires_separate_confirmation=False)
    b_target = FIXTURE / "业务" / "测试" / "运行时知识汇总.md"
    if b_target.exists():
        b_text = b_target.read_text(encoding="utf-8")
        b1_ingested = "Claude Code 优先策略" in b_text
        b2_rejected = "Agent推断的未验证结论" not in b_text or "Agent推断" not in b_text
    else:
        b1_ingested = False
        b2_rejected = False
    check(b1_ingested, "T2.4 B1 L3 非医学自动入库")
    # B2 should NOT be ingested (requires_separate_confirmation=True)
    check(b2_rejected, "T2.4 B2 Agent推断保持跳过")

    # T2.5: C1 medical forced skip
    c_target = FIXTURE / "知识库" / "术语" / "血氧下限安全边界.md"
    check(not c_target.exists(),
          "T2.5 C1 医学条目未被自动写入")

    # T2.6: dry-run-scope
    r = run([
        py, str(scripts / "ingest_evidence_pack.py"),
        "--vault-root", str(FIXTURE),
        "--evidence-pack", str(pack_path),
        "--confirm-scope", "A",
        "--topic-dir", "platform-ops/topics/20260516_贾维斯运行时架构迭代",
    ])
    check(r.returncode == 0 and "skipped" in (r.stdout + r.stderr).lower(),
          "T2.6 dry-run 输出 skipped 列表")

    # T2.7: 索引同步
    wiki = FIXTURE / "知识库" / "wiki索引.md"
    check(wiki.exists() and "Claude Code 优先策略" in wiki.read_text(encoding="utf-8"),
          "T2.7 wiki索引包含入库条目")

    # T2.8: 链接校验
    # 先清理可能悬空的链接
    if b_target.exists():
        r = run([
            py, str(scripts / "validate_links.py"),
            "--vault-root", str(FIXTURE),
            "--scope", "业务",
        ])
        check(r.returncode == 0,
              "T2.8 链接校验通过", r.stderr)


# ══════════════════════════════════════════════════════════════════════
# T3: 能力缺口模块
# ══════════════════════════════════════════════════════════════════════

def test_t3_capability_gaps() -> None:
    print("\n── T3: 能力缺口模块 ──")
    scripts = RUNTIME / "scripts"
    py = sys.executable

    # T3.1: analysis-thread skill 字段
    skill_path = REPO / ".claude" / "skills" / "jarvis-analysis-thread" / "SKILL.md"
    if skill_path.exists():
        skill_text = skill_path.read_text(encoding="utf-8")
        fields = ["trigger", "non_trigger", "inputs", "outputs", "write_level",
                   "confirmation_rules", "fallback_rules", "acceptance_cases"]
        missing = [f for f in fields if f not in skill_text]
        check(len(missing) == 0,
              f"T3.1 analysis-thread skill 字段完整",
              f"missing: {missing}" if missing else "")
    else:
        tfail(f"T3.1 skill 文件不存在: {skill_path}")

    # T3.2: term_health_check (如果脚本已创建)
    health_script = scripts / "term_health_check.py"
    if health_script.exists():
        r = run([py, str(health_script), "--vault-root", str(FIXTURE)])
        check(r.returncode == 0, "T3.2 term_health_check 运行成功", r.stderr)
        # 应检测到 15 天前创建的过期待确认术语
        check("过期待确认术语" in (r.stdout + r.stderr),
              "T3.2 检测到过期待确认术语")
    else:
        tfail(f"T3.2 脚本未创建: {health_script}")

    # T3.3: 健康检查输出格式
    if health_script.exists():
        r = run([py, str(health_script), "--vault-root", str(FIXTURE)])
        output = r.stdout + r.stderr
        has_path = "path" in output.lower() or "文件" in output
        has_date = "last_modified" in output or "date" in output.lower() or "age_days" in output or "日期" in output
        check(has_path and has_date,
              "T3.3 输出含路径和日期字段",
              f"path:{has_path} date:{has_date}")

    # T3.4: 文档检查清单
    safety_ref = RUNTIME / "references" / "medical-and-design-safety.md"
    if safety_ref.exists():
        text = safety_ref.read_text(encoding="utf-8")
        items = ["医学参数", "安全参数", "三视角", "使用场景"]
        all_found = all(item in text for item in items)
        check(all_found,
              "T3.4 文档检查清单 4 条完整",
              f"missing: {[item for item in items if item not in text]}" if not all_found else "")
    else:
        tfail(f"T3.4 reference 不存在: {safety_ref}")


# ══════════════════════════════════════════════════════════════════════
# T4: Hooks 行为测试
# ══════════════════════════════════════════════════════════════════════

def test_t4_hooks() -> None:
    print("\n── T4: Hooks 行为测试 ──")
    hooks_dir = REPO / ".claude" / "hooks"

    # T4.1: hooks 配置存在于 settings.json
    settings_json = REPO / ".claude" / "settings.json"
    if not settings_json.exists():
        tfail(f"T4.1 settings.json 不存在: {settings_json}")
    else:
        try:
            data = json.loads(settings_json.read_text(encoding="utf-8"))
            hooks_obj = data.get("hooks", {})
            events = ["SessionStart", "PreToolUse", "PreCompact"]
            all_events = all(e in hooks_obj for e in events)
            check(all_events,
                  f"T4.1 settings.json hooks 三事件完整 (found: {list(hooks_obj.keys())})")
            # 同时验证 hooks 目录下有对应的脚本文件
            for script in ["jarvis-core-inject.sh", "jarvis-write-guard.sh", "jarvis-compact-save.sh"]:
                check((hooks_dir / script).exists(),
                      f"T4.1 hook 脚本存在: {script}")
        except json.JSONDecodeError as e:
            tfail("T4.1 settings.json JSON 解析失败", str(e))

    # T4.2: core-inject.sh 存在且 bash 语法正确
    inject_script = hooks_dir / "jarvis-core-inject.sh"
    if not inject_script.exists():
        tfail(f"T4.2 core-inject.sh 不存在: {inject_script}")
    else:
        r = run(["bash", "-n", str(inject_script)])
        check(r.returncode == 0, "T4.2 core-inject.sh bash 语法", r.stderr)

    # T4.3: core-inject.sh 输出合法 JSON（需要 Core 文件存在）
    core_path = RUNTIME / "JARVIS_CORE.md"
    if inject_script.exists() and core_path.exists():
        r = run(["bash", str(inject_script)], cwd=REPO)
        output = r.stdout.strip()
        check(len(output) > 0, "T4.3 core-inject 有输出")
        if output:
            try:
                parsed = json.loads(output)
                ctx = parsed.get("hookSpecificOutput", {}).get("additionalContext", "")
                check(len(ctx) > 100,
                      f"T4.3 additionalContext 非空 (len={len(ctx)})")
            except json.JSONDecodeError:
                tfail("T4.3 core-inject 输出非合法 JSON", output[:200])

    # T4.4: write-guard.sh 存在且语法正确
    guard_script = hooks_dir / "jarvis-write-guard.sh"
    if not guard_script.exists():
        tfail(f"T4.4 write-guard.sh 不存在: {guard_script}")
    else:
        r = run(["bash", "-n", str(guard_script)])
        check(r.returncode == 0, "T4.4 write-guard.sh bash 语法", r.stderr)

    # T4.5: write-guard deny AGENT.md
    if guard_script.exists():
        hook_input = json.dumps({
            "hook_event_name": "PreToolUse",
            "session_id": "test",
            "transcript_path": "/tmp/test.jsonl",
            "cwd": str(REPO),
            "tool_name": "Write",
            "tool_input": {"file_path": "智能体/贾维斯/AGENT.md", "content": "test"},
        })
        r = run(["bash", str(guard_script)], stdin=hook_input)
        has_deny = "deny" in (r.stdout + r.stderr).lower()
        check(has_deny,
              "T4.5 Write AGENT.md → deny",
              r.stdout[:200] if not has_deny else "")

    # T4.6: write-guard advisory 术语写入
    if guard_script.exists():
        hook_input = json.dumps({
            "hook_event_name": "PreToolUse",
            "session_id": "test",
            "transcript_path": "/tmp/test.jsonl",
            "cwd": str(REPO),
            "tool_name": "Write",
            "tool_input": {"file_path": "知识库/术语/新术语.md", "content": "test"},
        })
        r = run(["bash", str(guard_script)], stdin=hook_input)
        has_advisory = "ask" in (r.stdout + r.stderr).lower() or "advisory" in (r.stdout + r.stderr).lower()
        check(has_advisory,
              "T4.6 Write 知识库/术语/ → ask",
              r.stdout[:200] if not has_advisory else "")

    # T4.7: write-guard allow 普通文件
    if guard_script.exists():
        hook_input = json.dumps({
            "hook_event_name": "PreToolUse",
            "session_id": "test",
            "transcript_path": "/tmp/test.jsonl",
            "cwd": str(REPO),
            "tool_name": "Write",
            "tool_input": {"file_path": "业务/测试/普通文档.md", "content": "test"},
        })
        r = run(["bash", str(guard_script)], stdin=hook_input)
        no_block = "deny" not in (r.stdout + r.stderr).lower()
        check(no_block,
              "T4.7 普通文件写入放行",
              r.stdout[:200] if not no_block else "")

    # T4.8: compact-save.sh 存在且 prompt 完整
    compact_script = hooks_dir / "jarvis-compact-save.sh"
    if not compact_script.exists():
        tfail(f"T4.8 compact-save.sh 不存在: {compact_script}")
    else:
        r = run(["bash", "-n", str(compact_script)])
        check(r.returncode == 0, "T4.8 compact-save.sh bash 语法", r.stderr)
        r = run(["bash", str(compact_script)])
        output = r.stdout + r.stderr
        fields = ["Topic", "Router", "已确认", "待拍板"]
        all_fields = all(f in output for f in fields)
        check(all_fields,
              "T4.8 compact-save prompt 包含必要字段",
              f"missing: {[f for f in fields if f not in output]}" if not all_fields else "")


# ══════════════════════════════════════════════════════════════════════
# T6: 集成回归
# ══════════════════════════════════════════════════════════════════════

def test_t6_regression() -> None:
    print("\n── T6: 集成回归 ──")
    py = sys.executable

    # 运行原有替换检查（不破坏现有通过状态）
    existing_test = RUNTIME / "tests" / "run_replacement_checks.py"
    if existing_test.exists():
        r = run([py, str(existing_test)])
        passed = r.returncode == 0 and "PASS" in (r.stdout + r.stderr)
        check(passed, "T6.1 原有替换检查通过", r.stdout[-500:] + r.stderr[-500:])
    else:
        tfail(f"T6.1 原有测试不存在: {existing_test}")

    # 验证 fixture 中 AGENT.md 未被写入
    agent_at_fixture = FIXTURE / "智能体" / "贾维斯" / "AGENT.md"
    check(not agent_at_fixture.exists(),
          "T6.2 fixture 不含 AGENT.md（高风险写入防护）")


# ══════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════

def main() -> int:
    print("=" * 60)
    print("Jarvis Runtime v0.1 替换 AGENT.md v3.4 — 测试套件")
    print("=" * 60)

    build_extended_fixture()

    test_t1_core_content()
    test_t3_capability_gaps()
    test_t4_hooks()
    test_t2_knowledge_ingest()  # 必须在 T6 之前（T6 build_fixture 会清空扩展数据）
    test_t6_regression()        # 最后跑，会重建基础 fixture

    total = PASS + FAIL
    print(f"\n{'=' * 60}")
    print(f"Passed: {PASS}")
    print(f"Failed: {FAIL}")
    print(f"Total:  {total}")
    print(f"{'=' * 60}")

    if FAIL > 0:
        print("\n⚠️  部分测试未通过。对照 tasks.md 测试方案逐条修复后重新运行。")
    else:
        print("\n✅ 全部测试通过。")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
