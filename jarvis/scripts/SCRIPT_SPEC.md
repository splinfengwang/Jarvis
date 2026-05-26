# Topic Scripts Spec

> 状态：Jarvis Runtime v0.1 production candidate。当前目录已提供可执行脚本；所有写入脚本默认 dry-run，只有显式 `--write` 才落盘。

## 原则

1. 脚本只负责机械、格式敏感、可验证的动作。
2. 脚本默认 dry-run；真正写入必须显式传 `--write`。
3. 脚本不得修改 `AGENT.md`。
4. 脚本每次写入前输出计划，写入后输出校验结果。
5. 脚本失败时不做部分回滚假装成功；应停止并报告已修改和未修改文件。
6. 脚本不做内容判断；Topic Capsule、Evidence Pack、Context Pack 的内容由 workflow 决定，脚本只校验格式和同步状态。

## 第一批脚本

| 脚本 | 用途 | 默认模式 | 写入目标 |
|---|---|---|---|
| `create_topic.py` | 创建 Topic 骨架并生成仪表盘待追加行 | dry-run | `platform-ops/topics/`、仪表盘 |
| `update_topic_status.py` | 同步索引、快照、仪表盘状态 | dry-run | Topic 索引、快照、仪表盘 |
| `update_snapshot.py` | 更新快照的最后动作、下一步、未解决问题、关联会话 | dry-run | `_上下文快照.md` |
| `validate_dashboard.py` | 检查仪表盘表格列数、Topic 链接、状态值 | read-only | 无 |
| `validate_links.py` | 检查 Topic/业务文档/术语双链是否悬空 | read-only | 无 |
| `locate_session_jsonl.py` | 定位 Claude Code / Codex Desktop 原始会话记录 | read-only | 无 |
| `knowledge_link_stats.py` | 统计知识库和业务文档双链引用次数 | read-only | 无 |
| `append_operation_log.py` | 向 `platform-ops/log.md` 追加一条操作记录 | dry-run | `platform-ops/log.md` |
| `extract_evidence_pack.py` | 从 Topic 与源文件构建 Evidence Pack 和确认清单 | dry-run | Topic 目录下的候选输出文件 |
| `ingest_evidence_pack.py` | 将已确认的 L1 Evidence Pack 术语项写入知识库 | dry-run | `知识库/术语/`、知识索引 |
| `sync_followup.py` | 同步仪表盘跟进事项区的一条事项 | dry-run | `platform-ops/仪表盘.md` |
| `sync_topic_index.py` | 同步索引的状态、Next Action、关键产出和时间线 | dry-run | `索引.md` |
| `confluence_query.py` | 读取或搜索 Confluence 页面 | read-only | 无 |

## `create_topic.py`

建议接口：

```bash
python create_topic.py --title "主题简称" --scope "一句话描述" --date YYYYMMDD \
  --session-tool "Codex Desktop" --session-id "<thread/session id>" \
  --session-jsonl "<jsonl path or 待确认>" --session-cwd "$PWD" --session-date YYYY-MM-DD \
  --write
```

必须生成：

- `索引.md`
- `_上下文快照.md`
- `_准入检查单.md`
- `讨论记录.md`
- 仪表盘追加行预览
- `_上下文快照.md` 关联会话表行

校验：

- 目录名符合 `YYYYMMDD_主题简称`
- 四个骨架文件存在
- 关联会话表存在；JSONL 未定位时字段为 `待确认`，不能省略该行
- Topic 双链在表格中已转义
- 仪表盘未被整页重写

## `update_snapshot.py`

建议接口：

```bash
python update_snapshot.py --topic-dir <path> \
  --last-action "已发生事实" --next-action "下一步" --unresolved "待拍板" \
  --session-tool "Codex Desktop" --session-id "<thread/session id>" \
  --session-jsonl "<jsonl path or 待确认>" --session-cwd "$PWD" --session-date YYYY-MM-DD \
  --write
```

校验：

- 只追加或更新快照中的事实性条目。
- 关联会话行不存在时追加，已存在时不重复。
- Topic 创建、冻结、关闭都必须让 workflow 调用本脚本或等价步骤处理当前会话行。

## `update_topic_status.py`

建议接口：

```bash
python update_topic_status.py --topic-dir <path> --status paused --note "下一步说明" --write
```

状态只允许：

- `doing`
- `paused`
- `blocked`
- `pending_extraction`
- `done`

校验：

- `索引.md` frontmatter 为机器值
- 快照和仪表盘为展示值
- `blocked` 必须包含阻塞物和恢复条件

## `locate_session_jsonl.py`

建议接口：

```bash
python locate_session_jsonl.py --tool codex --cwd "$PWD" --date YYYY-MM-DD
python locate_session_jsonl.py --tool claude-code --cwd "$PWD"
```

输出：

