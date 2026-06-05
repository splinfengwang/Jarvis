---
name: jarvis-init
description: 在 Claude Code 会话中初始化 Jarvis 行为框架。引导式对话：探测项目类型 → 角色协商 → 执行安装 → 验证 → Onboarding。用于"初始化 Jarvis""在这个项目装 Jarvis""帮我配置 Jarvis"。
next_skills: []
---

# jarvis-init

## 输入

- 当前项目根目录
- `jarvis.yaml`（如果存在）
- `CLAUDE.md`（如果存在）
- 项目结构（`.obsidian/`、`package.json`、`.git/` 等标志文件）
- `jarvis` CLI 是否在 PATH 中

## 输出

- 阶段 1-5 的完整引导对话
- 初始化完成后的目录结构
- `jarvis doctor` 验证结果
- onboarding 建议（根据项目类型）

## allowed_scripts

- `jarvis init` — CLI 安装命令（Bash 调用）
- `jarvis doctor` — CLI 检查命令（Bash 调用）

## required_references

- `jarvis/references/write-permission.md` — 写入裁决规则

## on_demand_references

- `jarvis/references/knowledge-base-structure.md` — 目录树规范（按需）

## write_level

- 创建目录/软链接/生成模板 → `record_write`（可自主执行）
- 修改已有 CLAUDE.md → `content_write`（需先展示引用内容并确认）
- 替换已有 CLAUDE.md → `content_write`（需确认 + 备份旧文件）

## 引导流程（5 阶段）

### 阶段 1：项目探测

**必须**先完成探测再执行任何操作。

1.1 检查 `jarvis.yaml` 是否存在：
  - 存在 → 读取版本号，报告"Jarvis 已安装 (vX.X)，要重新初始化吗？"
  - 用户确认"是"才继续，否则停止

1.2 扫描项目类型标志：
  - `.obsidian/` 存在 → Obsidian 知识库
  - `package.json` / `pyproject.toml` 存在 → 代码项目
  - `CLAUDE.md` 存在 → 已有 Claude Code 配置
  - 以上都无 → 新项目

1.3 向用户汇报探测结果，一次性说清楚：
  - 项目类型
  - 已有配置（CLAUDE.md、jarvis.yaml）
  - Jarvis 将添加什么（不替换什么）

**必须**等待用户确认后再进入阶段 2。

### 阶段 2：角色协商

**这是整个流程的核心差异点**——CLI 版的 `input()` 做不到的事。

如果 CLAUDE.md 存在：
  2.1 读取 CLAUDE.md，搜索角色/身份相关关键词（"你是""身份""角色""SYSTEM_BOOT""agent""协议"）
  2.2 提取 1-3 行角色摘要
  2.3 向用户汇报，格式如下：

  > 我读到 CLAUDE.md 里你的角色是 **[角色摘要]**。
  > 启动协议是 **[协议摘要]**。
  >
  > **Jarvis 不会改变这些。** 它只是在你的角色定义之下，
  > 提供一套行为约束：
  > - 三条铁律（文件优先读取、事实优先确证、写入优先确认）
  > - 三级写入裁决（记录/内容/高风险）
  > - Topic 跨会话状态管理
  > - 知识库 L1-L4/F 分层归档
  >
  > 我会在 CLAUDE.md 末尾追加一段声明，不影响原有内容。

  2.4 提出选项（自然语言表达，不是 A/S/R）：
  - 默认：追加引用到末尾
  - 可选：只安装框架不修改 CLAUDE.md
  - 可选：替换整个 CLAUDE.md（会先备份为 `.bak`）
  - 可选：把引用放在开头

  2.5 如果 CLAUDE.md 已有 Jarvis 引用 → 检测到并告知"已有引用，跳过"

如果 CLAUDE.md 不存在：
  - 告知用户"生成了一个基础 CLAUDE.md 模板，你可以在里面定义项目的角色和启动协议"

### 阶段 3：执行初始化

**先确认后执行。** 确认后下列步骤可**连续执行**，不需要逐步确认。

3.1 运行 `jarvis init <项目路径>`（使用 `--claude-mode` 传递阶段 2 的选择）：
  - `--claude-mode a` → 追加引用（默认）
  - `--claude-mode s` → 跳过
  - `--claude-mode r` → 替换+备份
  - CLI 处理目录创建、软链接、模板生成、jarvis.yaml 写入

3.2 如果 CLI 对 CLAUDE.md 追加了引用（阶段 2 默认选择），读回 CLAUDE.md 验证引用块已正确追加

3.3 简要汇报每步结果

### 阶段 4：验证

4.1 运行 `jarvis doctor <项目路径>`
4.2 解读结果：
  - 全通过 → "✅ 全部检查通过"
  - 有 warning → 逐一解释含义，区分"需要处理"vs"可以忽略"
  - 有 error → 定位原因，给出明确的修复步骤

### 阶段 5：Onboarding

5.1 告知核心信息：
  > **下次启动 Claude Code 时**，SessionStart hook 会自动注入 Core。
  > 你会在会话开头看到 `[Jarvis Path Config]` 路径映射表，
  > 这说明 Jarvis 已生效。

5.2 根据项目类型给出建议：

  **Obsidian 知识库**：
  > Jarvis 的 Topic 管理系统可以和你的 Obsidian 仪表盘配合。
  > 试试说"开一个 Topic：XXX"来开始一个新工作主题，
  > 或者"最近怎么样"来查看状态。

  **代码项目**：
  > 写代码时 Jarvis 会约束写入行为——先提案、确认后再改。
  > 你可以说"开一个 Topic"来追踪跨会话的开发工作。

  **新项目**：
  > 现在可以开始工作了。试试说"最近怎么样"看看仪表盘。

5.3 告知最常用的 3 个触发词：
  - "开一个 Topic：XXX" → 创建新工作主题
  - "最近怎么样" → 查看仪表盘状态
  - "继续上次" → 恢复暂停的 Topic

## 确认规则
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 阶段 3-4-5 可在阶段 2 确认后连续执行

## Fallback 规则
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- `jarvis` CLI 不在 PATH 中 → 检查 `pipx list` 或 `~/.local/bin/jarvis`，给出安装指导
- `jarvis init` 失败 → 读取错误输出，判断原因（权限/路径/Symlink），给出修复步骤
- 项目目录不可写 → 报告权限问题，停止
- `jarvis doctor` 有 error → 逐个分析原因，不直接重试已失败的操作

