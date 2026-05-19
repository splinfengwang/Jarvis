# 项目默认智能体入口

本项目主规程为 `智能体/贾维斯/runtime-v0.1/JARVIS_CORE.md`（v0.2）。

## 启动规则

1. 会话启动时，Core 通过 SessionStart hook 自动注入上下文（`.claude/hooks/jarvis-core-inject.sh`）。
2. Hook 不可用时，手动读取 `智能体/贾维斯/runtime-v0.1/JARVIS_BOOTSTRAP.md` 并遵循。
3. Jarvis Runtime v0.1 的 skill（`.claude/skills/jarvis-*`）、scripts、references 构成完整的可执行工作流。
4. `智能体/贾维斯/AGENT.md`（v3.4）作为 fallback/reference 保留。
5. 只有 runtime 失败、规则缺口影响执行，或林峰明确要求时，才回退到 `智能体/贾维斯/AGENT.md`。
6. 回退时必须说明触发原因，并记录到当前 Topic 或讨论记录。

## 默认边界

- 不自动修改 `AGENT.md`（PreToolUse hook 强制阻止）。
- 不自动知识入库（医学/安全类保持强制确认）。
- 不把 OpenViking 命中当事实。
- 写入动作按 Core §10 写入裁决 + `references/write-permission.md` 执行。

## Hooks 机制

- `SessionStart`：自动注入 Core 行为基线（`jarvis-core-inject.sh`）
- `PreToolUse`：写权限门禁 — 阻止 AGENT.md 修改 + 内容性写入提醒（`jarvis-write-guard.sh`）
- `PreCompact`：上下文压缩前保存 Topic 状态（`jarvis-compact-save.sh`）

## Runtime v0.2 状态

Phase 1-4 已执行完毕（Core 重写 401 行 覆盖率 100%、知识入库 L1-L4/F、能力缺口补齐、hooks 引擎上线）。Gate 5 真实任务验证待执行。