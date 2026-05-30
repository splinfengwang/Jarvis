<p align="center">
  <h1 align="center">Jarvis</h1>
  <p align="center"><strong>把聊天变成第二大脑。</strong></p>
  <p align="center">
    <a href="#安装"><img src="https://img.shields.io/badge/python-%E2%89%A53.10-blue" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  </p>
</p>

---

## 一句话定位

LLM 聊天的问题不是聊得不好——是聊完就没了。

昨天的决策、上周的分析、上个月确认过的参数——每一次新会话都是从零开始。你的 LLM 像个失忆的专家：聪明，但不可靠。

Jarvis 改变这件事。**每次对话结束后，术语被自动提取、判断被结构化、文档被索引。下一次讨论，agent 不是从头搜索，而是从你已经确认的知识库里精准定位。**

这不是"更好的聊天"。这是**知识复利**——你投入的每一次讨论，都在建设一个越来越聪明的第二大脑。



---

## 它怎么工作

### 会话开始：双层行为规程自动注入

每次你打开 Claude Code，Jarvis 的 SessionStart hook 把一份 88 行的行为规程注入到 agent 的上下文里。里面只有最必要的东西：

- **路由表**：你说"继续上次"，agent 知道去恢复 Topic；你说"萃取一下"，agent 知道走知识萃取流程
- **铁律**：文件读取优先于记忆、事实确证优先于推论、写入确认优先于自动执行
- **检索纪律**：查知识先走 wiki索引，不 grep 全项目；查进度先看仪表盘
- **输出纪律**：回复前标注哪些是文件原文，哪些是推断

规则不在 prompt 里——在 hook 里。agent 绕不过去。

### 讨论中：Topic 管理 + 知识分层

每个工作主题是一个 Topic。里面有讨论记录、上下文快照、产出文件。

讨论中提到的知识按五层沉淀：

| 层次 | 是什么 | 例 |
|---|---|---|
| L1 术语 | 一个概念的定义 | FeCO₂ 是什么 |
| L2 关系 | 概念之间怎么协作 | FeCO₂ 用于评定，EtCO₂ 只用于过程控制 |
| L3 判断 | 为什么这样选 | 氧疗 PPT 只讲氧疗，不讲无创通气——受众是基层医生 |
| L4 待验证 | 尚未有答案的问题 | 锚定差值在长期治疗中是否稳定？ |
| F 文件产物 | 对 PDF/PPT 的结构化提炼 | 产品能力清单、模块表 |

### 讨论后：萃取 → 入库 → 索引

Topic 关闭时，agent 不是把聊天记录存起来——而是：

1. 从讨论记录中抽取证据块（你说的、你确认的、你纠正的、文件里的）
2. 生成候选知识（术语/关系/判断/待验证）
3. 对照已有知识查重复/冲突
4. 分级确认（A 组可快速确认、B 组需拍板、C 组需验证）
5. 入库到 wiki索引 + 术语索引

### 下一次：检索纪律保证精准命中

一个月后你打开新会话问"之前讨论过的 FeCO₂ 怎么用"，agent 的行为是：

```
① 走 wiki索引 → 命中 FeCO₂（已确认）→ 读术语文件
② 术语文件 related 字段指向分析文档 → 深读
③ 回答引用 [引用] 已确认: [[术语/FeCO₂]] [[氧疗-临床流程]]
④ 不会 ls、不会 grep 全项目、不会 spawn 子 agent
```

而不是像普通的 LLM 那样全文搜索"FeCO₂"然后自己编一个定义。

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

## 内置能力速览

| 能力 | 说明 |
|---|---|
| **双层 Core** | Brief 版 88 行（Agent 每次必读）+ Full 版 575 行（按需查阅） |
| **16 个 Skill** | Topic 生命周期、知识萃取/入库/反馈、碎片分流、跟进同步、文件处理、Confluence 读取、知识库模型 |
| **3 个 Hook** | SessionStart（注入规程）、PreToolUse（写守卫）、PreCompact（状态保存） |
| **wiki索引 + 术语索引** | 知识库双索引体系。Agent 查知识先走索引，不走全文 grep |
| **L1-L4/F 五层知识** | 术语 → 关系 → 判断 → 待验证 → 文件产物。层层可检索 |
| **四层递进检索** | 索引 → 深读 → 限定 grep → 兜底。跳层必须声明原因 |
| **输出声明块** | 回复前标注：哪些是文件原文、哪些是推断、哪些是方案前提 |
| **会话审计** | 近况查询时附带合规自检 |
| **文件 + OpenViking 双后端** | 文件模式零依赖永在线，OpenViking 语义搜索按需启用 |

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

## 对比

别的工具解决"怎么调用模型"。Jarvis 解决"怎么让模型不退化"。

| | 典型 Agent 框架 | Jarvis |
|---|---|---|
| 知识从哪来 | RAG 灌进去的 | 从你的聊天里一步步萃取出来的 |
| 知识怎么存 | 向量数据库（黑盒） | 文件系统 + git（可读、可 diff、可回滚） |
| Agent 能找到什么 | 语义相似度排序的结果 | wiki索引 → 你确认过的定义 → 当时的决策理由 |
| 写文件安全吗 | 允许/禁止二元开关 | 三级裁决 + hook 门禁 + 写前自问 |
| 会话之间有记忆吗 | 没有 | Topic 快照 + 仪表盘 → 跨会话无缝接续 |
| LLM 会编造吗 | 管不了 | 输出声明块：推论不标注 = 禁止输出

---

## License

MIT
