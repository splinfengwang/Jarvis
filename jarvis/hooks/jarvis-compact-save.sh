#!/bin/bash
# Jarvis Runtime — PreCompact hook: prompt LLM to save state before compaction
# Reference: PUA PreCompact prompt pattern
set -euo pipefail

cat << 'EOF'
[PUA-COMPACT] [Jarvis — PreCompact State Checkpoint]

Context compaction is about to happen. You MUST immediately dump your Jarvis runtime state to ~/.jarvis/compact-state.md before compaction erases it.

Write the following to ~/.jarvis/compact-state.md (create ~/.jarvis/ if needed):

```markdown
# Jarvis State Dump — Compaction Checkpoint

## Timestamp
{current ISO timestamp}

## Active Topic
- topic_id:
- status:
- last_action:
- next_action:

## Router Output
- intent:
- topic_target:
- side_effect:
- recommended_skill:

## 已确认事实
- {list of facts confirmed this session}

## 待拍板
- {list of items waiting for user decision}

## 未解决问题
- {list of unresolved questions}

## Key Context
- {critical information that would be lost — file paths, decisions, parameters}
```

This is NOT optional. Compaction without state dump = losing Topic and Router state. The next session will restore from this file.

After writing, output: [Jarvis Checkpoint] State saved to ~/.jarvis/compact-state.md.
EOF

exit 0
