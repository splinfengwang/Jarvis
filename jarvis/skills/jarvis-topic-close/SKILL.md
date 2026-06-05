---
name: jarvis-topic-close
description: 关闭 Jarvis Topic 并转入待萃取。用于“这个 Topic 收一下”“这个结束”。关闭不等于自动知识萃取。
next_skills:
  - jarvis-knowledge-extract
---

# jarvis-topic-close

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
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 关闭前必须处理最终关联会话：扫描中间会话 + 当前会话追加
- 关闭时同步 索引.md 的 Next Action、关键产出和时间线
- 调用 memcommit_adapter.py --write 写入 OpenViking 记忆
- 全部步骤完成后，验证 git status --porcelain，仍有未提交变更 → 警告并重新 commit

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 仪表盘或索引同步失败时停止

