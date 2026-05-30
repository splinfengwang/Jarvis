---
name: jarvis-status
description: 读取 Jarvis 仪表盘、活跃 Topic 和待萃取区，回答“最近怎么样”“现在有哪些事”“当前下一步是什么”。只读，不写入。
next_skills: []
---

# jarvis-status

trigger:
- “最近怎么样”
- “现在有哪些事”
- “当前进展”
- “待拍板有哪些”

non_trigger:
- 用户要求创建、修改、冻结或关闭 Topic。
- 用户只问单个文件内容且不涉及工作状态。

inputs:
- `platform-ops/仪表盘.md`
- 活跃 Topic 的 `_上下文快照.md`，仅在需要补充最后动作、下一步、待拍板时读取。

outputs:
- 活跃 Topic 列表。
- 待萃取 Topic 列表。
- 每个 Topic 的状态、上次更新、下一步。
- 待拍板、跟进事项和阻塞项。
- 明确声明未写入。

required_references: []

on_demand_references:
- `jarvis/references/context-pack-spec.md`
- `jarvis/references/topic-lifecycle.md`

allowed_scripts:
- `jarvis/scripts/validate_dashboard.py`
- `jarvis/scripts/term_health_check.py`

write_level:
- none

confirmation_rules:
- 不更新仪表盘。
- 不更新快照。
- 不创建 Topic。

fallback_rules:
- 仪表盘缺失时停止并说明缺失，不用记忆猜测。
- Topic 链接不可读时列为缺口。

#### 会话审计

回答近况后，附加三项自检：

- [ ] 本次会话的知识查询是否先走了 wiki索引？（是/否/未涉及知识查询）
- [ ] 输出是否使用了声明块格式？（是/否/未涉及知识输出）
- [ ] 是否委托了子 Agent 做知识查询？（是/否/未委托子 Agent）

有否 → 简要说明原因，记录到本次会话的讨论记录（如当前有活跃 Topic）。

acceptance_cases:
- “最近怎么样” -> 输出活跃 Topic、待萃取、下一步、待拍板和跟进事项。
- 仪表盘表格异常 -> 报告异常，不修复。
- OpenViking 命中 -> 只作为线索，不当事实。
