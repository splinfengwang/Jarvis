#!/bin/bash
# Jarvis Runtime — SessionStart hook: inject JARVIS_CORE.md via additionalContext
# Supports plugin injection and path config mapping from jarvis.yaml
set -eo pipefail  # Note: NO -u — project environment may lack some vars in VSCode extension context

# Resolve jarvis home from hook's own location (works through symlinks)
# Supports both jarvis/hooks/ (legacy symlink) and adapters/claude/hooks/ (canonical)
# macOS: realpath/readlink -f not available by default — use python3 os.path.realpath as fallback
_hook_file="${BASH_SOURCE[0]}"
_hook_real="$([ -x /usr/bin/realpath ] && /usr/bin/realpath "$_hook_file" 2>/dev/null || true)"
[ -z "$_hook_real" ] && _hook_real="$(readlink -f "$_hook_file" 2>/dev/null || true)"
[ -z "$_hook_real" ] && _hook_real="$(python3 -c "import os; print(os.path.realpath('$_hook_file'))" 2>/dev/null || echo "$_hook_file")"
SCRIPT_DIR="$(cd "$(dirname "$_hook_real")" && pwd)"

# JARVIS_HOME is the jarvis/ package dir. Script lives at adapters/claude/hooks/ or jarvis/hooks/.
# From adapters/claude/hooks/: go up 3 levels then into jarvis/
# From jarvis/hooks/ (legacy symlink): go up 1 level
if [[ "$SCRIPT_DIR" == *"/adapters/"* ]]; then
    JARVIS_HOME="$(cd "$SCRIPT_DIR/../../../jarvis" && pwd)"
else
    JARVIS_HOME="$(dirname "$SCRIPT_DIR")"
fi
CORE_PATH="${JARVIS_HOME}/core/JARVIS_CORE.md"
COMPACT_STATE="${HOME}/.jarvis/compact-state.md"
JARVIS_YAML="${PWD}/jarvis.yaml"

# Save current session ID for locate_session_jsonl.py --session-id
mkdir -p "${HOME}/.jarvis" 2>/dev/null || true
# 获取当前会话 ID — SessionStart 时最新 transcript 就是当前会话
SESSION_ID=$(ls -t "${HOME}/.claude/transcripts/ses_"*.jsonl 2>/dev/null | head -1 | xargs basename | sed 's/ses_//;s/\.jsonl//')
# 兜底: 环境变量（极少情况）
[ -z "$SESSION_ID" ] && SESSION_ID="${CLAUDE_SESSION_ID:-${CODE_SESSION_ID:-}}"
[ -n "$SESSION_ID" ] && (echo "$SESSION_ID" > "${HOME}/.jarvis/current-session" 2>/dev/null || true)

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

# ── Core 注入 (plugin injection + path config) ──
if [ -f "$CORE_PATH" ]; then
    CORE_CONTENT=$(cat "$CORE_PATH")

    # Plugin injection: replace {{PLUGIN:NAME}} placeholders with plugin module content
    # Path config injection: append semantic→actual path mapping
    PLUGIN_RESOLVER="${JARVIS_HOME}/core/plugin_resolver.py"
    SNAPSHOT_SCRIPT="${JARVIS_HOME}/core/snapshot.py"
    if [ -f "$JARVIS_YAML" ] && [ -f "$PLUGIN_RESOLVER" ] && command -v python3 &>/dev/null; then
        # Step 1: Resolve plugins and path config
        CORE_CONTENT=$(python3 "$PLUGIN_RESOLVER" "$JARVIS_YAML" "$CORE_CONTENT" "$JARVIS_HOME")

        # Step 2: Generate knowledge snapshot from the resolved paths
        # Extract paths from YAML and pass to snapshot script
        SNAPSHOT_JSON=$(python3 -c "
import sys, json
# Read jarvis yaml to extract semantic paths from either paths: or core:
paths = {}
section = None
with open('$JARVIS_YAML') as f:
    for line in f:
        s = line.rstrip()
        stripped = s.strip()
        if stripped in ('paths:', 'core:'):
            section = stripped[:-1]
            continue
        if section and ':' in s and line.startswith('  '):
            k, v = s.split(':', 1)
            paths[k.strip()] = v.strip().strip(\"'\").strip('\"')
        elif section and stripped and not line.startswith('  '):
            section = None
if 'knowledge_base' not in paths and 'wiki_index' in paths:
    import os
    paths['knowledge_base'] = os.path.dirname(paths['wiki_index'])
if 'terms_dir' not in paths and 'terms_index' in paths:
    import os
    paths['terms_dir'] = os.path.dirname(paths['terms_index'])
if 'ops_dir' not in paths and 'dashboard' in paths:
    import os
    paths['ops_dir'] = os.path.dirname(paths['dashboard'])
json.dump(paths, sys.stdout)
")
        SNAPSHOT_BLOCK=$(python3 "$SNAPSHOT_SCRIPT" "$PWD" "$SNAPSHOT_JSON" 2>/dev/null || true)
        if [ -n "$SNAPSHOT_BLOCK" ]; then
            CORE_CONTENT="${CORE_CONTENT}"$'\n'"${SNAPSHOT_BLOCK}"
        fi
    fi

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
        # Security: skip if state file looks corrupted or is not a Jarvis dump
        # Validate state dump integrity — require all three markers anywhere in file
        HAS_DUMP=$(echo "$STATE_CONTENT" | grep -c "Jarvis State Dump" || true)
        HAS_TOPIC=$(echo "$STATE_CONTENT" | grep -c "Active Topic" || true)
        HAS_TIME=$(echo "$STATE_CONTENT" | grep -c "Timestamp" || true)
        if [ "$HAS_DUMP" -eq 0 ] || [ "$HAS_TOPIC" -eq 0 ] || [ "$HAS_TIME" -eq 0 ]; then
            STATE_CONTENT=""
        fi
        STATE_ESCAPED=$(escape_for_json "$STATE_CONTENT")
        context_parts="${context_parts}

[Jarvis State Recovery — Previous session state saved before compaction]
${STATE_CONTENT}
Restore: current Topic, Router output, confirmed facts, pending decisions from the saved state above."
    fi
fi

# ── 输出 ──
if [ -z "$context_parts" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[JARVIS_WARNING] Hook ran but produced no context. Check: python3 available? jarvis.yaml found? Core file readable at %s? Fallback: manually read JARVIS_BOOTSTRAP.md."}}\n' "$CORE_PATH"
    exit 0
fi

ESCAPED=$(escape_for_json "$context_parts")
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$ESCAPED"

exit 0
