#!/usr/bin/env python3
"""Report unresolved Obsidian wikilinks without modifying files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import list_markdown_files, print_validation, read_text, vault_root


def wikilink_target(raw: str) -> str:
    target = raw.split("|", 1)[0].strip()
    return target.rstrip("\\")


def strip_code_examples(text: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            lines.append("")
            continue
        lines.append("" if in_fence else line)
    without_fences = "\n".join(lines)
    return re.sub(r"`[^`\n]*`", "", without_fences)


def link_exists(root: Path, target: str) -> bool:
    clean = target.split("#", 1)[0].strip()
    if not clean or clean.startswith(("http://", "https://")):
        return True
    direct = root / clean
    candidates = [direct]
    if direct.suffix == ".md":
        candidates.append(direct)
    else:
        candidates.append(Path(str(direct) + ".md"))
    if "/" not in clean:
        candidates.extend(root.glob(f"**/{clean}.md"))
        candidates.extend(root.glob(f"**/{clean}/索引.md"))
    return any(path.exists() for path in candidates)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", default=".")
    parser.add_argument("--scope", default="platform-ops", help="Subdirectory to scan, default platform-ops")
    args = parser.parse_args()
    root = vault_root(args.vault_root)
    scan_root = root / args.scope
    if not scan_root.exists():
        return print_validation([f"scope not found: {scan_root}"])

    errors: list[str] = []
    warnings: list[str] = []
    for md in list_markdown_files(scan_root):
        for raw in re.findall(r"\[\[([^\]]+)\]\]", strip_code_examples(read_text(md))):
            target = wikilink_target(raw)
            if not link_exists(root, target):
                warnings.append(f"{md.relative_to(root)}: unresolved wikilink [[{raw}]]")

    print("plan:")
    print(f"- scan wikilinks under: {scan_root}")
    print("\ndiff preview:")
    print("(read-only)")
    return print_validation(errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
