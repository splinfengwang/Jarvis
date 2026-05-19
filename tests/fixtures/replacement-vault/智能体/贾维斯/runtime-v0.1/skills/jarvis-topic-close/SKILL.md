---
name: jarvis-topic-close
description: 关闭 Jarvis Topic 并转入待萃取。用于“这个 Topic 收一下”“这个结束”。关闭不等于自动知识萃取。
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
- `智能体/贾维斯/runtime-v0.1/references/topic-lifecycle.md`
- `智能体/贾维斯/runtime-v0.1/references/session-locating.md`

on_demand_references:
- `智能体/贾维斯/runtime-v0.1/research-cards/ByteRover.md`
- 仅在解释 pending extraction 设计来源、生命周期失败或修改 Topic 关闭协议时读取。

allowed_scripts:
- `智能体/贾维斯/runtime-v0.1/scripts/locate_session_jsonl.py`
- `智能体/贾维斯/runtime-v0.1/scripts/update_snapshot.py`
- `智能体/贾维斯/runtime-v0.1/scripts/update_topic_status.py`
- `智能体/贾维斯/runtime-v0.1/scripts/sync_topic_index.py`
- `智能体/贾维斯/runtime-v0.1/scripts/append_operation_log.py`
- `智能体/贾维斯/runtime-v0.1/scripts/validate_dashboard.py`

write_level:
- record_write

confirmation_rules:
- 关闭只同步状态，不自动萃取、不自动入库。
- 关闭前必须处理最终关联会话：能定位 JSONL 就写路径；不能定位就写 `待确认` 行。
- 关闭时同步 `索引.md` 的 Next Action、关键产出和时间线。
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。
- 如运行时提供 `memcommit`，尝试写入 OpenViking；失败时记录 `memory_commit: skipped_or_failed`，不阻塞本地 Topic 闭环。
- 若要归档到 Done，需要林峰明确确认。

fallback_rules:
- 无法定位 current Topic 时先确认。
- 仪表盘或索引同步失败时停止。

acceptance_cases:
- “这个 Topic 收一下” -> 状态为 `pending_extraction`。
- 最终会话进入 `_上下文快照.md` 的关联会话表。
- 不生成知识库条目。
- 待萃取内容只列清单。
