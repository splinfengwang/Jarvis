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
    echo "  NOTE  legacy settings.json detected at $LEGACY_SETTINGS (Reasonix does not use it for Jarvis v2)"
fi

echo "[Jarvis] Reasonix installation complete."
