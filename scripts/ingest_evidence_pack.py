#!/usr/bin/env python3
"""Ingest confirmed Evidence Pack items into the knowledge base (v0.3 multi-layer)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jarvis_lib import (
    add_common_args,
    apply_changes,
    now_date,
    obsidian_link_for_topic,
    prepare_change,
    print_validation,
    read_text,
    vault_root,
)


CONFIRMED_VALUES = {"confirmed", "user_confirmed", "已确认", "林峰确认", "verified"}
CONFIRMABLE_VALUES = {"needs_confirmation", *CONFIRMED_VALUES}
CAN_INGEST_VALUES = {True, "true", "after_confirmation"}
DOC_LAYERS = {"L2", "L3", "L4", "F"}

SAFETY_WHITELIST = [
    "安全收缩", "安全边界", "安全默认",
]

MEDICAL_SAFETY_KEYWORDS = [
    "血氧", "禁忌", "终止", "安全范围",
    "心率上限", "特殊人群", "孕妇",
]


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "\n".join(f"  - {value}" for value in values)


def one_line(text: str, limit: int = 80) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit]


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    raise SystemExit("validation result: failed - evidence pack must be a list or {items: [...]}")


# ── safety filter ─────────────────────────────────────────────────


def check_safety(claim: str) -> bool:
    cleaned = claim
    for w in SAFETY_WHITELIST:
        cleaned = cleaned.replace(w, "")
    for kw in MEDICAL_SAFETY_KEYWORDS:
        if kw in cleaned:
            return True
    return False


# ── content builders ──────────────────────────────────────────────


def build_term_content(item: dict, topic_link: str, extracted_at: str) -> str:
    title = item["title"]
    tags = item.get("tags") or ["术语", "平台"]
    if isinstance(tags, str):
        tags = [tags]
    source_files = [item.get("source_path", "")]
    source_files = [source for source in source_files if source]
    evidence_level = item.get("evidence_level", "用户确认")
    quality = item.get("quality", "描述级")
    return f"""---
status: 已确认
tags: [{", ".join(tags)}]
source_files:
{yaml_list(source_files)}
source_messages: []
processed_in:
  - {topic_link}
extracted_at: {extracted_at}
evidence_level: {evidence_level}
quality: {quality}
related: []
---

# {title}

{item["claim"]}

## 证据

- source_type: {item.get("source_type", "topic")}
- source_path: {item.get("source_path", "待确认")}
- source_excerpt: {item.get("source_excerpt", "待确认")}
"""


def build_doc_frontmatter(item: dict, topic_link: str, extracted_at: str) -> str:
    source_files = [item.get("source_path", "")]
    source_files = [source for source in source_files if source]
    return f"""---
status: 已确认
tags: [知识条目, 规则]
source_files:
{yaml_list(source_files)}
processed_in:
  - {topic_link}
