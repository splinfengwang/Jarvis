#!/bin/bash
set -eo pipefail

if [ -z "${JARVIS_HOME:-}" ]; then
    echo "[Jarvis] ERROR: JARVIS_HOME is not set"
    exit 1
fi

exec bash "${JARVIS_HOME}/installers/reasonix.sh"
