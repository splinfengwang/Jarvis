#!/usr/bin/env node
/**
 * Jarvis npm postinstall — 多平台注册入口。
 *
 * 检测目标平台（JARVIS_TARGET 环境变量或自动检测），
 * 调用对应平台的 installer。
 *
 * 安全约定：
 *   - 已有同名 skill/hook → 跳过（不覆盖用户自定义）
 *   - 已有平台配置文件 → 合并而非覆盖
 *   - 所有操作可安全重复执行
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PACKAGE_ROOT = __dirname;
const JARVIS_CLI = path.join(PACKAGE_ROOT, 'jarvis', 'cli.py');

// ── 平台检测 ──

function detectPlatform() {
  const fromEnv = process.env.JARVIS_TARGET;
  if (fromEnv && ['claude', 'reasonix', 'codex', 'all'].includes(fromEnv)) {
    return fromEnv;
  }
  const installCwd = process.env.INIT_CWD || process.cwd();
  const hasReasonix = fs.existsSync(path.join(installCwd, 'reasonix.toml'))
    || fs.existsSync(path.join(installCwd, '.reasonix'));
  const hasCodex = fs.existsSync(path.join(installCwd, '.codex'));

  if (hasReasonix && !hasCodex) return 'reasonix';
  if (hasCodex && !hasReasonix) return 'codex';
  return 'claude';
}

// ── 主流程 ──

const target = detectPlatform();
console.log(`\n=== Jarvis v${process.env.npm_package_version || '?'} — postinstall (target: ${target}) ===\n`);

try {
  execSync(
    `python3 "${JARVIS_CLI}" install --target ${target}`,
    { cwd: PACKAGE_ROOT, stdio: 'inherit', env: { ...process.env, JARVIS_HOME: path.join(PACKAGE_ROOT, 'jarvis') } }
  );
  console.log('\n=== Done ===');
  console.log('Jarvis installed successfully.');
  console.log('To initialize a project:  cd ~/my-project && jarvis init');
} catch (err) {
  console.error(`\n[Jarvis] Installation failed for target: ${target}`);
  console.error(err.message);
  process.exit(1);
}
