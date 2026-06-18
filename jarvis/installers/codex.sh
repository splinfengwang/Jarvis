#!/bin/bash
# Jarvis Adapter — Codex installer
set -eo pipefail

CODEX_DIR="${HOME}/.codex"
CODEX_SKILLS_DST="${CODEX_DIR}/skills"
SKILLS_SRC="${JARVIS_HOME}/skills"

echo "[Jarvis] Installing for Codex..."

mkdir -p "$CODEX_SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
    name=$(basename "$skill_dir")
    target="$CODEX_SKILLS_DST/$name"
    if [ -e "$target" ]; then
        echo "  SKIP  skill $name (already exists)"
    else
        ln -s "$skill_dir" "$target"
        echo "  LINK  skill $name"
    fi

    if [ ! -f "${skill_dir}agents/openai.yaml" ]; then
        echo "  WARN  skill $name is missing agents/openai.yaml (Codex UI metadata)"
    fi
done

echo "  NOTE  Codex does not support Jarvis hook injection."
echo "        Run 'jarvis init' inside each project so AGENTS.md can bootstrap Jarvis."
echo "[Jarvis] Codex installation complete."
