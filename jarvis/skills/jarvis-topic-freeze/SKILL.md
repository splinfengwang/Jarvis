---
name: jarvis-topic-freeze
description: 暂停或保存当前 Jarvis Topic。用于“这个先存一下”“先暂停”“先冻结”。只记录已发生事实和下一步。
next_skills:
  - jarvis-topic-resume
---

# jarvis-topic-freeze

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
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 冻结前必须处理关联会话：扫描中间会话 + 当前会话追加
- 冻结时同步 索引.md 的 Next Action、关键产出和时间线
- 调用 memcommit_adapter.py --write 写入 OpenViking 记忆
- 全部步骤完成后，验证 git status --porcelain

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 三位一体状态无法同步时停止，不做部分成功口头承诺
