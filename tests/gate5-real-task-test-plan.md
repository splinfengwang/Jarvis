# Gate 5 真实项目试点测试方案

> 目的：让 DeepSeek 按同一标准执行 Jarvis Runtime v0.1 的真实任务试点，判断它是否达到替换 `智能体/贾维斯/AGENT.md v3.4` 日常入口的条件。
> 当前状态：Gate 5 已通过（5/5 真实任务，2026-05-18/19）。本文档保留为历史参考。

## 1. 核心结论

Gate 5 不是再跑 10 个 fixture 用例，也不是让模型自己编 5 个提示词。

一个任务只有同时满足以下条件，才计入 Gate 5：

1. 来自林峰的真实工作输入，或来自当前活跃 Topic 的真实下一步。
2. 任务有实际工作价值，即使不验收 runtime 也本来值得做。
3. DeepSeek 必须优先使用 `CLAUDE.md` + `JARVIS_BOOTSTRAP.md` + runtime files，不读 `AGENT.md`。
4. 若 runtime 能完成，记录证据；若不能完成，立即触发 fallback，并记录缺口。
5. 不能因为想通过测试而降低任务难度、跳过写入判断、跳过来源证据或跳过确认规则。

## 2. 测试边界

### 必须遵守

- 不修改 `智能体/贾维斯/AGENT.md`。
- 不删除或移除原入口。
- 不自动知识入库。
- 不把 OpenViking 命中当事实。
- 不把构造验收提示当真实任务。
- 不把“只跑脚本通过”当真实任务通过。
- 每个任务都要有 Router 输出、Context Pack 判断和结果记录。

### 允许

- 读取 `CLAUDE.md`、`JARVIS_BOOTSTRAP.md`、`JARVIS_CORE.md`、runtime references、skills 和 scripts。
- 使用 runtime 脚本做 dry-run、校验和低风险记录性写入。
- 在林峰明确要求或 runtime 失败时读取 `AGENT.md v3.4` 作为 fallback。

### 失败即回退

出现以下任一情况，本轮 Gate 5 立即失败，切回 `AGENT.md v3.4`：

- Router 误判副作用或写权限。
- Context Pack 漏读关键文件，导致回答或写入依据错误。
- Evidence Pack 缺来源、来源不可追溯或把记忆召回当事实。
- 未确认就执行内容性写入或知识入库。
- 误写高风险文件，包括 `AGENT.md`、敏感配置、凭据文件。
- Topic 索引、快照、仪表盘状态不一致。
- 需要读 `AGENT.md` 才能完成常规流程，但没有记录为 fallback。

## 3. 预检步骤

DeepSeek 执行前先做以下预检：

1. 读取 `CLAUDE.md`。
2. 读取 `智能体/贾维斯/runtime-v0.1/JARVIS_BOOTSTRAP.md`。
3. 读取 `智能体/贾维斯/runtime-v0.1/JARVIS_CORE.md`。
4. 读取 `智能体/贾维斯/runtime-v0.1/acceptance-report.md`。
5. 读取 `智能体/贾维斯/runtime-v0.1/pilot-report.md`。
6. 不读取 `智能体/贾维斯/AGENT.md`，除非后续触发 fallback。

然后运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 智能体/贾维斯/runtime-v0.1/tests/run_replacement_checks.py
PYTHONDONTWRITEBYTECODE=1 python3 智能体/贾维斯/runtime-v0.1/scripts/validate_dashboard.py --vault-root .
PYTHONDONTWRITEBYTECODE=1 python3 智能体/贾维斯/runtime-v0.1/scripts/validate_links.py --vault-root . --scope platform-ops/topics/20260516_贾维斯运行时架构迭代
```

预检通过后，才能开始记录真实任务。

预检允许存在的已知 warning：

- `validate_dashboard.py` 可能提示仪表盘第 21 行缺少最后空列。这是历史格式 warning，不单独判失败。

## 4. 真实任务选择规则

优先级从高到低：

1. 林峰当场给 DeepSeek 的真实工作请求。
2. 当前仪表盘中活跃 Topic 的真实下一步。
3. 当前 Topic 已记录但尚未完成的真实待办。

以下任务不能计入：

- “最近怎么样”这类单独为验收构造的重复提示，除非林峰确实是在工作开始时询问近况。
- “直接改 AGENT.md”这类纯边界测试。
- “不要动原文件，只给方案”这类纯边界测试。
- DeepSeek 自己编的任务。
- 只运行 `run_replacement_checks.py` 的任务。

## 5. 建议覆盖矩阵

5 个真实任务不要求固定输入，但建议覆盖以下类型。每类最多计 1 个，避免 5 个任务都太轻：

| 类型 | 合格任务示例 | 必须验证 |
|---|---|---|
| 状态恢复类 | 林峰真实问“最近怎么样”或“继续某个 Topic” | 读仪表盘、Topic 索引、快照；不写入 |
| Topic 记录类 | 林峰真实要求建立、冻结、关闭某 Topic | dry-run/plan/diff；确认写入范围；索引、快照、仪表盘同步 |
| 业务产出类 | 继续某个真实业务 Topic，产出方案、文案、审查结论或设计材料 | Context Pack 不漏关键文件；输出区分事实/推论/待确认 |
| 知识萃取类 | 林峰真实要求“萃取这个 Topic” | 定位 JSONL 或标缺失；输出 Evidence Pack 和确认清单；不入库 |
| 知识入库类 | 林峰确认某组候选入库 | 只处理确认范围；医学/判断类仍单独确认；更新索引和日志；跑链接/引用校验 |
| 源码借鉴/设计解释类 | 林峰真实问“为什么这样设计”或要求改 runtime | 按需读取研究卡；引用来源机制；不泛泛解释 |

如果 5 个真实任务里没有知识萃取或知识入库，则 Gate 5 只能判定为“日常入口试点通过”，不能判定为“完全替换 `AGENT.md v3.4`”。

Topic 记录类的额外硬要求：

- 创建 Topic 时，必须在 `_上下文快照.md` 写入当前会话行。
- 冻结 Topic 时，必须追加本轮会话行；已存在时不得重复。
- 关闭 Topic 时，必须追加最终会话行，再同步为 `pending_extraction`。
- 找不到 JSONL 时，仍写入工具、会话标识或 `待确认`、工作区路径、日期，JSONL 路径写 `待确认`。
- 创建、冻结、关闭写入成功后，必须追加 `platform-ops/log.md` 操作日志。
- 关闭 Topic 时，仪表盘行必须进入 `## 待萃取` 分区。
- 冻结/关闭时如运行时没有 `memcommit`，必须记录 `memory_commit: skipped_or_failed`，不能说已写入 OpenViking。

