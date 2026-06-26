# Changelog

## v2.0.1 (2026-06-26)

### 协议优化
- **讨论记录产物回链**：`讨论记录.md` 新增“产物生成事件”规范，显式记录“讨论/决策 → 过程稿/定稿”的映射，提升 Topic 恢复和上下文追溯能力
- **职责边界收紧**：明确 `讨论记录.md` 记录关系和状态，不复制产物正文，避免 Topic 过程记录与正式产物双写漂移
- **知识萃取对齐**：`jarvis-knowledge-extract` 优先读取产物生成事件建立证据链，目录扫描退为补漏逻辑

### 文档同步
- `topic-lifecycle.md`、`knowledge-model.md`、`jarvis-knowledge-extract/SKILL.md` 三处规则同步更新，统一“讨论记录存关系，产物文件存正文”的约束

## v2.0.0 (2026-06-18)

### 三平台适配（Claude Code / Reasonix / Codex）
- **适配器架构**: 新增 `adapters/` 目录，将平台相关代码从核心逻辑中分离
  - `adapters/claude/` — Claude Code 适配器（含 hooks 和 install.sh）
  - `adapters/reasonix/` — Reasonix 适配器（原生 `reasonix.toml` / prompt / skills 配置）
  - `adapters/codex/` — Codex 适配器（`~/.codex/skills/` + `AGENTS.md` bootstrap）
- **核心提取**: `jarvis-core-inject.sh` 从 519 行缩减至 123 行，inline Python 拆为独立模块
  - `jarvis/core/plugin_resolver.py` — YAML 解析 + 插件注入 + 路径配置（平台无关）
  - `jarvis/core/snapshot.py` — 知识快照生成：术语/wiki/仪表盘/Topic 扫描（平台无关）
- **安装生命周期多平台化**
  - `jarvis install --target {claude|reasonix|codex|all}` — 安装到指定平台
  - `jarvis install --dry-run` — 预览安装操作
  - `postinstall.js` 基于安装目录自动检测平台（`JARVIS_TARGET` 环境变量覆盖）
- **Skill 元数据**: 19 个 skill 新增 `agents/openai.yaml`（Codex UI 兼容，含中文显示名）
- **项目配置**: `jarvis.yaml` 新增 `platform` 字段，`jarvis init` 自动检测平台并补 `AGENTS.md`
- **向后兼容**: `jarvis/hooks/` 保留软链指向 `adapters/claude/hooks/`，现有安装不断

## v1.10.0 (2026-06-06)

### 工程化
- **版本号 SSOT**: `package.json` 为版本号单一真相源，`npm run prepack` 自动注入到 `.md`/`.py`/`.json` 文件
- **废弃 install.sh**: 移除与 `jarvis init` 重复的 bash 初始化脚本，Python CLI 为唯一入口
- **jarvis init --sync**: 新增项目同步模式，升级后自动更新 `jarvis.yaml` 版本号 + 清理项目级 hook 配置
- **jarvis doctor 增强**: 新增版本不匹配检测和 hook 残留检测
- **npm 离线安装**: 支持 `npm install -g ./jarvis-agent-x.y.z.tgz`，`postinstall.js` 自动全局注册 skill/hook
- **postinstall.js 去重**: 重复安装自动跳过 hook 配置写入

## v1.9.0 (2026-06-05)

### 新增
- **Persona + Roundtable 多角色审查系统**: 5 个内置审查角色（设计评审员、边缘案例猎手、医学安全审查员、需求分析员、技术/架构评审员）+ 并行审查 + 汇总
- **Catalog 写入守卫**: hook 强制拦截非 catalog 目录的写入操作
- **11 个 Skill 增加 confirmation_rules gate**

### 改进
- **Skill 规范优化**: 去冗余、description 触发匹配、CORE 承重

## v1.8.0 (2026-06-03)