- 精确命中：JSONL 路径
- 多候选：按修改时间倒序列候选
- 未命中：说明缺失，不伪造路径

## `knowledge_link_stats.py`

建议接口：

```bash
python knowledge_link_stats.py --vault-root . --scope 知识库 --scope 业务
```

输出：

- 扫描文件数。
- 已解析双链数。
- 未解析双链目标。
- 入链为 0 的知识库/业务文件清单。
- 每个文件的 incoming / outgoing 统计。

约束：

- 只读，不写入引用统计文件。
- 忽略 fenced code block 和 inline code 中的示例双链。
- 表格内 `\|` 链接按 Obsidian 显示名分隔符处理。

## `append_operation_log.py`

建议接口：

```bash
python append_operation_log.py --type topic --summary "创建 Topic: 主题简称" --write
```

校验：

- 默认 dry-run。
- 只追加一条日志行，不重写历史日志。
- 已存在同一行时不重复追加。

## `sync_followup.py`

建议接口：

```bash
python sync_followup.py --item "等待王涛经理盲审反馈" --window "2026-05-20 前" \
  --status "进行中" --action "收到反馈后汇总三方评分" --write
```

约束：

- 默认 dry-run。
- 同名事项更新原行，不重复追加。
- 若跟进事项区只有占位行，写入前替换占位行。

## `ingest_evidence_pack.py`

建议接口：

```bash
python ingest_evidence_pack.py --evidence-pack <json> --confirm-scope A \
  --topic-dir platform-ops/topics/YYYYMMDD_主题 --write
```

约束：

- 默认 dry-run。
- 只处理确认范围内的条目。
- 自动写入两类条目：
  - `knowledge_layer: L1` 且 `memory_type: semantic` 的术语项
  - `knowledge_layer: L2/L3/L4/F` 且 `target_path` 明确的业务文档项
- `needs_source`、`candidate_only`、医学参数、安全边界、以及 `target_path` 缺失的非 L1 项必须阻断或跳过。
- 写入后同步 `知识库/wiki索引.md`；L1 术语另同步 `知识库/术语/术语索引.md`。

## `sync_topic_index.py`

建议接口：

```bash
python sync_topic_index.py --topic-dir platform-ops/topics/YYYYMMDD_主题 \
  --status paused --next-action "等待反馈" \
  --key-output "形成阶段结论" --timeline "阶段冻结" --write
```

约束：

- 默认 dry-run。
- 同步 frontmatter status、正文阶段显示、Next Action。
- 自动确保 `## 关键产出` 和 `## 时间线` 存在。

## `confluence_query.py`

建议接口：

```bash
python confluence_query.py --mode validate-config
python confluence_query.py --mode read-page --page-id 12345
python confluence_query.py --mode search-text --query "COPD"
```

约束：

- 只读。
- 默认读取 `platform-ops/.confluence-cookie`。
- 401/403 明确报 cookie/权限问题。
- 404 明确报页面不存在。
- 其他错误只回报状态码，不重复重试。

## `extract_evidence_pack.py`

建议接口：

```bash
python extract_evidence_pack.py --topic-dir platform-ops/topics/YYYYMMDD_主题 \
  --source 业务/某域/某文档.md --session-jsonl <jsonl path> --write
```

输出：

- `_evidence-pack.json`
- `_萃取确认清单.md`
- 缺失来源清单

约束：

- 默认 dry-run。
- 只构建候选，不写知识库。
- A 组 L1 项要带 `title`、`knowledge_layer`、`target_path`，以便后续确认后自动入库。
- 判断类、医学类、缺来源类必须进入非自动组。

## 验收用例

第一批脚本已通过 fixture 验证：

1. 创建一个临时 Topic，验证四个文件和仪表盘追加行。
2. 创建、冻结、关闭都写入关联会话行。
3. 将临时 Topic 从 doing 改为 paused，再改为 pending_extraction。
4. 仪表盘存在表格管道符，验证不会破坏列数。
5. Codex Desktop 无精确 thread id 时，能列出候选而不是假装命中。
6. 有悬空双链时，`validate_links.py` 能报告但不自动修复。
7. `knowledge_link_stats.py` 能输出入链、出链、零引用文件和未解析链接统计。
8. `append_operation_log.py` 只追加一条操作日志。
9. `extract_evidence_pack.py` 能从 Topic 和源文件生成 Evidence Pack 与确认清单。
10. `ingest_evidence_pack.py` 只写入确认范围内可入库 L1 术语，并跳过缺来源和判断类条目。
11. `sync_followup.py` 能新增或更新跟进事项表格行。
12. `sync_topic_index.py` 能同步状态、关键产出和时间线。
13. `confluence_query.py` 能完成配置校验并提供明确错误口径。

验证入口：

```bash
python3 智能体/贾维斯/runtime-v0.1/tests/run_replacement_checks.py
```
