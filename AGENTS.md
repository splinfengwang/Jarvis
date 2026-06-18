# Jarvis Source Repo

> 这是 Jarvis 框架源码仓库的通用智能体入口，供 Codex / Reasonix / 其他读取 `AGENTS.md` 的运行时使用。

## Startup

1. Read `jarvis/core/JARVIS_BOOTSTRAP.md`.
2. Then read `jarvis/core/JARVIS_CORE_BRIEF.md`.
3. Only read `jarvis/core/JARVIS_CORE_FULL.md` when you need protocol details or edge-case rules.

## Working Map

- Framework / protocol changes: start with `jarvis/core/`, `jarvis/references/`, `jarvis/skills/`
- Platform adapters: start with `jarvis/installers/`, `jarvis/platform_support.py`, `postinstall.js`
- Hook behavior: start with `jarvis/hooks/`
- Verification: start with `tests/`

## Repo-specific constraints

- This source repo itself is not a `jarvis init`-generated project. Do not assume `jarvis.yaml` exists here.
- Product docs live in `README.md`, `CHANGELOG.md`, and `UPGRADING-v2.md`.
- For multi-platform work, verify the real active entrypoint before concluding integration works.

## Default prohibitions

- Do not equate visible skills with active Jarvis protocol.
- Do not assume global config beats project-local `reasonix.toml` / `.codex` / `.claude` config.
- Do not claim adaptation is complete until the real runtime path has been verified.
