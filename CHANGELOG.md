# Changelog

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
