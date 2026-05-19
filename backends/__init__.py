#!/usr/bin/env python3
"""Memory backend factory — loads the configured backend for a project."""

from __future__ import annotations

from pathlib import Path

from jarvis_lib import load_jarvis_config


def get_backend(project_root: Path | None = None):
    """Return the configured memory backend for a project.

    Reads jarvis.yaml → backend field. Falls back to file backend.
    """
    if project_root is None:
        project_root = Path.cwd()
    root = Path(project_root).resolve()
    config = load_jarvis_config(root)
    backend_name = config.get("backend", "file")

    if backend_name == "openviking":
        try:
            from backends.openviking.adapter import create_backend
            return create_backend(root)
        except (ImportError, Exception):
            pass

    # Default: file backend (always available)
    from backends.file.adapter import create_backend
    return create_backend(root)
