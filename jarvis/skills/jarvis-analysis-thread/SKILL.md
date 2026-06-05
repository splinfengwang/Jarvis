---
name: jarvis-analysis-thread
description: 分析线程状态管理。用于"这个分析先存档""提案确认一下""这个方向废弃"。管理分析文档的状态流转（讨论中/提案/已确认/已废弃）和 related 双链。
next_skills:
  - jarvis-followup-sync
  - jarvis-topic-close
---

# jarvis-analysis-thread

inputs:
- 分析文档路径
- 目标状态
- 可选 related 双链更新

outputs:
- 状态变更计划
- frontmatter 更新预览
- related 双链更新预览

required_references: []

on_demand_references:
- `jarvis/references/analysis-thread.md`
- `jarvis/references/write-permission.md`

allowed_scripts:
- `jarvis/scripts/append_operation_log.py`

write_level:
- record_write (状态变更) / content_write after confirmation (修改分析正文)

confirmation_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- （本 skill 无特有规则，全部由 CORE 覆盖）

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 目标状态与当前状态相同时提示，不重复操作
