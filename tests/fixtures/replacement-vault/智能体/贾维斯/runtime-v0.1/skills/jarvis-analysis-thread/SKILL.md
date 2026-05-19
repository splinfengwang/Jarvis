---
name: jarvis-analysis-thread
description: 分析线程状态管理。用于"这个分析先存档""提案确认一下""这个方向废弃"。管理分析文档的状态流转（讨论中/提案/已确认/已废弃）和 related 双链。
---

# jarvis-analysis-thread

trigger:
- "这个分析先存档"
- "提案确认一下"
- "这个方向废弃"
- "这个分析状态更新为…"

non_trigger:
- 仅讨论分析内容，不涉及状态变更
- 创建新的分析文档（应走 Topic 创建或文件处理流程）

inputs:
- 分析文档路径
- 目标状态
- 可选 related 双链更新

outputs:
- 状态变更计划
- frontmatter 更新预览
- related 双链更新预览

required_references:
- `智能体/贾维斯/runtime-v0.1/references/analysis-thread.md`
- `智能体/贾维斯/runtime-v0.1/references/write-permission.md`

allowed_scripts:
- `智能体/贾维斯/runtime-v0.1/scripts/append_operation_log.py`

write_level:
- record_write (状态变更) / content_write after confirmation (修改分析正文)

confirmation_rules:
- 状态变更（仅改 frontmatter status）为记录性写入，可自主执行
- 修改分析结论正文为内容性写入，需确认
- `abandoned` 状态只标记，不删除文件

fallback_rules:
- 分析文档不存在时停止
- 目标状态与当前状态相同时提示，不重复操作

acceptance_cases:
- "这个分析先存档" → 状态改为 `proposed` 或 `discussing`
- "提案确认一下" → 状态改为 `proposed`，等待林峰确认
- "这个方向废弃" → 状态改为 `abandoned`