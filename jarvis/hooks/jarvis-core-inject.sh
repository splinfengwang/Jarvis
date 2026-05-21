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
from datetime import datetime

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

    # ── Knowledge snapshot ──
    try:
        project_root = os.getcwd()
        terms_dir = os.path.join(project_root, paths.get('terms_dir', '知识库/术语'))
        dashboard_path = os.path.join(project_root, paths.get('dashboard', 'platform-ops/仪表盘.md'))
        topics_dir = os.path.join(project_root, paths.get('topics', 'platform-ops/topics'))

        snapshot_lines = ["[JARVIS_KNOWLEDGE_SNAPSHOT]"]
        snapshot_lines.append("以下是你已确认的知识基线。")
        snapshot_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        snapshot_lines.append(f"快照时间: {snapshot_time}")
        snapshot_lines.append("快照内容已从源文件提取，可直接作为推理基础。但若源文件最后修改时间晚于快照时间，以源文件为准。")
        snapshot_lines.append("会话中新确认的知识不受此快照限制。")
        snapshot_lines.append("")
        total_chars = len("".join(snapshot_lines))

        # ── Source 0: Collect topic names first (needed by term sorting) ──
        topic_names = []
        if os.path.isfile(dashboard_path):
            try:
                with open(dashboard_path, encoding='utf-8') as f:
                    dash = f.read()
                in_active = False
                for line in dash.splitlines():
                    if line.strip() == '## 活跃 Topic':
                        in_active = True
                        continue
                    if in_active and line.startswith('## '):
                        break
                    if in_active and line.strip().startswith('|') and '|' in line[1:]:
                        cells = [c.strip() for c in line.split('|')[1:-1]]
                        if len(cells) >= 4 and ('[[' in cells[1] or '[' in cells[1]):
                            status = cells[0]
                            match = re.search(r'\[\[.*?\|(.*?)\]\]', cells[1])
                            if not match:
                                match = re.search(r'\[\[(.*?)\]\]', cells[1])
                            topic_name = match.group(1) if match else cells[1].replace('[[', '').replace(']]', '').split('|')[-1]
                            next_step = cells[3] if len(cells) > 3 else ''
                            topic_names.append((status, topic_name, next_step))
            except Exception:
                pass

        # ── Source 1: Confirmed terms (sorted by topic relevance, then mtime) ──
        term_entries = []
        if os.path.isdir(terms_dir):
            for fname in os.listdir(terms_dir):
                if not fname.endswith('.md') or fname == '术语索引.md':
                    continue
                fpath = os.path.join(terms_dir, fname)
                try:
                    with open(fpath, encoding='utf-8') as f:
                        raw = f.read()
                    # Extract frontmatter
                    fm = {}
                    if raw.startswith('---'):
                        end = raw.find('---', 3)
                        if end > 0:
                            for line in raw[3:end].splitlines():
                                line = line.strip()
                                if ':' in line and not line.startswith('-'):
                                    k, v = line.split(':', 1)
                                    fm[k.strip()] = v.strip()
                    if fm.get('status') == '已确认':
                        # Get title from first # heading
                        title = fname.replace('.md', '')
                        for line in raw.splitlines():
                            if line.startswith('# '):
                                title = line[2:].strip()
                                break
                        # Get one-line summary (first non-empty after frontmatter)
                        body = raw[end+3:].strip() if 'end' in dir() else raw
                        summary = ''
                        for line in body.splitlines():
                            stripped = line.strip()
                            if stripped and not stripped.startswith('#') and not stripped.startswith('>'):
                                summary = stripped[:120]
                                break
                        term_entries.append((fpath, os.path.getmtime(fpath), title, summary))
                except Exception:
                    pass

        if term_entries:
            # T4: Sort by topic relevance (Doing first), then by mtime
            doing_names = [name for status, name, _ in topic_names if 'Doing' in status] if topic_names else []
            def term_score(entry):
                fpath, mtime, title, summary = entry
                relevance = 0
                if doing_names:
                    try:
                        # Check if term frontmatter references any doing topic
                        with open(fpath, encoding='utf-8') as f:
                            raw = f.read()
                        for dname in doing_names:
                            if dname in raw:
                                relevance = 1
                                break
                    except Exception:
                        pass
                return (-relevance, -mtime)  # relevant first, then newest
            term_entries.sort(key=term_score)
            term_lines = ["## 已确认术语（最近 8 条）"]
            for _, _, title, summary in term_entries[:8]:
                entry = f"- **{title}**"
                if summary:
                    entry += f"：{summary}"
                term_lines.append(entry)
                total_chars += len(entry) + 1
            snapshot_lines.extend(term_lines)
            snapshot_lines.append("")
        else:
            snapshot_lines.append("（知识库暂无已确认术语）")
            snapshot_lines.append("")

        # ── Source 2: Wiki index structured overview ──
        wiki_path = os.path.join(project_root, paths.get('wiki_index', '知识库/wiki索引.md'))
        if os.path.isfile(wiki_path):
            try:
                with open(wiki_path, encoding='utf-8') as f:
                    wiki = f.read()
                # Parse sections: terms, analysis docs, decisions
                sections = {"术语": {"total": 0, "confirmed": 0, "entries": []},
                           "分析文档": {"total": 0, "confirmed": 0, "entries": []},
                           "决策记录": {"total": 0, "confirmed": 0, "entries": []}}
                current_section = None
                in_table = False
                for line in wiki.splitlines():
                    stripped = line.strip()
                    if stripped.startswith('## '):
                        name = stripped[3:].strip()
                        if '术语' in name: current_section = "术语"
                        elif '分析文' in name or '业务文档' in name: current_section = "分析文档"
                        elif '决策' in name: current_section = "决策记录"
                        else: current_section = None
                        in_table = False
                        continue
                    if stripped.startswith('|') and not stripped.startswith('|---') and current_section:
                        in_table = True
                        cells = [c.strip() for c in stripped.split('|')[1:-1]]
                        if len(cells) >= 3:
                            is_confirmed = '已确认' in cells[-1]
                            sec = sections[current_section]
                            sec["total"] += 1
                            if is_confirmed:
                                sec["confirmed"] += 1
                            # Extract title from wikilink: [[path|title]] -> title
                            title = cells[0]
                            match = re.search(r'\[\[.*?\|?(.*?)\]\]', cells[0])
                            if match: title = match.group(1)
                            summary = cells[1] if len(cells) > 1 else ''
                            sec["entries"].append((title, summary, is_confirmed))
                # Build overview
                overview = ["## 知识库概览"]
                total_confirmed = 0
                for sec_name in ["术语", "分析文档", "决策记录"]:
                    sec = sections[sec_name]
                    if sec["total"] > 0:
                        overview.append(f"{sec_name}: {sec['total']} 条 ({sec['confirmed']} 已确认)")
                        total_confirmed += sec["confirmed"]
                    else:
                        overview.append(f"{sec_name}: （无）")
                overview.append("")

                # Build key entries (confirmed only, top 8 total)
                confirmed_entries = []
                for sec_name in ["术语", "分析文档", "决策记录"]:
                    for title, summary, is_confirmed in sections[sec_name]["entries"]:
                        if is_confirmed:
                            confirmed_entries.append((sec_name, title, summary[:120] if summary else ''))
                if confirmed_entries:
                    key_lines = [f"## 关键条目 (共 {total_confirmed} 条已确认)"]
                    for sec_name, title, summary in confirmed_entries[:8]:
                        entry = f"- [{sec_name}] {title}"
                        if summary: entry += f" — {summary}"
                        key_lines.append(entry)
                        total_chars += len(entry) + 1
                    if len(confirmed_entries) > 8:
                        key_lines.append(f"（还有 {len(confirmed_entries)-8} 条未展示）")
                    snapshot_lines.extend(overview)
                    snapshot_lines.extend(key_lines)
                    snapshot_lines.append("")
                else:
                    snapshot_lines.extend(overview)
                    snapshot_lines.append("（暂无已确认条目）")
                    snapshot_lines.append("")
            except Exception:
                pass

        # ── Source 3: Active topics from dashboard ──
        if topic_names:
            topic_lines = ["## 活跃工作主题"]
            for status, name, next_step in topic_names[:5]:
                entry = f"- {status} {name}"
                if next_step and next_step != '|':
                    entry += f" → {next_step}"
                topic_lines.append(entry)
                total_chars += len(entry) + 1
            snapshot_lines.extend(topic_lines)
            snapshot_lines.append("")
        else:
            snapshot_lines.append("（暂无活跃工作主题）")
            snapshot_lines.append("")

        # ── Source 3: Key facts from topic snapshots ──
        fact_lines = []
        for status, topic_name, _ in topic_names[:5]:
            # T3/A4: State-based filtering
            snapshot_age_days = None
            found = False
            if os.path.isdir(topics_dir):
                for dname in sorted(os.listdir(topics_dir), reverse=True):
                    tdir = os.path.join(topics_dir, dname)
                    snap = os.path.join(tdir, '_上下文快照.md')
                    if not os.path.isfile(snap):
                        continue
                    try:
                        with open(snap, encoding='utf-8') as f:
                            content = f.read()
                        if topic_name not in content[:200]:
                            continue
                        # Extract snapshot time
                        snapshot_age_days = None
                        time_match = re.search(r'快照时间\*?\*?:\s*(\d{4}-\d{2}-\d{2})', content)
                        if time_match:
                            try:
                                snap_date = datetime.strptime(time_match.group(1), "%Y-%m-%d")
                                snapshot_age_days = (datetime.now() - snap_date).days
                            except Exception:
                                pass
                        # State-based display
                        is_doing = 'Doing' in status
                        is_paused = 'Paused' in status or 'paused' in status.lower()
                        if is_doing:
                            # Show topic + up to 3 confirmed facts
                            in_facts = False
                            facts = []
                            for line in content.splitlines():
                                if line.startswith('## ') and '已确认事实' in line:
                                    in_facts = True
                                    continue
                                if in_facts and line.startswith('## '):
                                    break
                                if in_facts and line.strip().startswith('- '):
                                    fact = line.strip()[2:][:150]
                                    if fact and fact not in ('暂无。', '-'):
                                        facts.append(fact)
