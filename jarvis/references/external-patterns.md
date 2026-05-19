# External Patterns

> 本文件记录外部项目的可采纳机制。它是优化参考，不是事实源，也不覆盖 `AGENT.md v3.4`。

## 采纳边界

外部做法只有同时满足以下条件，才进入 Jarvis Runtime：

1. 能解决 Jarvis 当前真实问题。
2. 不削弱 v3.4 的裁决层、写权限、Topic 状态、知识确认边界。
3. 可由 Claude Code-first 运行时实现。
4. 不要求把 Obsidian 改造成另一套平台。
5. 有明确输入、输出、失败模式和验收方式。

## Router Pattern

来源：BMAD。

用途：把自然语言转成意图、风险、副作用和下一步建议。

```text
用户表达
→ 意图分类
→ 副作用判断
→ 写权限判断
→ 建议 workflow / script
→ 必要时请求确认
```

限制：

- 默认只读。
- 不直接写文件。
- 不直接萃取。
- 不直接入库。
- 不替代具体 workflow 的边界判断。

## Topic Capsule Pattern

来源：ByteRover Context Tree、Obsidian Copilot Project Mode。

用途：让 Topic 从“文件夹”变成可恢复状态对象。

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
- 不自动改写 confirmed facts。
- 仪表盘仍只是入口，状态事实回到 Topic 本体确认。

## Evidence Pack Pattern

来源：ByteRover provenance / lifecycle、PlugMem memory unit、RegionFocus / GUI-Eyes 中间证据。

用途：让萃取候选带证据链。

最小字段：

```text
claim
knowledge_type
memory_type
source_type
source_path
source_excerpt
evidence_level
confidence
verification_status
usage_scope
linked_topic
related_entries
```

`memory_type` 建议值：

| 类型 | 含义 |
|---|---|
| semantic | 业务事实、术语、关系、判断 |
| procedural | 工作流、写权限、萃取规则、操作规范 |
| episodic | Topic 讨论记录、JSONL 会话、操作日志 |

限制：

- Evidence Pack 不是已确认知识。
- Agent 推断必须标注，不能直接入库。
- OCR / 视觉结果是证据，不是绝对事实。

## Context Pack Pattern

来源：Obsidian Copilot Project Mode、Khoj 多文档入口。

用途：定义不同任务的必读/选读上下文。

默认规则：

| 任务 | 必读 | 按需 |
|---|---|---|
| 近况查询 | 仪表盘、活跃 Topic 快照 | Topic 索引、讨论记录 |
| Topic 恢复 | 仪表盘、目标 Topic 快照、索引 | 讨论记录、关键产出 |
| 知识萃取 | Topic 快照、索引、讨论记录、关联会话表 | JSONL、源文件、业务文档、术语页 |
| 新命题 | wiki索引、memsearch 结果、仪表盘 | 相关业务文档、历史 Topic |

限制：

- Context Pack 只解决“读什么”，不解决“是否为事实”。
- 上下文命中不能替代确认入库。

## Visual Evidence Loop

来源：RegionFocus / GUI-Eyes。

用途：降低截图、OCR、表格、数字、界面状态误读风险。

后续流程：

```text
全局观察
→ 标出不确定区域
→ crop / zoom / OCR / table extract
→ 形成 claim-evidence 映射
→ 标注验证状态
→ 进入萃取确认清单
```

第一版只保留流程，不做 `jarvis-visual-evidence` skill。

## Connector Awareness

来源：AnythingLLM / Onyx / Open WebUI 等平台型项目。

用途：提醒后续 adapter 设计时考虑连接器、权限、MCP、外部资料入口。

限制：

- 不迁移到平台。
- 不引入多用户企业权限系统。
- 不把 RAG-first 作为知识治理核心。
- 不把向量召回结果作为事实。

## 不采纳清单

- BMAD 多角色团队和完整敏捷生命周期。
- 新 memory backend 替换 OpenViking / Obsidian。
- PlugMem 式自动 memory graph。
- Khoj / Obsidian Copilot 的 vault QA 作为终点。
- GUI grounding benchmark。
- RAG 平台迁移。
- agent 自动长期学习作为事实源。
