#!/bin/bash
# Jarvis Adapter — Claude Code installer
set -eo pipefail

CLAUDE_DIR="${HOME}/.claude"
SKILLS_SRC="${JARVIS_HOME}/skills"
HOOKS_SRC="${JARVIS_HOME}/hooks"
SKILLS_DST="${CLAUDE_DIR}/skills"
HOOKS_DST="${CLAUDE_DIR}/hooks"
SETTINGS_PATH="${CLAUDE_DIR}/settings.json"

echo "[Jarvis] Installing for Claude Code..."

mkdir -p "$SKILLS_DST" "$HOOKS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
    name=$(basename "$skill_dir")
    target="$SKILLS_DST/$name"
    if [ -e "$target" ]; then
        echo "  SKIP  skill $name (already exists)"
    else
        ln -s "$skill_dir" "$target"
        echo "  LINK  skill $name"
    fi
done

for hook_file in "$HOOKS_SRC"/*.sh; do
    name=$(basename "$hook_file")
    target="$HOOKS_DST/$name"
    if [ -e "$target" ]; then
        echo "  SKIP  hook $name (already exists)"
    else
        ln -s "$hook_file" "$target"
        echo "  LINK  hook $name"
    fi
done

export JARVIS_SETTINGS_JSON=$(cat <<JSON
{
  "permissions": {
    "allow": [],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(**/.env)",
      "Read(**/.env.*)",
      "Read(**/secrets/**)",
      "Read(**/*secret*)",
      "Read(**/*token*)"
    ]
  },
  "hooks": {
    "SessionStart": [
      {
        "match": "startup|resume|compact",
        "hooks": [
          { "type": "command", "command": "bash \"$HOOKS_DST/jarvis-core-inject.sh\"", "timeout": 15000 }
        ]
      }
    ],
    "PreToolUse": [
      {
        "match": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          { "type": "command", "command": "bash \"$HOOKS_DST/jarvis-write-guard.sh\"", "timeout": 15000 }
        ]
      }
    ],
    "PreCompact": [
      {
        "match": "*",
        "hooks": [
          { "type": "command", "command": "bash \"$HOOKS_DST/jarvis-compact-save.sh\"", "timeout": 15000 }
        ]
      }
    ]
  }
}
JSON
)

python3 - "$SETTINGS_PATH" <<'PY'
import json
import os
import pathlib
import sys

settings_path = pathlib.Path(sys.argv[1])
incoming = json.loads(os.environ["JARVIS_SETTINGS_JSON"])

if settings_path.is_file():
    try:
        current = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        current = {}
else:
    current = {}

hooks = current.setdefault("hooks", {})
for event, new_entries in incoming.get("hooks", {}).items():
    existing_entries = hooks.setdefault(event, [])
    existing_commands = {
        hook.get("command", "")
        for entry in existing_entries
        for hook in entry.get("hooks", [])
    }
    for entry in new_entries:
        entry_commands = [hook.get("command", "") for hook in entry.get("hooks", [])]
        if any(command in existing_commands for command in entry_commands):
            continue
        existing_entries.append(entry)
        existing_commands.update(entry_commands)

permissions = current.setdefault("permissions", {})
for key in ("allow", "deny", "ask"):
    incoming_rules = incoming.get("permissions", {}).get(key, [])
    if not incoming_rules:
        continue
    existing_rules = permissions.setdefault(key, [])
    for rule in incoming_rules:
        if rule not in existing_rules:
            existing_rules.append(rule)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("  WRITE settings.json")
PY

echo "[Jarvis] Claude Code installation complete."
