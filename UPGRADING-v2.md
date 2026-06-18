# Jarvis v2.0 迁移指南

## 概述

v2.0 将 Jarvis 从仅支持 Claude Code 扩展为支持三个平台：**Claude Code**、**Reasonix**、**Codex (OpenAI)**。

核心变化：
- 419 行 inline Python 从 `core-inject.sh` 拆分为独立的 `plugin_resolver.py` + `snapshot.py`
- Hook 脚本从 `jarvis/hooks/` 迁移到 `adapters/claude/hooks/`（旧位置保留软链）
- 安装逻辑从单平台改为多平台选择，其中 Reasonix / Codex 不再伪造 Claude hooks

## 对老用户的影响

### 🟢 不需要迁移（向后兼容）

- 已有的 `~/.claude/settings.json` **不受影响**——`postinstall.js` 检测到已有 Jarvis hook 配置会跳过
- 已有的 `~/.claude/skills/` 软链**仍然有效**
- `jarvis/hooks/jarvis-core-inject.sh` **路径仍可访问**（软链）
- `npm update -g jarvis-agent` 会**自动适配**新结构

### ⚠️ 可选的优化步骤

如果希望享受新架构的好处，可以重新安装：

```bash
# 重新安装到 Claude Code（合并新配置）
jarvis install --target claude

# 或通过 npm 升级后自动运行
npm update -g jarvis-agent
```

### 🔄 如果要迁移到 Reasonix 或 Codex

```bash
# 安装到 Reasonix
jarvis install --target reasonix

# 安装到 Codex
jarvis install --target codex
# 然后重启 Codex 以加载新 skill
```

注意：

- Reasonix 走 `~/.reasonix/config.toml` 的 `system_prompt_file` + `skills.paths`
- 项目内再生成 `REASONIX.md` + `reasonix.toml`，避免本地配置覆盖全局 bridge
- Codex 走 `~/.codex/skills/` + 项目 `AGENTS.md`
- 只有 Claude Code 继续使用 SessionStart / PreToolUse / PreCompact hooks

## 目录结构变化

```
v1.x                        v2.0
────                        ────
jarvis/hooks/               jarvis/hooks/ → adapters/claude/hooks/ (symlink)
                            adapters/
                              claude/hooks/    # 实体文件
                              reasonix/hooks/  # 兼容保留，不再作为主接入点
                              codex/hooks/     # 兼容保留，不再作为主接入点
                              claude/install.sh
                              reasonix/install.sh
                              codex/install.sh
jarvis/core/                jarvis/core/ + plugin_resolver.py + snapshot.py
```

## 常见问题

**Q: 升级后 hook 不生效了？**
A: 检查软链：`ls -la ~/.claude/hooks/jarvis-core-inject.sh`，应指向 `adapters/claude/hooks/core-inject.sh`。

**Q: 如何确认安装完整性？**
A: 运行 `jarvis doctor`，应该显示 "all 16 checks passed"。

**Q: 自定义的 settings.json 会被覆盖吗？**
A: 不会。安装器使用合并策略，已有配置保持不变，只追加缺失的 hook 事件。

**Q: Reasonix 里能看到 skill，但为什么之前不像 Jarvis？**
A: 因为 skill 发现和协议启动不是一回事。v2 现在改为 Reasonix 原生的 `system_prompt_file` + `skills.paths`，不再依赖无效的 `settings.json hooks`。
