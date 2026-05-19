# Jarvis Runtime v0.1 Comprehensive Audit - 2026-05-17

## 结论

Runtime v0.1 仍是 **替换候选**，不是正式替换版。

本轮审查确认 DeepSeek 指出的会话捕获缺口成立：v3.4 已明确要求 Topic 创建、冻结、关闭时维护关联会话，但 runtime 原实现没有把它落成 lifecycle 必经步骤。该缺口已修复并加入 fixture 断言。

## 审查范围

- `CLAUDE.md` bootstrap 入口。
- `智能体/贾维斯/runtime-v0.1/JARVIS_BOOTSTRAP.md`。
- `智能体/贾维斯/runtime-v0.1/JARVIS_CORE.md`。
- `.claude/skills/jarvis-*` 与 `runtime-v0.1/skills/jarvis-*`。
- `runtime-v0.1/references/`。
- `runtime-v0.1/scripts/`。
- `runtime-v0.1/tests/run_replacement_checks.py`。
- `智能体/贾维斯/AGENT.md v3.4` 的关键能力映射。
- 当前真实 `platform-ops/仪表盘.md` 结构。

## 已修复问题

### P0 - Topic 生命周期未捕获当前会话

原问题：

- `create_topic.py` 生成的关联会话曾是占位或未被 skill 强制调用。
- `jarvis-topic-freeze` 没有要求冻结时追加当前会话。
- `jarvis-topic-close` 没有要求关闭时追加最终会话。

修复：

- `create_topic.py` 支持 `--session-tool`、`--session-id`、`--session-jsonl`、`--session-cwd`、`--session-date`，创建时写入关联会话行。
- `update_snapshot.py` 支持结构化追加关联会话表行，已存在时不重复追加。
- `topic-lifecycle.md` 和 `session-locating.md` 明确 Topic 创建、冻结、关闭都必须写当前/最终会话。
- `jarvis-topic-create`、`jarvis-topic-freeze`、`jarvis-topic-close` 均要求先定位当前会话；JSONL 找不到时写 `待确认`，不能省略。
- `run_replacement_checks.py` 断言创建、冻结、关闭三步都产生会话行。

### P1 - 关闭 Topic 与知识萃取触发词冲突

原问题：

- `knowledge-extraction.md` 把“这个 Topic 收一下”列为萃取触发。
- 这会和 `jarvis-topic-close` 的“关闭不自动萃取”发生路由冲突。

修复：

- `knowledge-extraction.md` 已把“这个 Topic 收一下 / 这个话题结束 / 先关闭 / 先暂停 / 先存一下”列为明确不触发萃取。
- 替换测试增加关闭路径断言。

### P1 - 操作日志只有 reference，没有可执行脚本

原问题：

- v3.4 要求关键操作后写入 `platform-ops/log.md`。
- runtime 只有 `obsidian-conventions.md` 提到日志，没有脚本和 skill 调用路径。

修复：

- 新增 `scripts/append_operation_log.py`，默认 dry-run，`--write` 才追加日志。
- 脚本只追加一行，避免重写历史日志。
- `jarvis-topic-create`、`jarvis-topic-freeze`、`jarvis-topic-close` 已把该脚本列入 allowed scripts。
- 替换测试断言日志追加成功。

### P1 - 状态同步脚本不兼容历史仪表盘链接格式

原问题：

- 当前真实仪表盘中有 Topic 链接写作 `.../索引`，而 `update_topic_status.py` 只匹配 `.../索引.md`。
- 这会导致 fixture 通过，但真实仪表盘同步失败。

修复：

- `update_topic_status.py` 现在先匹配 `索引.md`，失败时兼容匹配去掉 `.md` 的历史链接。
- 已用真实当前 Topic 行完成一次状态同步验证。

### P1 - 仪表盘没有独立待萃取分区

原问题：

- v3.4 说仪表盘至少包含活跃 Topic、待萃取、跟进事项/归档。
- 当前真实仪表盘缺少独立“待萃取”分区。
- `update_topic_status.py` 只能改状态文本，不能把 Topic 行迁移到待萃取区。

修复：

