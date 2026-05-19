# Research Card: Platform Adapter Boundaries

source_project: AnythingLLM / Onyx / Open WebUI / Letta
source_url: https://github.com/Mintplex-Labs/anything-llm ; https://github.com/onyx-dot-app/onyx ; https://github.com/open-webui/open-webui ; https://github.com/letta-ai/letta
source_revision:
- AnythingLLM: `b1e5b6f961ed88c6d0f6f55186f4734ed3cd9439`
- Onyx: `49d0055da99ddfea32ab6108e08c49b0586d413c`
- Open WebUI: `3660bc00fd807deced3400a63bfa6db47811a3bb`
- Letta: `1131535716e8a31c9a437f8695e25ac98f203a24`

source_paths:
- `https://github.com/Mintplex-Labs/anything-llm/blob/b1e5b6f961ed88c6d0f6f55186f4734ed3cd9439/server/endpoints/mcpServers.js`
- `https://github.com/Mintplex-Labs/anything-llm/blob/b1e5b6f961ed88c6d0f6f55186f4734ed3cd9439/server/endpoints/agentSkillWhitelist.js`
- `https://github.com/onyx-dot-app/onyx/tree/49d0055da99ddfea32ab6108e08c49b0586d413c/backend/onyx/connectors`
- `https://github.com/onyx-dot-app/onyx/tree/49d0055da99ddfea32ab6108e08c49b0586d413c/docs`
- `https://github.com/open-webui/open-webui/tree/3660bc00fd807deced3400a63bfa6db47811a3bb/backend/open_webui/routers`
- `https://github.com/letta-ai/letta/tree/1131535716e8a31c9a437f8695e25ac98f203a24/letta`

mechanism_summary:
- 平台型 agent/RAG 系统普遍把 connector、工具权限、workspace 权限和 stateful memory 分开。
- AnythingLLM 有 MCP server 和 agent skill whitelist。
- Onyx 有 connector/RBAC/文档权限边界。
- Open WebUI 有工具/路由/API token/session 权限处理。
- Letta 强调 stateful agent memory 和 tool approval。

jarvis_mapping:
- 第一阶段只抽 adapter 边界，不接入这些平台。
- Claude Code 为主入口；Codex 只保持结构兼容。
- DeepSeek 接入需要单独 adapter，不把模型接入与 Jarvis workflow 混在一起。

adopted_parts:
- connector 权限边界必须显式。
- stateful memory 不能绕过知识确认。
- 工具白名单/可写范围必须受 settings 和 skill write_level 控制。

rejected_parts:
- 不实现 RAG 平台。
- 不实现统一 connector layer。
- 不接入 Letta-style stateful memory。
- 不把外部平台作为第一期依赖。

usable_rule:
- adapter 能读什么、写什么、是否可调用外部工具，必须先由 settings 和 skill 声明；未声明即不可用。

test_case:
- 输入：“接 DeepSeek 到 Codex 里试试。”
- 期望：Router 输出 adapter/setup intent，标记为第一期外，不直接修改 provider 配置或泄露 token。

failure_trigger_for_research:
- adapter 权限边界不清、模型接入影响 Topic/知识流程、或外部工具绕过 confirmation rules 时，回到平台 connector/permission/stateful memory 模型重新研究。
