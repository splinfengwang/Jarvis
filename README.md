# Jarvis

> LLM-native agent framework for long-term work assistance.
> An LLM 原生智能体框架，为长期工作助理场景设计。

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Jarvis 将 Claude Code 的 hooks、skills、行为规程打包为一个可安装、可配置、可扩展的框架。一次 `pip install`，一行 `jarvis init`，即可在任何项目中获得完整的智能体工作流。

---

## 快速开始

```bash
# 1. 安装
git clone https://github.com/splinfengwang/Jarvis.git
cd Jarvis
pip install -e .

# 2. 初始化项目
jarvis init ~/my-project

# 3. 检查安装
jarvis doctor ~/my-project

# 4. 启动 Claude Code → Core 自动注入
cd ~/my-project
claude
```

---

## 能力概览

| 模块 | 说明 |
|---|---|
| **Core 行为规程** | 身份定义、裁决优先级、三条铁律、写入裁决（记录/内容/高风险）、会话路由 |
| **Skill Pack（13个）** | Topic 生命周期（创建/冻结/恢复/关闭）、知识萃取/入库/反馈、碎片分流、跟进同步、分析线程、文件处理 |
| **Hooks 引擎** | SessionStart（Core 注入 + 插件注入 + 路径映射）、PreToolUse（写权限门禁）、PreCompact（状态保存） |
| **知识库模型** | L1 术语 / L2 关系与规则 / L3 判断与决策 / L4 待验证问题 / F 文件处理产物 |
| **领域插件** | 可插拔的安全规则、校验清单、知识分类维度（首个实例：medical-safety） |
| **记忆后端** | file（零依赖 grep 搜索）+ openviking（语义向量搜索） |
| **配置化** | jarvis.yaml — paths / plugins / backend 一站式配置 |
| **CLI 工具** | `jarvis init`（一键生成项目骨架）/ `jarvis doctor`（14 项完整性检查） |

---

## 架构

```
jarvis/                       # Python package
├── __init__.py
├── cli.py                    # jarvis 命令行入口
├── lib.py                    # 共享库（YAML parser、路径解析、写入裁决）
├── core/                     # JARVIS_CORE.md + JARVIS_BOOTSTRAP.md
├── references/               # 16 个参考规范
├── skills/                   # 13 个标准化 skill (jarvis-*)
├── scripts/                  # 19 个运维脚本
├── hooks/                    # 3 个 hook 脚本
├── plugins/
│   └── medical/              # 医学安全插件（5 模块）
├── backends/
│   ├── file/                 # 默认文件后端
│   └── openviking/           # OpenViking 语义搜索
└── templates/                # 项目模板（CLAUDE.md / 仪表盘 / wiki索引 / Topic骨架）
```

### 注入流程

```
Claude Code 启动
    │
    ▼
SessionStart hook (jarvis-core-inject.sh)
    │
    ├─ 1. 读取 jarvis/CORE.md
    ├─ 2. 读项目 jarvis.yaml → 激活的插件列表
    ├─ 3. 替换 {{PLUGIN:SAFETY}} {{PLUGIN:VALIDATION}} {{PLUGIN:CHECKLIST}}
    ├─ 4. 删除未匹配占位符
    ├─ 5. 注入 [Jarvis Path Config] 路径映射表
    │
    ▼
LLM 获得完整行为基线 + 领域规则 + 路径映射
```

### 知识库目录树

`jarvis init` 创建的标准项目结构：

```
<项目>/
├── jarvis.yaml               # 框架配置
├── CLAUDE.md                 # 项目入口
├── 知识库/
│   ├── wiki索引.md           # 全站导航
│   └── 术语/
│       └── 术语索引.md
├── 业务/                     # 分析文档按域组织
├── platform-ops/
│   ├── 仪表盘.md             # 工作仪表盘
│   ├── log.md                # 操作日志
│   └── topics/               # 工作主题
└── .claude/
    ├── skills/  → jarvis/skills/
    └── hooks/   → jarvis/hooks/
```

---

## 插件系统

领域特定的安全规则、校验清单、知识分类通过插件挂载。Core 中使用 `{{PLUGIN:NAME}}` 占位符，启动时自动注入。

### 内置插件：medical-safety

```yaml
# jarvis.yaml
plugins:
  - medical-safety
```

5 个模块：`safety`（医学决策边界 + 安全参数强制标注）、`validation`（三视角校验 + 知识引用规则）、`checklist`（方案提交检查清单）、`taxonomy`（术语分类维度）

### 自定义插件

```
plugins/<name>/
├── plugin.yaml       # name, version, description, provides
├── safety.md         # → {{PLUGIN:SAFETY}}
├── validation.md     # → {{PLUGIN:VALIDATION}}
└── checklist.md      # → {{PLUGIN:CHECKLIST}}
```

`plugin.yaml` 中 `provides` 的键名对应 Core 中的占位符。无插件时，占位符行被删除，框架正常运行。

---

## 配置参考

```yaml
# jarvis.yaml — 项目配置
jarvis_version: "1.0.0"
jarvis_home: "../../jarvis/jarvis"  # 指向 jarvis package 目录的相对路径

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

plugins:
  - medical-safety

backend: file  # file | openviking
```

---

## 命令

```bash
jarvis init [target]     # 初始化项目：目录树 + 软链接 + 模板 + jarvis.yaml
jarvis doctor [target]   # 14 项完整性检查
```

---

## 历史

Jarvis 起源于 KF580 精准氧疗平台项目，最初是嵌入在项目内的单一 `AGENT.md` 文件。经过 v3.0 重构、v3.4 规程迭代、Runtime 架构迭代、6 阶段产品化剥离，演进为当前 v1.0 独立框架。

- v0.1-v0.3：嵌入 KF580 项目的 Runtime
- v1.0：独立 Python package，pip 可安装

---

## License

MIT
