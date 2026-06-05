---
name: jarvis-help
description: Jarvis Runtime 的帮助、解释和模糊路由入口。用于“有哪些 Jarvis skill 可用”“为什么这样设计”“下一步可以做什么”“这个怎么用”等能力解释和方法论审查请求。涉及具体项目状态查询（如“最近怎么样”“当前进展”）委托 jarvis-status 处理；明确 workflow 请求由 Router 直接转对应 skill。
next_skills: []
---

# jarvis-help

定位：
- Bootstrap/Core 先形成 Router 输出；明确 workflow 直接转对应 skill。
- `jarvis-help` 只处理帮助、解释、能力概述和模糊请求，不拦截明确创建/冻结/关闭/萃取/入库意图。
- 涉及具体项目状态（活跃 Topic、进度、待办）→ 委托 `jarvis-status`。
- 用户输入模糊，需要先定向到合适的 Jarvis skill 时介入。

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
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 当前 Topic 讨论深入时（讨论记录 > 2000 字/含方案参数），提示可用 jarvis-roundtable

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- Router 字段无法填完整时，说明缺口并回退 AGENT.md v3.4
