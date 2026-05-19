#!/usr/bin/env python3
"""Ingest confirmed L1 Evidence Pack items into the knowledge base."""

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
MEDICAL_KEYWORDS = ("禁忌", "终止", "血氧", "心率", "孕妇", "儿童", "老年", "医学", "安全", "SpO2")


def load_items(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    raise SystemExit("validation result: failed - evidence pack must be a list or {items: [...]}")


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "\n".join(f"  - {value}" for value in values)


def one_line(text: str, limit: int = 80) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit]


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
processed_in:
  - {topic_link}
source_files:
{yaml_list(source_files)}
extracted_at: {extracted_at}
evidence_level: {item.get("evidence_level", "用户确认")}
quality: {item.get("quality", "归纳级")}
---
"""


def ensure_doc_content(existing: str, item: dict, topic_link: str, extracted_at: str, title: str) -> str:
    block = (
        f"### {title}\n\n"
        f"{item['claim']}\n\n"
        f"- source_type: {item.get('source_type', 'topic')}\n"
        f"- source_path: {item.get('source_path', '待确认')}\n"
        f"- source_excerpt: {item.get('source_excerpt', '待确认')}\n"
    )
    if block in existing:
        return existing
    if not existing.strip():
        return (
            build_doc_frontmatter(item, topic_link, extracted_at)
            + f"\n# {title}\n\n## 萃取补充\n\n{block}"
        )
    text = existing
    if not text.startswith("---\n"):
        text = build_doc_frontmatter(item, topic_link, extracted_at) + "\n" + text.lstrip()
    if "## 萃取补充" not in text:
        text = text.rstrip() + "\n\n## 萃取补充\n\n"
    return text.rstrip() + "\n\n" + block


def append_wiki_row_if_needed(text: str, row: str, title: str) -> str:
    return append_index_row(text, row, title)


def append_index_row(text: str, row: str, title: str) -> str:
    if title in text or row in text:
        return text
    if not text.strip():
        text = "# 索引\n\n| 条目 | 摘要 | 状态 |\n|---|---|---|\n"
    if "|---" not in text:
        text = text.rstrip() + "\n\n| 条目 | 摘要 | 状态 |\n|---|---|---|\n"
    return text.rstrip() + "\n" + row + "\n"


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
        if item.get("memory_type") != "semantic":
            if knowledge_layer == "L1":
                skipped.append(f"{item_id}: only semantic memory is automated for L1")
                continue
        if knowledge_layer == "L1" and item.get("memory_type") != "semantic":
            continue
        if item.get("requires_separate_confirmation") is True:
            skipped.append(f"{item_id}: requires separate confirmation")
            continue
        # 医学/安全类条目强制跳过
        claim_text = str(item.get("claim", ""))
        title_text = str(item.get("title", ""))
        if any(kw in claim_text or kw in title_text for kw in MEDICAL_KEYWORDS):
            skipped.append(f"{item_id}: medical/safety keyword detected, requires separate confirmation")
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


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--evidence-pack", required=True)
    parser.add_argument("--confirm-scope", action="append", required=True)
    parser.add_argument("--topic-dir", required=True)
    parser.add_argument("--date", default=now_date())
    parser.add_argument("--dry-run-scope", default="", help="Preview all items in scope without writing (e.g. A, B, C)")
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

    # --dry-run-scope: 预览全量可入库条目，不写入
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
    doc_buffers: dict[Path, str] = {}
    errors: list[str] = []

    for item in selected:
        knowledge_layer = item.get("knowledge_layer") or item.get("knowledge_type")
        target = (root / item["target_path"]).resolve()
        if root not in target.parents:
            errors.append(f"{item.get('id', 'unknown')}: target path outside vault")
            continue
        title = item["title"]
        if knowledge_layer == "L1":
            if target.exists():
                errors.append(f"{item.get('id', 'unknown')}: target already exists: {target}")
                continue
            content = build_term_content(item, topic_link, args.date)
            changes.append(prepare_change(target, content))
            rel = target.relative_to(root).with_suffix("").as_posix()
            row = f"| [[{rel}|{title}]] | {one_line(item['claim'])} | 已确认 |"
            wiki_text = append_index_row(wiki_text, row, title)
            term_index_text = append_index_row(term_index_text, row, title)
            continue
        if not item.get("target_path"):
            errors.append(f"{item.get('id', 'unknown')}: missing target_path for {knowledge_layer}")
            continue
        existing = doc_buffers.get(target, read_text(target))
        doc_buffers[target] = ensure_doc_content(existing, item, topic_link, args.date, title)
        rel = target.relative_to(root).with_suffix("").as_posix()
        row = f"| [[{rel}|{title}]] | {one_line(item['claim'])} | 已确认 |"
        wiki_text = append_wiki_row_if_needed(wiki_text, row, title)

    if selected:
        changes.append(prepare_change(wiki_index, wiki_text))
        changes.append(prepare_change(term_index, term_index_text))
    for path, content in doc_buffers.items():
        changes.append(prepare_change(path, content))

    print("skipped:")
    for item in skipped:
        print(f"- {item}")
    if errors:
        return print_validation(errors)
    apply_changes(changes, args.write)

    if args.write:
        for item in selected:
            target = root / item["target_path"]
            if not target.exists():
                errors.append(f"missing ingested file: {target}")
        for title in [item["title"] for item in selected]:
            if title not in read_text(wiki_index):
                errors.append(f"wiki index missing ingested title: {title}")
        for item in selected:
            if (item.get("knowledge_layer") or item.get("knowledge_type")) == "L1" and item["title"] not in read_text(term_index):
                errors.append(f"term index missing ingested title: {item['title']}")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
