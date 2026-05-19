# Runtime Research Card Source Review - 2026-05-18

## 结论

当前已采纳机制的源码级复核状态分为两档：

- 已完成复核：`BMAD`、`Obsidian Copilot`、`Khoj`、`ByteRover`、`RegionFocus`、`AnythingLLM`、`PlugMem`
- 仅做 adapter boundary 抽样，不作为第一期 adopted-source：`Onyx`、`Open WebUI`、`Letta`

## PlugMem 复核结果

此前 research card 使用了错误仓库地址。当前已确认可复核源为：

- repo: `TIMAN-group/PlugMem`
- commit: `317f1fc1902f32a64a5a043f6e46205cce58b05d`

已复核点：

1. `README.md`
   - 明确写出三类记忆：`Semantic`、`Procedural`、`Episodic`
   - 明确 episodic 是 interaction sequences，semantic/procedural 是 reusable knowledge
2. `openclaw-plugmem-plugin/src/config.ts`
   - `defaultGraphId` 作为默认写图
   - `sharedReadGraphIds` 只参与 recall fan-out，不作为写目标
3. `tests/test_api_memories.py`
   - 有 structured semantic/procedural/episodic 插入测试
   - 有 `session_id` stamping 测试
4. `tests/test_api_retrieval.py`
   - 有 retrieve / reason / consolidate
   - 有 recall audit log、session filter、timeline
5. `src/memory_structuring/structuring_inference.py`
   - semantic / procedural 抽取路径分离

对 Jarvis 的有效支撑：

- `memory_type = semantic/procedural/episodic`
- recall 证据不等于自动入库
- session-aware retrieval / episodic trace 的合理性
- read graph 与 write graph 分离

不继续采纳的部分：

- PlugMem memory graph 引擎本体
- 自动长期学习
- OpenClaw / Claude Code plugin UI

## 其他已采纳机制复核摘要

- `BMAD`
  - 复核 `bmad-help` 与 registry 思路，支撑 `jarvis-help` / router 的“只给下一步，不倾倒全目录”
- `Obsidian Copilot`
  - 复核 `projects.md` 与 `context-and-mentions.md`，支撑 Context Pack 的显式上下文装载
- `Khoj`
  - 复核 `similar_view.ts`，支撑 optional context / more context 展开
- `ByteRover`
  - 复核 `runtime-signals-schema.ts`，支撑运行时信号不污染正文
- `RegionFocus`
  - 复核 README debug/intermediate evidence，支撑视觉证据链
- `AnythingLLM`
  - 复核 whitelist / availability endpoint，支撑 tool/skill 白名单边界

## 未进入第一期 adopted-source 的来源

- `Onyx`
- `Open WebUI`
- `Letta`

它们当前只承担 adapter boundary 参考，不进入“必须源码级复核后才能签字”的第一期 adopted-source 集合。
