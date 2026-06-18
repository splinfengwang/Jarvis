#!/usr/bin/env python3
"""
Jarvis Knowledge Snapshot — platform-agnostic snapshot generator.

Scans the project's knowledge base (terms, wiki index, dashboard, topic
snapshots) and outputs a structured [JARVIS_KNOWLEDGE_SNAPSHOT] block.

Usage:
    python3 snapshot.py <project_root> <paths_json>
        project_root: absolute path to the project root
        paths_json:   JSON object with path overrides, e.g.:
                      {"terms_dir": "知识库/术语", "dashboard": "platform-ops/仪表盘.md", ...}
"""

import json
import os
import re
import sys
from datetime import datetime


# ── Dashboard parsing ──

def parse_active_topics(dashboard_path):
    """Extract active topic list from dashboard markdown table."""
    topic_names = []
    if not os.path.isfile(dashboard_path):
        return topic_names
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
    return topic_names


# ── Terms scanning ──

def scan_terms(terms_dir, topic_names):
    """Scan confirmed terms, sorted by topic relevance then mtime."""
    term_entries = []
    if not os.path.isdir(terms_dir):
        return term_entries
    for fname in os.listdir(terms_dir):
        if not fname.endswith('.md') or fname == '术语索引.md':
            continue
        fpath = os.path.join(terms_dir, fname)
        try:
            with open(fpath, encoding='utf-8') as f:
                raw = f.read()
            # Extract frontmatter
            fm = {}
            end = -1
            if raw.startswith('---'):
                end = raw.find('---', 3)
                if end > 0:
                    for line in raw[3:end].splitlines():
                        line = line.strip()
                        if ':' in line and not line.startswith('-'):
                            k, v = line.split(':', 1)
                            fm[k.strip()] = v.strip()
            if fm.get('status') != '已确认':
                continue
            # Get title from first # heading
            title = fname.replace('.md', '')
            for line in raw.splitlines():
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            # Get one-line summary
            body = raw[end + 3:].strip() if end > 0 else raw
            summary = ''
            for line in body.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('>'):
                    summary = stripped[:120]
                    break
            term_entries.append((fpath, os.path.getmtime(fpath), title, summary))
        except Exception:
            pass
    return term_entries


def sort_terms(term_entries, topic_names):
    """Sort terms: Doing-topic-relevant first, then by mtime."""
    doing_names = [name for status, name, _ in topic_names if 'Doing' in status] if topic_names else []
    if doing_names:

        def term_score(entry):
            fpath, mtime, title, summary = entry
            relevance = 0
            try:
                with open(fpath, encoding='utf-8') as f:
                    raw = f.read()
                for dname in doing_names:
                    if dname in raw:
                        relevance = 1
                        break
            except Exception:
                pass
            return (-relevance, -mtime)
    else:
        def term_score(entry):
            _, mtime, _, _ = entry
            return (0, -mtime)
    term_entries.sort(key=term_score)
    return term_entries


# ── Wiki index parsing ──

def parse_wiki_index(wiki_path):
    """Parse wiki index: sections (术语/分析文档/决策记录), entries, counts."""
    sections = {
        "术语": {"total": 0, "confirmed": 0, "entries": []},
        "分析文档": {"total": 0, "confirmed": 0, "entries": []},
        "决策记录": {"total": 0, "confirmed": 0, "entries": []},
    }
    if not os.path.isfile(wiki_path):
        return sections
    try:
        with open(wiki_path, encoding='utf-8') as f:
            wiki = f.read()
        current_section = None
        for line in wiki.splitlines():
            stripped = line.strip()
            if stripped.startswith('## '):
                name = stripped[3:].strip()
                if '术语' in name:
                    current_section = "术语"
                elif '分析文' in name or '业务文档' in name:
                    current_section = "分析文档"
                elif '决策' in name:
                    current_section = "决策记录"
                else:
                    current_section = None
                continue
            if stripped.startswith('|') and not stripped.startswith('|---') and current_section:
                cells = [c.strip() for c in stripped.split('|')[1:-1]]
                if len(cells) >= 3:
                    is_confirmed = '已确认' in cells[-1]
                    sec = sections[current_section]
                    sec["total"] += 1
                    if is_confirmed:
                        sec["confirmed"] += 1
                    title = cells[0]
                    match = re.search(r'\[\[.*?\|?(.*?)\]\]', cells[0])
                    if match:
                        title = match.group(1)
                    summary = cells[1] if len(cells) > 1 else ''
                    sec["entries"].append((title, summary, is_confirmed))
    except Exception:
        pass
    return sections


# ── Topic snapshot parsing ──

