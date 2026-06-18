#!/usr/bin/env python3
"""
Jarvis Plugin Resolver — platform-agnostic YAML parsing + plugin injection.

Reads jarvis.yaml, resolves {{PLUGIN:XXX}} placeholders in Core content,
and appends semantic-to-actual path mappings.

Usage:
    python3 plugin_resolver.py <jarvis_yaml_path> <core_content> <jarvis_home>
        Reads jarvis_yaml_path and core_content from CLI args, outputs
        processed content to stdout.

    python3 plugin_resolver.py --stdin
        Reads a JSON object from stdin: {"jarvis_yaml": "...", "core_content": "...", "jarvis_home": "..."}
"""

import json
import os
import re
import sys
from pathlib import Path

_parent = str(Path(__file__).resolve().parents[2])
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from jarvis.platform_support import build_path_config_block, extract_semantic_paths


# ── Simple YAML parser (no PyYAML dependency) ──

def parse_jarvis_yaml(path):
    """Parse jarvis.yaml — extracts semantic path config and plugins sections."""
    result = {}
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    in_paths = False
    in_core = False
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
        if stripped == 'core:':
            in_core = True
            continue
        if stripped == 'plugins:':
            in_plugins = True
            in_paths = False
            in_core = False
            continue
        if in_paths and ':' in stripped and line.startswith('  '):
            k, v = stripped.split(':', 1)
            paths[k.strip()] = v.strip().strip('"').strip("'")
        elif in_paths and not line.startswith('  '):
            in_paths = False
        if in_core and ':' in stripped and line.startswith('  '):
            k, v = stripped.split(':', 1)
            paths[k.strip()] = v.strip().strip('"').strip("'")
        elif in_core and not line.startswith('  '):
            in_core = False
        if in_plugins and stripped.startswith('- '):
            plugins.append(stripped[2:].strip().strip('"').strip("'"))
        elif in_plugins and not line.startswith('  ') and not stripped.startswith('-'):
            in_plugins = False
    result['paths'] = extract_semantic_paths({"paths": paths} if "knowledge_base" in paths or "terms_dir" in paths else {"core": paths})
    result['plugins'] = plugins
    return result


def read_plugin_yaml(path):
    """Read a plugin.yaml manifest — extracts name and provides mapping."""
    result = {'provides': {}}
    with open(path, encoding='utf-8') as f:
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


def build_name_to_dir_index(plugins_base):
    """Build plugin name → directory path index."""
    name_to_dir = {}
    if not os.path.isdir(plugins_base):
        return name_to_dir
    for entry in os.listdir(plugins_base):
        entry_path = os.path.join(plugins_base, entry)
        if not os.path.isdir(entry_path):
            continue
        py = os.path.join(entry_path, 'plugin.yaml')
        if os.path.isfile(py):
            p = read_plugin_yaml(py)
            name_to_dir[p.get('name', entry)] = entry_path
        name_to_dir[entry] = entry_path
    return name_to_dir


def resolve_plugin_content(plugins, plugins_base, name_to_dir):
    """Resolve {{PLUGIN:XXX}} content by reading plugin module files."""
    injections = {}
    for plugin_name in plugins:
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
                with open(module_path, encoding='utf-8') as mf:
                    injections[module_name] = mf.read().strip()
    return injections


def apply_plugin_injections(core_content, injections):
    """Replace {{PLUGIN:NAME}} placeholders in core_content."""
    for module_name, content in injections.items():
        placeholder = '{{PLUGIN:' + module_name + '}}'
        if placeholder in core_content:
            core_content = core_content.replace(placeholder, content)
    # Remove unmatched {{PLUGIN:*}} lines
    lines = core_content.split('\n')
    filtered = [line for line in lines if '{{PLUGIN:' not in line]
    return '\n'.join(filtered)


def build_path_config(config, jarvis_home):
    """Build semantic-to-actual path mapping block."""
    return build_path_config_block(config.get('paths', {}), jarvis_home) + "\n"


def resolve(jarvis_yaml_path, core_content, jarvis_home):
    """
    Main entry point: parse config, inject plugins, append path config.

    Returns processed core_content string.
    """
    config = parse_jarvis_yaml(jarvis_yaml_path)
    plugins = config.get('plugins', [])

    plugins_base = os.path.join(jarvis_home, 'plugins')
    name_to_dir = build_name_to_dir_index(plugins_base)
    injections = resolve_plugin_content(plugins, plugins_base, name_to_dir)
    core_content = apply_plugin_injections(core_content, injections)

    path_block = build_path_config(config, jarvis_home)
    core_content = core_content + "\n" + path_block

    return core_content


def main():
    if len(sys.argv) >= 4:
        # CLI args mode: jarvis_yaml_path core_content jarvis_home
        jarvis_yaml_path = sys.argv[1]
        core_content = sys.argv[2]
        jarvis_home = sys.argv[3]
        result = resolve(jarvis_yaml_path, core_content, jarvis_home)
        sys.stdout.write(result + "\n")
    elif len(sys.argv) == 2 and sys.argv[1] == '--stdin':
        # JSON stdin mode
        data = json.load(sys.stdin)
        result = resolve(
            data.get('jarvis_yaml', ''),
            data.get('core_content', ''),
            data.get('jarvis_home', ''),
        )
        sys.stdout.write(result + "\n")
    else:
        print("Usage: python3 plugin_resolver.py <jarvis_yaml_path> <core_content> <jarvis_home>", file=sys.stderr)
        print("   or: python3 plugin_resolver.py --stdin", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
