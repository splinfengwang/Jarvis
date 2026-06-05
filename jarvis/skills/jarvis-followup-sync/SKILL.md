---
name: jarvis-followup-sync
description: 记录或更新跟进事项。用于“记一下这个跟进事项”“这个到时候提醒我”“等对方回复后继续”。只处理有时间窗口、外部责任人或明确下一步动作的事项。
next_skills: []
---

# jarvis-followup-sync

inputs:
- 事项名称。
- 截止日期或时间窗口。
- 当前状态。
- 下一步动作。

outputs:
- 跟进事项写入计划。
- 仪表盘跟进事项区 diff preview。
- validation result。

required_references: []

on_demand_references:
- `jarvis/references/write-permission.md`
- `jarvis/references/topic-lifecycle.md`

allowed_scripts:
- `jarvis/scripts/sync_followup.py`
- `jarvis/scripts/append_operation_log.py`
- `jarvis/scripts/validate_dashboard.py`

write_level:
- record_write

confirmation_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 必须有事项名和下一步动作
- 若截止/窗口缺失但用户明确说"后续提醒"，先补成 待确认 再记录

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 不把知识条目、Topic 状态、医学判断误写进跟进事项区

