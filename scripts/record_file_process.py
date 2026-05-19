#!/usr/bin/env python3
"""Write an OCR/document-processing artifact into 业务/<域>/ for review and reuse."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from jarvis_lib import add_common_args, apply_changes, now_date, prepare_change, print_validation, read_text, vault_root


def slugify(text: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|#\[\]\n\r\t]+", "", text).strip()
    return re.sub(r"\s+", "", cleaned)


def yaml_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "\n".join(f"  - {value}" for value in values)


def build_doc(source_file: str, processed_in: str, quality: str, title: str, content: str, extracted_at: str) -> str:
    return f"""---
status: 待确认
source_files:
  - {source_file}
processed_in:
  - {processed_in}
extracted_at: {extracted_at}
evidence_level: OCR文档解析
quality: {quality}
related: []
---

# {title}

## 来源

- source_file: {source_file}
- processed_in: {processed_in}
- quality: {quality}

## OCR / 文档解析结果

{content.strip()}

## 人工复核

- [ ] 林峰已核对 OCR / 文档解析结果
- [ ] 关键数字、表格、参数无误
- [ ] 可进入后续理解、推断或知识萃取
"""


def append_wiki_index(text: str, row: str, title: str) -> str:
    if title in text or row in text:
        return text
    if not text.strip():
        text = "# 索引\n\n| 条目 | 摘要 | 状态 |\n|---|---|---|\n"
    if "|---" not in text:
        text = text.rstrip() + "\n\n| 条目 | 摘要 | 状态 |\n|---|---|---|\n"
    return text.rstrip() + "\n" + row + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--quality", required=True, choices=["描述级", "对比级", "归纳级"])
    parser.add_argument("--processed-in", required=True)
    parser.add_argument("--content-file", default="")
    parser.add_argument("--content", default="")
    parser.add_argument("--date", default=now_date())
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    if not args.content and not args.content_file:
        return print_validation(["either --content or --content-file is required"])
    content = args.content
    if args.content_file:
        content_path = Path(args.content_file)
        if not content_path.is_absolute():
            content_path = (root / args.content_file).resolve()
        if not content_path.exists():
            return print_validation([f"content file not found: {content_path}"])
        content = read_text(content_path)
    source_path = Path(args.source_file)
    if not source_path.is_absolute():
        source_path = (root / args.source_file).resolve()
    if not source_path.exists():
        return print_validation([f"source file not found: {source_path}"])

    domain_dir = root / "业务" / args.domain
    title_slug = slugify(args.title)
    target = domain_dir / f"{args.date} {args.domain}-{title_slug}.md"
    if target.exists():
        return print_validation([f"target already exists: {target}"])

    processed_in = args.processed_in
    doc = build_doc(source_path.as_posix(), processed_in, args.quality, args.title, content, args.date)
    wiki_index = root / "知识库" / "wiki索引.md"
    wiki_text = append_wiki_index(
        read_text(wiki_index),
        f"| [[{target.relative_to(root).with_suffix('').as_posix()}|{args.title}]] | OCR / 文档解析产物 | 待确认 |",
        args.title,
    )

    changes = [
        prepare_change(target, doc),
        prepare_change(wiki_index, wiki_text),
    ]
    apply_changes(changes, args.write)

    errors: list[str] = []
    if args.write:
        if not target.exists():
            errors.append(f"missing generated artifact: {target}")
        if args.title not in read_text(wiki_index):
            errors.append("wiki index missing file-process artifact")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
