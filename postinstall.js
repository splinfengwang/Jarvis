#!/usr/bin/env node
/**
 * Jarvis npm postinstall — 全局注册 skill 和 hook 到 Claude Code。
 *
 * 做的事：
 *   1. 把所有 skill 软链到 ~/.claude/skills/
 *   2. 把所有 hook 脚本软链到 ~/.claude/hooks/
 *   3. 把 hook 触发配置合并写入 ~/.claude/settings.json
 *
 * 安全约定：
 *   - 已有同名 skill/hook → 跳过（不覆盖用户自定义）
 *   - 已有 settings.json → 合并而非覆盖
 *   - 所有操作可安全重复执行
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const PACKAGE_ROOT = __dirname;
const CLAUDE_DIR = path.join(os.homedir(), '.claude');
const SKILLS_SRC = path.join(PACKAGE_ROOT, 'jarvis', 'skills');
const HOOKS_SRC = path.join(PACKAGE_ROOT, 'jarvis', 'hooks');
const SKILLS_DST = path.join(CLAUDE_DIR, 'skills');
const HOOKS_DST = path.join(CLAUDE_DIR, 'hooks');
const SETTINGS_PATH = path.join(CLAUDE_DIR, 'settings.json');

const HOOK_CONFIG = {
  SessionStart: [
    {
      matcher: 'startup|resume|compact',
      hooks: [
        {
          type: 'command',
          command: `bash "${HOOKS_DST}/jarvis-core-inject.sh"`,
          timeout: 15,
        },
      ],
    },
  ],
  PreToolUse: [
    {
      matcher: 'Write|Edit|MultiEdit|Bash',
      hooks: [
        {
          type: 'command',
          command: `bash "${HOOKS_DST}/jarvis-write-guard.sh"`,
          timeout: 15,
        },
      ],
    },
  ],
  PreCompact: [
    {
      matcher: '*',
      hooks: [
        {
          type: 'command',
          command: `bash "${HOOKS_DST}/jarvis-compact-save.sh"`,
          timeout: 15,
        },
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// 工具函数
// ---------------------------------------------------------------------------

function symlink(src, dst, label) {
  try {
    if (fs.existsSync(dst)) {
      const stat = fs.lstatSync(dst);
      if (stat.isSymbolicLink() && fs.realpathSync(dst) === fs.realpathSync(src)) {
        console.log(`  [skip] ${label} (already linked)`);
        return;
      }
      console.log(`  [skip] ${label} (path exists — not overwriting)`);
      return;
    }
    fs.symlinkSync(src, dst);
    console.log(`  [ok]   ${label}`);
  } catch (err) {
    console.error(`  [ERROR] ${label} — ${err.message}`);
  }
}

function hasJarvisHooks(settings) {
  // Check if settings already contains Jarvis hook config
  const hooks = settings.hooks || {};
  for (const event of ['SessionStart', 'PreToolUse', 'PreCompact']) {
    const list = hooks[event] || [];
    for (const entry of list) {
      for (const h of entry.hooks || []) {
        if (h.command && h.command.includes('jarvis-')) {
          return true;
        }
      }
    }
  }
  return false;
}

function mergeSettings(existing, incoming) {
  // Deep merge: incoming overrides existing on conflict
  const merged = JSON.parse(JSON.stringify(existing));
  for (const [key, value] of Object.entries(incoming)) {
    if (key === 'hooks') {
      // Hook merge: concat arrays per hook event
      merged.hooks = merged.hooks || {};
      for (const [event, hookList] of Object.entries(value)) {
        merged.hooks[event] = merged.hooks[event] || [];
        merged.hooks[event].push(...hookList);
      }
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      merged[key] = mergeSettings(merged[key] || {}, value);
    } else {
      merged[key] = value;
    }
  }
  return merged;
}

// ---------------------------------------------------------------------------
// 主流程
// ---------------------------------------------------------------------------

console.log('');
console.log('=== Jarvis v1.9.0 — postinstall ===');

// 1. 创建目录
fs.mkdirSync(SKILLS_DST, { recursive: true });
fs.mkdirSync(HOOKS_DST, { recursive: true });

// 2. 软链 skills
const skillDirs = fs.readdirSync(SKILLS_SRC, { withFileTypes: true })
  .filter(d => d.isDirectory())
  .map(d => d.name);

console.log(`\n--- Linking skills (${skillDirs.length} found) ---`);
for (const name of skillDirs) {
  symlink(
    path.join(SKILLS_SRC, name),
    path.join(SKILLS_DST, name),
    name
  );
}

// 3. 软链 hooks
const hookFiles = fs.readdirSync(HOOKS_SRC, { withFileTypes: true })
  .filter(f => f.isFile() && f.name.endsWith('.sh'))
  .map(f => f.name);

console.log(`\n--- Linking hooks (${hookFiles.length} found) ---`);
for (const name of hookFiles) {
  symlink(
    path.join(HOOKS_SRC, name),
    path.join(HOOKS_DST, name),
    name
  );
}

// 4. 写入 settings.json
console.log('\n--- Configuring hooks ---');
const force = process.env.FORCE_JARVIS_HOOKS === '1';
let settings;
if (fs.existsSync(SETTINGS_PATH)) {
  try {
    settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf-8'));
  } catch {
    console.log('  [warn] settings.json parse failed — creating new');
    settings = {};
  }
} else {
  settings = {};
}

if (!force && hasJarvisHooks(settings)) {
  console.log('  [skip] Hook config unchanged (already present)');
} else {
  if (force) {
    console.log('  [info] FORCE_JARVIS_HOOKS=1 — rewriting hook config');
  } else {
    console.log('  [info] Merging into ~/.claude/settings.json');
  }
  settings = mergeSettings(settings, { hooks: HOOK_CONFIG });
  fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2) + '\n');
  console.log('  [ok]   Hook config written to ~/.claude/settings.json');
}

// 5. 提示下一步
console.log('');
console.log('=== Done ===');
console.log('');
console.log('Jarvis skills and hooks are now available in all Claude Code projects.');
console.log('To initialize a project:');
console.log('  cd ~/my-project && jarvis init');
console.log('Or in any Claude Code session, type /jarvis-init');
