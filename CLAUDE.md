# Jarvis Source Repo

> 这是 Jarvis 框架源码仓库的智能体入口，不是产品介绍页。产品说明见 `README.md`。

## 启动规则

1. 进入本仓库会话后，先读取 `jarvis/core/JARVIS_BOOTSTRAP.md`。
2. 再读取 `jarvis/core/JARVIS_CORE_BRIEF.md`；只有需要细节时再查 `jarvis/core/JARVIS_CORE_FULL.md`。
3. 处理需求前，先判断当前工作属于哪一层：
   - 框架/协议变更：优先看 `jarvis/core/`、`jarvis/references/`、`jarvis/skills/`
   - 平台接入：优先看 `jarvis/installers/`、`jarvis/platform_support.py`、`postinstall.js`
   - 会话/写入守卫：优先看 `jarvis/hooks/`
   - 回归验证：优先看 `tests/`
4. 若涉及 Reasonix / Codex / Claude 的平台差异，先区分事实、假设、推论，再改代码。

## 仓库边界

- 本仓库自身不是通过 `jarvis init` 生成的业务项目；不要假设这里一定存在 `jarvis.yaml`。
- 产品介绍、安装说明、升级指南分别以 `README.md`、`CHANGELOG.md`、`UPGRADING-v2.md` 为准。
- 修改框架协议时，优先保证多平台行为一致、可验证、可回退。

## 默认禁令

- 不把 skill 可见性当作协议已生效。
- 不把全局配置当作项目级配置一定生效；`reasonix.toml` / `.codex` / `.claude` 的本地覆盖优先检查。
- 不在未验证平台真实入口前声称“已适配”。
