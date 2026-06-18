#!/usr/bin/env python3
"""Jarvis — LLM-native agent framework."""

from pathlib import Path
import re
from setuptools import setup, find_packages

# Read version from __init__.py (single source of truth for Python side)
_init = Path(__file__).parent / "jarvis" / "__init__.py"
_version = re.search(r'__version__\s*=\s*"([^"]+)"', _init.read_text(encoding="utf-8")).group(1)

setup(
    name="jarvis-agent",
    version=_version,
    description="Jarvis — An LLM-native agent framework for long-term work assistance.",
    author="Lin Feng",
    license="MIT",
    packages=find_packages(include=["jarvis", "jarvis.*"]),
    include_package_data=True,
    package_data={
        "jarvis": [
            "core/*.md",
            "references/*.md",
            "skills/*/SKILL.md",
            "skills/*/agents/openai.yaml",
            "hooks/*.sh",
            "installers/*.sh",
            "plugins/*/*.md",
            "plugins/*/*.yaml",
            "backends/*/*.py",
            "backends/*.py",
            "templates/*.md.tmpl",
            "templates/*.json.tmpl",
            "templates/*.md",
            "templates/Topic骨架/*.md",
            "scripts/*.py",
            "scripts/*.md",
            "research-cards/*.md",
            "AGENT_v3.4.md",
        ],
    },
    entry_points={
        "console_scripts": [
            "jarvis=jarvis.cli:main",
        ],
    },
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "openviking": ["openviking-client"],
    },
)
