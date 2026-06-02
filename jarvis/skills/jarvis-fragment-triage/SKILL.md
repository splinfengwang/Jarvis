---
name: jarvis-fragment-triage
description: 对碎片输入做分流，并检测是否已经偏离当前 Topic。用于“顺便说一句…”“这个先记一下”“我们换个话题”。默认只做路由和治理判断，不直接写入。
next_skills:
  - jarvis-topic-create
  - jarvis-followup-sync
  - jarvis-topic-freeze
---

# jarvis-fragment-triage

trigger:
- “顺便说一句…”
- “这个先记一下”
- “我们换个话题”
- 出现与当前 Topic 弱相关的碎片输入

non_trigger:
- 用户已经明确要求某个具体 skill 执行。
- 单一明确问题且不涉及 Topic 治理。

inputs:
- 用户碎片输入。
- 当前 Topic 快照、索引。
- `platform-ops/仪表盘.md`。

outputs:
- fragment_type
- current_topic_relation
- recommended_action
- needs_freeze / needs_followup / needs_topic_create
- reason

required_references: []

on_demand_references:
- `jarvis/references/conversation-governance.md`
- `jarvis/references/topic-lifecycle.md`
- `jarvis/references/context-pack-spec.md`

allowed_scripts:
- `jarvis/scripts/sync_followup.py`
- `jarvis/scripts/update_snapshot.py`
- `jarvis/scripts/update_topic_status.py`

write_level:
- none by default

confirmation_rules:
> ⚠️ 只做路由和治理判断，不直接写入。要写入 → 走对应 skill。
- 默认只给路由判断，不直接写入。
- 若判定为 followup，推荐 `jarvis-followup-sync`。
- 若判定为 topic_switch，先建议是否冻结当前 Topic。

fallback_rules:
- 当前 Topic 不明确时，不做漂移判断，只做碎片分流。
- 无法判断 fragment_type 时退回 `jarvis-help`。

acceptance_cases:
- “王涛经理下周给反馈，先记一下” -> `fragment_type=followup`。
- “我们换去聊新松彩页” -> `fragment_type=topic_switch`，建议先冻结当前 Topic。
- “顺便补一句背景” -> `fragment_type=quick_context`，不写入。
