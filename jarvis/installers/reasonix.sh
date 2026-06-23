#!/bin/bash
# Jarvis Adapter — Reasonix installer
set -eo pipefail

REASONIX_DIR="${HOME}/.reasonix"
CONFIG_PATH="${REASONIX_DIR}/config.toml"
PROMPTS_DIR="${REASONIX_DIR}/prompts"
PROMPT_PATH="${PROMPTS_DIR}/jarvis-system.md"
SKILLS_PATH="${JARVIS_HOME}/skills"
LEGACY_SETTINGS="${REASONIX_DIR}/settings.json"

echo "[Jarvis] Installing for Reasonix..."

mkdir -p "$PROMPTS_DIR" "$REASONIX_DIR"

python3 - "$PROMPT_PATH" "$CONFIG_PATH" "$SKILLS_PATH" <<'PY'
import pathlib
import sys

from jarvis.platform_support import merge_reasonix_config_text, reasonix_prompt_text

prompt_path = pathlib.Path(sys.argv[1])
config_path = pathlib.Path(sys.argv[2])
skills_path = sys.argv[3]

prompt_path.write_text(reasonix_prompt_text(), encoding="utf-8")

existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
updated, prompt_managed, existing_prompt = merge_reasonix_config_text(
    existing,
    skills_path=skills_path,
    prompt_path=str(prompt_path),
)
config_path.write_text(updated, encoding="utf-8")

print(f"  WRITE {prompt_path}")
print("  MERGE config.toml")
if not prompt_managed and existing_prompt:
    print(f"  WARN  preserved existing system_prompt_file: {existing_prompt}")
    print(f"        Jarvis prompt written to {prompt_path}; merge it manually if needed.")
PY

if [ -f "$LEGACY_SETTINGS" ]; then
    python3 - "$LEGACY_SETTINGS" <<'PY'
import json
import pathlib
import shutil
import sys
import time

settings_path = pathlib.Path(sys.argv[1])
try:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
except Exception:
    print(f"  WARN  legacy settings.json is not valid JSON: {settings_path}")
    raise SystemExit(0)

names = ("jarvis-core-inject.sh", "jarvis-write-guard.sh", "jarvis-compact-save.sh")
hooks = settings.get("hooks")
changed = False

if isinstance(hooks, dict):
    for event in list(hooks.keys()):
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        kept_entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                kept_entries.append(entry)
                continue
            command = str(entry.get("command", ""))
            nested = entry.get("hooks")
            if any(name in command for name in names):
                changed = True
                continue
            if isinstance(nested, list):
                kept_nested = [
                    hook for hook in nested
                    if not any(name in str(hook.get("command", "")) for name in names)
                ]
                if len(kept_nested) != len(nested):
                    changed = True
                if kept_nested:
                    entry["hooks"] = kept_nested
                    kept_entries.append(entry)
                elif nested:
                    changed = True
            else:
                kept_entries.append(entry)
        if kept_entries:
            hooks[event] = kept_entries
        else:
            del hooks[event]
            changed = True
    if not hooks:
        settings.pop("hooks", None)
        changed = True

if changed:
    backup = settings_path.with_suffix(settings_path.suffix + f".bak-{int(time.time())}")
    shutil.copy2(settings_path, backup)
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  CLEAN legacy settings.json Jarvis hooks (backup: {backup})")
else:
    print("  OK    legacy settings.json has no Jarvis hooks")
PY
fi

echo "[Jarvis] Reasonix installation complete."
