#!/usr/bin/env bash
# Jarvis install script — installs Jarvis framework into a target project.
#
# Usage: bash install.sh [target-project-dir]
#   If target-project-dir is omitted, defaults to current directory.
#
# What it does:
#   1. Detects target project structure
#   2. Creates symlinks: .claude/skills/<skill> → jarvis/skills/<skill>
#   3. Creates symlinks: .claude/hooks/<hook> → jarvis/hooks/<hook>
#   4. Generates CLAUDE.md if missing
#   5. Generates .claude/settings.json if missing (hook config)
#   6. Creates jarvis.yaml config
#   7. Initializes knowledge base directory tree
#   8. Initializes platform-ops/ skeleton (dashboard + log)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JARVIS_PKG="$SCRIPT_DIR/jarvis"  # Python package dir (core/hooks/skills/templates live here)
TARGET="${1:-$(pwd)}"

echo "=== Jarvis v1.7.0 Install ==="
echo "Target: $TARGET"
echo "Jarvis:  $JARVIS_PKG"

# ---------------------------------------------------------------------------
# 1. Create .claude directories
# ---------------------------------------------------------------------------
mkdir -p "$TARGET/.claude/skills" "$TARGET/.claude/hooks"

# ---------------------------------------------------------------------------
# 2. Symlink skills
# ---------------------------------------------------------------------------
echo ""
echo "--- Linking skills ---"
for skill_dir in "$JARVIS_PKG/skills"/*/; do
    skill_name=$(basename "$skill_dir")
    target_link="$TARGET/.claude/skills/$skill_name"
    if [ -L "$target_link" ] || [ -d "$target_link" ]; then
        echo "  [skip] $skill_name (already exists)"
    else
        ln -s "$skill_dir" "$target_link"
        echo "  [ok]   $skill_name"
    fi
done

# ---------------------------------------------------------------------------
# 3. Symlink hooks
# ---------------------------------------------------------------------------
echo ""
echo "--- Linking hooks ---"
for hook in "$JARVIS_PKG/hooks"/*.sh; do
    hook_name=$(basename "$hook")
    target_link="$TARGET/.claude/hooks/$hook_name"
    if [ -L "$target_link" ] || [ -f "$target_link" ]; then
        echo "  [skip] $hook_name (already exists)"
    else
        ln -s "$hook" "$target_link"
        echo "  [ok]   $hook_name"
    fi
done

# ---------------------------------------------------------------------------
# 4. Generate CLAUDE.md if missing
# ---------------------------------------------------------------------------
if [ -f "$TARGET/CLAUDE.md" ]; then
    echo ""
    echo "  [skip] CLAUDE.md already exists"
else
    cat > "$TARGET/CLAUDE.md" << 'CLAUDE_EOF'
# 项目默认智能体入口

本项目使用 [Jarvis](https://github.com/linfeng/jarvis) (v1.7.0) 作为智能体框架。

## 启动规则

1. 会话启动时，Core 通过 SessionStart hook 自动注入上下文。
2. Hook 不可用时，手动读取 jarvis 安装目录下的 `core/JARVIS_BOOTSTRAP.md` 并遵循。
3. Jarvis 的 skill、scripts、references 构成完整的可执行工作流。

## 默认边界

- 不自动修改 Core 文件。
- 不自动知识入库。
- 不把记忆检索命中当事实。
- 写入动作按 Core 写入裁决 + `references/write-permission.md` 执行。

## 项目配置

见 `jarvis.yaml`。
CLAUDE_EOF
    echo "  [ok]   CLAUDE.md generated"
fi

# ---------------------------------------------------------------------------
# 5. Generate settings.json if missing
# ---------------------------------------------------------------------------
if [ -f "$TARGET/.claude/settings.json" ]; then
    echo "  [skip] .claude/settings.json already exists"
else
    cat > "$TARGET/.claude/settings.json" << 'SETTINGS_EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(**/.env)",
      "Read(**/.env.*)",
      "Read(**/secrets/**)",
      "Read(**/*secret*)",
      "Read(**/*token*)"
    ],
    "disableBypassPermissionsMode": "disable"
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|compact",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PROJECT_DIR}/.claude/hooks/jarvis-core-inject.sh\"",
            "timeout": 15
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PROJECT_DIR}/.claude/hooks/jarvis-write-guard.sh\"",
            "timeout": 15
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PROJECT_DIR}/.claude/hooks/jarvis-compact-save.sh\"",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
SETTINGS_EOF
    echo "  [ok]   .claude/settings.json generated"
fi

