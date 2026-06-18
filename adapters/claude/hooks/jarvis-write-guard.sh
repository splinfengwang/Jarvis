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
PERMISSION_MODE=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('permissionMode','') or d.get('permission_mode',''))" 2>/dev/null || echo "")
if [ -z "$PERMISSION_MODE" ] && [ -n "$TRANSCRIPT" ]; then
    PERMISSION_MODE=$(echo "$TRANSCRIPT" | python3 -c "
import re, sys
text = sys.stdin.read()
matches = re.findall(r'\"permissionMode\":\"([^\"]+)\"', text)
print(matches[-1] if matches else '')
" 2>/dev/null || echo "")
fi

emit_decision() {
    local decision="$1"
    local reason="$2"

    if [ "$decision" = "ask" ] && [ "$PERMISSION_MODE" = "bypassPermissions" ]; then
        printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"[Jarvis Guard] bypassPermissions 已开启；以下提醒仅作为风险提示，不再触发确认：%s"}}\n' "$reason"
        printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}\n'
        return 0
    fi

    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":"%s"}}\n' "$decision" "$reason"
}

if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ] && [ "$TOOL_NAME" != "MultiEdit" ] && [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

FILE_PATH=""
if [ "$TOOL_NAME" = "Bash" ]; then
    COMMAND=$(echo "$HOOK_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")
    DANGER='rm[[:space:]]+-[rRf]|git[[:space:]]+reset[[:space:]]+--hard|git[[:space:]]+clean[[:space:]]+-[fd]|mv[[:space:]].*[[:space:]]/(bin|etc|dev|lib)|dd[[:space:]]+if=|>[[:space:]]*(/dev|/etc|/bin)|chmod[[:space:]]+-R[[:space:]]+777'
    if echo "$COMMAND" | grep -qiE "$DANGER"; then
        emit_decision "ask" "[Jarvis Guard] high-risk bash command"
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
    emit_decision "ask" "[Jarvis Guard] content-write: knowledge terms require confirmation"
    exit 0
fi

# ── catalog gate: new file into writable catalog → ask ──
if [ "$TOOL_NAME" = "Write" ]; then
    JARVIS_YAML="${CLAUDE_PROJECT_DIR:-$PWD}/jarvis.yaml"
    if [ -f "$JARVIS_YAML" ]; then
        CATALOG_MATCH=$(python3 -c "
import sys, re
yaml = open('$JARVIS_YAML').read()
# Only match names under catalogs: section
cs = yaml.find('catalogs:')
if cs >= 0:
    tail = yaml[cs:]
    end = len(tail)
    for m in re.finditer(r'^[a-zA-Z]', tail[10:], re.MULTILINE):
        end = m.start() + 10; break
    cy = tail[:end]
    names = re.findall(r'^  ([\\u4e00-\\u9fa5\\w-]+):', cy, re.MULTILINE)
    names = [n for n in names if n not in ('writable', 'description', 'catalogs')]
else:
    names = []
file = '$FILE_PATH'.replace('\$CLAUDE_PROJECT_DIR/', '').replace('\$PWD/', '')
for name in names:
    if file.startswith(name + '/') or file == name:
        print(name)
        sys.exit(0)
" 2>/dev/null || echo "")
        if [ -n "$CATALOG_MATCH" ]; then
            emit_decision "ask" "[Jarvis Guard] catalog-write: 新建文件到 ${CATALOG_MATCH}/ 目录。请确认该内容已在活跃 Topic 中讨论并确认过。"
            exit 0
        fi
    fi
fi

exit 0
