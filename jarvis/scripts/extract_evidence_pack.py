#!/usr/bin/env python3
"""Build an executable Evidence Pack and confirmation checklist from a Topic."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import (
    add_common_args,
    apply_changes,
    now_date,
    prepare_change,
    print_validation,
    read_text,
    vault_root,
    write_json_result,
)


MEDICAL_KEYWORDS = ("禁忌", "终止", "血氧", "心率", "孕妇", "儿童", "老年", "医学", "安全", "SpO2")
DEFINITION_HEADINGS = ("定义", "术语", "概念", "词汇", "名词")
RELATION_HEADINGS = ("关系", "规则", "流程", "协作", "架构")
DECISION_HEADINGS = ("决策", "判断", "取舍", "结论")
RISK_HEADINGS = ("风险", "待验证", "医学", "安全")
SKELETON_FILES = {"索引.md", "_上下文快照.md", "_准入检查单.md", "讨论记录.md"}


def normalize_heading(line: str) -> str:
    return re.sub(r"^#+\s*", "", line).strip()


def section_map(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if re.match(r"^#{2,4}\s+", line):
            current = normalize_heading(line)
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return sections


def extract_list_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif re.match(r"^\d+\.\s+", stripped):
            items.append(re.sub(r"^\d+\.\s+", "", stripped))
    return items


def source_type_for(path: Path, topic_dir: Path) -> str:
    return "topic" if topic_dir in path.parents else "source_file"


def make_claim_from_definition(title: str, definition: str) -> str:
    definition = definition.strip()
    if definition.startswith(title):
        return definition
    if definition.startswith(("是", "指", "包括")):
        return f"{title}{definition}"
    if definition.startswith("用于"):
        return f"{title}是{definition}"
    return f"{title}：{definition}"


def safe_term_title(title: str) -> str:
    return re.sub(r"[\\/:*?\"<>|#\[\]\n\r\t]+", "", title).strip()


def next_id(group: str, counters: Counter[str]) -> str:
    counters[group] += 1
    return f"{group}{counters[group]}"


def build_item(
    *,
    item_id: str,
    group: str,
    title: str,
    claim: str,
    knowledge_type: str,
    knowledge_layer: str,
    memory_type: str,
    source_type: str,
    source_path: str,
    source_excerpt: str,
    evidence_level: str,
    confidence: str,
    verification_status: str,
    usage_scope: str,
    can_ingest: str | bool,
    linked_topic: str,
    requires_separate_confirmation: bool,
    target_path: str = "",
) -> dict:
    title = safe_term_title(title) or f"{group}-{item_id}"
    if not target_path:
        if knowledge_layer == "L1":
            target_path = f"知识库/术语/{title}.md"
        elif knowledge_layer == "L2":
            target_path = f"知识库/业务文档/{title}.md"
        elif knowledge_layer in ("L3", "L4"):
            target_path = None  # L3 handled by human import plan, L4 by pending questions
    return {
        "id": item_id,
        "group": group,
        "title": title,
        "claim": claim.strip(),
        "knowledge_type": knowledge_type,
        "knowledge_layer": knowledge_layer,
        "memory_type": memory_type,
        "source_type": source_type,
        "source_path": source_path,
        "source_excerpt": source_excerpt.strip(),
        "evidence_level": evidence_level,
        "confidence": confidence,
        "verification_status": verification_status,
        "usage_scope": usage_scope,
        "can_ingest": can_ingest,
        "linked_topic": linked_topic,
        "related_entries": [],
        "target_path": target_path,
        "requires_separate_confirmation": requires_separate_confirmation,
    }


def extract_definition_items(path: Path, heading: str, items: list[str], topic_name: str, topic_dir: Path, counters: Counter[str]) -> list[dict]:
    output: list[dict] = []
    for entry in items:
        title = ""
        definition = ""
        if "：" in entry:
            title, definition = entry.split("：", 1)
        elif ":" in entry:
            title, definition = entry.split(":", 1)
        else:
            continue
        title = safe_term_title(title)
        if not title or not definition.strip():
            continue
        output.append(
            build_item(
                item_id=next_id("A", counters),
                group="A",
                title=title,
                claim=make_claim_from_definition(title, definition),
                knowledge_type="fact",
                knowledge_layer="L1",
                memory_type="semantic",
                source_type=source_type_for(path, topic_dir),
                source_path=path.as_posix(),
                source_excerpt=f"{heading}: {entry}",
                evidence_level="primary",
                confidence="medium",
                verification_status="needs_confirmation",
                usage_scope="knowledge_base",
                can_ingest="after_confirmation",
                linked_topic=topic_name,
                requires_separate_confirmation=False,
            )
        )
    return output


def extract_relation_items(path: Path, heading: str, items: list[str], topic_name: str, topic_dir: Path, counters: Counter[str], root: Path | None = None) -> list[dict]:
    output: list[dict] = []
    vault_root = root
    target_path = path.relative_to(vault_root).as_posix() if "业务/" in path.as_posix() else ""
    for entry in items:
        output.append(
            build_item(
                item_id=next_id("B", counters),
                group="B",
                title=entry[:24],
                claim=entry,
                knowledge_type="relation",
                knowledge_layer="L2",
                memory_type="semantic",
                source_type=source_type_for(path, topic_dir),
                source_path=path.as_posix(),
                source_excerpt=f"{heading}: {entry}",
                evidence_level="primary" if source_type_for(path, topic_dir) == "topic" else "secondary",
                confidence="medium",
                verification_status="needs_confirmation",
                usage_scope="knowledge_base" if target_path else "manual_ingest_plan",
                can_ingest="after_confirmation",
                linked_topic=topic_name,
                requires_separate_confirmation=source_type_for(path, topic_dir) != "topic",
                target_path=target_path,
            )
        )
    return output


def extract_decision_items(path: Path, heading: str, items: list[str], topic_name: str, topic_dir: Path, counters: Counter[str], root: Path | None = None) -> list[dict]:
    output: list[dict] = []
    vault_root = root
    target_path = path.relative_to(vault_root).as_posix() if "业务/" in path.as_posix() else ""
    for entry in items:
        output.append(
            build_item(
                item_id=next_id("B", counters),
                group="B",
                title=entry[:24],
                claim=entry,
                knowledge_type="decision",
                knowledge_layer="L3",
                memory_type="episodic",
                source_type=source_type_for(path, topic_dir),
                source_path=path.as_posix(),
                source_excerpt=f"{heading}: {entry}",
                evidence_level="primary" if source_type_for(path, topic_dir) == "topic" else "secondary",
                confidence="medium",
                verification_status="needs_confirmation",
                usage_scope="knowledge_base" if target_path else "manual_ingest_plan",
                can_ingest="after_confirmation",
                linked_topic=topic_name,
                requires_separate_confirmation=source_type_for(path, topic_dir) != "topic",
                target_path=target_path,
            )
        )
    return output


def extract_risk_items(path: Path, heading: str, items: list[str], topic_name: str, topic_dir: Path, counters: Counter[str], root: Path | None = None) -> list[dict]:
    output: list[dict] = []
    vault_root = root
    target_path = path.relative_to(vault_root).as_posix() if "业务/" in path.as_posix() else ""
    for entry in items:
        is_medical = any(keyword in entry for keyword in MEDICAL_KEYWORDS)
        output.append(
            build_item(
                item_id=next_id("C", counters),
                group="C",
                title=entry[:24],
                claim=entry,
                knowledge_type="medical_candidate" if is_medical else "procedure",
                knowledge_layer="L4",
                memory_type="semantic",
                source_type=source_type_for(path, topic_dir),
                source_path=path.as_posix(),
                source_excerpt=f"{heading}: {entry}",
                evidence_level="primary",
                confidence="low",
                verification_status="needs_confirmation" if is_medical else "needs_review",
                usage_scope="knowledge_base" if target_path and not is_medical else "candidate_only",
                can_ingest="after_confirmation" if target_path and not is_medical else False,
                linked_topic=topic_name,
                requires_separate_confirmation=is_medical or source_type_for(path, topic_dir) != "topic",
                target_path=target_path,
            )
        )
    return output


def infer_items_from_file(path: Path, topic_name: str, topic_dir: Path, counters: Counter[str], root: Path | None = None) -> list[dict]:
    text = read_text(path)
    sections = section_map(text)
    vault_root = root
    output: list[dict] = []
    for heading, body in sections.items():
        items = extract_list_items(body)
        if not items:
            continue
        if any(keyword in heading for keyword in DEFINITION_HEADINGS):
            output.extend(extract_definition_items(path, heading, items, topic_name, topic_dir, counters))
        elif any(keyword in heading for keyword in RELATION_HEADINGS):
            output.extend(extract_relation_items(path, heading, items, topic_name, topic_dir, counters, vault_root))
        elif any(keyword in heading for keyword in DECISION_HEADINGS):
            output.extend(extract_decision_items(path, heading, items, topic_name, topic_dir, counters, vault_root))
        elif any(keyword in heading for keyword in RISK_HEADINGS):
            output.extend(extract_risk_items(path, heading, items, topic_name, topic_dir, counters, vault_root))
    return output


def build_checklist(topic_name: str, generated_at: str, items: list[dict], missing_sources: list[str]) -> str:
    groups = {"A": [], "B": [], "C": [], "D": []}
    for item in items:
        groups.setdefault(item["group"], []).append(item)

    def lines_for(group: str, title: str, action: str) -> list[str]:
        output = [f"## {group}. {title}", ""]
        output.append("| # | 我们的理解 | 类型 | 准备用法 | 证据来源 | 建议动作 |")
        output.append("|---|---|---|---|---|---|")
        if not groups[group]:
            output.append("| - | 无 | - | - | - | - |")
        else:
            for item in groups[group]:
                output.append(
                    f"| {item['id']} | {item['claim']} | {item['knowledge_type']} | {item['usage_scope']} | "
                    f"{item['source_type']} + {item['source_path']} | {action} |"
                )
        output.append("")
        return output

    lines = [
        f"# 萃取确认清单: {topic_name}",
        "",
        f"> 创建时间: {generated_at}",
        "> 状态: 待确认",
        "",
    ]
    lines.extend(lines_for("A", "可快速确认", "建议确认"))
    lines.extend(lines_for("B", "需要林峰拍板", "人工入库计划"))
    lines.extend(lines_for("C", "需要验证", "待验证"))
    if missing_sources:
        lines.extend(["## D. 缺失来源", ""])
        for missing in missing_sources:
            lines.append(f"- {missing}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--topic-dir", required=True)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--session-jsonl", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--date", default=now_date())
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    topic_dir = Path(args.topic_dir)
    if not topic_dir.is_absolute():
        topic_dir = (root / topic_dir).resolve()
    if not topic_dir.exists():
        return print_validation([f"missing topic dir: {topic_dir}"])

    topic_name = topic_dir.name.split("_", 1)[-1]
    counters: Counter[str] = Counter()
    items: list[dict] = []
    missing_sources: list[str] = []
    used_paths: set[Path] = set()

    default_paths = [topic_dir / name for name in ("索引.md", "_上下文快照.md", "讨论记录.md")]
    for path in default_paths:
        if path.exists():
            used_paths.add(path)
        else:
            missing_sources.append(f"missing topic file: {path.relative_to(root).as_posix()}")

    for raw_source in args.source:
        source_path = Path(raw_source)
        if not source_path.is_absolute():
            source_path = (root / raw_source).resolve()
        if source_path.exists():
            used_paths.add(source_path)
        else:
            missing_sources.append(f"missing source file: {raw_source}")

    for path in sorted(used_paths):
        items.extend(infer_items_from_file(path, topic_name, topic_dir, counters, root))

    session_path = Path(args.session_jsonl).expanduser() if args.session_jsonl else None
    if session_path:
        if not session_path.exists():
            missing_sources.append(f"missing session jsonl: {session_path}")
        else:
            line_count = sum(1 for _ in session_path.open("r", encoding="utf-8", errors="ignore"))
            items.append(
                build_item(
                    item_id=next_id("B", counters),
                    group="B",
                    title="原始会话证据可用",
                    claim=f"原始会话 JSONL 可用，共 {line_count} 行，可用于回溯本 Topic 的对话证据。",
                    knowledge_type="procedure",
                    knowledge_layer="L4",
                    memory_type="episodic",
                    source_type="session_jsonl",
                    source_path=str(session_path),
                    source_excerpt="JSONL path resolved for extraction.",
                    evidence_level="primary",
                    confidence="high",
                    verification_status="verified",
                    usage_scope="evidence_trace",
                    can_ingest=False,
                    linked_topic=topic_name,
                    requires_separate_confirmation=True,
                )
            )
    else:
        missing_sources.append("session_jsonl not provided")

    payload = {
        "topic": topic_name,
        "generated_at": args.date,
        "items": items,
        "missing_sources": missing_sources,
    }
    checklist = build_checklist(topic_name, args.date, items, missing_sources)

    print("plan:")
    print(f"- extract evidence pack from: {topic_dir}")
    if args.source:
        for source in args.source:
            print(f"- include source: {source}")
    print("\ndiff preview:")
    if args.write:
        print("(see planned output files below)")
    else:
        print("(read-only)")
    write_json_result(payload)
    print("\nchecklist preview:")
    print(checklist)

    errors: list[str] = []
    changes = []
    output_json = Path(args.output_json).resolve() if args.output_json else topic_dir / "_evidence-pack.json"
    output_md = Path(args.output_md).resolve() if args.output_md else topic_dir / "_萃取确认清单.md"
    if args.write:
        changes.append(prepare_change(output_json, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"))
        changes.append(prepare_change(output_md, checklist))
        apply_changes(changes, True)
        if not output_json.exists() or not output_md.exists():
            errors.append("expected evidence output files were not written")
    return print_validation(errors, [f"missing sources: {len(missing_sources)}"] if missing_sources else [])


if __name__ == "__main__":
    raise SystemExit(main())
