# Evidence Pack Spec

## 输出字段

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
id:
group:
title:
knowledge_layer:
target_path:
requires_separate_confirmation:
```

## 枚举

- `knowledge_type`: `fact` / `decision` / `preference` / `procedure` / `medical_candidate` / `design_rationale`
- `memory_type`: `semantic` / `procedural` / `episodic`
- `source_type`: `topic` / `source_file` / `session_jsonl` / `openviking_hit` / `confluence` / `image` / `research_card`
- `evidence_level`: `primary` / `secondary` / `recall_only` / `visual_intermediate`
- `verification_status`: `verified` / `needs_confirmation` / `needs_source` / `needs_review`
- `can_ingest`: `false` / `candidate_only` / `after_confirmation`
- `knowledge_layer`: `L1` / `L2` / `L3` / `L4` / `F`

## 样例

### 正常 1：事实

input: `AGENT.md v3.4 当前存在`

expected_output:

```yaml
claim: AGENT.md 当前版本为 v3.4。
knowledge_type: fact
memory_type: semantic
source_type: source_file
source_path: 智能体/贾维斯/AGENT.md
source_excerpt: "版本：v3.4"
evidence_level: primary
confidence: high
verification_status: verified
usage_scope: Jarvis runtime baseline
can_ingest: candidate_only
linked_topic: 贾维斯运行时架构迭代
related_entries: []
id: A1
group: A
title: AGENT.md v3.4
knowledge_layer: L1
target_path: 知识库/术语/AGENT.md v3.4.md
requires_separate_confirmation: false
```

### 正常 2：决策

input: `Claude Code 优先，Codex 第二优先级兼容`

expected_output:

```yaml
claim: Jarvis Runtime v0.1 以 Claude Code 为第一落地运行时，Codex 保持结构兼容。
knowledge_type: decision
memory_type: episodic
source_type: topic
source_path: platform-ops/topics/20260516_贾维斯运行时架构迭代/索引.md
source_excerpt: "运行时适配优先级：Claude Code 第一，Codex 第二"
evidence_level: primary
confidence: high
verification_status: verified
usage_scope: runtime implementation
can_ingest: after_confirmation
linked_topic: 贾维斯运行时架构迭代
related_entries: []
id: B1
group: B
title: Claude Code 优先
knowledge_layer: L3
target_path: null
requires_separate_confirmation: true
```

### 正常 3：偏好

input: `至少不能影响现有工作`

expected_output:

```yaml
claim: 第一版 Skill Pack 不得影响现有工作。
knowledge_type: preference
memory_type: semantic
source_type: topic
source_path: platform-ops/topics/20260516_贾维斯运行时架构迭代/2026-05-16 不影响现有工作原则.md
source_excerpt: "最小 Skill Pack 不得影响现有工作"
evidence_level: primary
confidence: high
verification_status: verified
usage_scope: runtime safety boundary
can_ingest: after_confirmation
linked_topic: 贾维斯运行时架构迭代
related_entries: []
id: A2
group: A
title: 不影响现有工作
knowledge_layer: L2
target_path: null
requires_separate_confirmation: true
```

### 正常 4：流程

input: `Topic 关闭不自动萃取`

expected_output:

```yaml
claim: Topic 关闭只进入待萃取状态，不自动执行知识萃取或入库。
knowledge_type: procedure
memory_type: procedural
source_type: research_card
source_path: 智能体/贾维斯/runtime-v0.1/research-cards/ByteRover.md
source_excerpt: "Topic 关闭只能转 pending extraction，不能自动萃取或入库。"
evidence_level: secondary
confidence: medium
verification_status: needs_confirmation
usage_scope: topic lifecycle
can_ingest: candidate_only
linked_topic: 贾维斯运行时架构迭代
related_entries:
  - 智能体/贾维斯/AGENT.md