# Update the display logic after extracting snapshot for this topic
                        if is_doing:
                            # Show facts
                            if facts:
                                summary = '; '.join(facts[:3])
                                fact_lines.append(f"- {topic_name}: {summary}")
                        elif is_paused and snapshot_age_days is not None and snapshot_age_days <= 30:
                            fact_lines.append(f"- {topic_name} [{status}] — 最近活跃")
                        elif is_paused:
                            fact_lines.append(f"- {topic_name} ({status}, {snapshot_age_days}d未更新)" if snapshot_age_days else f"- {topic_name} ({status})")
                        else:
                            fact_lines.append(f"- {topic_name} ({status})")
                        found = True
                        break
                    except Exception:
                        pass
                if not found:
                    fact_lines.append(f"- {topic_name}: （无快照）")

        if fact_lines:
            fact_section = ["## 关键结论"] + fact_lines[:8]
            fact_chars = sum(len(l) + 1 for l in fact_section)
            if total_chars + fact_chars > 2500:
                # Truncate
                while fact_lines and total_chars + sum(len(l)+1 for l in fact_lines[:len(fact_lines)+1]) > 2500:
                    fact_lines.pop()
                if fact_lines:
                    fact_lines.append("...（已截断，完整列表可搜索知识库）")
            snapshot_lines.extend(["## 关键结论"] + fact_lines[:8])
            snapshot_lines.append("")

        snapshot_lines.append("[/JARVIS_KNOWLEDGE_SNAPSHOT]")
        core_content = core_content + "\n" + "\n".join(snapshot_lines)
    except Exception as e:
        import sys as _sys; print(f"[JARVIS WARN] Knowledge snapshot failed: {e}", file=_sys.stderr)

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
