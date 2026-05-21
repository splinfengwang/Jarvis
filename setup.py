#!/usr/bin/env python3
"""Jarvis — LLM-native agent framework."""

from setuptools import setup, find_packages

setup(
    name="jarvis-agent",
    version="1.4.0",
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
            "hooks/*.sh",
            "plugins/*/*.md",
            "plugins/*/*.yaml",
            "backends/*/*.py",
            "backends/*.py",
            "templates/*.md.tmpl",
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
