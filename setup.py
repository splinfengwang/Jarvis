#!/usr/bin/env python3
"""Jarvis — LLM-native agent framework."""

from setuptools import setup, find_packages

setup(
    name="jarvis-agent",
    version="1.0.0",
    description="Jarvis — An LLM-native agent framework for long-term work assistance.",
    author="Lin Feng",
    license="MIT",
    packages=find_packages(where="scripts"),
    package_dir={"": "scripts"},
    py_modules=["jarvis_lib"],
    entry_points={
        "console_scripts": [
            "jarvis=jarvis_cli:main",
        ],
    },
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "openviking": ["openviking-client"],
    },
)
