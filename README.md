<p align="center">
  <h1 align="center">Jarvis</h1>
  <p align="center"><strong>面向长期 Agent 协作的工作记忆运行时。</strong></p>
  <p align="center">把一次次 LLM 对话，变成可恢复、可验证、可复用的工作知识系统。</p>
  <p align="center">
    <a href="README.md">中文</a> · <a href="README.en.md">English</a>
  </p>
  <p align="center">
    <a href="#安装"><img src="https://img.shields.io/badge/python-%E2%89%A53.10-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
</p>

<p align="center">
  <img src="assets/jarvis-hero-persona-light.png" alt="Jarvis 拟人化工作记忆助理形象图" width="100%">
</p>

---

## 一句话定位

Jarvis 是一个面向长期工作的 Agent Runtime。

它不是新的聊天机器人，不是 prompt 合集，也不是把文档塞进向量库的 RAG 外壳。它的目标更底层：给 LLM 一套可执行的工作秩序，让它在持续协作中知道该读什么、该记录什么、什么能写、什么必须确认、哪些结论能进入长期知识库。

如果普通 LLM 会话是一次性的智力外包，Jarvis 要做的是把它升级成一套持续运转的工作记忆系统：

```text
Conversation → Topic → Evidence → Knowledge → Reuse
```

每一次讨论都不是孤立事件，而是被放进同一条链路：上下文可恢复，结论可追溯，知识可复用，写入可审计。

---

## 产品主张

LLM 的瓶颈正在从“能不能回答”转向“能不能长期可靠地一起工作”。

Jarvis 的判断是：未来的个人工作知识库，不应该靠人事后手动整理；也不应该让 Agent 无约束地自动改写。更合理的形态是：

> Agent 在工作过程中受约束地沉淀知识，人保留关键判断和确认权，文件系统保留最终可审计状态。

所以 Jarvis 不追求“无感自动化”。它追求的是一种更可靠的协作结构：

- 对 Agent：给它路由、检索、写入和萃取纪律
- 对人：保留拍板权，只在真正影响未来判断时确认
- 对知识库：让每条知识都有来源、状态、位置和复用口径
- 对未来会话：让“继续上次”成为可执行动作，而不是记忆幻觉

---

## 设计思想

### 1. 对话是界面，不是记忆

普通 LLM 协作容易停在“聊完了”。Jarvis 的目标不是把聊天记录保存下来，而是把讨论中真正有未来价值的信息拆成更稳定的资产：

- 术语和概念：以后讨论时不再反复解释
- 关系和规则：概念之间如何协作，流程如何运转
- 判断和决策：为什么选这个方案，放弃了什么
- 待验证问题：哪些关键问题还不能被当作事实
- 文件处理产物：PDF、PPT、OCR、网页、Confluence 等资料的结构化整理

这使知识库不是事后整理的文档仓库，而是在工作过程中自然生长的判断系统。

### 2. 没有治理的记忆，是风险资产

Jarvis 的核心不是“让 Agent 多做事”，而是让 Agent 在做事前先遵守边界：

- 事实、证据、推论、偏好、待验证问题必须区分
- 涉及项目知识时，先读 `知识库/wiki索引.md`，不能直接全项目乱搜
- OpenViking / 记忆搜索只能作为召回线索，不能单独当事实
- 内容性写入和高风险写入必须先确认
- Topic 关闭不等于自动入库，知识入库必须经过 Evidence Pack 和确认清单

这套约束通过 Core、Skill、Hook 和脚本共同执行，而不只依赖 Agent 自觉。

### 3. Topic 是长期工作的原子单元

Jarvis 把一个持续推进的工作命题抽象成 Topic。Topic 记录的不只是文件，还包括：

- 当前范围
- 最后动作
- 下一步
- 已确认事实
- 当前推论
- 待拍板事项
- 未解决问题
- 关联会话记录
- 关键产出
- 待萃取状态

所以“继续上次”时，Agent 不应该凭记忆回答，而应该恢复 Topic：读仪表盘、读快照、读索引，然后汇报“上次做到哪里、下一步是什么、之前卡在哪里”。

### 4. 知识必须可检查

Jarvis 默认使用文件系统和 Markdown，而不是把所有东西直接丢进黑盒向量库。

这样做的取舍是：

- 好处：人能读，Git 能 diff，错误能回滚，双链能追溯
- 代价：需要维护索引、命名、状态和确认流程

