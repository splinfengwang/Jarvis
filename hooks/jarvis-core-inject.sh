#!/bin/bash
# Jarvis Runtime — SessionStart hook: inject JARVIS_CORE.md via additionalContext
# Supports plugin injection from jarvis.yaml
set -euo pipefail

# Resolve jarvis home from hook's own location (works through symlinks)
SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}" 2>/dev/null || readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")" && pwd)"
JARVIS_HOME="$(dirname "$SCRIPT_DIR")"
CORE_PATH="${JARVIS_HOME}/core/JARVIS_CORE.md"
COMPACT_STATE="${HOME}/.jarvis/compact-state.md"
JARVIS_YAML="${PWD}/jarvis.yaml"

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

# ── Core 注入 (with plugin injection) ──
if [ -f "$CORE_PATH" ]; then
    CORE_CONTENT=$(cat "$CORE_PATH")

    # Plugin injection: replace {{PLUGIN:NAME}} placeholders with plugin module content
    if [ -f "$JARVIS_YAML" ] && command -v python3 &>/dev/null; then
        CORE_CONTENT=$(python3 - "$JARVIS_YAML" "$CORE_CONTENT" << 'PYEOF'
import sys, os

jarvis_yaml_path = sys.argv[1]
core_content = sys.argv[2]

# Simple YAML parser for jarvis.yaml (avoid PyYAML dependency)
def read_simple_yaml(path):
    """Read a minimal YAML file and return top-level scalars and lists."""
    result = {}
    with open(path) as f:
        current_key = None
        current_list = None
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith('#'):
                continue
            # list item
            if stripped.startswith('- ') or stripped.startswith('-'):
                item = stripped.lstrip('- ').strip().strip('"').strip("'")
                if current_key and current_list is not None:
                    current_list.append(item)
                continue
            # key: value
            if ':' in stripped:
                # Check if it's a nested key
                indent = len(line) - len(line.lstrip())
                if indent == 0 or current_key is None:
                    parts = stripped.split(':', 1)
                    key = parts[0].strip()
                    value = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else ''
                    if value == '':
                        current_key = key
                        current_list = []
                        result[key] = current_list
                    else:
                        current_key = key
                        result[key] = value
                        current_list = None
    return result

def read_plugin_yaml(path):
    """Read a plugin.yaml and return provides dict."""
    result = {'provides': {}}
    with open(path) as f:
        in_provides = False
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('name:'):
                result['name'] = stripped.split(':', 1)[1].strip()
            elif stripped.startswith('provides:'):
                in_provides = True
            elif in_provides and ':' in stripped and not stripped.startswith(' '):
                in_provides = False
            elif in_provides and ':' in stripped:
                parts = stripped.strip().split(':', 1)
                module_name = parts[0].strip()
                filename = parts[1].strip().strip('"').strip("'")
                result['provides'][module_name] = filename
    return result

try:
    yaml_config = read_simple_yaml(jarvis_yaml_path)
    jarvis_home = yaml_config.get('jarvis_home', os.path.dirname(os.path.dirname(__file__)))
    plugins = yaml_config.get('plugins', [])
    if isinstance(plugins, str):
        plugins = [plugins]

    # Build injection map
    injections = {}
    for plugin_name in plugins:
        plugin_dir = os.path.join(jarvis_home, 'plugins', plugin_name)
        if not os.path.isdir(plugin_dir):
            continue
        plugin_yaml = os.path.join(plugin_dir, 'plugin.yaml')
        if not os.path.isfile(plugin_yaml):
            continue
        plugin = read_plugin_yaml(plugin_yaml)
        for module_name, filename in plugin.get('provides', {}).items():
            module_path = os.path.join(plugin_dir, filename)
            if os.path.isfile(module_path):
                with open(module_path) as mf:
                    injections[module_name] = mf.read().strip()
except Exception:
    injections = {}

# Perform replacements
import re
for module_name, content in injections.items():
    placeholder = '{{' + '{{PLUGIN:' + module_name + '}}' + '}}'
    # Actually the placeholder is {{PLUGIN:NAME}}
    placeholder = '{{PLUGIN:' + module_name + '}}'
    if placeholder in core_content:
        core_content = core_content.replace(placeholder, content)

# Remove unmatched {{PLUGIN:*}} placeholders (whole line)
lines = core_content.split('\n')
filtered = [line for line in lines if '{{PLUGIN:' not in line]
core_content = '\n'.join(filtered)

print(core_content)
PYEOF
)
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
