# Research Card: PlugMem

source_project: PlugMem
source_url: https://github.com/TIMAN-group/PlugMem
source_revision: `317f1fc1902f32a64a5a043f6e46205cce58b05d`

source_paths:
- `https://github.com/TIMAN-group/PlugMem/blob/317f1fc1902f32a64a5a043f6e46205cce58b05d/README.md`
- `https://github.com/TIMAN-group/PlugMem/blob/317f1fc1902f32a64a5a043f6e46205cce58b05d/openclaw-plugmem-plugin/src/config.ts`
- `https://github.com/TIMAN-group/PlugMem/blob/317f1fc1902f32a64a5a043f6e46205cce58b05d/tests/test_api_memories.py`
- `https://github.com/TIMAN-group/PlugMem/blob/317f1fc1902f32a64a5a043f6e46205cce58b05d/tests/test_api_retrieval.py`
- `https://github.com/TIMAN-group/PlugMem/blob/317f1fc1902f32a64a5a043f6e46205cce58b05d/src/memory_structuring/structuring_inference.py`

mechanism_summary:
- README 明确给出三类记忆：semantic、procedural、episodic，并说明 episodic 是长交互序列、semantic/procedural 是可复用知识单元。
- `openclaw-plugmem-plugin/src/config.ts` 明确区分 `defaultGraphId` 和 `sharedReadGraphIds`；写入不会打到 shared read graph。
- `tests/test_api_memories.py` 覆盖 structured semantic/procedural/episodic 插入和 `session_id` stamping。
- `tests/test_api_retrieval.py` 覆盖 retrieve/reason/consolidate 和 recall audit log / session timeline。
- `src/memory_structuring/structuring_inference.py` 显式区分 semantic 抽取和 procedural 抽取函数。

jarvis_mapping:
- 映射为 Evidence Pack 的 `memory_type`。
- 映射为“不自动入库”：候选证据即使可召回，也必须确认后才写知识库。
- 映射为 OpenViking 口径：召回线索不是事实依据。

adopted_parts:
- `semantic`：业务事实、概念、定义。
- `procedural`：可复用流程、操作规程。
- `episodic`：会话事件、Topic 进展。
- read graph 和 write graph 分离。

rejected_parts:
- 不实现 memory graph 引擎。
- 不自动从对话抽取并写入长期知识。
- 不把 plugin 分支能力作为第一期依赖。

usable_rule:
- Evidence Pack 必须标注 `memory_type`，且 `can_ingest` 只表示进入确认/入库决策流，不表示跳过人工确认。

test_case:
- 输入：“A 组全确认。”
- 期望：只处理确认范围内的 Evidence Pack；医学参数和判断类仍按确认规则处理。

failure_trigger_for_research:
- Evidence Pack 缺少来源、claim 不可追溯、memory_type 使用混乱、或候选知识被自动写入时，回到 PlugMem README/config/retrieval tests 重新研究。
