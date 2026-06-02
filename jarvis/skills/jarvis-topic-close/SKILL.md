---
name: jarvis-topic-close
description: 关闭 Jarvis Topic 并转入待萃取。用于“这个 Topic 收一下”“这个结束”。关闭不等于自动知识萃取。
next_skills:
  - jarvis-knowledge-extract
---

# jarvis-topic-close

trigger:
- “这个 Topic 收一下”
- “这个话题结束”
- “关闭这个 Topic”

non_trigger:
- “先存一下”或临时暂停。
- “萃取一下”或“入库”。
- 用户明确禁止写入。

inputs:
- 当前 Topic。
- 关闭理由。
- 最终状态摘要。
- 当前会话信息；关闭时必须追加最终会话行。

outputs:
- 关闭计划。
- `pending_extraction` 状态同步预览。
- 待萃取清单。
- 最终关联会话追加预览。
- OpenViking 写入结果：`committed` / `skipped_or_failed`。
- validation result。

required_references:
- `jarvis/references/session-locating.md`

on_demand_references:
- `jarvis/references/topic-lifecycle.md`
- `jarvis/research-cards/ByteRover.md`
- 仅在解释 pending extraction 设计来源、生命周期失败或修改 Topic 关闭协议时读取。

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
- 关闭只同步状态，不自动萃取、不自动入库。
- 关闭前必须处理最终关联会话：① 快照中最后一次记录的会话到当前会话之间，扫描是否有遗漏的中间会话 JSONL（按 `.claude/sessions/` 修改时间排序）。有 → 补入关联会话表。② 当前会话追加到关联会话表。定位不到 → 标 `待确认 — tool=工具名, session=会话ID, date=日期, cwd=工作区路径`。
- 关闭时同步 `索引.md` 的 Next Action、关键产出和时间线。
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。
- 关闭写入完成后，调用 `memcommit_adapter.py --write --repo-root . --kind topic_close --topic <topic> --summary <摘要> --fact <事实> --decision <决策>` 写入 OpenViking 记忆。`--write` 为必传标志，缺省为 dry-run 仅预览不写入。若 adapter 返回 `skipped_or_failed`，记录 `memory_commit: skipped_or_failed` 到日志，不阻塞本地 Topic 闭环。
- 关闭后必须将当前 Topic 相关变更提交到 git（`git add` 当前 Topic 目录 + 仪表盘 + log + 知识库变更，`git commit -m "✅ 关闭: <Topic>"`）。未经 commit 的关闭不完整，Topic 内容不受 git 保护。
- 若要归档到 Done，需要林峰明确确认。

fallback_rules:
- 无法定位 current Topic 时先确认。
- 仪表盘或索引同步失败时停止。

acceptance_cases:
- “这个 Topic 收一下” -> 状态为 `pending_extraction`。
- 最终会话进入 `_上下文快照.md` 的关联会话表。
- 不生成知识库条目。
- 待萃取内容只列清单。
