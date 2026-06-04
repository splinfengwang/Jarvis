---
name: jarvis-roundtable
description: 发起多角色并行审查 — 从 Topic 中提取上下文，spawn 多个独立子 agent 各带不同 persona 独立分析，汇总后向用户汇报。用于"多角度看一下""拉个会讨论""圆桌审查"。
---

# jarvis-roundtable

## 定位

Roundtable 是 Jarvis 的多角色审查机制。与 BMAD 的 party mode（单一 LLM 扮演多角色）不同，Roundtable 利用 `task` 工具 spawn 真正的独立子 agent——每个带独立的上下文、独立的 persona 指令、独立分析后返回结构化结论。主 agent 收集所有结论后合成汇报。

trigger:
- "多角度看一下""多方视角审查"
- "拉个会讨论一下""圆桌讨论"
- "roundtable""review this topic from multiple angles"

non_trigger:
- 用户只想问一个问题、不涉及 Topic 审查
- 用户明确说"用 PM 视角看就行"（单一 persona，不需要 roundtable）

## 流程

### Step 0: Gating — 触发前检查

```
1. 定位当前活跃 Topic（读仪表盘）
   → 无活跃 Topic → 告知用户先建 Topic，转 jarvis-topic-create
   
2. 读 Topic 文件：索引.md + 讨论记录.md + _上下文快照.md
   → 总字数 < 500 字符 → 告知内容不足，建议先展开讨论
   → 总字数 >= 500 → 进入 Step 1
```

### Step 1: 选择 Persona

```
1. 调用 list_personas() 获取所有可用 persona
2. 展示列表（格式：icon + title + 一句话 role）
3. 推荐 2-3 个匹配当前 Topic 主题的 persona
4. 让用户确认或调整选择（选择哪些、是否加减）
5. 用户可临时指定不在列表中的角色（给出角色名 + 一句话审查视角）
```

推荐逻辑（简单关键词匹配，用户最终决定）：
- Topic 标题含"方案/设计/交互" → 推荐 design-reviewer + pm-analyst
- Topic 标题含"技术/架构/实现" → 推荐 technical-auditor + edge-case-hunter
- Topic 标题含"参数/医学/安全/临床" → 推荐 medical-safety
- 默认推荐 edge-case-hunter + pm-analyst

### Step 2: 准备子 Agent Prompt

```python
from jarvis.lib import load_persona, resolve_persona_prompt

# 为每个选中的 persona 生成独立的 sub-agent prompt
for name in selected_personas:
    persona = load_persona(name)
    # topic_summary = Topic 索引 + 讨论记录的核心摘要（≤500字）
    prompt = resolve_persona_prompt(persona, topic_summary)
```

Sub-agent prompt 包含：
- Persona 的 identity（你是谁）
- Persona 的 principles（怎么判断）
- Persona 的 analysis_lens（审什么维度）
- Persona 的 output_format（输出格式要求）
- Topic 内容摘要（待分析的内容）
- 约束：只分析、不写文件

### Step 3: Spawn 子 Agent（并行）

使用 `task` 工具，为每个 persona spawn 一个子 agent：

```
task(
    description="Roundtable: [persona name]",
    prompt="[resolve_persona_prompt 的输出]",
    tools=["read_file", "grep", "glob", "ls"]
)
```

- 每个子 agent 只给 `read_file / grep / glob / ls` 工具（只读）
- 子 agent 可以深入阅读 Topic 文件和相关引用文件
- 子 agent 不会看到其他 agent 的输出（独立上下文）
- 使用 `run_in_background=true` 并行执行

主 agent 等待所有子 agent 完成（或用 `wait` 收集结果）。

### Step 4: 异常处理

单个子 agent 出现以下情况时不中断整体流程：

| 情况 | 处理 |
|---|---|
| 超时 | 标注 `[未完成]`，跳过该 persona |
| 返回空 | 标注 `[无输出]`，可能该视角不适用 |
| 返回格式异常 | 保留原始输出，标注 `[格式异常]` |

至少有一个子 agent 成功时才进入 Step 5。全部失败时告知用户并建议减少 persona 数量重试。

### Step 5: 合成汇报

主 agent 将各子 agent 的输出合成为统一汇报：

```
## Roundtable 审查：[Topic 标题]

参与角色：pm-analyst (📋), design-reviewer (🎨), medical-safety (🏥)

### pm-analyst: 需求分析
[子 agent 的完整 output，保留其 output_format 结构]

### design-reviewer: 设计评审
[子 agent 的完整 output]

### medical-safety: 医学安全审查
[子 agent 的完整 output]

### 🔍 共识与分歧

**共识点:**
- [多个 agent 都指出的问题]

**分歧点:**
- [不同 agent 给出矛盾判断的地方]

**优先级建议:**
- [高优先级修复项，含来源 agent]
```

### Step 6 (可选): 交叉审阅

仅在用户要求或发现明显分歧时触发：

```
1. 主 agent 将各子 agent 的核心结论压缩为 ≤300 字摘要
2. 重新 spawn 每个子 agent，给：原结论 + 摘要 + "与你的分析是否有矛盾？"
3. 收集追加意见，更新汇报
```

### Step 7: 写入讨论记录

用户确认后，将 Roundtable 审查结果追加到 Topic/讨论记录.md：

```markdown
## [日期] Roundtable 审查

**参与角色**: [列表]
**审查范围**: [topic_summary 的前 100 字]

[审查汇报的 Markdown 内容]
```

写入前展示 diff preview，用户确认后写入。

## inputs
- 当前活跃 Topic 的索引.md、讨论记录.md、_上下文快照.md
- `list_personas()` 的 persona 列表
- 用户的 persona 选择

## outputs
- Roundtable 审查报告（Markdown）
- 追加到讨论记录（用户确认后）

## write_level
- `none`：Roundtable 本身只读，不直接写文件
- 写入讨论记录需用户确认，走 record_write

## allowed_tools (for主 agent orchestrating)
- `task` — 用于 spawn 子 agent
- `read_file` / `grep` / `ls` — 用于读取 Topic 文件
- `write_file` / `edit_file` — 仅在 Step 7 写入讨论记录时使用

## acceptance_cases
- Topic 内容充足，用户选 3 个 persona → 3 个子 agent 并行分析 → 合成汇报
- Topic 内容不足 → 拒绝，提示先展开讨论
- 无活跃 Topic → 转 topic-create
- 用户临时指定角色 → 不持久化 persona，直接作为 prompt 传入
- 1 个子 agent 超时 → 标注未完成，用剩余 2 个的结果继续
- 全部失败 → 告知用户重试
