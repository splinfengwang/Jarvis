# Router Spec

## 输出字段

```yaml
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

## 枚举

- `side_effect`: `none` / `read_only` / `record_write` / `content_write` / `high_risk_write`
- `write_level`: `none` / `dry_run` / `write_after_confirmation` / `high_risk_explicit_confirmation`
- `fallback_to_agent`: `false` / `true`

## 样例

### 正常 1：近况查询

input: `最近怎么样`

expected_output:

```yaml
intent: status_query
topic_target: null
side_effect: read_only
write_level: none
recommended_skill: jarvis-status
recommended_script: null
required_context_pack: status_context
needs_confirmation: false
fallback_to_agent: false
reason: 需要读取仪表盘和活跃 Topic 快照；不需要写入。
```

### 正常 2：Topic 恢复

input: `继续贾维斯运行时架构`

expected_output:

```yaml
intent: topic_resume
topic_target: 贾维斯运行时架构迭代
side_effect: read_only
write_level: none
recommended_skill: jarvis-topic-resume
recommended_script: null
required_context_pack: topic_resume_context
needs_confirmation: false
fallback_to_agent: false
reason: 用户给出明确恢复目标，先读索引和快照。
```

### 正常 3：Topic 创建

input: `先建立 Topic：测试替换验收`

expected_output:

```yaml
intent: topic_create
topic_target: 测试替换验收
side_effect: record_write
write_level: write_after_confirmation
recommended_skill: jarvis-topic-create
recommended_script: create_topic.py
required_context_pack: topic_create_context
needs_confirmation: false
fallback_to_agent: false
reason: 用户已明确要求建立 Topic；脚本仍先输出 plan/diff preview，若标题、范围、目录名和仪表盘行无歧义，可同轮 --write。
```

### 正常 4：Topic 冻结

input: `这个先存一下`

expected_output:

```yaml
intent: topic_freeze
topic_target: current_topic
side_effect: record_write
write_level: write_after_confirmation
recommended_skill: jarvis-topic-freeze
recommended_script: update_topic_status.py
required_context_pack: topic_current_context
needs_confirmation: false
fallback_to_agent: false
reason: 冻结只记录已发生事实和下一步，不自动萃取。
```

### 正常 5：Topic 关闭

input: `这个 Topic 收一下`

expected_output:

```yaml
intent: topic_close
topic_target: current_topic
side_effect: record_write
write_level: write_after_confirmation
recommended_skill: jarvis-topic-close
recommended_script: update_topic_status.py
required_context_pack: topic_current_context
needs_confirmation: false
fallback_to_agent: false
reason: Topic 关闭只同步状态到 pending_extraction 并列出待萃取清单，不自动萃取或入库。
```

### 正常 6：知识萃取

input: `萃取一下这个 Topic`

expected_output:

```yaml
intent: knowledge_extract
topic_target: current_topic
side_effect: read_only
write_level: none
recommended_skill: jarvis-knowledge-extract
recommended_script: locate_session_jsonl.py
required_context_pack: extraction_context
needs_confirmation: false
fallback_to_agent: false
reason: 萃取先生成 Evidence Pack 和确认清单，不自动入库。
```

### 失败 1：直接改 AGENT

input: `直接改 AGENT.md`

expected_output:

```yaml
intent: high_risk_edit_request
topic_target: null
side_effect: high_risk_write
write_level: high_risk_explicit_confirmation
recommended_skill: null
recommended_script: null
required_context_pack: null
needs_confirmation: true
fallback_to_agent: false
reason: 修改 AGENT.md 是高风险写入，必须单独明确确认；runtime 默认拒绝直接执行。
```

### 失败 2：禁止写入

input: `不要动原文件，只给方案`

expected_output:

```yaml
intent: analysis_only
topic_target: null
side_effect: none
write_level: none
recommended_skill: null
recommended_script: null
required_context_pack: minimal_context
needs_confirmation: false
fallback_to_agent: false
reason: 用户明确禁止写文件，不能更新 Topic、仪表盘或知识库。
```

### 失败 3：自动入库诱导

input: `把刚才所有结论都入库`

expected_output:

```yaml
intent: knowledge_ingest_request
topic_target: current_topic
side_effect: content_write
write_level: write_after_confirmation
recommended_skill: jarvis-knowledge-ingest
recommended_script: null
required_context_pack: evidence_pack_context
needs_confirmation: true
fallback_to_agent: false
reason: 入库必须有确认范围和 Evidence Pack；不能把所有结论自动写入。
```

### 边界 1：模糊继续

input: `继续上次那个`

expected_output:

```yaml
intent: topic_resume_ambiguous
topic_target: null
side_effect: read_only
write_level: none
recommended_skill: jarvis-status
recommended_script: null
required_context_pack: status_context
needs_confirmation: true
fallback_to_agent: false
reason: 目标 Topic 不明确，先读仪表盘列候选，不猜测。
```

### 边界 2：外部 adapter

input: `把 DeepSeek 接到 Codex 里面试试`

expected_output:

```yaml
intent: adapter_setup_request
topic_target: null
side_effect: high_risk_write
write_level: high_risk_explicit_confirmation
recommended_skill: jarvis-help
recommended_script: null
required_context_pack: adapter_context
needs_confirmation: true
fallback_to_agent: false
reason: 模型/provider 配置涉及凭据和运行时边界，第一期只给 adapter 方案，不直接改配置。
```