Jarvis 接受这个成本，因为长期工作知识最重要的是可解释性和可治理性，而不是单次召回看起来“像相关”。

---

## 它和常见方案的区别

| 问题 | 典型聊天/RAG/Agent 框架 | Jarvis 的取舍 |
|---|---|---|
| 会话结束后剩下什么 | 聊天记录或向量片段 | Topic 快照、证据包、确认后的知识条目 |
| Agent 怎么知道该读什么 | 搜索相似内容或让模型自由探索 | Router + Context Pack + wiki索引纪律 |
| 记忆能不能直接当事实 | 经常混在回答里 | 只能作为线索，必须回源确认 |
| 写文件怎么控风险 | 允许/禁止工具调用 | 记录性、内容性、高风险三级裁决 |
| 知识怎么进入长期库 | 自动总结或人工整理 | Evidence Pack → 分组确认 → 入库同步索引 |
| 多轮工作怎么恢复 | 依赖模型记忆或用户复述 | 仪表盘 + Topic Capsule + 关联会话 |
| 错了怎么办 | 很难追溯 | Markdown + Git + 双链 + 来源字段 |

Jarvis 的核心不是“更会聊”，而是让 Agent 从临时助手变成受治理的长期工作合作者。

---

## 产品模型

Jarvis 由八类对象组成。

| 对象 | 作用 | 典型位置 |
|---|---|---|
| Core | Agent 的行为规程：路由、检索、写入裁决、事实口径、安全边界 | `jarvis/core/` |
| Skill | 可触发的工作流：创建 Topic、恢复 Topic、知识萃取、入库、圆桌审查等 | `jarvis/skills/` |
| Hook | 在 Claude Code 生命周期中注入 Core、拦截写入、保存 compact 前状态 | `jarvis/hooks/` |
| Topic | 持续工作命题的状态容器 | `platform-ops/topics/<Topic>/` |
| Knowledge | 已确认或待确认的知识资产，按 L1-L4/F 分层 | `知识库/`、`业务/` |
| Catalog | 项目内容目录注册表，控制哪些目录只读、哪些可写 | `jarvis.yaml` |
| Persona | 可复用审查角色，用于 Roundtable 多角色审查 | `jarvis/personas/`、`jarvis.yaml` |
| Backend | 记忆检索后端，默认文件搜索，可选 OpenViking 语义搜索 | `jarvis/backends/` |

### 执行层分工

Jarvis 不是把所有动作都做成一个全自动后台服务，而是把确定性操作和判断性操作分开：

| 层级 | 负责什么 | 例子 |
|---|---|---|
| Hook 自动执行 | 会话启动、写入前拦截、compact 前状态保存 | 注入 Core、阻止高风险写入 |
| CLI / Script 确定性执行 | 可验证的文件结构和状态同步 | 创建 Topic、更新仪表盘、生成 Evidence Pack |
| Skill 编排 | 让 Agent 按流程读取、判断、解释、提案 | 萃取、入库、圆桌审查、目录注册 |
| 用户确认 | 内容性判断、知识确认、高风险动作授权 | 是否入库、是否合并术语、是否采纳方案 |

这个分工是有意为之：确定性动作交给脚本，判断性动作保留给 Agent 和人共同完成，避免“自动化很快，但错了没人知道”。

---

## 核心能力

### 1. 会话启动时自动建立行为基线

安装后，Jarvis 通过 Claude Code hooks 在会话启动时注入 Core。

启动链路：

```text
Claude Code SessionStart
  → jarvis-core-inject.sh
  → 读取 JARVIS_CORE.md
  → 读取项目 jarvis.yaml
  → 注入插件模块
  → 注入语义路径映射
  → 注入知识快照
  → Agent 获得本轮工作规则
```

同时还有两个辅助 hook：

- `jarvis-write-guard.sh`：在写文件和高风险 Bash 前进行保护
- `jarvis-compact-save.sh`：在上下文压缩前提示保存运行状态

### 2. Router 把自然语言请求映射到工作流

你不需要记命令。日常直接用自然语言触发：

