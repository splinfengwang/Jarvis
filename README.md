<p align="center">
  <h1 align="center">Jarvis</h1>
  <p align="center"><strong>让 LLM 学会协作，而不是只会聊天。</strong></p>
  <p align="center">
    <a href="#安装"><img src="https://img.shields.io/badge/python-%E2%89%A53.10-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
</p>

---

## 一句话定位

**Jarvis 是一个 LLM 原生智能体框架。** 它不生成 prompt，不编排 workflow，不做 tool calling 封装。它做一件更底层的事：**在每次会话启动时，把一套完整的行为规程注入 LLM 上下文，让 LLM 成为一个知道"怎么协作、怎么思考、怎么不犯错"的工作助理。**

用一句话说：LangChain 解决"怎么调用"，Jarvis 解决"怎么工作"。

---

## 它解决的问题

长期用 LLM 做工作助理的人都会遇到这三个问题。不是偶尔，是每次：

| 问题 | 现象 |
|---|---|
| **上下文失忆** | 新会话从零开始。昨天的决策、设计到一半的方案——全没了 |
| **缺乏判断力** | LLM 分不清什么是你确认过的、什么是它猜的、什么是搜索命中的。它把推论当事实，把搜索当证据 |
| **行为退化** | 同一个 LLM，今天知道先读文件再下结论，明天凭记忆乱猜。核心行为跨会话不一致 |

Jarvis 要解决的，不是"让 LLM 变聪明"，而是**让 LLM 变可靠**。

---

## 设计哲学

### 不是库，是规程

大多数 LLM 工具是库——你 import，调用 API，控制流程。Jarvis 是规程——它把"怎么工作"的规则注入到 LLM 的上下文起始位置，让 LLM 自己判断、自己决策、自己遵守纪律。

### 三条铁律

| 铁律 | 防什么 |
|---|---|
| 文件读取优先于记忆猜测 | "上次我看过"→ 文件已被改 |
| 事实确证优先于推论建议 | "我们应该用 X"→ 没说是猜的 |
| 写入确认优先于自动执行 | "我把你的文件改了"→ 未经确认 |

这三条不是 prompt 里的建议——它们通过 SessionStart hook 每次自动注入，PreToolUse hook 在文件操作层面做门禁。

### 事实与推论必须可区分

Jarvis 强制 LLM 在输出中区分五类信息：**事实**（源文件确认的）、**证据**（可追溯到原文的）、**推论**（Jarvis 归纳的）、**偏好**（用户表达过的）、**待验证问题**（目前不确定的）。推论不标注不能输出。OpenViking 搜索结果只是"线索"，必须回源文件确认。

### 写入不是二元的

不是"能写 / 不能写"。是三级：
- **记录性写入**：建 Topic、追加讨论记录 → 可自主执行
- **内容性写入**：修改方案、编辑知识条目 → 先提案，确认后执行
- **高风险写入**：删除文件、批量迁移、改 Core → 严格审批

判断标准：这次写入会不会改变未来 Jarvis 对业务、知识、规则的判断？

### 插件是可组合的提示词

`{{PLUGIN:SAFETY}}` → 启动时替换为医学安全规则。无插件时占位符删除。插件不修改 Core。

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/splinfengwang/Jarvis.git
cd Jarvis

# 2. 安装（选一种）

# 方式 A: pipx（推荐，macOS homebrew Python 用户首选）
brew install pipx && pipx ensurepath
pipx install -e .

# 方式 B: venv（需要每次激活）
python3 -m venv .venv && source .venv/bin/activate && pip install -e .

# 方式 C: 系统 pip（需要 --break-system-packages）
pip3 install --break-system-packages -e .

# 3. 初始化项目
jarvis init ~/my-project
cd ~/my-project

# 4. 启动 Claude Code → Core 自动注入
claude
```

### 初始化后的项目

```
my-project/
├── jarvis.yaml              # 配置（插件、后端、路径）
├── CLAUDE.md                # 项目入口
├── 知识库/wiki索引.md
├── 业务/
├── platform-ops/
│   ├── 仪表盘.md            # 工作仪表盘
│   ├── log.md               # 操作日志
│   └── topics/              # 工作主题
└── .claude/                 # → jarvis/skills + jarvis/hooks
```

### 升级

```bash
# editable install 直接 git pull 即可
cd ~/path/to/jarvis
git pull