### 新增
- **知识萃取三步优化**: 快照时效检查 + 自动关联 + 交叉验证
- **对照已有知识 6 种结果**: 互补 + 应关联双写
- **萃取第 2 步新增外部来源结构化整理前置步骤**
- **补齐检查重构**: 从独立表格改为内联到确认清单

### 修复
- **会话定位三层兜底**: ID 匹配 → 内容搜索 → 待确认
- **JSONL 定位修复**: session-id 精确匹配 + 模糊匹配容错 + locate_session_jsonl 三个修复
- **Topic 生命周期修复**: freeze/close/resume 全部补齐会话关联记录 + git commit 时序修正
- **SessionStart hook**: ls -t 主路径，环境变量降为兜底

## v1.7.0 (2026-05-26)

### 重构
- **Core 拆分为 brief/full**: brief 版 ~60 行（路由+铁律+检索+输出），agent 每次必读；full 版 575 行（完整参考），按需查阅。hook 注入 brief 版
- **E 组拆分为 E+G**: E 组只管 F 层文件处理产物。新增 G 组管理 Topic 完整文档独立存放（3 步：复制→更新 wiki索引→原文件改名 _archived）

### 新增
- **jarvis-status 会话审计**: 回答近况时附加三项自检（wiki索引合规/声明块格式/子Agent委托）
- **目录规格表**: knowledge-model skill 新增 8 个文件夹的完整职责定义

### 修复
- 写守卫 + bash 加固
- 脚本 sys.path 批量修复（17 个脚本可独立运行）
- 旧模块名 `jarvis_lib` → `jarvis.lib`
- Core 路由表兜底行增加任务性质判断

## v1.6.0 (2026-05-26)

### 新增
- **jarvis-knowledge-model skill**: 从 AGENT_v3.4 §3 提取完整知识模型（L1-L4/F、ABC 分类、术语生命周期、入账规则）
- **双重治理解决**: AGENT_v3.4 降级为历史参考，Bootstrap/Core 明确 Core + Skills 为主规程

### 修复
- **写守卫扩展**: 保护范围扩展到全部框架关键文件 + bash 危险命令检测加固
- **hook 超时**: SessionStart/PreToolUse/PreCompact 从 5s 提升到 15s
- **compact 校验**: head -3 改为全文件 grep 三标记验证
- **Linux trash**: 新增 gio trash + XDG Trash 回退
- **CLI 版本**: 从 jarvis/__init__.py 动态读取，不再硬编码

## v1.5.0 (2026-05-23)

### 重构
- **Core 重组为三层决策树**: §0 入口路由表（15 个 skill 触发词映射）、§§1-7 行动约束层、§§8-14 深度上下文层。路由决策从 400 行后提前到前 60 行
- **References 降级**: 所有 skill 的 required_references 从 2-3 个降至 ≤1 个，超出移入 on_demand_references
- **路径漂移修复**: 15 个 SKILL.md 中 `智能体/贾维斯/runtime-v0.1/` → `jarvis/`

### 新增
- **next_skills 字段**: 6 个 skill 定义显式过渡边，形成完整的工作流图
- **写操作关键规范**: Core §6 新增 5 条规范（禁止整页重写仪表盘、双链转义、批量先创建后关联等）
- **confuence_query.py**: 从 fixtures 恢复到 jarvis/scripts/

### 修复
- `install.sh` 日期变量 `date=$date` 自赋值 → `date=$(date +%Y-%m-%d)`
- 不存在的引用 `medical-and-design-safety.md` → `plugins/medical/safety.md`
- 版本号统一为 1.5.0（`__init__.py` 为单一真相源）

## v1.4.1 (2026-05-22)