| 你说 | Jarvis 应该走 |
|---|---|
| “最近怎么样”“现在有哪些事” | `jarvis-status` |
| “继续 XX”“接着上次” | `jarvis-topic-resume` |
| “开一个 Topic”“先建立话题” | `jarvis-topic-create` |
| “先存一下”“今天先到这” | `jarvis-topic-freeze` |
| “这个 Topic 收一下” | `jarvis-topic-close` |
| “萃取一下这个 Topic” | `jarvis-knowledge-extract` |
| “A 组全确认”“这几条入库” | `jarvis-knowledge-ingest` |
| “记一下这个跟进” | `jarvis-followup-sync` |
| “顺便说一句” | `jarvis-fragment-triage` |
| “查一下 Confluence” | `jarvis-confluence-read` |
| “把 OCR 结果落文档” | `jarvis-file-process` |
| “多角度看一下”“拉个会讨论” | `jarvis-roundtable` |
| “新建一个审查角色” | `jarvis-persona-create` |
| “建个目录叫 X，以后都放这里” | `jarvis-catalog-register` |

Router 的原则是：先判断目标和副作用，再决定读什么、写不写、是否需要确认。

### 3. Topic 生命周期管理

Topic 是 Jarvis 的主工作单元。

标准结构：

```text
platform-ops/topics/YYYYMMDD_主题简称/
├── 索引.md
├── _上下文快照.md
├── _准入检查单.md
├── 讨论记录.md
├── 参考资料/
├── 过程稿/
└── 定稿/
```

状态流转：

| 状态 | 含义 |
|---|---|
| `doing` / `[🟢 Doing]` | 当前正在推进 |
| `paused` / `[🟡 Paused]` | 暂停，可恢复 |
| `blocked` / `[🔴 Blocked]` | 被外部依赖阻塞 |
| `pending_extraction` / `[📋 待萃取]` | 工作完成，等待知识萃取 |
| `done` / `[⚪ Done]` | 萃取完成，归档 |

Topic 关闭时不会自动入库，而是进入“待萃取”。这是一个刻意设计：工作完成和知识确认是两件事。

Topic 状态变更不是只改一个文件。冻结、恢复、关闭会围绕三件事做同步：

- Topic 本体：`索引.md`、`_上下文快照.md`、`讨论记录.md`
- 全局入口：`platform-ops/仪表盘.md`、`platform-ops/log.md`
- 外部保护：需要时通过 Git 保存可回滚的工作点

### 4. Context Pack：只读该读的文件

Jarvis 不鼓励 Agent 每次把整个项目扫一遍。

不同任务有不同读取深度：

| 场景 | 优先读取 |
|---|---|
| 近况查询 | 仪表盘、活跃 Topic 快照 |
| Topic 恢复 | 仪表盘、目标 Topic 快照、索引 |
| 新工作命题 | wiki索引、仪表盘、相关业务文档 |
| 知识萃取 | Topic 四件套、关联会话 JSONL、源文件 |
| 深度溯源 | 知识库正文、Topic 记录、Confluence 原文、JSONL |

这背后的原则是：上下文不是越多越好，而是要可解释、够用、能回源。

### 5. Evidence Pack：先形成证据包，再谈入库

知识萃取不是“总结一下聊天记录”。

`jarvis-knowledge-extract` 会把 Topic 和源材料拆成 Evidence Pack，并输出确认清单：

- A. 可快速确认
- B. 需要拍板
- C. 需要验证或裁决
- D. 建议不入库
- E. 文件处理产物
- G. Topic 完整文档

每条候选知识都必须带来源、可信度、准备用法和入库建议。没有来源的 claim 不进入确认清单。

确认后，`jarvis-knowledge-ingest` 才会按范围写入知识库，并同步 `wiki索引.md`、`术语索引.md` 和操作日志。

### 6. L1-L4/F 知识分层

Jarvis 把知识分为五层：

| 层级 | 内容 | 推荐载体 |
|---|---|---|
| L1 | 术语和概念定义 | `知识库/术语/` |
| L2 | 关系、规则、流程 | `业务/<域>/` |
| L3 | 判断、决策、取舍理由 | `业务/<域>/` 或 Topic 定稿 |
| L4 | 待验证问题、未解决问题 | Topic / 分析文档 |
| F | 文件处理产物，如 OCR/PDF/PPT 结构化整理 | `业务/<域>/` |

这套分层的目的不是分类好看，而是控制复用风险：定义可以高频复用，判断必须带上下文，待验证问题不能被误用成事实。

### 7. 多角色 Roundtable 审查

Jarvis 内置 5 个 persona：

- `pm-analyst`：需求完整性和优先级
- `design-reviewer`：交互流程和用户体验
- `edge-case-hunter`：边界条件和极端场景
- `technical-auditor`：技术可行性和架构一致性
- `medical-safety`：医学安全和参数依据