extracted_at: {extracted_at}
evidence_level: {item.get("evidence_level", "用户确认")}
quality: {item.get("quality", "归纳级")}
related: []
---
"""


def build_business_doc_content(item: dict, topic_link: str, extracted_at: str) -> str:
    title = item["title"]
    return (
        build_doc_frontmatter(item, topic_link, extracted_at)
        + f"\n# {title}\n\n{item['claim']}\n\n## 证据\n\n"
        + f"- source_type: {item.get('source_type', 'topic')}\n"
        + f"- source_path: {item.get('source_path', '待确认')}\n"
        + f"- source_excerpt: {item.get('source_excerpt', '待确认')}\n"
    )


# ── wiki / term index helpers ─────────────────────────────────────


def append_index_row(text: str, row: str, title: str) -> str:
    if title in text or row in text:
        return text
    if not text.strip():
        text = "# 索引\n\n| 条目 | 摘要 | 状态 |\n|---|---|---|\n"
    if "|---" not in text:
        text = text.rstrip() + "\n\n| 条目 | 摘要 | 状态 |\n|---|---|---|\n"
    return text.rstrip() + "\n" + row + "\n"


def append_wiki_row_if_needed(text: str, row: str, title: str) -> str:
    return append_index_row(text, row, title)


def _append_list_item_to_section(text: str, section_heading: str, list_item: str) -> str:
    """Append a `- [[link]] — summary` line under a markdown heading section."""
    lines = text.splitlines()
    heading_idx = None
    for i, line in enumerate(lines):
        if line.strip() == section_heading:
            heading_idx = i
            break
    if heading_idx is None:
        if not text.strip():
            return f"{section_heading}\n\n{list_item}\n"
        return text.rstrip() + f"\n\n{section_heading}\n\n{list_item}\n"
    insert_at = heading_idx + 1
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1
    lines.insert(insert_at, list_item)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _usage_scope_to_term_section(usage_scope: str) -> str:
    mapping = {
        "jarvis": "### 核心组件",
        "runtime": "### 核心组件",
        "行为规范": "### 核心组件",
        "skill": "### 核心组件",
        "知识库": "### 核心组件",
        "平台": "### 核心组件",
    }
    for key, section in mapping.items():
        if key in usage_scope.lower():
            return section
    return "### 核心组件"


def append_term_list_item(text: str, item: dict) -> str:
    """Append a term as a domain-grouped list item instead of a flat table row."""
    title = item["title"]
    claim = item["claim"]
    usage = item.get("usage_scope", "平台体系")
    section = _usage_scope_to_term_section(usage)
    rel = f"知识库/术语/{title}"
    list_item = f"- [[{rel}|{title}]] — {one_line(claim, 60)}"
    if title in text or list_item in text:
        return text
    return _append_list_item_to_section(text, section, list_item)


# ── handlers ──────────────────────────────────────────────────────


def handle_L1(item: dict, root: Path, topic_link: str, date: str,
              wiki_text: str, term_index_text: str, skip_safety: bool,
              errors: list[str], changes: list, target: Path | None = None) -> tuple[str, str]:
    if target is None:
        target = (root / item["target_path"]).resolve()
    if root not in target.parents:
        raise SystemExit(f"{item.get('id', 'unknown')}: target path outside vault")
    title = item["title"]

    if not skip_safety and check_safety(item.get("claim", "") + item.get("title", "")):
        raise SystemExit(
            f"{item.get('id', 'unknown')}: medical/safety keyword detected. "
            "Use --skip-safety-check to override after manual review."
        )

    if target.exists():
        errors.append(f"{item.get('id', 'unknown')}: target already exists: {target}")
        return wiki_text, term_index_text

    content = build_term_content(item, topic_link, date)
    changes.append(prepare_change(target, content))
    rel = target.relative_to(root).with_suffix("").as_posix()
    row = f"| [[{rel}|{title}]] | {one_line(item['claim'])} | 已确认 |"
    wiki_text = append_index_row(wiki_text, row, title)
    term_index_text = append_term_list_item(term_index_text, item)
    return wiki_text, term_index_text


def handle_L2(item: dict, root: Path, topic_link: str, date: str,
              wiki_text: str, errors: list[str], changes: list) -> str:
    target_path = item.get("target_path")
    if not target_path:
        title_slug = re.sub(r"[\\/:*?\"<>|]+", "", item["title"]).strip()
        target_path = f"知识库/业务文档/{title_slug}.md"
    target = (root / target_path).resolve()
    if root not in target.parents:
        raise SystemExit(f"{item.get('id', 'unknown')}: target path outside vault")
    if target.exists():
        errors.append(f"{item.get('id', 'unknown')}: L2 target already exists, refusing to overwrite: {target}")
        return wiki_text

    content = build_business_doc_content(item, topic_link, date)
    changes.append(prepare_change(target, content))
    title = item["title"]
    rel = target.relative_to(root).with_suffix("").as_posix()
    row = f"| [[{rel}|{title}]] | {one_line(item['claim'])} | 已确认 |"
    wiki_text = append_wiki_row_if_needed(wiki_text, row, title)
    return wiki_text


def handle_L3(item: dict, root: Path, topic_link: str, date: str,
              topic_dir: Path, errors: list[str], changes: list) -> None:
    plan_path = topic_dir / "_人工入库计划.md"
    existing = read_text(plan_path)
    plan_header = "# 人工入库计划\n\n> 以下条目为 L3 判断/决策类知识，需人工确认后入库。\n\n"
    entry_block = (
        f"## {item['title']}\n\n"
        f"**claim**: {item['claim']}\n\n"
        f"**建议落点**: {item.get('target_path') or '待指定'}\n\n"
        f"**入库前置条件**: 林峰确认 claim 准确性、确认落点路径\n\n"
        f"**需确认问题**: 该判断在当前上下文是否仍然成立？是否有新的决策覆盖？\n\n"
        f"**来源**: {item.get('source_path', '待确认')} | "
        f"**提取时间**: {date}\n\n---\n"
    )
    if entry_block in existing:
        return
    new_text = existing
    if not existing.strip():
        new_text = plan_header + "\n" + entry_block
    else:
        new_text = existing.rstrip() + "\n\n" + entry_block
    changes.append(prepare_change(plan_path, new_text))


def handle_L4(item: dict, root: Path, topic_link: str, date: str,
              errors: list[str], changes: list) -> None:
    target = root / "知识库" / "待验证问题.md"
    existing = read_text(target)
    header = "| 问题 | 来源 Topic | 提取时间 | 状态 |\n|---|---|---|---|\n"
    claim = item["claim"]
    linked_topic = item.get("linked_topic", "待确认")
    row = f"| {one_line(claim, 80)} | {linked_topic} | {date} | 待验证 |"
    if claim in existing:
        return
    new_text = existing
    if not existing.strip():
        new_text = "# 待验证问题\n\n" + header + row + "\n"
    elif "|---" not in existing:
        new_text = existing.rstrip() + "\n\n" + header + row + "\n"
    else:
        new_text = existing.rstrip() + "\n" + row + "\n"
    changes.append(prepare_change(target, new_text))


def handle_F(item: dict, root: Path, topic_link: str, date: str,
             wiki_text: str, errors: list[str], changes: list) -> str:
    title = item["title"]
    section_heading = "## 文件处理产物"
    list_item = f"- **{title}**: {one_line(item['claim'], 100)} (来源: {item.get('source_path', '待确认')})"
    new_text = _append_list_item_to_section(wiki_text, section_heading, list_item)
    if new_text != wiki_text:
        wiki_path = root / "知识库" / "wiki索引.md"
        changes.append(prepare_change(wiki_path, new_text))
    return new_text


# ── routing ───────────────────────────────────────────────────────


def route_ingest(item: dict, root: Path, topic_link: str, date: str,
                 topic_dir: Path, wiki_text: str, term_index_text: str,
                 skip_safety: bool, errors: list[str], changes: list) -> tuple[str, str]:
    layer = item.get("knowledge_layer") or item.get("knowledge_type")
    mtype = item.get("memory_type", "")

    if layer == "L1" and mtype == "semantic":
        return handle_L1(item, root, topic_link, date, wiki_text, term_index_text,
                         skip_safety, errors, changes)
    elif layer == "L2" and mtype in ("semantic", "procedural"):
        wiki_text = handle_L2(item, root, topic_link, date, wiki_text, errors, changes)
        return wiki_text, term_index_text
    elif layer == "L3":
        handle_L3(item, root, topic_link, date, topic_dir, errors, changes)
        return wiki_text, term_index_text
    elif layer == "L4":
        handle_L4(item, root, topic_link, date, errors, changes)
        return wiki_text, term_index_text
    elif layer == "F":
        wiki_text = handle_F(item, root, topic_link, date, wiki_text, errors, changes)
        return wiki_text, term_index_text
    else:
        errors.append(f"{item.get('id', 'unknown')}: unsupported layer/type {layer}/{mtype}")
        return wiki_text, term_index_text


# ── item selection ────────────────────────────────────────────────


def choose_items(items: list[dict], confirmed_scopes: set[str]) -> tuple[list[dict], list[str]]:
    selected: list[dict] = []
    skipped: list[str] = []
    for item in items:
        item_id = item.get("id", "unknown")
        group = str(item.get("group", "")).strip()
        if group not in confirmed_scopes and item_id not in confirmed_scopes:
            skipped.append(f"{item_id}: not in confirmed scope")
            continue
        if item.get("can_ingest") not in CAN_INGEST_VALUES:
            skipped.append(f"{item_id}: can_ingest is not true")
            continue
        verification_status = str(item.get("verification_status", "")).strip()
        if verification_status not in CONFIRMABLE_VALUES:
            skipped.append(f"{item_id}: verification_status is not confirmable")
            continue
        knowledge_layer = item.get("knowledge_layer") or item.get("knowledge_type")
        if knowledge_layer not in {"L1", *DOC_LAYERS}:
            skipped.append(f"{item_id}: unsupported knowledge layer {knowledge_layer}")
            continue
        required_fields = ["title", "claim"]
        if knowledge_layer == "L1":
            required_fields.append("target_path")
        for required in required_fields:
            if not item.get(required):
                skipped.append(f"{item_id}: missing {required}")
                break
        else:
            selected.append(item)
    return selected, skipped


# ── main ──────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--evidence-pack", required=True)
    parser.add_argument("--confirm-scope", action="append", required=True)
    parser.add_argument("--topic-dir", required=True)
    parser.add_argument("--date", default=now_date())
    parser.add_argument("--dry-run-scope", default="", help="Preview all items in scope without writing (e.g. A, B, C)")
    parser.add_argument("--skip-safety-check", action="store_true",
                        help="Allow items with safety keywords to pass the filter after manual review")
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    evidence_path = Path(args.evidence_pack)
    if not evidence_path.is_absolute():
        evidence_path = (root / evidence_path).resolve()
    topic_dir = Path(args.topic_dir)
    if not topic_dir.is_absolute():
        topic_dir = (root / topic_dir).resolve()
    topic_link = obsidian_link_for_topic(topic_dir, topic_dir.name.split("_", 1)[-1], root)
    items = load_items(evidence_path)
    selected, skipped = choose_items(items, set(args.confirm_scope))

    if args.dry_run_scope:
        scope = set(args.dry_run_scope.split(","))
        preview_selected, preview_skipped = choose_items(items, scope)
        print(f"dry-run-scope: {args.dry_run_scope}")
        print(f"would ingest: {len(preview_selected)} items")
        for item in preview_selected:
            print(f"  - {item.get('id')}: {item.get('title')} ({item.get('knowledge_layer')})")
        print(f"would skip: {len(preview_skipped)} items")
        for skip_reason in preview_skipped:
            print(f"  - {skip_reason}")
        return print_validation([])

    changes = []
    wiki_index = root / "知识库" / "wiki索引.md"
    term_index = root / "知识库" / "术语" / "术语索引.md"
    wiki_text = read_text(wiki_index)
    term_index_text = read_text(term_index)
    errors: list[str] = []

    for item in selected:
        wiki_text, term_index_text = route_ingest(
            item, root, topic_link, args.date, topic_dir,
            wiki_text, term_index_text, args.skip_safety_check, errors, changes,
        )

    if selected:
        changes.append(prepare_change(wiki_index, wiki_text))
        changes.append(prepare_change(term_index, term_index_text))

    print("skipped:")
    for item in skipped:
        print(f"- {item}")
    if errors:
        return print_validation(errors)
    apply_changes(changes, args.write)

    if args.write:
        for item in selected:
            layer = item.get("knowledge_layer") or item.get("knowledge_type")
            if layer == "L1":
                target = root / item["target_path"]
                if not target.exists():
                    errors.append(f"missing ingested file: {target}")
            elif layer == "L2":
                tp = item.get("target_path")
                if not tp:
                    tp = f"知识库/业务文档/{re.sub(r'[\\\\/:*?\"<>|]+', '', item['title']).strip()}.md"
                if not (root / tp).exists():
                    errors.append(f"missing ingested file: {tp}")
        wiki_layers = {"L1", "L2", "F"}
        for item in selected:
            layer = item.get("knowledge_layer") or item.get("knowledge_type")
            if layer in wiki_layers and item["title"] not in read_text(wiki_index):
                errors.append(f"wiki index missing ingested title: {item['title']}")
            if layer == "L1" and item["title"] not in read_text(term_index):
                errors.append(f"term index missing ingested title: {item['title']}")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())