# 不需要重跑 pipx install 或 jarvis init
# 软链接 + editable install 会跟随源码自动更新
```

### 安装检查

```bash
jarvis doctor ~/my-project
# 16 项检查：
#   [OK] jarvis.yaml
#   [OK] CLAUDE.md
#   [OK] core/JARVIS_CORE_BRIEF.md
#   [OK] .claude/skills/ (16 skills)
#   [OK] .claude/hooks/ (3 hooks)
#   [OK] .claude/settings.json
#   [OK] wiki索引 / 术语索引 / 仪表盘 / 操作日志 / Topic目录
#   All checks passed.
```

---

## 内置能力

### Core 行为规程（双层结构）

- **Brief 版（88 行）**：路由表 + 铁律 + 检索纪律 + 输出声明块。Agent 每次会话必读
- **Full 版（575 行）**：完整参考。会话模式详解、协作原则、分析/设计路径、回退原则、插件系统。按需查阅

### Skill Pack（16 个）

Topic 创建/冻结/恢复/关闭、知识萃取/入库/反馈、碎片分流、跟进同步、分析线程管理、文件处理、Confluence 读取、状态查询、**知识库模型**（术语分类/生命周期/入账规则/目录规格）

### 知识检索体系

- **四层递进检索**：L1 索引 → L2 深读 → L3 限定 grep → L4 兜底（OpenViking + 全项目 grep）
- **三入口职责分离**：wiki索引（知识）、术语索引（domain浏览）、仪表盘（进度）
- **输出声明块**：回复前标注 [引用] 已确认/待确认 + [推论] 推断依据 + [方案] 前提假设
- **检索降级反馈**：每次降级记录索引缺口 → 近况查询时提醒维护

### 索引维护闭环

- wiki索引 + 术语索引 双索引体系
- 8 个文件夹完整目录规格（存什么/谁创建/谁消费/怎么维护）
- 会话审计：近况查询时附带合规自检
- 定期对照（7 天）+ 事件驱动（Topic关闭/萃取时补索引）

### Hooks 引擎（3 个）

| Hook | 时机 | 作用 |
|---|---|---|
| SessionStart | 会话启动 | 注入 Core + 插件 + 路径映射 |
| PreToolUse | 写/编辑/Bash | 阻止 Core 修改 + 知识入库确认提醒 |
| PreCompact | 压缩前 | 提示保存 Topic 状态 |

### 知识库模型（L1-L4/F）

L1 术语与概念 → L2 关系与规则 → L3 判断与决策 → L4 待验证问题 → F 文件处理产物。结构化、可检索、可复用。

### 记忆后端

| 后端 | 说明 |
|---|---|
| file（默认） | grep + 文件系统，零依赖 |
| openviking | 语义向量搜索，需 openviking-server |

### 配置化

所有路径通过 `jarvis.yaml` 配置，脚本读配置不读硬编码。无配置时 fallback 默认值。

---

## 架构

```
每次会话启动
    │
    ├─ 1. SessionStart hook 读 core/JARVIS_CORE_BRIEF.md（88行精简版）
    ├─ 2. 读项目 jarvis.yaml → 激活的插件列表
    ├─ 3. 替换 {{PLUGIN:SAFETY}} {{PLUGIN:VALIDATION}} {{PLUGIN:CHECKLIST}}
    ├─ 4. 删除未匹配占位符（无插件时框架正常运行）
    ├─ 5. 注入 [Jarvis Path Config] 路径映射
    │
    ▼
LLM 获得完整行为基线 + 领域规则 + 路径映射 → 开始工作
```

---

## 边界与反制

Jarvis 内置了"抗退化"机制——预置了 LLM 最常见的合理化借口和反制策略：

| LLM 会说 | Jarvis 的反制 |
|---|---|
| "上次我们讨论了…" | 从 Topic 快照或 JSONL 确认，不凭记忆 |
| "这个写入是记录性的" | 对写入裁决表判断 |
| "先假设…" | 用工具验证，找到证据再下结论 |
| "已经读过了" | 文件可能已被修改，重新读 |
| "OpenViking 说…" | 搜索结果是线索，必须回源文件确认 |
| "这个应该没问题" | 写权限、安全边界没有"应该" |

---

## 与同类项目的区别

Jarvis 不和其他 LLM 工具竞争"模型调用""工作流编排""提示词管理"。它的定位是**行为规程层**——在 LLM 的 context 顶部注入一套让它学会协作的规则系统。

| 对比维度 | 典型 Agent 框架 | Jarvis |
|---|---|---|
| 关注点 | 怎么调用模型、怎么串联工具 | LLM 怎么思考、怎么判断、怎么自律 |
| 核心机制 | tool calling + workflow | SessionStart 注入行为规程 |
| 状态管理 | 外部数据库或向量存储 | 文件系统 + git（Topic 四件套） |
| 插件模型 | 代码级别的 function/tool | 提示词模块（`{{PLUGIN:NAME}}`） |
| 安全模型 | API key 权限 | 三级写入裁决 + hook 门禁 |
| 知识管理 | RAG pipeline | L1-L4/F 分层 + 证据归属标注 |

---

## License

MIT
