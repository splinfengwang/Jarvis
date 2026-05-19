# Conversation Governance

## 目的

处理两类高频治理问题：

1. 当前对话是否已经漂移出当前 Topic。
2. 用户给出的碎片信息应进入哪条轨道。

## 漂移检测

当存在 current Topic 时，比较新输入与 Topic 的一句话描述、当前下一步、最近关键产出。

规则：

1. 连续 2 条用户消息与当前 Topic 无关，才触发漂移提醒。
2. 只是一条临时插问，不立即触发切换。
3. 用户明确说“切”“换个话题”“先存一下”时，直接进入切换流程。
4. 触发漂移时，输出三选一建议：
   - 继续当前 Topic
   - 先冻结当前 Topic，再开新 Topic
   - 只是补一条跟进事项，不必切 Topic

## 碎片输入分流

碎片信息默认分到以下轨道之一：

| 轨道 | 特征 | 动作 |
|---|---|---|
| followup | 有时间窗口、责任人、明确下一步 | `jarvis-followup-sync` |
| knowledge_candidate | 新术语、规则、定义、判断依据 | 留在当前 Topic 或后续进入萃取 |
| topic_switch | 明确新命题，且与当前 Topic 无关 | 先冻结再切换或新建 Topic |
| status_update | 明确状态变化 | `jarvis-topic-freeze` / `jarvis-topic-close` / `update_topic_status.py` |
| quick_context | 只是补充背景，没有独立动作 | 仅补充上下文，不写入 |

## 输出协议

```yaml
fragment_type:
current_topic_relation:
recommended_action:
needs_freeze:
needs_followup:
needs_topic_create:
reason:
```

## 约束

- 只有 followup / status_update / topic_switch 才默认涉及写入建议。
- 没有明确下一步动作的碎片信息，不写入跟进事项区。
- 漂移提醒不等于强制切换；最终由林峰拍板。
