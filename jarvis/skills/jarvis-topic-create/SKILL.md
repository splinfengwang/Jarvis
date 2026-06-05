---
name: jarvis-topic-create
description: 创建 Jarvis Topic 骨架。用于“先建立 Topic”“开一个 Topic”“新建话题”。脚本默认 dry-run；当用户明确要求建立 Topic 且计划校验无冲突时，可在同轮用 --write 执行记录性写入。
next_skills: []
---

# jarvis-topic-create

inputs:
- Topic 标题。
- 一句话范围说明。
- 可选日期。
- `platform-ops/仪表盘.md`。
- 当前会话信息：工具、会话标识、JSONL 路径、工作区路径、日期；JSONL 未定位时必须写 `待确认`。

outputs:
- 创建计划。
- 四个 Topic 文件预览 + 三个标准子目录（`参考资料/`、`过程稿/`、`定稿/`）。
- 仪表盘追加行预览。
- `_上下文快照.md` 的关联会话行。
- validation result。

## 产出规范

Topic 创建后，讨论过程中产生的文件必须遵循 `jarvis/references/topic-lifecycle.md` 的目录和命名规范：
- **过程稿/**：迭代中间版本，`YYYYMMDD-主题-文档类型-vN.M.md`
- **定稿/**：用户确认的最终产出，`YYYYMMDD-主题-文档类型.md`
- **参考资料/**：外部输入材料（PDF/PPT/图片等），保持原名
- 根目录仅保留四件套骨架文件和元数据（`_萃取清单.md` 等）
- 二级子目录无例外，文件名同样必须带日期和主题前缀

required_references:
- `jarvis/references/write-permission.md`
- `jarvis/references/topic-lifecycle.md`

on_demand_references:
- `jarvis/references/session-locating.md`

allowed_scripts:
- `jarvis/scripts/create_topic.py`
- `jarvis/scripts/locate_session_jsonl.py`
- `jarvis/scripts/append_operation_log.py`
- `jarvis/scripts/validate_dashboard.py`

write_level:
- record_write
- script default remains dry-run

confirmation_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 创建前：读取 ~/.jarvis/current-session 获取 session_id → locate_session_jsonl

fallback_rules:
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- （本 skill 无特有规则，全部由 CORE 覆盖）
