# Changelog

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