# ---------------------------------------------------------------------------
# 6. Generate jarvis.yaml if missing
# ---------------------------------------------------------------------------
JARVIS_HOME="$JARVIS_PKG"
if [ -f "$TARGET/jarvis.yaml" ]; then
    echo "  [skip] jarvis.yaml already exists"
else
    cat > "$TARGET/jarvis.yaml" << YAML_EOF
# Jarvis project configuration
jarvis_version: "1.7.0"
jarvis_home: "${JARVIS_HOME}"

paths:
  knowledge_base: 知识库
  wiki_index: 知识库/wiki索引.md
  terms_dir: 知识库/术语
  terms_index: 知识库/术语/术语索引.md
  business_dir: 业务
  ops_dir: platform-ops
  dashboard: platform-ops/仪表盘.md
  log: platform-ops/log.md
  topics: platform-ops/topics

plugins: []

backend: file
YAML_EOF
    echo "  [ok]   jarvis.yaml generated"
fi

# ---------------------------------------------------------------------------
# 7. Initialize knowledge base directory tree
# ---------------------------------------------------------------------------
echo ""
echo "--- Initializing knowledge base ---"
mkdir -p "$TARGET/知识库/术语"
mkdir -p "$TARGET/业务"

if [ ! -f "$TARGET/知识库/wiki索引.md" ]; then
    date=$(date +%Y-%m-%d)
    cat > "$TARGET/知识库/wiki索引.md" << KB_EOF
---
tags: [索引, wiki导航]
created: $date
last_updated: $date
---

# Wiki 索引

> 全 wiki 扁平导航表。覆盖术语、分析文档、决策记录。每行含链接 + 一句话摘要 + 状态。

---

## 术语（L1）

| 页面 | 一句话摘要 | 状态 |
|------|-----------|------|
| （暂无） | — | — |

---

## 分析文档

（暂无）

---

## 决策记录

（暂无）
KB_EOF
    echo "  [ok]   知识库/wiki索引.md"
fi

if [ ! -f "$TARGET/知识库/术语/术语索引.md" ]; then
    cat > "$TARGET/知识库/术语/术语索引.md" << TI_EOF
---
tags: [索引, 术语]
last_updated: $date
---

# 术语索引

> 按 domain 分组导航，每个术语一条独立笔记。

（暂无术语）
TI_EOF
    echo "  [ok]   知识库/术语/术语索引.md"
fi

# ---------------------------------------------------------------------------
# 8. Initialize platform-ops skeleton
# ---------------------------------------------------------------------------
echo ""
echo "--- Initializing platform-ops ---"
mkdir -p "$TARGET/platform-ops/topics"

if [ ! -f "$TARGET/platform-ops/仪表盘.md" ]; then
    cat > "$TARGET/platform-ops/仪表盘.md" << DB_EOF
---
tags:
  - 仪表盘
  - 启动入口
assistant: Jarvis
last_reviewed: $date
---

# 工作启动仪表盘（Jarvis）

> 用途：每次会话启动时的第一信息源。

---

## 活跃 Topic

| 状态 | Topic | 上次更新 | 下一步 | |
|---|---|---|---|---|
| （暂无） | — | — | — | |

## 待萃取

| 状态 | Topic | 上次更新 | 下一步 | |
|---|---|---|---|---|
| （暂无） | — | — | — | |

## 已归档

| 状态 | Topic | 完成时间 | 备注 |
|---|---|---|---|
| （暂无） | — | — | — |

## 跟进事项

| 事项 | 截止/窗口 | 状态 | 动作 |
|------|------|------|------|
| （暂无） | — | — | — |

## 待拍板

- （暂无）

---

## 维护规则

1. 本页按双区结构维护：活跃 Topic + 跟进事项
2. Topic 状态按状态图例，通过三位一体同步更新
3. 已完成 Topic 移入"已归档"区，不删除
4. 状态变更时立即更新
DB_EOF
    echo "  [ok]   platform-ops/仪表盘.md"
fi

if [ ! -f "$TARGET/platform-ops/log.md" ]; then
    cat > "$TARGET/platform-ops/log.md" << LOG_EOF
# 操作日志

> append-only 操作记录。格式：`## [YYYY-MM-DD] 操作类型 | 简述`

---

## [$date] install | Jarvis v1.7.0 安装
LOG_EOF
    echo "  [ok]   platform-ops/log.md"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=== Install complete ==="
echo ""
echo "Next steps:"
echo "  1. Review jarvis.yaml and adjust paths if needed"
echo "  2. Start a new Claude Code session — Core will auto-inject via hook"
echo "  3. Run 'jarvis doctor' to verify installation"
