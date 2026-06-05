---
name: jarvis-knowledge-feedback
description: 记录知识在实际应用中的反馈。用于“这条先别用”“这条有冲突”“应用中发现不对”。会把反馈回写到知识条目，并在需要时建议进入跟进事项。
next_skills: []
---

# jarvis-knowledge-feedback

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
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 必须明确指向具体知识条目

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 条目不明确时先列候选

