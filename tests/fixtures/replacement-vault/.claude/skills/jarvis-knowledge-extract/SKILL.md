---
name: jarvis-knowledge-extract
description: 从 Topic 或会话中生成 Evidence Pack 和确认清单。用于“萃取一下这个 Topic”“整理可入库知识”。不自动入库。
---

# jarvis-knowledge-extract

trigger:
- “萃取一下这个 Topic”
- “整理一下可入库知识”
- “把这个话题提炼一下”

non_trigger:
- 用户直接确认某组入库时，转 `jarvis-knowledge-ingest`。
- 没有 Topic 或来源时，不继续抽象。

inputs:
- Topic 索引、快照、讨论记录。
- 可选 JSONL 原始会话。
- 相关源文件。

outputs:
- Evidence Pack 列表。
- 确认清单。
- 缺失来源清单。
- 不入库声明。

required_references:
- `智能体/贾维斯/runtime-v0.1/references/evidence-pack-spec.md`
- `智能体/贾维斯/runtime-v0.1/references/knowledge-extraction.md`

on_demand_references:
- `智能体/贾维斯/runtime-v0.1/research-cards/PlugMem.md`
- `智能体/贾维斯/runtime-v0.1/research-cards/ByteRover.md`
- 仅在解释 Evidence Pack 来源、发生证据追溯失败或修改萃取协议时读取。

allowed_scripts:
- `智能体/贾维斯/runtime-v0.1/scripts/extract_evidence_pack.py`
- `智能体/贾维斯/runtime-v0.1/scripts/locate_session_jsonl.py`
- `智能体/贾维斯/runtime-v0.1/scripts/validate_links.py`
- `智能体/贾维斯/runtime-v0.1/scripts/knowledge_link_stats.py`

write_level:
- none

confirmation_rules:
- 只生成候选，不写知识库。
- 医学参数、判断类、产品承诺必须标为需确认。
- 若调用脚本，默认只生成 `_evidence-pack.json` 和 `_萃取确认清单.md` 的预览；不自动进入入库。

fallback_rules:
- JSONL 找不到时标缺失，不伪造原始会话路径。
- 来源不可追溯的 claim 不进入确认清单。

acceptance_cases:
- “萃取一下这个 Topic” -> 输出 Evidence Pack 和确认清单。
- 缺 JSONL -> 标 `needs_source`。
- OpenViking 命中 -> `recall_only`，不可入库。
- 产出的 A 组 L1 术语项可在后续确认后被 `ingest_evidence_pack.py` 自动写入。
