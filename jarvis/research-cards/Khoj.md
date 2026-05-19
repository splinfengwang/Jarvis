# Research Card: Khoj

source_project: Khoj
source_url: https://github.com/khoj-ai/khoj
source_revision: `9258f57dceab19d52a1a0bdac54eb38576c29187`

source_paths:
- `https://github.com/khoj-ai/khoj/blob/9258f57dceab19d52a1a0bdac54eb38576c29187/src/khoj/search_type/text_search.py`
- `https://github.com/khoj-ai/khoj/blob/9258f57dceab19d52a1a0bdac54eb38576c29187/src/khoj/utils/helpers.py`
- `https://github.com/khoj-ai/khoj/blob/9258f57dceab19d52a1a0bdac54eb38576c29187/src/interface/obsidian/src/similar_view.ts`

mechanism_summary:
- text search 支持跨 entry type 的检索和 rerank。
- Obsidian similar view 支持用当前文件或输入 query 找相似文档，并提供 “More context” 展开。
- agent/tool 描述将搜索作为可被 agent 调用的上下文入口。

jarvis_mapping:
- 映射为 connector/context 参考：先找候选，再按 Context Pack 决定是否读取。
- 第一阶段不实现 Khoj 后端或索引。

adopted_parts:
- 多文档入口意识。
- “更多上下文”按需展开。
- 结果需保留来源文件。

rejected_parts:
- 不实现 embedding/rerank/search 服务。
- 不把相似搜索结果当事实。
- 不进入第一期 adapter 实现。

usable_rule:
- 语义命中只能产生 optional context 候选；事实判断必须读源文件原文。

test_case:
- 输入：“为什么 Context Pack 这样设计？”
- 期望：回答引用 Obsidian Copilot 和 Khoj 的 context selection 机制，而不是只说“为了节省上下文”。

failure_trigger_for_research:
- Context Pack 对多文档入口或候选上下文处理不清时，回到 Khoj text search / similar view 重新研究。
