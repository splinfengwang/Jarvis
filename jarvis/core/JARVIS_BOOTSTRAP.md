# JARVIS_BOOTSTRAP.md

> 状态：Jarvis v2.0.1 bootstrap
> 默认入口：`CLAUDE.md` 只加载本 bootstrap、Core、skills 和必要 references。
> `AGENT_v3.4.md` 为历史参考和设计背景，日常行为以 `core/JARVIS_CORE_BRIEF.md` + `skills/` 为准。

## 启动步骤

1. 读取 `core/JARVIS_CORE_BRIEF.md`（精简版，~60 行，Agent 每次会话必读）。
2. 需要细节时按需读取 `core/JARVIS_CORE_FULL.md`（完整参考，575 行）。
2. 根据用户输入先形成 Router 输出，不直接执行副作用动作。
3. 若 Router 需要上下文，生成 Context Pack 并只读必需文件。
4. 若涉及知识、历史结论或原始依据，生成 Evidence Pack。
5. 若匹配 project skill，优先使用 skills。
6. 若要写文件，必须按 `references/write-permission.md` 和对应 skill 的 `confirmation_rules` 判断。
7. 若 runtime 文件、skill 或脚本不足以完成任务，按 Core §12 回退原则处理，并记录缺口到当前 Topic。

## 默认禁令

- 不把记忆检索命中当事实。
- 不自动知识入库。
- 不自动改 Core 文件。
- 不在未确认范围内执行内容性写入。
- 不在高风险动作上复用隐含授权。

## 必读索引

- Core：`core/JARVIS_CORE.md`
- Router：`references/router-spec.md`
- Context Pack：`references/context-pack-spec.md`
- Evidence Pack：`references/evidence-pack-spec.md`
- 写权限：`references/write-permission.md`
- 知识库目录树：`references/knowledge-base-structure.md`

## 按需读取

- 脚本：只有 Router 或 skill 推荐具体脚本时读取 `scripts/` 中对应文件。
- 研究卡：只有以下情况读取 `research-cards/`：
  - 用户追问"为什么这样设计 / 借鉴了什么"。
  - Router、Context Pack、Evidence Pack 边界发生失败，需要按 Re-Research Loop 回源。
  - 正在修改 runtime 协议、skill 边界或外部借鉴映射。
