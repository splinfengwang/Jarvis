---
name: jarvis-help
description: Jarvis Runtime v0.1 的帮助、解释和模糊路由入口。用于“最近怎么样”“下一步做什么”“继续哪个 Topic”“为什么这样设计”“有哪些 Jarvis skill 可用”等状态、路由、解释和下一步建议请求；明确 workflow 请求由 Router 直接转对应 skill。
next_skills: []
---

# jarvis-help

定位：
- Bootstrap/Core 先形成 Router 输出；明确 workflow 直接转对应 skill。
- `jarvis-help` 只处理帮助、解释、状态概览和模糊请求，不拦截明确创建/冻结/关闭/萃取/入库意图。

trigger:
- 用户询问近况、下一步、当前状态、可用能力、如何继续。
- 用户要求解释 Router、Context Pack、Evidence Pack 或外部借鉴依据。
- 用户输入模糊，需要先定向到合适的 Jarvis skill。

non_trigger:
- 用户已经明确要求创建、冻结、关闭、萃取或入库时，直接转对应 skill。
- 用户明确禁止读取项目文件时，只基于当前对话回答。

inputs:
- 用户原始请求。
- `platform-ops/仪表盘.md`。
- 必要时读取 `jarvis/references/router-spec.md`。

outputs:
- Router 输出。
- 推荐 skill / script。
- 必需上下文列表。
- 下一步建议，区分必做和可选。

required_references:
- `jarvis/core/JARVIS_CORE.md`

on_demand_references:
- `jarvis/core/JARVIS_BOOTSTRAP.md`
- `jarvis/references/router-spec.md`

allowed_scripts:
- none

write_level:
- none

confirmation_rules:
- 不写文件，不更新 Topic，不入库。
- 若下一步涉及写入，只推荐对应 skill，不代替执行。

fallback_rules:
- Router 字段无法填完整时，说明缺口并回退 `AGENT.md v3.4`。
- 外部借鉴解释找不到研究卡时，不得声称已研究源码。

acceptance_cases:
- “最近怎么样” -> 推荐 `jarvis-status`，读仪表盘，不写入。
- “继续上次那个” -> 先列候选，不猜测。
- “为什么 Context Pack 这样设计” -> 引用 Context Pack spec 和研究卡。
