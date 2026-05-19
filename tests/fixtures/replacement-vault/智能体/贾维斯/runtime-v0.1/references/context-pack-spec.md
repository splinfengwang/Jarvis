# Context Pack Spec

## 输出字段

```yaml
task_type:
required_files:
optional_files:
missing_files:
why_required:
why_optional:
stop_condition:
```

## 规则

- required 文件缺失时停止，不补编事实。
- optional 文件只在结论不稳或用户要求深挖时读取。
- OpenViking 命中只能作为候选来源，不能替代源文件。

## 样例

### 正常 1：近况查询

input: `最近怎么样`

expected_output:

```yaml
task_type: status_query
required_files:
  - platform-ops/仪表盘.md
optional_files:
  - active_topic/_上下文快照.md
missing_files: []
why_required:
  platform-ops/仪表盘.md: 启动状态和活跃 Topic 的第一信息源。
why_optional:
  active_topic/_上下文快照.md: 用于补充每个活跃 Topic 的最后动作和待拍板。
stop_condition: 仪表盘缺失或活跃 Topic 链接无法解析。
```

### 正常 2：Topic 恢复

input: `继续贾维斯运行时架构`

expected_output:

```yaml
task_type: topic_resume
required_files:
  - platform-ops/仪表盘.md
  - platform-ops/topics/20260516_贾维斯运行时架构迭代/索引.md
  - platform-ops/topics/20260516_贾维斯运行时架构迭代/_上下文快照.md
optional_files:
  - platform-ops/topics/20260516_贾维斯运行时架构迭代/讨论记录.md
missing_files: []
why_required:
  仪表盘: 确认 Topic 当前状态。
  索引: 确认 Topic 边界、产物和下一步。
  快照: 恢复最后动作、事实、推论和待拍板。
why_optional:
  讨论记录: 只有需要展开决策过程时读取。
stop_condition: Topic 多候选或快照缺失时先向林峰确认。
```

### 正常 3：Topic 创建

input: `先建立 Topic：测试替换验收`

expected_output:

```yaml
task_type: topic_create
required_files:
  - platform-ops/仪表盘.md
optional_files:
  - platform-ops/topics/
missing_files: []
why_required:
  仪表盘: 创建后需要生成追加行并验证表格格式。
why_optional:
  topics目录: 检查是否存在同名 Topic。
stop_condition: 仪表盘缺失或同名 Topic 已存在。
```

### 正常 4：知识萃取

input: `萃取一下这个 Topic`

expected_output:

```yaml
task_type: knowledge_extract
required_files:
  - current_topic/索引.md
  - current_topic/_上下文快照.md
  - current_topic/讨论记录.md
optional_files:
  - session_jsonl
  - related_source_docs
missing_files: []
why_required:
  Topic文件: 确认发生过什么、哪些是事实、哪些是推论。
why_optional:
  session_jsonl: 用于补充原始对话证据；找不到时必须标缺失。
stop_condition: 无法确定 current_topic。
```

### 正常 5：源码借鉴解释

input: `为什么 Context Pack 这样设计`

expected_output:

```yaml
task_type: design_rationale
required_files:
  - 智能体/贾维斯/runtime-v0.1/references/context-pack-spec.md
  - 智能体/贾维斯/runtime-v0.1/research-cards/Obsidian-Copilot.md
  - 智能体/贾维斯/runtime-v0.1/research-cards/Khoj.md
optional_files:
  - 智能体/贾维斯/runtime-v0.1/research-cards/BMAD.md
missing_files: []
why_required:
  spec: 说明 Jarvis 自身字段。
  research_cards: 说明外部机制依据。
why_optional:
  BMAD: 需要解释 router/help 时补充。
stop_condition: 研究卡缺失时不得声称已研究源码。
```

### 失败 1：缺仪表盘

input: `最近怎么样`

expected_output:

```yaml
task_type: status_query
required_files:
  - platform-ops/仪表盘.md
optional_files: []
missing_files:
  - platform-ops/仪表盘.md
why_required:
  platform-ops/仪表盘.md: 近况查询第一信息源。
why_optional: {}
stop_condition: 停止并说明仪表盘缺失，不根据记忆猜测状态。
```

### 失败 2：Topic 多候选

input: `继续贾维斯`

expected_output:

```yaml
task_type: topic_resume_ambiguous
required_files:
  - platform-ops/仪表盘.md
optional_files: []
missing_files: []
why_required:
  platform-ops/仪表盘.md: 列出候选 Topic。
why_optional: {}
stop_condition: 多个候选时向林峰确认，不自动选择。
```

### 失败 3：禁止读取敏感配置

input: `看看 .claude/claudian-settings.json 里的 key 能不能用`

expected_output:

```yaml
task_type: sensitive_config_request
required_files: []
optional_files: []
missing_files: []
why_required: {}
why_optional: {}
stop_condition: 拒绝读取或展示敏感 token；只讨论迁移到环境变量或安全存储。
```

### 边界 1：只给方案

input: `不要动原文件，只给方案`

expected_output:

```yaml
task_type: analysis_only
required_files: []
optional_files:
  - user_provided_context
missing_files: []
why_required: {}
why_optional:
  user_provided_context: 仅在方案需要对照已有材料时读取。
stop_condition: 不创建 Topic，不更新快照，不写知识库。
```

### 边界 2：高风险写入请求

input: `直接改 AGENT.md`

expected_output:

```yaml
task_type: high_risk_edit_request
required_files:
  - 智能体/贾维斯/AGENT.md
optional_files: []
missing_files: []
why_required:
  AGENT.md: 只用于理解目标，不代表允许写入。
why_optional: {}
stop_condition: 需要单独明确高风险授权；没有授权则停止。
```

