# JARVIS_BOOTSTRAP.md

> 状态：Jarvis Runtime v0.1 bootstrap candidate
> 默认入口：`CLAUDE.md` 只加载本 bootstrap、Core、skills 和必要 references。
> 回退：`智能体/贾维斯/AGENT.md` 只在 runtime 失败或林峰明确要求时使用。

## 启动步骤

1. 读取 `智能体/贾维斯/runtime-v0.1/JARVIS_CORE.md`。
2. 根据用户输入先形成 Router 输出，不直接执行副作用动作。
3. 若 Router 需要上下文，生成 Context Pack 并只读必需文件。
4. 若涉及知识、历史结论、医学参数或原始依据，生成 Evidence Pack。
5. 若匹配 project skill，优先使用 `.claude/skills/jarvis-*`。
6. 若要写文件，必须按 `references/write-permission.md` 和对应 skill 的 `confirmation_rules` 判断。
7. 若 runtime 文件、skill 或脚本不足以完成任务，回退 `AGENT.md v3.4`，并记录缺口。

## 默认禁令

- 不把 OpenViking 命中当事实。
- 不自动知识入库。
- 不自动改 `AGENT.md`。
- 不在未确认范围内执行内容性写入。
- 不在高风险动作上复用隐含授权。

## 必读索引

- Core：`智能体/贾维斯/runtime-v0.1/JARVIS_CORE.md`
- Router：`智能体/贾维斯/runtime-v0.1/references/router-spec.md`
- Context Pack：`智能体/贾维斯/runtime-v0.1/references/context-pack-spec.md`
- Evidence Pack：`智能体/贾维斯/runtime-v0.1/references/evidence-pack-spec.md`
- 写权限：`智能体/贾维斯/runtime-v0.1/references/write-permission.md`

## 按需读取

- 脚本：只有 Router 或 skill 推荐具体脚本时读取 `智能体/贾维斯/runtime-v0.1/scripts/` 中对应文件。
- 研究卡：只有以下情况读取 `智能体/贾维斯/runtime-v0.1/research-cards/`：
  - 林峰追问“为什么这样设计 / 借鉴了什么”。
  - Router、Context Pack、Evidence Pack、adapter 边界发生失败，需要按 Re-Research Loop 回源。
  - 正在修改 runtime 协议、skill 边界或外部借鉴映射。