`jarvis-roundtable` 会从当前 Topic 提取上下文，让多个独立子 agent 按不同 persona 并行审查，再由主 agent 汇总共识、分歧和优先级建议。

用户也可以通过 `jarvis-persona-create` 把新的审查角色写入 `jarvis.yaml`。

### 8. Catalog 与插件扩展

Catalog 解决“项目里有哪些内容目录、哪些可写”的问题。

```yaml
catalogs:
  产品方案:
    writable: true
    description: "确认后的产品方案和设计文档"
  外部资料:
    writable: false
    description: "只读引用，不由 Jarvis 改写"
```

插件解决“不同领域有不同安全边界”的问题。当前内置 medical 插件，可注入：

- 领域安全规则
- 多视角校验
- 交付检查清单
- 医学知识分类维度

在项目中启用：

```yaml
plugins:
  - medical-safety
```

---

## 日常使用方式

### 初始化一个项目

```bash
npm install -g jarvis-agent
jarvis init ~/my-project
cd ~/my-project
claude
```

初始化后项目会得到：

```text
my-project/
├── jarvis.yaml
├── CLAUDE.md
├── 知识库/
│   ├── wiki索引.md
│   └── 术语/
│       └── 术语索引.md
├── 业务/
├── platform-ops/
│   ├── 仪表盘.md
│   ├── log.md
│   └── topics/
└── .claude/
    ├── skills/
    ├── hooks/
    └── settings.json
```

### 开始一个新工作命题

对 Agent 说：

```text
先建立一个 Topic：服务需求管理方案
范围是梳理养老机构服务需求从登记到派单的完整流程。
```

Jarvis 应该：

1. 判断是否满足 Topic 准入
2. dry-run 创建计划
3. 生成 Topic 四件套和三个子目录
4. 更新仪表盘
5. 记录当前会话来源

### 推进讨论和产出

讨论过程中，阶段性草稿放在：

```text
platform-ops/topics/<Topic>/过程稿/
```

用户确认后的最终版本放在：

```text
platform-ops/topics/<Topic>/定稿/
```

文件命名遵守：

```text
YYYYMMDD-主题-文档类型.md
YYYYMMDD-主题-文档类型-v0.1.md
```

### 暂停和恢复

暂停：

```text
这个先存一下，下一步是补异常流程。
```

恢复：

```text
继续服务需求管理方案。
```

Jarvis 应该恢复并汇报：

1. 上次做到哪里
2. 接下来该做什么
3. 之前卡在哪里或待拍板是什么

### 关闭和萃取

关闭 Topic：

```text
这个 Topic 收一下，进入待萃取。
```

萃取知识：

```text
萃取一下这个 Topic。
```

确认入库：

```text
A 组全确认，C 组先保持待验证，G1 独立存放。
```

Jarvis 的边界是：关闭不自动萃取，萃取不自动入库，入库必须有明确确认范围。

### 查询已有知识

直接问：

```text
之前我们怎么定义服务需求的？
```

Jarvis 应该先读 `知识库/wiki索引.md` 或 `知识库/术语/术语索引.md`，再读取命中的具体文件；如果降级到搜索，必须说明索引缺口，并把缺口记录到 wiki索引。

---

## CLI

| 命令 | 作用 |
|---|---|
| `jarvis init <path>` | 初始化项目骨架 |
| `jarvis init --sync <path>` | 同步已有项目版本，清理可能重复触发的项目级 hook |
| `jarvis doctor <path>` | 检查安装、skill、hook、索引、仪表盘和后端 |
| `jarvis status <path>` | 查看 Jarvis 项目配置状态 |
| `jarvis upgrade [path]` | 基于 git tag 升级框架 |
| `jarvis uninstall <path>` | 从项目中移除 Jarvis，默认保留用户数据 |
| `jarvis bootstrap` | 只全局注册 `/jarvis-init` skill |
| `jarvis version` | 查看当前版本 |

离线安装：

```bash
npm pack jarvis-agent
npm install -g ./jarvis-agent-x.y.z.tgz
jarvis init ~/my-project
```

源码安装：

```bash
git clone https://github.com/splinfengwang/Jarvis.git
cd Jarvis
pip install -e .
jarvis init ~/my-project
```

安装检查：

```bash
jarvis doctor ~/my-project
```

---

## 内置 Skill

当前内置 19 个 skill。