### 改进
- **Wiki 索引结构化**: 快照不再 dump wikilink 行，改为按 section 解析（术语/分析文档/决策记录）+ 关键条目摘要
- **快照元数据**: 时间戳 + 可信度声明 + "新确认不受此限制"
- **Topic 状态分级**: [🟢 Doing] 详情 / [🟡 Paused ≤30d] 一行 / >30d 折叠 / 其他状态折叠
- **术语排序优化**: 活跃 Doing Topic 相关术语优先展示
- **检索跳过规则**: Core §6.3 新增"快照已有不需重复检索"
- **捕获噪音过滤**: Core §12.6 新增"UI 偏好/单次调整不算知识"
### 修复
- 快照可信度声明: 源文件修改时间晚于快照时以源文件为准
- 摘要提取规则: 精确定义跳过 frontmatter/空行/标题/引用/表格行

## v1.4.0 (2026-05-21)

### 新增
- **知识快照**: SessionStart hook 新增 [JARVIS_KNOWLEDGE_SNAPSHOT] 注入（术语+wiki索引+Topic+结论，≤2500字符）
- **检索前置规则**: Core §6.3 "被动降级"改为"主动检索"——讨论新概念前先 memsearch
- **知识捕获规则**: Core §12.6 升级——讨论中产出知识时主动提议入库，每轮最多2条
- **检索可信度调整**: Core §3 "检索是线索，已确认条目可直接推理"
### 改进
- 知识快照扫描4个数据源：术语文件、wiki索引、仪表盘、Topic快照
- 快照健壮性：任何扫描失败不阻止Core注入


## v1.2.1 (2026-05-20)

### 修复
- **bootstrap broken symlink 崩溃**：`Path.unlink(missing_ok=True)` + `is_symlink()` 检查
- **bootstrap 非 symlink 保护**：拒绝覆盖用户文件（`--force` 可强制）
- **upgrade 静默降级检测**：目标版本比当前旧时 warn + 需 `--force`
- **`--claude-mode`**：`jarvis init --claude-mode a|s|r`，agent 驱动的 init 不再被 `input()` 阻塞
- **`load_project_config` 异常不再静默**：写入 stderr
- **DRY**：`_get_latest_tag` / `_get_available_versions` 合并

## v1.2.0 (2026-05-20)

### 新增
- **jarvis bootstrap**：一次性全局安装 `/jarvis-init`，之后任何项目直接可用

## v1.1.0 (2026-05-20)

### 新增
- **版本化升级**：`jarvis upgrade` 基于 git tag 驱动，支持 `--check`（仅检查）和 `--tag vX.Y.Z`（指定版本）
- **生命周期管理**：`jarvis uninstall`（保留用户数据，`--purge` 强制清除）、`jarvis status`（插件/后端/路径状态）、`jarvis --version`（版本号 + 最新可用 tag）
- **jarvis-init skill**：在 Claude Code 会话内通过 5 阶段对话初始化 Jarvis（项目探测 → 角色协商 → 执行 → 验证 → Onboarding）
- **交互式 CLAUDE.md 处理**：`jarvis init` 检测到已有 CLAUDE.md 时预览内容、提供 A/S/R 选项（追加/跳过/替换+备份）
- **pipx 安装支持**：`pipx install -e .` 一行安装，`jarvis` 命令全局可用

### 变更
- **Core §1 收敛为行为框架**：不再定义"你是 Jarvis"，改为"你已启用 Jarvis 行为框架，角色由项目 CLAUDE.md 定义"

### 修复
- 插件名解析：`medical-safety`（manifest name）可正确映射到 `plugins/medical/`（目录名）
- KF580 hooks 替换为 jarvis v1.0 软链接，修复 split-brain 启动问题
- jarvis_home 从绝对路径改为 hook symlink 自解析

---

## v1.0.0 (2026-05-19)

### 初始发布
- Core v1.0（429 行行为规程）
- 13 个标准 skill（Topic 生命周期、知识萃取/入库/反馈、碎片分流、跟进同步、分析线程）
- 3 个 Hook（SessionStart + 插件注入 + 路径映射）
- 领域插件系统（medical-safety 5 模块）
- 记忆后端（file 默认 + openviking 可选）
- jarvis.yaml 配置化
- jarvis init / jarvis doctor CLI
- pip install -e . 支持
- Python package 结构
