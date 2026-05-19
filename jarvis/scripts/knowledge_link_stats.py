#!/usr/bin/env python3
"""Count Obsidian wikilink references for knowledge and business documents."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from jarvis.lib import list_markdown_files, print_validation, read_text, vault_root, write_json_result


DEFAULT_SCOPES = ["知识库", "业务", "platform-ops/topics"]


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


def wikilink_target(raw: str) -> str:
    target = raw.split("|", 1)[0].strip()
    return target.rstrip("\\").split("#", 1)[0].strip()


def target_candidates(root: Path, target: str, stem_index: dict[str, list[Path]]) -> list[Path]:
    if not target or target.startswith(("http://", "https://")):
        return []
    direct = root / target
    candidates = [direct] if direct.suffix == ".md" else [Path(str(direct) + ".md"), direct]
    existing = [path for path in candidates if path.exists()]
    if existing:
        return existing
    if "/" not in target:
        return stem_index.get(target, [])
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", default=".")
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Subdirectory to scan. Repeatable. Defaults to 知识库, 业务, platform-ops/topics.",
    )
    args = parser.parse_args()

    root = vault_root(args.vault_root)
    scopes = args.scope or DEFAULT_SCOPES
    warnings: list[str] = []
    errors: list[str] = []

    scan_files: list[Path] = []
    for scope in scopes:
        scan_root = root / scope
        if not scan_root.exists():
            warnings.append(f"scope not found: {scan_root}")
            continue
        scan_files.extend(list_markdown_files(scan_root))

    if not scan_files:
        errors.append("no markdown files found in requested scopes")

    all_markdown = list_markdown_files(root)
    stem_index: dict[str, list[Path]] = {}
    for path in all_markdown:
        stem_index.setdefault(path.stem, []).append(path)

    incoming: Counter[Path] = Counter()
    outgoing: Counter[Path] = Counter()
    unresolved: Counter[str] = Counter()

    for source in scan_files:
        text = strip_code_examples(read_text(source))
        for raw in re.findall(r"\[\[([^\]]+)\]\]", text):
            target = wikilink_target(raw)
            matches = target_candidates(root, target, stem_index)
            if matches:
                outgoing[source] += 1
                incoming[matches[0]] += 1
            elif target:
                outgoing[source] += 1
                unresolved[target] += 1

    rows = []
    for path in sorted(scan_files):
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "incoming": incoming[path],
                "outgoing": outgoing[path],
            }
        )
    zero_incoming = [
        row["path"]
        for row in rows
        if row["incoming"] == 0 and not row["path"].endswith(("索引.md", "wiki索引.md"))
    ]
    payload = {
        "scopes": scopes,
        "scanned_files": len(scan_files),
        "resolved_links": sum(incoming.values()),
        "unresolved_links": dict(sorted(unresolved.items())),
        "zero_incoming": zero_incoming[:100],
        "files": rows,
    }

    print("plan:")
    print(f"- scan wikilink reference counts under: {', '.join(scopes)}")
    print("\ndiff preview:")
    print("(read-only)")
    write_json_result(payload)
    return print_validation(errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
