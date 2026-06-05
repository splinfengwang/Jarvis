#!/usr/bin/env python3
"""Jarvis 技能规范优化 — 回归测试套件

覆盖:
  T1 — 所有 skill 的 YAML frontmatter 完整性
  T2 — Body 中无 trigger/non_trigger/acceptance_cases 残留
  T3 — confirmation_rules/fallback_rules 含 CORE 引用
  T4 — create_topic.py 骨架完整性
  T5 — CORE_BRIEF 关键规则
  T6 — knowledge-model 正确归类
  T7 — help/status 描述正交性
  T8 — CORE_FULL 版本与路由表
  T9 — roundtable 无 trigger 残留

运行方式:
    python3 jarvis/tests/test_skill_spec.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "jarvis" / "skills"
CORE_DIR = REPO / "jarvis" / "core"
REFS = REPO / "jarvis" / "references"

PASS = 0
FAIL = 0

def tpass(label: str) -> None:
    global PASS; PASS += 1
    print(f"  ✅  {label}")

def tfail(label: str, detail: str = "") -> None:
    global FAIL; FAIL += 1
    print(f"  ❌  {label}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"      {line}")

def check(cond: bool, label: str, detail: str = "") -> None:
    tpass(label) if cond else tfail(label, detail)

def skill_list() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))

def skill_name(p: Path) -> str:
    return p.parent.name


def test_t1_frontmatter() -> None:
    print("\n── T1: YAML frontmatter 完整性 ──")
    for f in skill_list():
        name = skill_name(f)
        content = f.read_text(encoding="utf-8")
        parts = content.split("---")
        if len(parts) < 3:
            tfail(f"{name}: 无 YAML frontmatter"); continue
        yaml_block = parts[1]
        ok = True
        if "name:" not in yaml_block:
            tfail(f"{name}: 缺 name 字段"); ok = False
        if "description:" not in yaml_block:
            tfail(f"{name}: 缺 description 字段"); ok = False
        if ok:
            tpass(f"{name}: name + description 完整")


def test_t2_no_residues() -> None:
    print("\n── T2: Body 无残留字段 ──")
    bad = ["trigger:", "non_trigger:", "acceptance_cases:"]
    for f in skill_list():
        name = skill_name(f)
        content = f.read_text(encoding="utf-8")
        body = content.split("---", 2)[2] if content.count("---") >= 2 else content
        found = [a for a in bad if a in body]
        check(len(found) == 0, f"{name}: 无残留",
              f"残留: {found}" if found else "")


def test_t3_core_reference() -> None:
    print("\n── T3: confirmation/fallback 含 CORE 引用 ──")
    for f in skill_list():
        name = skill_name(f)
        content = f.read_text(encoding="utf-8")
        if name == "jarvis-roundtable":
            continue
        has_confirm = "confirmation_rules:" in content
        has_fallback = "fallback_rules:" in content
        if has_confirm:
            check("通用规则见 JARVIS_CORE" in content,
                  f"{name}/confirmation_rules 含 CORE 引用")
        if has_fallback:
            check("通用规则见 JARVIS_CORE" in content,
                  f"{name}/fallback_rules 含 CORE 引用")

    rt = SKILLS / "jarvis-roundtable" / "SKILL.md"
    rt_content = rt.read_text(encoding="utf-8")
    check("confirmation_rules:" not in rt_content,"roundtable 无 confirmation_rules")
    check("fallback_rules:" not in rt_content,"roundtable 无 fallback_rules")


def test_t4_create_topic() -> None:
    print("\n── T4: create_topic.py 骨架 ──")
    sp = REPO / "jarvis" / "scripts" / "create_topic.py"
    check(sp.exists(), "create_topic.py 存在")
    if not sp.exists(): return
    src = sp.read_text(encoding="utf-8")
    for d in ["参考资料", "过程稿", "定稿"]:
        check(f"{d}/.gitkeep" in src, f"files dict 含 {d}/.gitkeep")
    check("### 定稿" in src and "### 过程稿" in src and "### 参考资料" in src,
          "索引模板含 3 分区")
    tpl = REPO / "jarvis" / "templates" / "Topic骨架" / "索引.md"
    if tpl.exists():
        txt = tpl.read_text(encoding="utf-8")
        check("### 定稿" in txt and "### 过程稿" in txt and "### 参考资料" in txt,
              "模板文件含 3 分区")


def test_t5_core_brief() -> None:
    print("\n── T5: CORE_BRIEF 关键规则 ──")
    bp = CORE_DIR / "JARVIS_CORE_BRIEF.md"
    check(bp.exists(), "CORE_BRIEF 存在")
    if not bp.exists(): return
    b = bp.read_text(encoding="utf-8")
    check("写入分级" in b, "含写入分级表")
    check("record_write" in b, "含 record_write")
    check("content_write" in b, "含 content_write")
    check("high_risk" in b, "含 high_risk")
    check("通用回退规则" in b, "含通用回退")
    check("仪表盘缺失" in b, "回退: 仪表盘缺失")
    check("同名 Topic" in b, "回退: 同名冲突")
    check("脚本执行失败" in b, "回退: 脚本失败")


def test_t6_knowledge_model() -> None:
    print("\n── T6: knowledge-model 归类 ──")
    check(not (SKILLS / "jarvis-knowledge-model").exists(),
          "skills/ 中无 knowledge-model")
    check((REFS / "knowledge-model.md").exists(),
          "references/knowledge-model.md 存在")
    for sn in ["jarvis-knowledge-extract", "jarvis-knowledge-ingest"]:
        sk = SKILLS / sn / "SKILL.md"
        if sk.exists():
            txt = sk.read_text(encoding="utf-8")
            check("jarvis/references/knowledge-model.md" in txt,
                  f"{sn}: 引用路径更新")
            stale = "jarvis-knowledge-model" in txt and "references" not in txt
            check(not stale, f"{sn}: 无旧引用")


def test_t7_help_status() -> None:
    print("\n── T7: help/status 描述正交 ──")
    hf = SKILLS / "jarvis-help" / "SKILL.md"
    sf = SKILLS / "jarvis-status" / "SKILL.md"
    if hf.exists():
        ht = hf.read_text(encoding="utf-8")
        check("委托 jarvis-status" in ht, "help 委托状态查询")
        check("jarvis-status" in [l for l in ht.split("\n") if l.startswith("description:")][0],
              "help description 提及 status")
    if sf.exists():
        st = sf.read_text(encoding="utf-8")
        dl = [l for l in st.split("\n") if l.startswith("description:")][0]
        check("最近怎么样" in dl, "status description 保留最近怎么样")


def test_t8_core_full() -> None:
    print("\n── T8: CORE_FULL 版本与路由表 ──")
    fp = CORE_DIR / "JARVIS_CORE_FULL.md"
    check(fp.exists(), "CORE_FULL 存在")
    if not fp.exists(): return
    f = fp.read_text(encoding="utf-8")
    check("v1.8.0" in f, "版本 v1.8.0")
    check("jarvis-catalog-register" in f, "路由表: catalog-register")
    check("jarvis-roundtable" in f, "路由表: roundtable")
    check("jarvis-persona-create" in f, "路由表: persona-create")
    check("jarvis-topic-organize" in f, "路由表: topic-organize")
    check("过程稿" in f and "定稿" in f, "产出规范: 过程稿/定稿")


def test_t9_roundtable() -> None:
    print("\n── T9: roundtable 无残留 ──")
    rt = SKILLS / "jarvis-roundtable" / "SKILL.md"
    if not rt.exists():
        tfail("roundtable 缺失"); return
    text = rt.read_text(encoding="utf-8")
    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    check("trigger:" not in body, "body 无 trigger")
    check("non_trigger:" not in body, "body 无 non_trigger")
    check("confirmation_rules:" not in text, "无 confirmation_rules")
    check("fallback_rules:" not in text, "无 fallback_rules")


def main() -> int:
    print("=" * 60)
    print("Jarvis 技能规范优化 — 回归测试套件")
    print("=" * 60)
    test_t1_frontmatter()
    test_t2_no_residues()
    test_t3_core_reference()
    test_t4_create_topic()
    test_t5_core_brief()
    test_t6_knowledge_model()
    test_t7_help_status()
    test_t8_core_full()
    test_t9_roundtable()
    total = PASS + FAIL
    print(f"\n{'=' * 60}")
    print(f"通过: {PASS}  失败: {FAIL}  总计: {total}")
    print(f"{'=' * 60}")
    if FAIL > 0: print("\n⚠️  有测试未通过")
    else: print("\n✅ 全部通过")
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
