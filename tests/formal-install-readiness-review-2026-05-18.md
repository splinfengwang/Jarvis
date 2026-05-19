# Jarvis Runtime v0.1 Formal Install Readiness Review - 2026-05-18

## 结论

**当前不能签字为“可正式安装、可完全替代并提升 `智能体/贾维斯/AGENT.md v3.4`”。**

原因不是脚本跑不通，而是仍有数个核心能力只停留在 reference / skill 文案层，尚未形成可稳定执行、可验收闭环的 workflow。换句话说：它已经是一个强候选包，但还不是“正式替代包”。

## 审查方法

本轮按三层交叉审查：

1. 逐条审查 `.claude/skills/jarvis-*`、`runtime-v0.1/references/`、`runtime-v0.1/scripts/` 的声明能力。
2. 对照 `智能体/贾维斯/AGENT.md v3.4` 的执行能力，而不是只对照概念摘要。
3. 回到 research cards 中引用的 GitHub pinned commit 源码，验证借鉴点是否真的存在于源码或官方文档中。

## 已验证可成立的借鉴点

### 1. BMAD 的 help/router 取向

已验证：BMAD 的 `bmad-help` 确实是“定位当前状态并推荐下一步”，强调只给相关项而不是倾倒全目录。  
源码依据：

- `bmad-help` 的 purpose / desired outcomes 明确写了“know what to do next”“don't dump the entire catalog”。  
  Source: [BMAD bmad-help](https://github.com/bmad-code-org/BMAD-METHOD/blob/5090cfb09617eeb9c5fb547d4d10529d9886adcd/src/core-skills/bmad-help/SKILL.md)

结论：`jarvis-help` 借鉴这个方向是合理的。

### 2. Obsidian Copilot 的上下文显式装载

已验证：Project mode 确实预加载项目上下文；context-and-mentions 也明确支持 active note、selected text、`@note`、`@folder`、`@URL` 这些显式上下文来源。  
源码/文档依据：

- [projects.md](https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/docs/projects.md)
- [context-and-mentions.md](https://github.com/logancyang/obsidian-copilot/blob/ba378e838953a9594a8116fea1d28fc9c5c187a6/docs/context-and-mentions.md)

结论：Context Pack 的 `required/optional/why_required/stop_condition` 方向是有源码支撑的。

### 3. Khoj 的“更多上下文”展开

已验证：Khoj 的 similar view 确实提供 `More context` / `Less context` 展开，不是一次性把全文都塞给模型。  
源码依据：

- [similar_view.ts](https://github.com/khoj-ai/khoj/blob/9258f57dceab19d52a1a0bdac54eb38576c29187/src/interface/obsidian/src/similar_view.ts)

结论：把多文档候选放进 optional context，而不是默认全读，这个借鉴是成立的。

### 4. ByteRover 的 runtime sidecar 信号

已验证：ByteRover 源码明确把 runtime signals 放到 sidecar，而不是共享 markdown frontmatter，理由是避免每次查询污染内容并制造 merge conflict。  
源码依据：

- [runtime-signals-schema.ts](https://github.com/campfirein/byterover-cli/blob/93f2514378c114a5293b22f6e7bf5a029078093d/src/server/core/domain/knowledge/runtime-signals-schema.ts)

结论：Jarvis 把状态信号、访问统计与知识正文分离，这个借鉴是成立的。

### 5. RegionFocus 的中间视觉证据

已验证：README 明确提到 debug 会保存 intermediate step images，例如 stars、zoom-ins 和投影回原图的结果。  
源码依据：

- [RegionFocus README](https://github.com/tiangeluo/RegionFocus/blob/f69575db87a7402cf4b859f709eb51e1a3ff9b3e/README.md)

结论：把视觉/OCR claim 降为证据链而不是直接事实，这个借鉴是成立的。

### 6. AnythingLLM 的技能白名单/可用性边界

已验证：AnythingLLM 确实有 agent skill whitelist endpoint 和 tool availability 检查入口。  
源码依据：

- [agentSkillWhitelist.js](https://github.com/Mintplex-Labs/anything-llm/blob/b1e5b6f961ed88c6d0f6f55186f4734ed3cd9439/server/endpoints/agentSkillWhitelist.js)

结论：用 settings + skill write_level 做能力白名单，这个方向是合理的。

## 源码复核更新

### 已处理 - PlugMem research card 已恢复到可复核源码源

此前 research card 使用了错误仓库地址。现已确认可复核源为：

- repo: `TIMAN-group/PlugMem`
- commit: `317f1fc1902f32a64a5a043f6e46205cce58b05d`

已复核：

- `README.md`：三类记忆 `semantic / procedural / episodic`
- `openclaw-plugmem-plugin/src/config.ts`：`defaultGraphId` vs `sharedReadGraphIds`
- `tests/test_api_memories.py`：三类 memory 插入与 `session_id` stamping
- `tests/test_api_retrieval.py`：retrieve/reason/consolidate、recall audit、session timeline
- `src/memory_structuring/structuring_inference.py`：semantic / procedural structuring 分离

对应汇总见：

- [research-card-source-review-2026-05-18.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/tests/research-card-source-review-2026-05-18.md:1)

结论：**PlugMem 不再是“仓库不可复核”型外部阻塞。**

## 仍然阻止正式替代的本地缺口

### 已处理 - `jarvis-knowledge-extract` 已补可执行萃取实现

已新增：

- [extract_evidence_pack.py](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/scripts/extract_evidence_pack.py:1)
- `_evidence-pack.json` / `_萃取确认清单.md` fixture 生成验证

当前状态：**已从“无实现”提升为“有实现但候选质量仍待真实任务验证”**。

### 已处理 - 跟进事项管理与碎片分流已补成 workflow

`AGENT.md` 不只是有 Topic 创建/冻结/关闭，还包括：

- 讨论漂移检测，见 [AGENT.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:258)
- 跟进事项管理与碎片信息分流，见 [AGENT.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:886)
- 近况查询要覆盖待萃取 Topic、跟进事项、风险阻塞，见 [AGENT.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:244) 和 [1032](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:1032)

runtime 当前已补：

- [jarvis-followup-sync](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/.claude/skills/jarvis-followup-sync/SKILL.md:1)
- [sync_followup.py](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/scripts/sync_followup.py:1)
- [jarvis-fragment-triage](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/.claude/skills/jarvis-fragment-triage/SKILL.md:1)
- [conversation-governance.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/references/conversation-governance.md:1)

但仍缺：

- 更深的自动化漂移记忆与跨 Topic 统计

结论：**Topic 运维已从“无 workflow”提升到“有治理 workflow”，但仍未达到 `AGENT.md` 全量治理水平。**

### 已处理 - 状态同步脚本已补 `索引.md` 关键产出/时间线同步

已新增 [sync_topic_index.py](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/scripts/sync_topic_index.py:1)，并把 Topic 冻结/关闭 skill 接到索引同步。

当前状态：**已从“只改 frontmatter”提升为“可同步状态、Next Action、关键产出、时间线”**。

### P1 - 知识入库自动化能力仍然只覆盖 L1 semantic

`jarvis-knowledge-ingest` 已经被我收紧，不再假装全自动。现在它明确：

- 自动脚本只处理 `L1 + semantic`
- 其他条目只能出人工入库计划

见 [jarvis-knowledge-ingest](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/.claude/skills/jarvis-knowledge-ingest/SKILL.md:43)。

对应脚本 `ingest_evidence_pack.py` 也确实只接受：

- `knowledge_type == "L1"`
- `memory_type == "semantic"`

见 [ingest_evidence_pack.py](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/scripts/ingest_evidence_pack.py:105)。

这比原 `AGENT.md` 的 L1-L4 / F 全域入账能力更窄，原规程见 [AGENT.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:866)。

结论：**这一项是“安全收缩”，不是“能力等价”。**

### 已处理 - Confluence 已补只读可执行链路

`AGENT.md` 里 Confluence 有：

- 基础地址
- 读页面 API
- 搜正文/搜标题/搜评论 API
- Cookie 文件位置
- 401/403/404 错误处理

见 [AGENT.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:135)。

runtime 现在已补：

- [jarvis-confluence-read](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/.claude/skills/jarvis-confluence-read/SKILL.md:1)
- [confluence_query.py](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/scripts/confluence_query.py:1)
- fixture `validate-config` 校验

结论：**已从“规则回填”提升为“只读可执行链路”，但真实在线读取仍待验证。**

### 已处理 - 知识应用反馈已补 workflow

原规程要求：

- 引用待确认知识时要显式标注
- 应用后冲突/过期/待确认要回写
- 高频应用但未确认的知识要进入跟进事项

见 [AGENT.md](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:423) 和 [481](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/AGENT.md:481)。

runtime 已补：

- [jarvis-knowledge-feedback](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/.claude/skills/jarvis-knowledge-feedback/SKILL.md:1)
- [record_knowledge_feedback.py](/Users/wanglinfeng/oc-local/KF580业务/KF580业务/智能体/贾维斯/runtime-v0.1/scripts/record_knowledge_feedback.py:1)

当前状态：**应用反馈已可回写知识条目并同步索引状态，但“高频未确认知识自动升跟进事项”仍需真实任务策略验证。**

## 为什么不能说“可正式安装”

正式安装不是“脚本通过 + 文档齐全”，而是至少满足这三条：

1. 关键高频流程有可稳定执行的 workflow，不靠模型临场自由发挥。
2. 相对 `AGENT.md` 没有把长期运维能力降级成“以后再补”。
3. 外部借鉴的源码依据可复核，不是 research card 自述。

当前 v0.1 还没有同时满足这三条。

## 当前可以怎么定性

更准确的定性是：

- **可运行候选**
- **可灰度安装做试点**
- **不能正式替代 `AGENT.md v3.4`**

## 建议的正式替代门槛

至少补完以下几项，才适合重新评审“正式安装”：

1. 扩展知识入库自动化到 `L1-L4/F` 的明确执行策略，降低当前只支持 `L1 semantic` 的收缩幅度。
2. 在真实任务里验证 Confluence 读取、知识萃取、知识入库、知识反馈、`memcommit` 可用性。
3. 视真实任务结果决定是否需要把“高频未确认知识 -> 跟进事项”做成自动规则，而不是仅靠 skill 判断。
