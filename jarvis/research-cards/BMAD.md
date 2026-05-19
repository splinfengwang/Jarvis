# Research Card: BMAD

source_project: BMAD-METHOD
source_url: https://github.com/bmad-code-org/BMAD-METHOD
source_revision: `5090cfb09617eeb9c5fb547d4d10529d9886adcd`

source_paths:
- `https://github.com/bmad-code-org/BMAD-METHOD/blob/5090cfb09617eeb9c5fb547d4d10529d9886adcd/src/core-skills/bmad-help/SKILL.md`
- `https://github.com/bmad-code-org/BMAD-METHOD/blob/5090cfb09617eeb9c5fb547d4d10529d9886adcd/src/core-skills/module-help.csv`
- `https://github.com/bmad-code-org/BMAD-METHOD/blob/5090cfb09617eeb9c5fb547d4d10529d9886adcd/docs/reference/core-tools.md`
- `https://github.com/bmad-code-org/BMAD-METHOD/blob/5090cfb09617eeb9c5fb547d4d10529d9886adcd/docs/reference/agents.md`

mechanism_summary:
- `bmad-help` 是总入口 skill，读取 catalog/config/artifacts 后推荐下一步，而不是倾倒全部流程。
- `module-help.csv` 用统一字段表达 skill、menu-code、phase、preceded-by、followed-by、required、outputs。
- agent docs 区分 workflow trigger 和 conversational trigger，前者启动结构化流程，后者要求用户提供上下文。

jarvis_mapping:
- 映射为 `jarvis-help`、Router Spec、skill trigger/non_trigger 字段。
- Jarvis 不照搬 BMAD 的 phase，而采用 Topic 状态、写权限和知识边界作为 gating。

adopted_parts:
- 总入口 help skill。
- 显式 registry 字段。
- 推荐下一步时同时说明 required/optional。
- 区分结构化 workflow 触发和自由对话触发。

rejected_parts:
- 不引入 BMAD 的完整模块阶段制。
- 不让 help skill 自动执行写入。
- 不把 menu-code 作为 Jarvis 的主要用户入口。

usable_rule:
- 当用户问“最近怎么样 / 接下来干什么 / 继续哪个”时，`jarvis-help` 必须先扫描 runtime registry、仪表盘和 Topic 状态，再给最小可执行下一步。

test_case:
- 输入：“最近怎么样？”
- 期望：Router 输出 `intent=status_query`，推荐 `jarvis-status`，无写入，读取仪表盘和 Topic 快照。

failure_trigger_for_research:
- Router 误判副作用、写权限、workflow skill，或 `jarvis-help` 倾倒全量菜单而不能给下一步时，回到 BMAD help/router/workflow registry 重新研究。
