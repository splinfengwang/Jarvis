---
name: jarvis-persona-create
description: 引导用户创建自定义审查角色 (persona)。用于"新建一个审查角色""定义一个审查员""创建 persona"。借鉴 BMAD 的 persona 设计技巧，引导用户写出高质量的审查角色定义。
---

# jarvis-persona-create

## 定位

Jarvis 内置了 5 个审查角色（pm-analyst、design-reviewer、edge-case-hunter、technical-auditor、medical-safety）。用户可以通过 `jarvis.yaml` 的 `personas:` 段追加项目级自定义角色，或在 `jarvis/personas/` 目录创建框架级角色。

本 skill 引导用户完成 persona 的创建过程，借鉴 BMAD 的 persona 设计技巧：
- 原则不是"要做什么"，而是"如何判断"
- identity 给出具体经验，不给抽象标签
- 一个 persona 只负责一个判断维度
- `analysis_lens` 是具体的审查切入点，不是笼统的方向

## 流程

### Step 1: 确认角色名和审查目标

先确认两件事：
1. **角色名**（内部标识，小写英文+连字符，如 `compliance-auditor`）
2. **审查目标**（一句话：这个角色审什么？）

```python
from jarvis.lib import load_persona

# Check if name already exists
existing = load_persona(name)
if existing and existing.source == "builtin":
    # Can still override at project level, warn user
```

若用户只说了笼统的意图（如"帮我审查方案"），先追问具体审查维度，避免创建过于宽泛的 persona。

### Step 2: 构建 identity — 避免抽象标签

引导用户给出具体的经验和领域知识：

**差的 identity**："你是资深方案审查员"
**好的 identity**："你是资深产品方案审查员，8 年以上 B2B 医疗产品经验。擅长从临床场景出发发现方案与用户实际需求之间的差距。"

询问用户：
- 这个角色有什么具体的领域经验？（年限、行业、产品类型）
- 他/她擅长发现什么样的问题？
- 有没有特别熟悉的标准、规范或方法论？

### Step 3: 构建 analysis_lens — 具体审查维度

这是 persona 的核心。引导用户列出 3-6 个**具体的审查维度**：

**差的维度**："检查方案是否完整"
**好的维度**："检查方案中每个关键医学参数是否有明确的来源引用（文献/指南/知识库条目），标注验证状态"

引导技巧：
- 追问"你希望这个角色看到方案时，第一个检查什么？第二呢？"
- 每个维度应该是可操作的："检查 X 是否 Y"
- 维度之间应该互补，不重叠
- 每次只列 1 个维度，确认后继续下一个，最多 6 个

### Step 4: 提炼 principles — 如何判断

引导用户把原则写成"如何判断"的行为指引：

**差的原则**："确保安全"
**好的原则**："存疑时默认保守，不替用户做安全决策"、"每个安全参数必须附验证状态标注"

引导技巧：
- "如果这个角色发现一个参数没有标注来源，他应该怎么做？"
- "什么情况下这个角色会说'需要更多信息'而不是'方案有问题'？"
- 3-4 条为宜，每条一行

### Step 5: 生成 output_format — 推荐结构化模板

根据审查目标推荐输出格式。标准模板如下（可按需调整）：

```markdown
## [角色名]审查

### [核心发现 1]
**具体问题:** [描述]
**建议:** [改进方案]

### [核心发现 2]
...

### 综合结论
该方案在 [审查维度] 方面：[安全/有保留/需关注]
```

对用户说："这是推荐的结构化输出格式，需要调整吗？"

### Step 6: 预览 + 确认 + 写入

输出完整的 persona YAML 预览：

```yaml
personas:
  [name]:
    title: [用户确认的]
    icon: [emoji]
    role: [一句话角色定位]
    identity: |
      [多行身份描述]
    principles:
      - [原则 1]
      - [原则 2]
    analysis_lens:
      - [维度 1]
      - [维度 2]
    output_format: |
      [输出格式]
```

用户确认后，使用 `register_persona()` 写入 `jarvis.yaml` 的 `personas:` 段：

```python
from jarvis.lib import register_persona

ok = register_persona(
    root, name,
    title=title,
    icon=icon,
    role=role,
    identity=identity,
    principles=principles,
    analysis_lens=analysis_lens,
    output_format=output_format,
)
if not ok:
    # jarvis.yaml missing
    pass
```

写入后读回验证 `load_persona(name)` 返回正常。

## inputs
- 用户对审查角色的需求描述
- `jarvis.lib` 的 `load_persona()` / `list_personas()` / `register_persona()`
- 5 个内置 persona 的定义（作为格式参考，可展示给用户）

## outputs
- 完整的 persona YAML 定义
- 写入 `jarvis.yaml` 的 `personas:` 段

## write_level
- `content_write`：修改 `jarvis.yaml` 属于内容性写入，必须先提案、用户确认后执行

## confirmation_rules
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 每步只确认 1-2 个决策点，不要一次塞所有字段
- 如果用户已经足够具体（如"需要 GDPR 合规审查员，检查数据是否加密…"），直接从第 3 步开始，不需要从头引导
- 写入后读回验证

## fallback_rules
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- `jarvis.yaml` 不存在时停止
- 写入失败时告知原因
