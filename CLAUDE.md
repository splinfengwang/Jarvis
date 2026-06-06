# Jarvis

> An LLM-native agent framework for long-term work assistance.

## 项目说明

Jarvis 是一个可复用的 LLM 智能体框架，提供：

- **Core 行为规程**：身份定义、裁决优先级、铁律、写入裁决、会话路由
- **Skill Pack**：19 个标准化工作流 skill（Topic 管理、知识萃取、碎片分流等）
- **Hooks 引擎**：SessionStart / PreToolUse / PreCompact 三个 hook
- **知识库模型**：L1-L4/F 知识分层 + wiki 索引 + 术语管理
- **领域插件**：可插拔的领域安全规则、校验清单、知识分类
- **记忆后端**：默认文件系统 + 可选语义搜索（OpenViking）

## 目录结构

```
jarvis/
├── jarvis/
│   ├── core/          # 核心行为规程
│   ├── skills/        # 19 个标准 skill
│   ├── hooks/         # 3 个 hook 脚本
│   ├── scripts/       # 17 个运维脚本
│   ├── references/    # 14 个参考规范
│   ├── templates/     # 项目模板
│   ├── personas/      # 审查角色
│   ├── plugins/       # 领域插件（medical 等）
│   ├── backends/      # 记忆后端适配器
│   └── research-cards/ # 外部借鉴研究
├── package.json        # npm 包配置
├── setup.py            # Python 包配置
├── postinstall.js      # npm 全局安装后自动注册 skill/hook
└── .claude-plugin/     # Claude Code plugin 清单
```

## 安装

```bash
# 方式 1: npm（推荐）
npm install -g jarvis-agent

# 方式 2: pip（备选）
pip install -e .

# 初始化项目
jarvis init /path/to/project
```

## 插件系统

领域插件放在 `plugins/{name}/`：

```
plugins/medical/
├── plugin.yaml       # name, version, description, provides
├── safety.md         # 安全规则
├── validation.md     # 校验清单
└── taxonomy.md       # 知识分类维度
```

Core 中的 `{{PLUGIN:XXX}}` 占位符在加载时由对应插件模块替换。

## 开发

```bash
# 开发安装
cd /path/to/jarvis
pip install -e .
jarvis init /path/to/test-project

# 验证
jarvis doctor
```

## License

MIT
