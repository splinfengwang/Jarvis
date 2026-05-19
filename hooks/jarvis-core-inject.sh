#!/bin/bash
# Jarvis Runtime — SessionStart hook: inject JARVIS_CORE.md via additionalContext
# Reference: PUA session-restore.sh pattern
set -euo pipefail

# Resolve jarvis home from hook's own location (works through symlinks)
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}" 2>/dev/null || readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")" && pwd)"
JARVIS_HOME="$(dirname "$SCRIPT_DIR")"
CORE_PATH="${JARVIS_HOME}/core/JARVIS_CORE.md"
COMPACT_STATE="${HOME}/.jarvis/compact-state.md"

escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

context_parts=""

# ── Core 注入 ──
if [ -f "$CORE_PATH" ]; then
    CORE_CONTENT=$(cat "$CORE_PATH")
    context_parts="<JARVIS_CORE>
[Jarvis Runtime Core — Behavioral Baseline]

You are Jarvis, the user's long-term work assistant. The following behavioral baseline overrides your default behavior for ALL tasks in this session.

${CORE_CONTENT}

This Core is injected via SessionStart hook. It is always present in your context. Follow it strictly.
</JARVIS_CORE>"
fi

# ── Compaction 状态恢复 ──
if [ -f "$COMPACT_STATE" ]; then
    if [ "$(uname)" = "Darwin" ]; then
        age=$(( $(date +%s) - $(stat -f %m "$COMPACT_STATE") ))
    else
        age=$(( $(date +%s) - $(stat -c %Y "$COMPACT_STATE") ))
    fi

    if [ "$age" -le 7200 ]; then
        STATE_CONTENT=$(cat "$COMPACT_STATE")
        STATE_ESCAPED=$(escape_for_json "$STATE_CONTENT")
        context_parts="${context_parts}

[Jarvis State Recovery — Previous session state saved before compaction]
${STATE_CONTENT}
Restore: current Topic, Router output, confirmed facts, pending decisions from the saved state above."
    fi
fi

# ── 输出 ──
if [ -z "$context_parts" ]; then
    exit 0
fi

ESCAPED=$(escape_for_json "$context_parts")
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$ESCAPED"

exit 0
