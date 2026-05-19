# Research Card: Obsidian Copilot

source_project: obsidian-copilot
source_url: https://github.com/logancyang/obsidian-copilot
source_revision: `ba378e838953a9594a8116fea1d28fc9c5c187a6`

source_paths:
- `https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/docs/projects.md`
- `https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/docs/context-and-mentions.md`
- `https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/designdocs/TOOLS.md`
- `https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/designdocs/MESSAGE_ARCHITECTURE.md`
- `https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/src/types/message.ts`

mechanism_summary:
- Project mode / context mentions 把 vault、active note、selected text、tags、folders 变成显式上下文。
- Message architecture 使用 ContextManager 和 PromptContextEnvelope，强调编辑或再生成时刷新上下文。
- Tool registry 区分 requiresVault，说明工具能否访问 vault。

jarvis_mapping:
- 映射为 Context Pack：任务需要哪些文件、为什么需要、缺什么就停止。
- 映射为 required/optional 文件分层，避免机械全库读取。

adopted_parts:
- 上下文显式打包。
- required/optional 分离。
- vault 访问能力作为工具边界。
- 上下文过期时重新处理。

rejected_parts:
- 不实现 Obsidian 插件 UI。
- 不实现实时 selected text / active note 捕获。
- 不实现完整 token budget compaction。

usable_rule:
- Jarvis 在读文件前必须能说明 `why_required`；缺少 required 文件时不能继续伪造判断。

test_case:
- 输入：“继续贾维斯运行时架构。”
- 期望：Context Pack 包含仪表盘、该 Topic 的索引和快照；讨论记录为 optional；找不到 Topic 时进入停止条件。

failure_trigger_for_research:
- Context Pack 漏读关键文件、把 optional 当 required、或缺 required 仍继续判断时，回到 Obsidian Copilot Project Mode / ContextManager 重新研究。
