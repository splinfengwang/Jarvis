#!/usr/bin/env python3
"""File backend adapter — zero-dependency grep-based memory search."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


class FileBackend:
    """Grep-based memory search over local files."""

    def __init__(self, project_root: Path, memory_dir: Optional[Path] = None):
        self._root = Path(project_root).resolve()
        self._memory_dir = memory_dir or self._resolve_memory_dir()

    @staticmethod
    def _resolve_memory_dir() -> Path:
        """Resolve the per-project memory directory for Claude Code."""
        cwd = os.getcwd()
        encoded = cwd.lstrip("/").replace("/", "-")
        memory = Path.home() / ".claude" / "projects" / encoded / "memory"
        if memory.is_dir():
            return memory
        # Fallback: project-local memory dir
        return Path(cwd) / ".claude" / "memory"

    def available(self) -> bool:
        return True  # Always available (grep is universal)

    def search(self, query: str, scope: str = "memory") -> list[dict]:
        """Grep search. Returns [{key, content, score}] sorted by recency."""
        if scope == "memory":
            search_dir = self._memory_dir
        else:
            search_dir = self._root

        if not search_dir.is_dir():
            return []

        results: list[dict] = []
        try:
            # Use grep -rli to find matching files
            proc = subprocess.run(
                ["grep", "-rli", query, str(search_dir)],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode not in (0, 1):
                return []
            files = [Path(p) for p in proc.stdout.strip().split("\n") if p]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            files = []

        for f in files[:20]:  # Limit to 20 most recent
            try:
                mtime = f.stat().st_mtime
                content = f.read_text(encoding="utf-8")[:2000]
                results.append({
                    "key": str(f.relative_to(search_dir)),
                    "content": content,
                    "score": mtime,  # Use mtime as score proxy
                    "path": str(f),
                })
            except Exception:
                continue

        # Sort by recency (higher mtime = more recent)
        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    def read(self, key: str) -> str:
        """Read memory file by key (relative path from memory dir)."""
        path = self._memory_dir / key
        if path.is_file():
            return path.read_text(encoding="utf-8")
        # Try project root
        path = self._root / key
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return ""

    def write(self, key: str, content: str) -> bool:
        """Write to memory file."""
        path = self._memory_dir / key
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return True
        except OSError:
            return False

    def delete(self, key: str) -> bool:
        """Delete memory file (moves to Trash on macOS, unlinks otherwise)."""
        path = self._memory_dir / key
        if not path.exists():
            return False
        try:
            # Try macOS Trash first
            script = (
                'tell application "Finder" to delete '
                f'(POSIX file "{path}" as alias)'
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
        try:
            path.unlink()
            return True
        except OSError:
            return False


def create_backend(project_root: Path, **kwargs) -> FileBackend:
    return FileBackend(project_root, **kwargs)
