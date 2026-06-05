---
name: jarvis-knowledge-ingest
description: 按林峰确认范围把 Evidence Pack 入库，或给出人工入库计划。用于“A 组全确认”“这几条确认入库”。只处理明确确认范围。
next_skills: []
---

# jarvis-knowledge-ingest

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
- `jarvis/references/knowledge-model.md`
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
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 入库后必须立即更新 wiki索引 和 术语索引。索引不同步 = 入库未完成
- 确认项标记为 ✅ 互补 时：新条目入库后，同时更新被补充的已有条目（正文末尾追加新内容）
- 确认项标记为 🔗 应关联 时：新条目入库后，同时更新被引用的已有条目（related 字段追加新条目）
- 不能把 candidate_only 或 needs_source 条目写入正式知识库
- v0.2 自动脚本可处理：L1 semantic + L2/L3/L4/F 有明确 target_path 条目
- 以下必须跳过输出人工入库计划：requires_separate_confirmation / medical-safety / missing target_path
- --dry-run-scope 参数可预览指定组全部可入库条目

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- Evidence Pack 字段不完整时停止
- 写入后必须验证链接和索引
- 若确认范围内只有非 L1 / 非 semantic 条目，输出人工入库计划，不调用自动写入脚本

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

