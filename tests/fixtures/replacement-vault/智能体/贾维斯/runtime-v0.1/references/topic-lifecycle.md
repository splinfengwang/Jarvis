# Topic Lifecycle

## 目的

Topic 是持续工作容器，不是所有问题都需要创建。Topic 规则负责让跨会话工作可恢复、可关闭、可萃取。

## 创建准入

满足任一条件时创建 Topic：

| 条件 | 说明 |
|---|---|
| 林峰明确要求 | “开一个 Topic”“先建立个 Topic” |
| 预计跨会话推进 | 当前工作无法在本轮自然结束 |
| 会产生可交付文件 | 方案、报告、PPT、评审、草案、清单 |
| 有外部依赖或跟进事项 | 有责任人、截止窗口、等待反馈 |
| 会形成决策链 | 后续需要追踪范围、取舍、风险、未解决问题 |
| 需要知识萃取 | 本轮内容未来需要入库或复用 |

不创建 Topic：单次问答、临时评价、简单状态确认、用户明确说只讨论/不写入/不建档。

## 标准骨架

```text
platform-ops/topics/YYYYMMDD_主题简称/
  ├── 索引.md
  ├── _上下文快照.md
  ├── _准入检查单.md
  └── 讨论记录.md
```

## Topic Capsule

吸收 ByteRover Context Tree 和 Obsidian Copilot Project Mode 思路。Topic Capsule 是可恢复状态对象，不是独立 skill。

最小字段：

```text
topic_id
status
scope
last_action
next_action
confirmed_facts
decisions
open_questions
risk_boundaries
key_files
context_pack
source_sessions
do_not_touch
```

限制：

- 不塞整个 vault。
- 不自动改写 confirmed_facts。
- 仪表盘是入口，状态事实以 Topic 本体为准。

## 会话捕获

Topic 生命周期动作必须维护 `_上下文快照.md` 的 `## 6. 关联会话` 表。

必经时机：

| 动作 | 必须记录 |
|---|---|
| Topic 创建 | 当前会话行 |
| Topic 冻结 | 如果本轮会话未在表内，追加当前会话行 |
| Topic 关闭 | 追加最终会话行 |
| 知识萃取 | 优先使用关联会话表里的 JSONL 路径 |

执行规则：

1. 先按 `references/session-locating.md` 或 `locate_session_jsonl.py` 定位当前会话 JSONL。
2. 精确命中时写入 `工具 / 会话标识 / JSONL 路径 / 工作区路径 / 日期`。
3. 找不到精确 JSONL 时，仍写入工具、会话标识或 `待确认`、工作区路径和日期；JSONL 路径写 `待确认`。
4. 同一会话行已存在时不得重复追加。
5. 不允许把会话捕获留给后续萃取阶段补做。

## 状态值

| 机器值 | 展示值 | 含义 |
|---|---|---|
| `doing` | `[🟢 Doing]` | 当前焦点 |
| `paused` | `[🟡 Paused]` | 暂停，可恢复 |
| `blocked` | `[🔴 Blocked]` | 外部依赖阻塞 |
| `pending_extraction` | `[📋 待萃取]` | 工作完成，等待知识萃取 |
| `done` | `[⚪ Done]` | 萃取完成，归档 |

冲突裁决顺序：本轮明确状态变更 > `_上下文快照.md` > `索引.md` > 仪表盘。

## 冻结

触发：漂移切换、林峰主动暂停、需要保存现场。

必须同步：

1. 仪表盘状态和简注。
2. `_上下文快照.md` 的最后动作、下一步、未解决问题、切换原因。
3. `_上下文快照.md` 的 `## 6. 关联会话` 追加当前会话行。
4. `索引.md` 的 status、Next Action、关键产出、时间线日志。

## 恢复

恢复时先读 `_上下文快照.md`，向林峰汇报：

1. 上次做到哪里。
2. 接下来该做什么。
3. 之前卡在哪里。

确认后再切回 Doing。

## 关闭

Topic 工作目的达成时：

1. 全量更新快照。
2. `_上下文快照.md` 的 `## 6. 关联会话` 追加最终会话行。
3. `索引.md` 改为 `pending_extraction`，并同步 Next Action、关键产出、时间线日志。
4. 仪表盘移入待萃取区，并保持 Topic 行状态为 `[📋 待萃取]`。
5. 不自动萃取，等林峰主动触发。
