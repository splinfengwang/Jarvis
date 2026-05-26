#!/bin/bash
# Jarvis Runtime — PreToolUse hook: write permission guard
# Pattern: PUA integrity guard — check transcript for activation markers first
set -eo pipefail  # Note: NO -u — VSCode extension env may lack some vars

HOOK_INPUT=$(cat)

# ── Jarvis activation check (PUA-style transcript scanning) ──
# If SessionStart hook failed silently, Jarvis markers won't be in transcript.
# Detect this early and at least warn the agent.
TRANSCRIPT=$(echo "$HOOK_INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
# Try transcript_path first, then fallback to checking if hook input has session context
tp = d.get('transcript_path', '')
if tp:
    try:
        with open(tp) as f:
            # Read last 50KB — sufficient for recent context
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 50000))
            print(f.read())
        sys.exit(0)
    except: pass
print('')
" 2>/dev/null || echo "")
JARVIS_ACTIVE="false"
if [ -n "$TRANSCRIPT" ] && echo "$TRANSCRIPT" | grep -q '\[JARVIS_CORE\]\|\[JARVIS_KNOWLEDGE_SNAPSHOT\]'; then
    JARVIS_ACTIVE="true"
fi
# Also check: if hook input mentions jarvis, consider it active
if echo "$HOOK_INPUT" | grep -qi 'jarvis'; then
    JARVIS_ACTIVE="true"
fi
TOOL_NAME=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ] && [ "$TOOL_NAME" != "MultiEdit" ] && [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

FILE_PATH=""
if [ "$TOOL_NAME" = "Bash" ]; then
    COMMAND=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
    DANGER='rm[[:space:]]+-[rRf]|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+clean[[:space:]]+-[fd]|mv[[:space:]].*[[:space:]]/(bin|etc|dev|lib)|dd[[:space:]]+if=|>[[:space:]]*(/dev|/etc|/bin)|chmod[[:space:]]+-R[[:space:]]+777'
    if echo "$COMMAND" | grep -qiE "$DANGER"; then
        printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"[Jarvis Guard] high-risk bash command"}}\n'
        exit 0
    fi
    exit 0
else
    FILE_PATH=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin).get('tool_input',{}); print(d.get('file_path','') or d.get('path','') or d.get('notebook_path',''))" 2>/dev/null || echo "")
fi

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Warn if Jarvis Core not detected — SessionStart hook may have failed
if [ "$JARVIS_ACTIVE" != "true" ] && [ "$TOOL_NAME" != "Bash" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[JARVIS_WARNING] Jarvis Core markers not detected in transcript. SessionStart hook may have failed. Read CLAUDE.md startup rules for manual bootstrap. Write guard operating in reduced mode — framework file protection still active."}}\n'
fi

# deny: critical Jarvis framework files
CRITICAL='JARVIS_CORE\.md|JARVIS_BOOTSTRAP\.md|AGENT_v3\.4\.md|/SKILL\.md|/hooks/[^/]+\.sh|/scripts/[^/]+\.py|jarvis/cli\.py|jarvis/lib\.py|jarvis/__init__\.py'
if echo "$FILE_PATH" | grep -qE "(^|/)($CRITICAL)"; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[Jarvis Guard] Framework file modification requires explicit authorization"}}\n'
    exit 0
fi

# advisory: knowledge base term write
if echo "$FILE_PATH" | grep -qE '(^|/)术语/'; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"[Jarvis Guard] content-write: knowledge terms require confirmation"}}\n'
    exit 0
fi

exit 0
