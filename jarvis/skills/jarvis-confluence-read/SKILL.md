---
name: jarvis-confluence-read
description: 读取或搜索公司 Confluence 文档。用于“查一下 Confluence 这个页面”“搜一下公司文档里有没有这个词”。只读，不写入。
next_skills: []
---

# jarvis-confluence-read

inputs:
- 页面 ID 或搜索关键词。
- 可选搜索类型：标题、正文、评论。

outputs:
- 命中的页面或搜索结果。
- 若失败，返回明确错误类型。
- 明确声明未写入。

required_references: []

on_demand_references:
- `jarvis/references/memory-and-sources.md`

allowed_scripts:
- `jarvis/scripts/confluence_query.py`

write_level:
- none

confirmation_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 页面 ID 缺失时优先走搜索模式

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 401/403 → 明确提示 Cookie 过期或权限不足
- 404 → 明确提示页面不存在
- 其他错误 → 回报状态码，不重复重试

