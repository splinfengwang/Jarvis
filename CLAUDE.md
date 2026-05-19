# Jarvis

> An LLM-native agent framework for long-term work assistance.
> Version: 1.0.0

## 项目说明

Jarvis 是一个可复用的 LLM 智能体框架，提供：

- **Core 行为规程**：身份定义、裁决优先级、铁律、写入裁决、会话路由
- **Skill Pack**：13 个标准化工作流 skill（Topic 管理、知识萃取、碎片分流等）
- **Hooks 引擎**：SessionStart / PreToolUse / PreCompact 三个 hook
- **知识库模型**：L1-L4/F 知识分层 + wiki 索引 + 术语管理
- **领域插件**：可插拔的领域安全规则、校验清单、知识分类
- **记忆后端**：默认文件系统 + 可选语义搜索（OpenViking）

## 目录结构

```
jarvis/
├── CLAUDE.md
├── package.json
├── setup.py
├── install.sh              # 一键安装到目标项目
├── core/                   # 核心行为规程
│   ├── JARVIS_CORE.md
│   └── JARVIS_BOOTSTRAP.md
├── references/             # 14 个参考规范
├── skills/                 # 13 个标准 skill
├── scripts/                # 17 个运维脚本
├── hooks/                  # 3 个 hook 脚本
├── tests/                  # 测试与验收
├── research-cards/         # 外部借鉴研究
├── plugins/                # 领域插件（medical 等）
├── backends/               # 记忆后端适配器
│   ├── file/
│   └── openviking/
└── templates/              # 项目模板
```

## 安装

```bash
# 安装到目标项目
bash /path/to/jarvis/install.sh /path/to/target-project

# 或开发模式
cd target-project
ln -s /path/to/jarvis/skills/* .claude/skills/
ln -s /path/to/jarvis/hooks/*.sh .claude/hooks/
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
# 开发安装（软链接模式）
cd /path/to/test-project
bash /path/to/jarvis/install.sh .

# 验证
jarvis doctor
```

## License

MIT