- 真实 `platform-ops/仪表盘.md` 已新增 `## 待萃取` 分区。
- `update_topic_status.py` 现在在 `pending_extraction` 时把 Topic 行迁移到待萃取区。
- `validate_dashboard.py` 现在同时校验活跃 Topic 和待萃取两张表。
- fixture 会断言关闭后仪表盘出现 `## 待萃取`、`[📋 待萃取]` 和目标 Topic。

### P1 - 知识入库缺端到端 fixture 验收

原问题：

- `jarvis-knowledge-ingest` 有规则，但没有可执行入库脚本。
- 不能证明“A 组全确认”只写确认范围，也不能证明 `needs_source` 和判断类被跳过。

修复：

- 新增 `ingest_evidence_pack.py`。
- v0.1 自动脚本只处理 `can_ingest: true`、`verification_status: confirmed`、`knowledge_type: L1`、`memory_type: semantic` 的术语项。
- fixture 验证：A1 写入 `知识库/术语/测试替换术语.md`，同步 `知识库/wiki索引.md` 与 `知识库/术语/术语索引.md`；B1 判断类和 A2 缺来源条目不写入。

### P1 - OpenViking 写入 adapter 边界不清

原问题：

- v3.4 规定 Topic 冻结、关闭时写 OpenViking 记忆。
- runtime 只说明 OpenViking 是召回线索，没有规定写入失败如何降级。

修复：

- `memory-and-sources.md` 已新增“记忆写入 adapter”。
- 规则明确：有 `memcommit` 就调用；没有或失败时不得声称已写入 OpenViking。
- 降级时必须保证 Topic 快照、讨论记录、仪表盘和 `platform-ops/log.md` 已同步，并在 Gate 5 记录 `memory_commit: skipped_or_failed`。
- `jarvis-topic-freeze`、`jarvis-topic-close` 已要求输出 OpenViking 写入结果。

## 仍未解除的正式替换阻塞

### P0 - Gate 5 真实任务仍为 0/5

当前自动测试只能证明 fixture 可运行，不能证明真实项目连续工作可替换 `AGENT.md`。

处理要求：

- 按 `tests/gate5-real-task-test-plan.md` 执行真实任务。
- 5 个任务必须来自林峰真实输入或当前活跃 Topic 真实下一步。
- 任一 P0/P1 失败立即回退 `AGENT.md v3.4`。

### P1 - 真实知识入库仍需人工确认任务验证

fixture 只覆盖已确认 L1 术语。真实知识入库仍需验证：

- 林峰明确确认范围。
- 医学类、判断类、安全边界类仍单独确认。
- 非 L1 条目进入人工计划，不由 v0.1 自动脚本写入。

### P1 - OpenViking 记忆写入仍需真实 Claude Code 环境验证

runtime 已补 adapter 降级规则，但仍需在真实 Claude Code 环境验证 `memcommit` 是否可用。

正式替换前需要在 Gate 5 观察：

- Claude Code 环境是否有可用记忆工具。
- 若没有，是否正确记录 `memory_commit: skipped_or_failed`。
- 不得把“没写 memory”伪装成已完成。

## 当前验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 智能体/贾维斯/runtime-v0.1/tests/run_replacement_checks.py
PASS: Jarvis Runtime v0.1 replacement checks passed
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 智能体/贾维斯/runtime-v0.1/scripts/validate_links.py --vault-root . --scope 智能体/贾维斯/runtime-v0.1 --scope platform-ops/topics/20260516_贾维斯运行时架构迭代
validation result: passed
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 智能体/贾维斯/runtime-v0.1/scripts/validate_dashboard.py --vault-root .
validation result: passed with warning: line 21 missing trailing empty column
```

runtime 目录无 `__pycache__` 或 `.pyc`。

## 替换判断

当前不建议移除原入口。

可进入下一步：

- 继续 Runtime-first 真实任务试点。
- DeepSeek 执行 Gate 5 时必须重点检查：会话捕获、操作日志、关闭不萃取、知识入库确认边界、仪表盘分区迁移和状态一致性。

不可执行：

- 删除或禁用 `智能体/贾维斯/AGENT.md`。
- 宣称 runtime 已正式替换 v3.4。
- 用 fixture 通过替代 Gate 5 真实任务通过。
