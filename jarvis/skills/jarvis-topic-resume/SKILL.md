---
name: jarvis-topic-resume
description: 恢复已有 Jarvis Topic。用于“继续...”“接着上次...”“恢复某 Topic”。只读索引、快照和必要讨论记录。
next_skills: []
---

# jarvis-topic-resume

inputs:
- Topic 名称或关键词。
- `platform-ops/仪表盘.md`。
- 匹配到的 `索引.md` 和 `_上下文快照.md`。
- 当前会话信息：工具、会话标识、JSONL 路径、工作区路径、日期。JSONL 未定位时写 `待确认 — tool=工具名, session=会话ID, date=日期, cwd=工作区路径`。

outputs:
- Topic 匹配结果。
- 最后动作。
- 已确认事实、当前推论、待拍板。
- 下一步建议。
- 若讨论记录 > 2000 字且含方案/参数/设计讨论，推荐 `jarvis-roundtable` 多角色审查。

required_references: []

on_demand_references:
- `jarvis/references/context-pack-spec.md`
- `jarvis/references/topic-lifecycle.md`

allowed_scripts:
- `jarvis/scripts/locate_session_jsonl.py`

write_level:
- record_write

confirmation_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 恢复后追加当前会话到快照的关联会话表。session_id 从 ~/.jarvis/current-session 读取 → locate
- 不更新快照的最后动作/下一步/未解决问题，不写讨论记录

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 找不到 Topic 时，按 jarvis-status 列候选

#### 恢复后自检

Topic 恢复完成、用户开始新一轮讨论后，判断：本次讨论是否产生了新的工作命题？是 → 提议建 Topic（走 `jarvis-topic-create`）。不是 → 继续当前 Topic。

