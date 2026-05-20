#!/bin/bash
# Jarvis Runtime — SessionStart hook: inject JARVIS_CORE.md via additionalContext
# Supports plugin injection and path config mapping from jarvis.yaml
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

# ── Core 注入 (plugin injection + path config) ──
if [ -f "$CORE_PATH" ]; then
    CORE_CONTENT=$(cat "$CORE_PATH")

    # Plugin injection: replace {{PLUGIN:NAME}} placeholders with plugin module content
    # Path config injection: append semantic→actual path mapping
    if [ -f "$JARVIS_YAML" ] && command -v python3 &>/dev/null; then
        CORE_CONTENT=$(python3 - "$JARVIS_YAML" "$CORE_CONTENT" "$JARVIS_HOME" << 'PYEOF'
import sys, os, re

jarvis_yaml_path = sys.argv[1]
core_content = sys.argv[2]
jarvis_home = sys.argv[3]  # Resolved by bash from hook symlink — portable, no absolute paths

# ── Simple YAML parser (no PyYAML dependency) ──
def parse_jarvis_yaml(path):
    result = {}
    with open(path) as f:
        raw = f.read()
    # Parse paths section
    in_paths = False
    in_plugins = False
    paths = {}
    plugins = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped == 'paths:':
            in_paths = True
            continue
        if stripped == 'plugins:':
            in_plugins = True
            in_paths = False
            continue
        if in_paths and ':' in stripped and line.startswith('  '):
            k, v = stripped.split(':', 1)
            paths[k.strip()] = v.strip().strip('"').strip("'")
        elif in_paths and not line.startswith('  '):
            in_paths = False
        if in_plugins and stripped.startswith('- '):
            plugins.append(stripped[2:].strip().strip('"').strip("'"))
        elif in_plugins and not line.startswith('  ') and not stripped.startswith('-'):
            in_plugins = False
    result['paths'] = paths
    result['plugins'] = plugins
    return result

def read_plugin_yaml(path):
    result = {'provides': {}}
    with open(path) as f:
        in_provides = False
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('name:'):
                result['name'] = stripped.split(':', 1)[1].strip()
            elif stripped == 'provides:':
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
    config = parse_jarvis_yaml(jarvis_yaml_path)
    plugins = config.get('plugins', [])

    # ── Build name→dir index for plugin resolution ──
    plugins_base = os.path.join(jarvis_home, 'plugins')
    name_to_dir = {}
    if os.path.isdir(plugins_base):
        for entry in os.listdir(plugins_base):
            entry_path = os.path.join(plugins_base, entry)
            if not os.path.isdir(entry_path):
                continue
            py = os.path.join(entry_path, 'plugin.yaml')
            if os.path.isfile(py):
                p = read_plugin_yaml(py)
                name_to_dir[p.get('name', entry)] = entry_path
            name_to_dir[entry] = entry_path

    # ── Plugin injection ──
    injections = {}
    for plugin_name in plugins:
        # Resolve by directory name first, then by manifest name
        plugin_dir = os.path.join(plugins_base, plugin_name)
        if not os.path.isdir(plugin_dir):
            plugin_dir = name_to_dir.get(plugin_name, '')
        if not plugin_dir or not os.path.isdir(plugin_dir):
            continue
        plugin_yaml = os.path.join(plugin_dir, 'plugin.yaml')
        if not os.path.isfile(plugin_yaml):
            continue
        plugin = read_plugin_yaml(plugin_yaml)
        for module_name, filename in plugin.get('provides', {}).items():
            module_path = os.path.join(plugin_dir, filename)
            if os.path.isfile(module_path):
                # Security: prevent path traversal outside plugin directory
                real_path = os.path.realpath(module_path)
                real_plugin = os.path.realpath(plugin_dir)
                if not real_path.startswith(real_plugin):
                    continue
                with open(module_path) as mf:
                    injections[module_name] = mf.read().strip()

    for module_name, content in injections.items():
        placeholder = '{{PLUGIN:' + module_name + '}}'
        if placeholder in core_content:
            core_content = core_content.replace(placeholder, content)

    # Remove unmatched {{PLUGIN:*}} lines
    lines = core_content.split('\n')
    filtered = [line for line in lines if '{{PLUGIN:' not in line]
    core_content = '\n'.join(filtered)

    # ── Path config injection ──
    label_map = {
        "dashboard": "仪表盘", "log": "操作日志", "topics": "Topic目录",
        "wiki_index": "wiki索引", "terms_index": "术语索引",
        "terms_dir": "术语目录", "knowledge_base": "知识库",
        "business_dir": "业务目录", "ops_dir": "平台运维",
    }
    path_lines = ["[Jarvis Path Config — semantic to actual file mapping]"]
    path_lines.append("Use these paths when skills reference files by name:")
    paths = config.get('paths', {})
    for key, value in paths.items():
        label = label_map.get(key, key)
        path_lines.append(f"- {label} -> {value}")
    path_lines.append("")
    core_content = core_content + "\n" + "\n".join(path_lines)

except Exception:
    # On any error, just remove unmatched placeholders
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
        # Security: skip if state file looks corrupted or is not a Jarvis dump
        if ! echo "$STATE_CONTENT" | head -3 | grep -q "Jarvis State Dump\|Active Topic\|Timestamp"; then
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
    exit 0
fi

ESCAPED=$(escape_for_json "$context_parts")
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$ESCAPED"

exit 0
