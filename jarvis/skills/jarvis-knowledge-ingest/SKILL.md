---
name: jarvis-knowledge-ingest
description: 按林峰确认范围把 Evidence Pack 入库，或给出人工入库计划。用于“A 组全确认”“这几条确认入库”。只处理明确确认范围。
next_skills: []
---

# jarvis-knowledge-ingest

trigger:
- “A 组全确认”
- “这几条确认入库”
- “把确认范围写入知识库”

non_trigger:
- 只要求萃取或整理。
- 没有 Evidence Pack。
- 用户没有明确确认范围。

inputs:
- Evidence Pack。
- 林峰确认范围。
- 目标知识库路径或既有索引。

outputs:
- 入库计划。
- 自动写入的条目列表。
- 需要人工入库的条目列表。
- 不写入条目及原因。
- 索引和日志更新结果。

required_references:
- `jarvis/references/evidence-pack-spec.md`

on_demand_references:
- `jarvis-knowledge-model`
- `jarvis/references/knowledge-model-and-ingest.md`
- `jarvis/plugins/medical/safety.md`

allowed_scripts:
- `jarvis/scripts/ingest_evidence_pack.py`
- `jarvis/scripts/validate_links.py`
- `jarvis/scripts/knowledge_link_stats.py`
- `jarvis/scripts/append_operation_log.py`

write_level:
- content_write after confirmation

confirmation_rules:
> ⚠️ 入库后必须立即更新 wiki索引 和 术语索引。索引不同步 = 入库未完成。
- 只处理林峰明确确认的组或条目。
- 确认项标记为 `✅ 互补` 时：新条目入库后，同时更新被补充的已有条目（正文末尾追加新内容）。
- 确认项标记为 `🔗 应关联` 时：新条目入库后，同时更新被引用的已有条目（related 字段追加新条目）。
- 医学参数、安全边界、判断类内容仍需单独确认。
- 不能把 `candidate_only` 或 `needs_source` 条目写入正式知识库。
- v0.2 自动脚本可处理以下条目：
  - `knowledge_layer: L1` 且 `memory_type: semantic` 的术语项（自动创建术语文件）
  - `knowledge_layer: L2/L3/L4/F` 且 `target_path` 明确、`requires_separate_confirmation=False` 的条目（自动追加到业务文档）
- 以下条目必须跳过，输出人工入库计划：
  - `requires_separate_confirmation=True`
  - 医学/安全类关键词（血氧、禁忌、终止等）命中
  - `target_path` 缺失的非 L1 条目
- `--dry-run-scope` 参数可预览指定组全部可入库条目（如 `--dry-run-scope B`）
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。

fallback_rules:
- Evidence Pack 字段不完整时停止。
- 目标路径不明确时先确认。
- 写入后必须验证链接和索引。
- 若确认范围内只有非 L1 / 非 semantic 条目，输出人工入库计划，不调用自动写入脚本。

#### E 组处理：F 层产物入库

E 组确认后，将处理产物写入 `业务/<域>/`，按 F 层规范标记 frontmatter（`quality` + `source_files`）。更新 wiki索引。

#### G 组处理：Topic 完整文档独立存放

G 组确认后，三步执行：

```
1. 复制到 业务/<域>/，按命名规范改名，补 frontmatter
2. 更新 wiki索引
3. 原文件改名 _archived_原文件名.md
```

不修双链。不删原文件。wiki索引是唯一权威入口。

对建议归档的文件：移到 `知识资产/` 或保留在 Topic。

acceptance_cases:
- “A 组全确认” -> 只处理 A 组。
- `needs_source` 条目 -> 不入库。
- 医学/判断类 -> 单独确认后才写。
- 非 L1 且 `target_path` 明确 -> 自动写入目标业务文档。
- 非 L1 且 `target_path` 缺失 -> 阻断并报错。
- fixture 入库后同步 `知识库/wiki索引.md`、`知识库/术语/术语索引.md`，并通过链接/引用校验。
