# Knowledge Base Structure

## 目的

定义 Jarvis 项目的标准目录树。所有脚本和 skill 通过 `jarvis.yaml` 中的 paths 配置查找文件，不依赖硬编码路径。

## 标准目录树

`jarvis init` 创建的默认结构：

```
<项目根目录>/
├── jarvis.yaml                # Jarvis 项目配置（必须）
├── CLAUDE.md                  # 项目入口（引用 jarvis 框架）
│
├── 知识库/
│   ├── wiki索引.md            # 全 wiki 扁平导航（术语 + 分析文档 + 决策记录）
│   └── 术语/
│       ├── 术语索引.md         # 按 domain 分组的术语导航
│       └── *.md               # 每个术语一条独立笔记
│
├── 业务/                      # 分析文档按业务域组织
│   └── <域>/
│       ├── 索引.md
│       └── *.md
│
├── platform-ops/
│   ├── 仪表盘.md              # 工作仪表盘（会话启动入口）
│   ├── log.md                 # append-only 操作日志
│   └── topics/
│       └── <YYYYMMDD_主题简称>/
│           ├── 索引.md
│           ├── _上下文快照.md
│           ├── _准入检查单.md
│           └── 讨论记录.md
│
└── .claude/
    ├── skills/                # → 软链接到 jarvis/skills/
    └── hooks/                 # → 软链接到 jarvis/hooks/
```

## jarvis.yaml paths 配置

```yaml
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
```

## 使用规则

1. 脚本通过 `jarvis/lib.py` 的 `get_path(key)` 函数获取路径，不硬编码
2. Skill 的 SKILL.md 中引用路径使用概念名（"仪表盘""wiki索引"），由框架解析
3. 用户可通过修改 `jarvis.yaml` 自定义路径（如将 `知识库` 改为 `docs/kb`）
4. `jarvis init` 使用默认中文路径，`jarvis doctor` 验证路径存在

## 最小要求

以下结构是 scripts 和 skills 正常工作的必要条件：

- `jarvis.yaml` 存在且 paths 段完整
- 知识库目录 + wiki索引 + 术语索引 存在
- platform-ops 目录 + 仪表盘 + log + topics 目录存在
- .claude/skills 和 .claude/hooks 软链接已建立

`jarvis doctor` 检查这些条件。