id: B2
group: B
title: Topic 关闭不自动萃取
knowledge_layer: L2
target_path: null
requires_separate_confirmation: true
```

### 正常 5：源码借鉴

input: `Context Pack 受 Obsidian Copilot 和 Khoj 启发`

expected_output:

```yaml
claim: Context Pack 采用显式上下文打包和按需展开候选文件的设计。
knowledge_type: design_rationale
memory_type: semantic
source_type: research_card
source_path: 智能体/贾维斯/runtime-v0.1/research-cards/Obsidian-Copilot.md
source_excerpt: "映射为 Context Pack：任务需要哪些文件、为什么需要、缺什么就停止。"
evidence_level: secondary
confidence: medium
verification_status: verified
usage_scope: runtime protocol explanation
can_ingest: candidate_only
linked_topic: 贾维斯运行时架构迭代
related_entries:
  - 智能体/贾维斯/runtime-v0.1/research-cards/Khoj.md
id: B3
group: B
title: Context Pack 设计来源
knowledge_layer: L3
target_path: null
requires_separate_confirmation: true
```

### 失败 1：OpenViking 命中

input: `OpenViking 搜到某结论`

expected_output:

```yaml
claim: 待定。
knowledge_type: fact
memory_type: semantic
source_type: openviking_hit
source_path: viking://...
source_excerpt: 命中摘要
evidence_level: recall_only
confidence: low
verification_status: needs_source
usage_scope: recall clue only
can_ingest: false
linked_topic: null
related_entries: []
id: D1
group: D
title: OpenViking 命中
knowledge_layer: L4
target_path: null
requires_separate_confirmation: true
```

### 失败 2：缺原始 JSONL

input: `根据上次聊天萃取`

expected_output:

```yaml
claim: 待定。
knowledge_type: decision
memory_type: episodic
source_type: session_jsonl
source_path: null
source_excerpt: null
evidence_level: primary
confidence: low
verification_status: needs_source
usage_scope: extraction blocked
can_ingest: false
linked_topic: current_topic
related_entries: []
id: D2
group: D
title: 缺原始会话
knowledge_layer: L4
target_path: null
requires_separate_confirmation: true
```

### 失败 3：医学参数

input: `把这个医学参数入库`

expected_output:

```yaml
claim: 医学参数候选，需林峰确认。
knowledge_type: medical_candidate
memory_type: semantic
source_type: source_file
source_path: source_required
source_excerpt: source_required
evidence_level: primary
confidence: low
verification_status: needs_confirmation
usage_scope: candidate only, no clinical decision
can_ingest: false
linked_topic: current_topic
related_entries: []
id: C1
group: C
title: 医学参数候选
knowledge_layer: L4
target_path: null
requires_separate_confirmation: true
```

### 边界 1：视觉证据

input: `截图里按钮是灰色`

expected_output:

```yaml
claim: 截图中的目标按钮疑似灰色。
knowledge_type: fact
memory_type: episodic
source_type: image
source_path: image_path_required
source_excerpt: crop_or_visual_marker_required
evidence_level: visual_intermediate
confidence: medium
verification_status: needs_review
usage_scope: visual analysis only
can_ingest: false
linked_topic: current_topic
related_entries: []
id: C2
group: C
title: 视觉证据
knowledge_layer: L4
target_path: null
requires_separate_confirmation: true
```

### 边界 2：用户偏好

input: `我希望第一版保持 AGENT 文件水平`

expected_output:

```yaml
claim: 林峰希望第一版 Skill Pack 保持 AGENT.md v3.4 的工作水平。
knowledge_type: preference
memory_type: semantic
source_type: topic
source_path: platform-ops/topics/20260516_贾维斯运行时架构迭代/_上下文快照.md
source_excerpt: "第一版 Skill Pack 最好能保持现有 AGENT.md 文件水平"
evidence_level: primary
confidence: high
verification_status: verified
usage_scope: runtime scope decision
can_ingest: after_confirmation
linked_topic: 贾维斯运行时架构迭代
related_entries: []
id: B4
group: B
title: 保持 AGENT 水平
knowledge_layer: L3
target_path: null
requires_separate_confirmation: true
```