| 分组 | Skill |
|---|---|
| 项目初始化 | `jarvis-init` |
| Topic 生命周期 | `jarvis-topic-create`、`jarvis-topic-resume`、`jarvis-topic-freeze`、`jarvis-topic-close`、`jarvis-topic-organize` |
| 状态和治理 | `jarvis-status`、`jarvis-fragment-triage`、`jarvis-followup-sync` |
| 知识闭环 | `jarvis-knowledge-extract`、`jarvis-knowledge-ingest`、`jarvis-knowledge-feedback` |
| 文件和来源 | `jarvis-file-process`、`jarvis-confluence-read` |
| 分析资产 | `jarvis-analysis-thread` |
| 扩展机制 | `jarvis-catalog-register`、`jarvis-persona-create`、`jarvis-roundtable` |
| 帮助入口 | `jarvis-help` |

---

## 工程结构

```text
jarvis/
├── core/             # Core 行为规程和 bootstrap
├── skills/           # 19 个 Jarvis skill
├── hooks/            # SessionStart / PreToolUse / PreCompact hooks
├── scripts/          # 17 个可执行维护脚本
├── references/       # Topic、知识、证据、写入、插件等规范
├── templates/        # 初始化项目模板
├── personas/         # 内置审查角色
├── plugins/          # 领域插件
├── backends/         # file / openviking 记忆后端
└── research-cards/   # 外部系统借鉴记录
```

关键文件：

| 文件 | 作用 |
|---|---|
| `jarvis/core/JARVIS_CORE.md` | 会话注入的精简运行时规则 |
| `jarvis/core/JARVIS_CORE_FULL.md` | 完整行为规程和设计细节 |
| `jarvis/core/JARVIS_BOOTSTRAP.md` | Core 未自动注入时的手动启动入口 |
| `jarvis/references/topic-lifecycle.md` | Topic 生命周期和文件命名规范 |
| `jarvis/references/knowledge-model.md` | L1-L4/F 知识模型 |
| `jarvis/references/evidence-pack-spec.md` | Evidence Pack 格式 |
| `jarvis/references/write-permission.md` | 写入裁决规则 |

---

## 配置

项目配置文件是 `jarvis.yaml`。

最小配置：

```yaml
jarvis_version: "1.10.0"
jarvis_home: "/path/to/jarvis"

paths:
  knowledge_base: 知识库
  wiki_index: 知识库/wiki索引.md
  terms_dir: 知识库/术语
  terms_index: 知识库/术语/术语索引.md
  business_dir: 业务
  ops_dir: platform-ops
  dashboard: platform-ops/仪表盘.md
  log: platform-ops/log.md
  topics: platform-ops/topics

plugins: []
backend: file
```

可选扩展：

```yaml
backend: openviking

catalogs:
  产品方案:
    writable: true
    description: "确认后的产品和设计方案"

personas:
  compliance-auditor:
    title: "合规审查员"
    role: "从合规和审计角度检查方案"
```

---

## 安全边界和已知取舍

Jarvis 有意保留一些“慢步骤”：

- 需要索引，而不是直接全文搜索
- 需要确认清单，而不是自动入库
- 需要写入分级，而不是所有文件都能直接改
- 需要 Topic 状态同步，而不是只靠聊天上下文

这些步骤增加了短期摩擦，但换来长期工作的可恢复性、可追溯性和可治理性。

当前边界：

- Jarvis 不是模型调用框架，不负责 provider 编排
- Jarvis 不替代 Git、Obsidian、Confluence 或 OpenViking
- OpenViking 是可选召回层，不是事实源
- Roundtable 依赖当前 Agent 环境支持子 agent / task 工具
- Confluence 读取依赖本地 cookie 配置
- 领域插件只注入规则，不替用户做领域决策

Jarvis 对回答本身也有约束：涉及项目知识时，Agent 应先声明引用来源、待确认内容、推论依据和方案前提。没有来源的结论不能伪装成事实。

---

## 适合什么场景

Jarvis 特别适合：

- 长周期产品方案讨论
- 业务知识库持续维护
- 频繁跨会话恢复上下文
- 需要保留决策链和取舍理由的工作
- 需要多人视角审查但实际由 Agent 辅助完成的方案评审
- 医疗、政企、B2B 等对术语、边界和证据要求高的领域

不适合：

- 一次性问答
- 不需要沉淀的闲聊
- 只追求快速生成、不关心可追溯性的内容生产
- 完全不愿维护目录、索引和确认流程的工作方式

---

## License

MIT
