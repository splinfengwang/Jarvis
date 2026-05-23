---
name: jarvis-topic-resume
description: 恢复已有 Jarvis Topic。用于“继续...”“接着上次...”“恢复某 Topic”。只读索引、快照和必要讨论记录。
---

# jarvis-topic-resume

trigger:
- “继续 <Topic>”
- “恢复 <Topic>”
- “接着上次”

non_trigger:
- 明确创建新 Topic。
- 明确关闭、冻结或萃取。

inputs:
- Topic 名称或关键词。
- `platform-ops/仪表盘.md`。
- 匹配到的 `索引.md` 和 `_上下文快照.md`。

outputs:
- Topic 匹配结果。
- 最后动作。
- 已确认事实、当前推论、待拍板。
- 下一步建议。

required_references: []

on_demand_references:
- `jarvis/references/context-pack-spec.md`
- `jarvis/references/topic-lifecycle.md`

allowed_scripts:
- none

write_level:
- none

confirmation_rules:
- 模糊匹配或多候选时先确认。
- 不更新快照，不写讨论记录。

fallback_rules:
- 找不到 Topic 时，按 `jarvis-status` 列候选。
- 快照缺失时停止并说明需要补上下文。

acceptance_cases:
- “继续贾维斯运行时架构” -> 读仪表盘、索引、快照并输出恢复摘要。
- “继续上次那个” -> 多候选时询问。
- 快照缺失 -> 不编造最后动作。

