# Plugin System

## 目的

Jarvis Core 包含通用行为规程。领域特定的安全规则、校验清单、知识分类维度通过"领域插件"挂载。插件不修改 Core，只在注入时替换占位符。

## 插件目录

```
plugins/{name}/
├── plugin.yaml       # 元信息（必需）
├── {module}.md       # 模块内容文件（由 plugin.yaml 声明）
└── ...
```

## plugin.yaml

```yaml
name: <plugin-name>        # 唯一标识
version: <semver>          # 版本号
description: <text>        # 一句话描述
provides:                  # 模块 → 文件 映射
  MODULE_NAME: file.md     # 键名对应 Core 中的 {{PLUGIN:MODULE_NAME}}
parameters:                # （可选）可配置参数
  key: value
```

`provides` 中的键名必须与 Core 中的占位符名匹配。例如 `SAFETY: safety.md` → 替换 `{{PLUGIN:SAFETY}}`。

## Core 占位符

Core 中使用 `{{PLUGIN:NAME}}` 作为注入点：

```markdown
## 7.3 领域决策边界

通用描述...

{{PLUGIN:SAFETY}}

## 7.4 校验规则

通用框架...
```

## 注入规则

1. 会话启动时，SessionStart hook 读取项目的 `jarvis.yaml`，找到 `plugins: [name1, name2]`
2. 对每个激活的插件，读取 `plugin.yaml`，找到 `provides` 映射
3. 对每个 `provides` 条目，读取对应模块文件内容，替换 Core 中的 `{{PLUGIN:NAME}}`
4. 未被任何插件覆盖的占位符：删除该行（空置）
5. 多个插件提供同一模块：按 plugins 列表顺序，后声明的覆盖

## 安装

插件安装到 jarvis 的 `plugins/` 目录或项目本地目录。在项目的 `jarvis.yaml` 中声明：

```yaml
plugins:
  - medical-safety
```

## 禁用

从 `jarvis.yaml` 的 `plugins` 列表中移除即可。Core 恢复为通用模式（占位符行空置）。

## 默认行为

无插件激活时，Core 中的 `{{PLUGIN:*}}` 占位符被删除，对应章节仅保留通用框架内容。项目可正常运行，不强制安装任何领域插件。
