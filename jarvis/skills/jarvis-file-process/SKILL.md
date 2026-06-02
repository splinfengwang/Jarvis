---
name: jarvis-file-process
description: 将 OCR / 文档解析结果立刻文档化为可人工复核、可后续复用的业务文档。用于“先把这份 OCR 结果落文档”“把这份宣传页解析结果整理出来”。不直接做知识入库。
next_skills:
  - jarvis-knowledge-extract
---

# jarvis-file-process

trigger:
- “先把这份 OCR 结果落文档”
- “把这份宣传页解析结果整理出来”
- “先出一个可人工复核的文档”

non_trigger:
- 用户只要求口头总结，不要求落文档。
- 用户已经明确要求直接做知识萃取。

inputs:
- 原始文件路径。
- OCR / 文档解析结果。
- 目标业务域。
- 文档标题。
- 质量分级：`描述级` / `对比级` / `归纳级`。
- 来源 Topic。

outputs:
- 业务文档写入计划。
- `业务/<域>/` 文档预览。
- `知识库/wiki索引.md` 同步结果。
- validation result。

required_references:
- `jarvis/references/knowledge-extraction.md`

on_demand_references:
- `jarvis/references/knowledge-model-and-ingest.md`
- `jarvis/references/write-permission.md`

allowed_scripts:
- `jarvis/scripts/record_file_process.py`
- `jarvis/scripts/append_operation_log.py`
- `jarvis/scripts/validate_links.py`

write_level:
- content_write after confirmation

confirmation_rules:
> ⚠️ F 层产物必须标记 source_files + quality（📝/🔍/🧠）frontmatter。不标记 = 无法区分来源。
- 该 skill 的目标是“先落可复核文档”，不是直接知识入库。
- 文档必须保留 `source_files`、`processed_in`、`evidence_level=OCR文档解析`、`quality`。
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。

fallback_rules:
- 原始文件路径不存在时停止。
- 没有 OCR / 文档解析内容时不落文档。
- 不把 OCR 结果直接写进正式知识条目。

acceptance_cases:
- “把这份宣传页 OCR 结果整理出来” -> 生成 `业务/<域>/` 文档，供人工复核。
- 关键数字待核对 -> 文档中保留人工复核检查项。
- 后续其他 Topic 可通过 `wiki索引` 找到这份文档。