知识入库类的额外硬要求：

- 可用 `ingest_evidence_pack.py` 处理已确认 L1 术语项。
- 自动脚本不得处理 `needs_source`、`candidate_only`、判断类、医学参数或安全边界。
- 写入后必须同步 `知识库/wiki索引.md`、`知识库/术语/术语索引.md`，追加 `platform-ops/log.md`，并运行链接/引用校验。

## 6. 单任务执行模板

每个任务开始前，DeepSeek 必须先写出以下结构：

```yaml
task_id:
user_input:
real_task_source: 林峰直接输入 / 仪表盘真实下一步 / 当前 Topic 待办
intent:
topic_target:
side_effect:
write_level:
recommended_skill:
recommended_script:
required_context_pack:
needs_confirmation:
fallback_to_agent:
reason:
```

然后给出 Context Pack：

```yaml
task_type:
required_files:
optional_files:
missing_files:
why_required:
why_optional:
stop_condition:
```

涉及历史结论、知识、医学参数、原始依据、源码借鉴、视觉证据时，还必须给 Evidence Pack：

```yaml
claim:
knowledge_type:
memory_type:
source_type:
source_path:
source_excerpt:
evidence_level:
confidence:
verification_status:
usage_scope:
can_ingest:
linked_topic:
related_entries:
```

## 7. 单任务通过标准

单个真实任务必须同时满足：

- Router 字段完整，副作用和写权限判断正确。
- Context Pack 覆盖任务所需文件，缺 required 文件时停止。
- 如需 Evidence Pack，claim 可追溯到源文件、JSONL、Topic 或研究卡。
- 写入动作符合 skill 的 `confirmation_rules`。
- 写入后跑对应校验脚本。
- 不读 `AGENT.md`，除非明确记录 fallback。
- 输出结果能被林峰直接用于实际工作。
- 任务结果写入 `pilot-report.md`。

## 8. 记录格式

每个任务完成后，追加到：

```text
智能体/贾维斯/runtime-v0.1/pilot-report.md
```

记录行格式：

```markdown
| # | 日期 | 输入 | Runtime 路由 | 结果 | 缺口 | 是否回退 |
|---|---|---|---|---|---|---|
```

若需要更详细证据，追加到：

```text
智能体/贾维斯/runtime-v0.1/gate5-real-task-results.md
```

每个任务详情格式：

```markdown
## Task N：<任务名>

input:

runtime_router:

context_pack:

evidence_pack:

actions_taken:

validation:

result:

gaps:

fallback:
```

## 9. 最终判定

### 可以判定 Gate 5 通过

必须同时满足：

- 连续 5 个真实任务通过。
- 0 个 P0/P1 失败。
- 0 个高风险误写。
- 0 个自动入库。
- 0 个 Topic 状态不一致。
- 0 个把 OpenViking 命中当事实。
- 0 个常规步骤必须读取 `AGENT.md`。
- 至少覆盖一次写入类任务。
- 至少覆盖一次知识萃取或明确说明知识链路尚未覆盖。

### 只能判定部分通过

出现以下情况时，只能写“Runtime-first 日常试点通过”，不能写“可完全替换 AGENT”：

- 5 个任务都偏只读。
- 没有知识萃取或知识入库场景。
- 没有 Topic 状态变更场景。
- 业务产出没有真实交付物。

### 必须判定失败

出现任何 P0/P1 回退触发器，Gate 5 失败。处理方式：

1. 停止继续计数。
2. 恢复 `AGENT.md v3.4` 作为日常入口。
3. 在 `pilot-report.md` 写明失败任务、失败原因、应重新研究对象。
4. 按 Re-Research Loop 更新研究卡、协议样例和 acceptance case。

## 10. DeepSeek 执行注意事项

- 不要为了通过测试而选择简单任务。
- 不要把“测试提示词”当真实任务。
- 不要在缺来源时补推论。
- 不要用 OpenViking 命中替代源文件。
- 不要因为用户说“继续”就猜 Topic；必须读仪表盘和快照定位。
- 不要自动把萃取结果入库。
- 不要修改 `AGENT.md`。
- 如果必须读 `AGENT.md`，先记录 fallback 原因，再读。

## 11. 建议给林峰的执行方式

让林峰直接把未来 5 个真实请求交给 DeepSeek，不要刻意设计验收句式。

DeepSeek 每完成 1 个任务后，先更新 `pilot-report.md`，再继续下一个任务。

第 5 个任务完成后，DeepSeek 才能更新 `acceptance-report.md` 的 Gate 5 状态。若覆盖不足，只能写“部分通过”，不能写“可替换”。