def scan_topic_snapshots(topics_dir, topic_names):
    """Extract key facts from topic snapshots, state-aware."""
    fact_lines = []
    for status, topic_name, _ in topic_names[:5]:
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
                    time_match = re.search(r'快照时间\*?\*?:\s*(\d{4}-\d{2}-\d{2})', content)
                    if time_match:
                        try:
                            snap_date = datetime.strptime(time_match.group(1), "%Y-%m-%d")
                            snapshot_age_days = (datetime.now() - snap_date).days
                        except Exception:
                            pass
                    is_doing = 'Doing' in status
                    is_paused = 'Paused' in status or 'paused' in status.lower()
                    facts = []
                    if is_doing:
                        in_facts = False
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
                    if is_doing:
                        if facts:
                            summary = '; '.join(facts[:3])
                            fact_lines.append(f"- {topic_name}: {summary}")
                        else:
                            fact_lines.append(f"- {topic_name} [Doing]")
                    elif is_paused and snapshot_age_days is not None and snapshot_age_days <= 30:
                        fact_lines.append(f"- {topic_name} [{status}] — 最近活跃")
                    elif is_paused:
                        age_str = f", {snapshot_age_days}d未更新" if snapshot_age_days else ""
                        fact_lines.append(f"- {topic_name} ({status}{age_str})")
                    else:
                        fact_lines.append(f"- {topic_name} ({status})")
                    found = True
                    break
                except Exception:
                    pass
        if not found:
            fact_lines.append(f"- {topic_name}: （无快照）")
    return fact_lines


# ── Main snapshot builder ──

def generate_snapshot(project_root, paths):
    """
    Generate knowledge snapshot text block.

    Args:
        project_root: Absolute path to project root
        paths: Dict with key->path mappings (same keys as jarvis.yaml paths: section)
               Expected keys: terms_dir, dashboard, topics, wiki_index

    Returns:
        String containing [JARVIS_KNOWLEDGE_SNAPSHOT] block
    """
    terms_dir = os.path.join(project_root, paths.get('terms_dir', '知识库/术语'))
    dashboard_path = os.path.join(project_root, paths.get('dashboard', 'platform-ops/仪表盘.md'))
    topics_dir = os.path.join(project_root, paths.get('topics', 'platform-ops/topics'))
    wiki_path = os.path.join(project_root, paths.get('wiki_index', '知识库/wiki索引.md'))

    snapshot_lines = ["[JARVIS_KNOWLEDGE_SNAPSHOT]"]
    snapshot_lines.append("以下是你已确认的知识基线。")
    snapshot_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    snapshot_lines.append(f"快照时间: {snapshot_time}")
    snapshot_lines.append("快照内容已从源文件提取，可直接作为推理基础。但若源文件最后修改时间晚于快照时间，以源文件为准。")
    snapshot_lines.append("会话中新确认的知识不受此快照限制。")
    snapshot_lines.append("")
    total_chars = len("".join(snapshot_lines))

    # Source 0: Topic names
    topic_names = parse_active_topics(dashboard_path)

    # Source 1: Confirmed terms
    term_entries = scan_terms(terms_dir, topic_names)
    if term_entries:
        term_entries = sort_terms(term_entries, topic_names)
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

    # Source 2: Wiki index
    sections = parse_wiki_index(wiki_path)
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

    confirmed_entries = []
    for sec_name in ["术语", "分析文档", "决策记录"]:
        for title, summary, is_confirmed in sections[sec_name]["entries"]:
            if is_confirmed:
                confirmed_entries.append((sec_name, title, summary[:120] if summary else ''))

    if confirmed_entries:
        key_lines = [f"## 关键条目 (共 {total_confirmed} 条已确认)"]
        for sec_name, title, summary in confirmed_entries[:8]:
            entry = f"- [{sec_name}] {title}"
            if summary:
                entry += f" — {summary}"
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

    # Source 3: Active topics
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

    # Source 4: Topic snapshots facts
    fact_lines = scan_topic_snapshots(topics_dir, topic_names)
    if fact_lines:
        fact_section = ["## 关键结论"] + fact_lines[:8]
        fact_chars = sum(len(l) + 1 for l in fact_section)
        if total_chars + fact_chars > 2500:
            while fact_lines and total_chars + sum(len(l) + 1 for l in fact_lines[:len(fact_lines) + 1]) > 2500:
                fact_lines.pop()
            if fact_lines:
                fact_lines.append("...（已截断，完整列表可搜索知识库）")
        snapshot_lines.extend(["## 关键结论"] + fact_lines[:8])
        snapshot_lines.append("")

    snapshot_lines.append("[/JARVIS_KNOWLEDGE_SNAPSHOT]")
    return "\n".join(snapshot_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 snapshot.py <project_root> [paths_json]", file=sys.stderr)
        print("   or: python3 snapshot.py --stdin", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == '--stdin':
        data = json.load(sys.stdin)
        project_root = data.get('project_root', os.getcwd())
        paths = data.get('paths', {})
    else:
        project_root = sys.argv[1]
        paths = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    snapshot = generate_snapshot(project_root, paths)
    sys.stdout.write(snapshot + "\n")


if __name__ == '__main__':
    main()
