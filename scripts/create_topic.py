#!/usr/bin/env python3
"""Create a Jarvis Topic skeleton and dashboard row."""

from __future__ import annotations

import argparse
from pathlib import Path

from jarvis_lib import (
    STATUS_DISPLAY,
    add_common_args,
    add_session_args,
    append_active_topic_row,
    apply_changes,
    build_session_row,
    dashboard_path,
    ensure_single_line_insert,
    now_compact_date,
    now_date,
    obsidian_link_for_topic,
    prepare_change,
    print_validation,
    safe_topic_slug,
    topics_root,
    vault_root,
)


def build_index(title: str, status: str, scope: str) -> str:
    return f"""---
topic: {title}
status: {status}
priority: P1
tags: [topic]
---

# {title}

> **一句话描述**：{scope or "待补充"}

## 核心文档索引

- （待补充）

## 当前状态

- **阶段**：{STATUS_DISPLAY[status]}
- **Next Action**：待补充

## 关键产出

- 暂无。

## 时间线

- {now_date()} Topic 创建

## 本轮边界

- 未经明确确认，不执行内容性写入或高风险写入
"""


def build_snapshot(title: str, status: str, scope: str, session_row: str) -> str:
    return f"""# 上下文快照: {title}

> **快照时间**: {now_date()}
> **状态**: {STATUS_DISPLAY[status]}

## 1. 最后动作

- Topic 创建：{scope or title}

## 2. 已确认事实

- Topic 已建立，后续事实需基于源文件、用户明确表达或已确认知识补充。

## 3. 当前推论

- 暂无。

## 4. 待拍板

- 暂无。

## 5. 下一步动作

- 补充 Topic 范围、输入材料和下一步执行计划。

## 6. 关联会话

| 工具 | 会话标识 | JSONL 路径 | 工作区路径 | 日期 |
|------|------|------|------|------|
{session_row}
"""


def build_checklist(title: str, scope: str) -> str:
    return f"""# Topic 准入检查单: {title}

## 是否需要 Topic

- [x] 林峰明确要求或任务需要持续追踪
- [ ] 预计跨会话推进
- [ ] 会产生可交付文件
- [ ] 有外部依赖或跟进事项
- [ ] 会形成决策链
- [ ] 需要后续知识萃取或复用

## 准入理由

{scope or "待补充"}

## 范围内

- 待补充

## 范围外

- 未经确认的内容性写入
- 高风险文件修改
"""


def build_log(title: str, scope: str) -> str:
    return f"""# 讨论记录: {title}

## {now_date()} Topic 创建

### 背景

{scope or "待补充"}

### 下一步

- 补充上下文并推进当前任务。
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    add_session_args(parser)
    parser.add_argument("--title", required=True)
    parser.add_argument("--scope", default="")
    parser.add_argument("--date", default=now_compact_date())
    parser.add_argument("--status", default="doing", choices=sorted(STATUS_DISPLAY))
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    session_row = build_session_row(
        args.session_tool,
        args.session_id,
        args.session_jsonl,
        args.session_cwd or str(root),
        args.session_date or now_date(),
    )
    slug = safe_topic_slug(args.title)
    topic_dir = topics_root(root) / f"{args.date}_{slug}"
    dash = dashboard_path(root)
    errors: list[str] = []

    if topic_dir.exists() and not args.write:
        errors.append(f"topic already exists: {topic_dir}")
    if topic_dir.exists() and args.write:
        errors.append(f"refuse to overwrite existing topic: {topic_dir}")
    if not dash.exists():
        errors.append(f"dashboard not found: {dash}")
    if errors:
        return print_validation(errors)

    files = {
        topic_dir / "索引.md": build_index(args.title, args.status, args.scope),
        topic_dir / "_上下文快照.md": build_snapshot(args.title, args.status, args.scope, session_row),
        topic_dir / "_准入检查单.md": build_checklist(args.title, args.scope),
        topic_dir / "讨论记录.md": build_log(args.title, args.scope),
    }
    row = (
        f"| {STATUS_DISPLAY[args.status]} | "
        f"{obsidian_link_for_topic(topic_dir, args.title, root)} | "
        f"{now_date()} | {args.scope or '待补充'} | |"
    )
    dashboard_before = dash.read_text(encoding="utf-8")
    dashboard_after = append_active_topic_row(dashboard_before, row)
    ensure_single_line_insert(dashboard_before, dashboard_after, "dashboard topic creation")

    changes = [prepare_change(path, content) for path, content in files.items()]
    changes.append(prepare_change(dash, dashboard_after))
    apply_changes(changes, args.write)

    if args.write:
        for path in files:
            if not path.exists():
                errors.append(f"missing generated file: {path}")
        if row not in dash.read_text(encoding="utf-8"):
            errors.append("dashboard row not found after write")
    return print_validation(errors)


if __name__ == "__main__":
    raise SystemExit(main())
