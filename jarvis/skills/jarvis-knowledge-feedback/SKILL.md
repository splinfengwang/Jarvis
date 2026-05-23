---
name: jarvis-knowledge-feedback
description: 记录知识在实际应用中的反馈。用于“这条先别用”“这条有冲突”“应用中发现不对”。会把反馈回写到知识条目，并在需要时建议进入跟进事项。
---

# jarvis-knowledge-feedback

trigger:
- “这条先别用”
- “这条有冲突”
- “应用中发现不对”
- “这个知识先标存疑”

non_trigger:
- 用户只是查询知识内容。
- 没有指向具体知识条目。

inputs:
- 知识条目路径或名称。
- 反馈内容。
- 可选新状态：`待确认` / `已确认` / `存疑` / `已废弃`。

outputs:
- 反馈记录计划。
- 条目状态更新结果。
- 若需要，建议进入跟进事项。
- validation result。

required_references:
- `jarvis/plugins/medical/safety.md`

on_demand_references:
- `jarvis/references/knowledge-model-and-ingest.md`

allowed_scripts:
- `jarvis/scripts/record_knowledge_feedback.py`
- `jarvis/scripts/sync_followup.py`
- `jarvis/scripts/append_operation_log.py`

write_level:
- content_write after confirmation

confirmation_rules:
- 必须明确指向具体知识条目。
- 若反馈涉及医学参数、安全边界或核心判断，默认转 `存疑` 或 `待确认`，并建议跟进事项。
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。

fallback_rules:
- 条目不明确时先列候选。
- 用户只说“感觉不对”但没有具体条目时，不写入。

acceptance_cases:
- “这条先别用” -> 条目写入应用反馈，可改成 `存疑`。
- “这个知识先标存疑” -> frontmatter 状态更新为 `存疑`。
- 医学条目有冲突 -> 建议进入跟进事项。
