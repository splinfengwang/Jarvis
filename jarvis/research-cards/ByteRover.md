# Research Card: ByteRover

source_project: byterover-cli
source_url: https://github.com/campfirein/byterover-cli
source_revision: `93f2514378c114a5293b22f6e7bf5a029078093d`

source_paths:
- `https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/README.md`
- `https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/AGENTS.md`
- `https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/CHANGELOG.md`
- `https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/scripts/migrate-frontmatter-complete.ts`
- `https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/src/shared/transport/events/context-tree-events.ts`
- `https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/src/server/core/domain/knowledge/runtime-signals-schema.ts`

mechanism_summary:
- ByteRover 使用 `.brv/context-tree` 作为结构化长期上下文树。
- context-tree markdown frontmatter 保持 semantic fields；runtime signals 如 maturity/recency/access count 迁移到 sidecar，避免查询污染知识文件。
- `brv dream` 做后台整理，带 review pending 和 undo，避免不确定修改直接落入长期上下文。
- JSON output 提供 matchedDocs/tier/duration/topScore 等检索 provenance。

jarvis_mapping:
- 映射为 Topic Capsule 和 Evidence Pack provenance 字段。
- 映射为 Topic 生命周期：关闭后进入待萃取，不自动整理入库。
- 映射为“运行时信号不污染正文”：状态同步和知识正文分开。

adopted_parts:
- provenance 必填。
- lifecycle / maturity 概念。
- 不确定内容进入待确认状态。
- derived/runtime signals 不写入知识正文。

rejected_parts:
- 不接入 ByteRover CLI。
- 不实现 context-tree、dream、swarm。
- 不实现 provider federation。

usable_rule:
- Evidence Pack 必须能说明 claim 来自哪里；Topic 关闭只能转 pending extraction，不能自动萃取或入库。

test_case:
- 输入：“这个 Topic 收一下。”
- 期望：状态进入 `pending_extraction`，生成待萃取标记，不自动写知识库。

failure_trigger_for_research:
- Evidence Pack 缺 provenance、Topic 生命周期混乱、或关闭时自动入库时，回到 ByteRover context-tree/provenance/lifecycle 重新研究。
