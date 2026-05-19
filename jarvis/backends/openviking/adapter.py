#!/usr/bin/env python3
"""OpenViking backend adapter — semantic vector search via OpenViking server."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional


class OpenVikingBackend:
    """Semantic search via OpenViking server."""

    def __init__(self, project_root: Path, config_path: Optional[Path] = None):
        self._root = Path(project_root).resolve()
        self._config = config_path or Path.home() / ".openviking" / "ov.conf"
        self._available: Optional[bool] = None

    def available(self) -> bool:
        if self._available is not None:
            return self._available
        # Check if openviking-server is reachable
        try:
            result = subprocess.run(
                ["ov", "status"],
                capture_output=True, text=True, timeout=5,
            )
            self._available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._available = False
        return self._available

    def search(self, query: str, scope: str = "memory") -> list[dict]:
        """Semantic search via `ov find`."""
        if not self.available():
            return []

        try:
            result = subprocess.run(
                ["ov", "find", query, "--limit", "20", "--json"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            results = []
            for item in data if isinstance(data, list) else data.get("results", []):
                results.append({
                    "key": item.get("key", item.get("path", "")),
                    "content": item.get("content", item.get("text", ""))[:2000],
                    "score": item.get("score", item.get("distance", 0.0)),
                    "path": item.get("path", ""),
                })
            return results
        except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def read(self, key: str) -> str:
        """Read via OpenViking memread."""
        if not self.available():
            return ""
        try:
            result = subprocess.run(
                ["ov", "memread", key],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def write(self, key: str, content: str) -> bool:
        """Write via OpenViking memcommit."""
        if not self.available():
            return False
        try:
            result = subprocess.run(
                ["ov", "memcommit", "--key", key, "--content", content],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def delete(self, key: str) -> bool:
        if not self.available():
            return False
        try:
            result = subprocess.run(
                ["ov", "delete", key],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


def create_backend(project_root: Path, **kwargs) -> OpenVikingBackend:
    return OpenVikingBackend(project_root, **kwargs)
