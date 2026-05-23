---
name: jarvis-topic-create
description: 创建 Jarvis Topic 骨架。用于“先建立 Topic”“开一个 Topic”“新建话题”。脚本默认 dry-run；当用户明确要求建立 Topic 且计划校验无冲突时，可在同轮用 --write 执行记录性写入。
---

# jarvis-topic-create

trigger:
- “先建立 Topic：...”
- “开一个 Topic”
- “这个单独建个话题”

non_trigger:
- 用户明确说只讨论、不要写入、不要建档。
- 单次轻量问答。

inputs:
- Topic 标题。
- 一句话范围说明。
- 可选日期。
- `platform-ops/仪表盘.md`。
- 当前会话信息：工具、会话标识、JSONL 路径、工作区路径、日期；JSONL 未定位时必须写 `待确认`。

outputs:
- 创建计划。
- 四个 Topic 文件预览。
- 仪表盘追加行预览。
- `_上下文快照.md` 的关联会话行。
- validation result。

required_references:
- `jarvis/references/write-permission.md`

on_demand_references:
- `jarvis/references/topic-lifecycle.md`
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
- 创建前必须尝试定位当前会话 JSONL；无法精确定位时，仍把 JSONL 路径写为 `待确认`，不能省略关联会话表。
- 第一步必须输出创建计划和 diff preview。
- 若用户已明确要求建立 Topic，且标题、范围、目录名、仪表盘行无歧义，可在同轮执行 `--write`。
- 写入成功后追加一条 `platform-ops/log.md` 操作日志。
- 若用户只是讨论是否建立、或输入含糊，则停在 dry-run 等确认。
- 不修改 `AGENT.md`。

fallback_rules:
- 仪表盘缺失、同名 Topic 已存在或表格无法定位时停止。
- 脚本失败时不得手工整页重写仪表盘。

acceptance_cases:
- “先建立 Topic：测试替换验收” -> dry-run 生成四文件、仪表盘行和关联会话行。
- `--write` 后四文件存在，仪表盘行格式正确。
- JSONL 未定位 -> 关联会话表仍有工具、工作区、日期，JSONL 字段为 `待确认`。
- “不要动原文件，只给方案” -> 不触发。
