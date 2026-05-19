# Session Locating

## 目的

知识萃取需要读取原始会话记录，而不是依赖压缩后的上下文记忆。

## 会话路径

| 工具 | 会话目录 | 文件格式 | 定位方式 |
|---|---|---|---|
| Claude Code | `~/.claude/projects/<cwd-encoded>/` | `<session-uuid>.jsonl` | 列出 `.jsonl`，按修改时间倒序定位 |
| Codex Desktop | `~/.codex/sessions/YYYY/MM/DD/` | `rollout-*.jsonl` | 优先用 `~/.codex/session_index.jsonl` 按 thread id 定位日期，再结合日期目录和修改时间确认 |

`<cwd-encoded>` = 当前工作目录中非字母数字字符替换为 `-`。

## 关联会话表

```markdown
| 工具 | 会话标识 | JSONL 路径 | 工作区路径 | 日期 |
|---|---|---|---|---|
| Codex Desktop | <thread_id> | ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl | <cwd> | YYYY-MM-DD |
```

会话标识只是定位线索；JSONL 路径才是可复核的原始记录入口。

## 定位规则

1. 快照中有 JSONL 路径，优先使用该路径。
2. 只有会话标识，按工具映射查找。
3. 找不到精确文件，按日期、修改时间、工作区路径列候选，并标注需确认。
4. 文件缺失或不可读，标注 `会话文件缺失`，不得把“用户原话”作为强证据。

## 生命周期写入规则

Topic 创建、冻结、关闭都必须把当前会话写入 `_上下文快照.md` 的关联会话表。

| 情况 | 写入方式 |
|---|---|
| 已定位 JSONL | 写入真实 JSONL 路径 |
| 只知道工具或会话标识 | JSONL 路径写 `待确认`，保留工具、会话标识、工作区路径、日期 |
| 完全无法定位 | 工具和会话标识写 `待确认`，工作区路径和日期仍必须写 |
| 行已存在 | 不重复追加 |

这一步不是知识萃取的一部分，而是 Topic 可恢复性的基础记录。

## 读取规则

1. 先用 Topic 快照确定时间段、关键词、决策点。
2. 再在 JSONL 中定位相关轮次。
3. 只提取与萃取目标相关的消息。
4. 关键判断保留 source_messages 或片段定位。
5. JSONL 是证据层，不是知识层；入库仍必须经过确认流程。
