---
name: jarvis-topic-freeze
description: 暂停或保存当前 Jarvis Topic。用于“这个先存一下”“先暂停”“先冻结”。只记录已发生事实和下一步。
next_skills:
  - jarvis-topic-resume
---

# jarvis-topic-freeze

trigger:
- “这个先存一下”
- “先暂停”
- “先冻结”
- “今天先到这”

non_trigger:
- 用户要求关闭 Topic。
- 用户要求知识萃取或入库。
- 用户明确禁止写入。

inputs:
- 当前 Topic。
- 最后动作。
- 下一步。
- 待拍板或阻塞项。
- 当前会话信息；本轮会话未在关联会话表内时必须追加。

outputs:
- 冻结计划。
- 快照更新预览。
- 状态同步预览。
- 关联会话追加预览。
- OpenViking 写入结果：`committed` / `skipped_or_failed`。
- validation result。

required_references:
- `jarvis/references/write-permission.md`

on_demand_references:
- `jarvis/references/topic-lifecycle.md`
- `jarvis/references/session-locating.md`

allowed_scripts:
- `jarvis/scripts/locate_session_jsonl.py`
- `jarvis/scripts/update_snapshot.py`
- `jarvis/scripts/update_topic_status.py`
- `jarvis/scripts/sync_topic_index.py`
- `jarvis/scripts/append_operation_log.py`
- `jarvis/scripts/validate_dashboard.py`
- `jarvis/scripts/memcommit_adapter.py`

write_level:
- record_write

confirmation_rules:
- 只记录已发生事实，不写新判断。
- 冻结前必须处理关联会话：① 快照中最后一次记录的会话到当前会话之间，扫描是否有遗漏的中间会话 JSONL（按 `.claude/sessions/` 修改时间排序）。有 → 补入关联会话表。② 当前会话追加到关联会话表。定位不到 → 标 `待确认`。
- 冻结时同步 `索引.md` 的 Next Action、关键产出和时间线。
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。
- 冻结写入完成后，调用 `memcommit_adapter.py --write --repo-root . --kind topic_freeze --topic <topic> --summary <摘要> --fact <事实> --decision <决策>` 写入 OpenViking 记忆。`--write` 为必传标志，缺省为 dry-run 仅预览不写入。若 adapter 返回 `skipped_or_failed`，记录 `memory_commit: skipped_or_failed` 到日志，不阻塞本地 Topic 闭环。
- 冻结后必须将当前 Topic 相关变更提交到 git（`git add` 当前 Topic 目录 + 仪表盘 + log，`git commit -m "🧊 冻结: <Topic>"`）。未经 commit 的冻结不完整，Topic 内容不受 git 保护。
- 当前 Topic 不明确时先确认。

fallback_rules:
- 三位一体状态无法同步时停止，不做部分成功口头承诺。
- 高风险文件不在本 skill 写入范围内。

acceptance_cases:
- “这个先存一下” -> 快照、索引、仪表盘状态一致，且当前会话进入关联会话表。
- 只有推论没有事实 -> 标为推论或待验证。
- 无当前 Topic -> 先确认。
