# Memory And Sources

## 三层信息模型

| 层 | 作用 | 可否单独作为事实 |
|---|---|---|
| OpenViking 语义记忆 | 召回线索、历史偏好、Topic 入口 | 否 |
| Obsidian / Topic / 知识库正文 | 深度知识层、工作记录、已确认知识 | 视状态而定 |
| 源文档 / Confluence / JSONL | 原始证据层 | 可作为证据，仍需按场景确认 |

## OpenViking 使用

需要历史上下文时：

1. 先 `memsearch(scope="memory")`。
2. 命中不足再 `memsearch(scope="project")`。
3. 只有跨项目或泛化长期偏好才扩大到 `scope="all"`。
4. 命中后用 `memread` 读取原文。

OpenViking 命中不能直接写成事实。事实判断必须回到源文件、Topic 文件、知识库正文、Confluence 原文或 JSONL 原始记录。

## Confluence 处理

Confluence 公司文档是源文档层之一。

默认入口与参数：

- 基础地址：`https://www.kf580.com/kd`
- 读页面：`GET /rest/api/content/{id}?expand=body.storage`
- 搜正文：`GET /rest/api/content/search?cql=text~"关键词" AND type=page`
- 搜标题：`GET /rest/api/content/search?cql=title~"关键词"`
- 搜评论：`GET /rest/api/content/search?cql=type=comment AND text~"关键词"`
- 认证：读取 `platform-ops/.confluence-cookie`，请求时作为 `Cookie` 头发送。

错误处理：

| 返回 | 处理 |
|---|---|
| 401 / 403 | 告知 Cookie 过期或权限不足 |
| 404 | 告知未找到页面，不假定 Cookie 问题 |
| 其他错误 | 告知错误码，不反复重试 |

## 降级策略

OpenViking 不可用时：

1. 读 `platform-ops/仪表盘.md` 获取当前状态。
2. 本地搜索 `知识库/`、`业务/`、`platform-ops/topics/`。
3. 说明“记忆检索暂不可用，基于当前对话和本地文件工作”。

不要暴露无关技术细节，只说明对当前判断的影响。

## 记忆写入 adapter

OpenViking 写入是可选 adapter，不是替代 Topic 文件的主记录。

触发时机：

| 时机 | 目标内容 |
|---|---|
| Topic 冻结 | 本轮事实、决策、偏好、下一步 |
| Topic 关闭 | final summary、待萃取状态、后续动作 |
| 稳定规则修复 | 可复用事实、明确偏好、后续承诺 |

执行规则：

1. 如果运行时提供 `memcommit`，优先调用 `memcommit`。
2. 有 `session_id` 时传入 `session_id`；没有时使用 durable-note fallback。
3. 如果 `memcommit` 不可用或失败，不得声称已写入 OpenViking。
4. 降级时必须保证 Topic 快照、讨论记录、仪表盘和 `platform-ops/log.md` 已同步。
5. 降级结果在 Pilot / Gate 5 记录中标为 `memory_commit: skipped_or_failed`。

## Connector 边界

吸收 AnythingLLM / Onyx / Open WebUI 等平台型项目的连接器意识，但不采用平台化路线。

可参考：

- 外部资料入口
- MCP / tool connector
- 权限和凭据隔离
- 错误处理

禁止：

- 把 Jarvis 迁移成 RAG 平台。
- 用 RAG-first 替代确认入库。
- 把向量召回结果当作事实。
- 引入多用户企业权限系统作为第一版目标。
