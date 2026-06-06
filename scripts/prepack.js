#!/usr/bin/env node
/**
 * Jarvis prepack — 幂等版本注入脚本。
 *
 * 从 package.json 读取版本号，在所有源文件中查找并替换版本号模式。
 * 幂等：多次运行结果一致。源文件始终持有真实版本号。
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// ---------------------------------------------------------------------------
// 1. 读取版本号
// ---------------------------------------------------------------------------
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf-8'));
const version = pkg.version;

if (!version) {
  console.error('[prepack] ERROR: version not found in package.json');
  process.exit(1);
}

console.log(`[prepack] Version: ${version}`);

// ---------------------------------------------------------------------------
// 2. 文件列表：路径 → [pattern, replacement]
//    每个 pattern 匹配「任意版本号字符串」，确保幂等
// ---------------------------------------------------------------------------
const semver = /\d+\.\d+\.\d+/;

const targets = [
  // Python
  {
    file: 'jarvis/__init__.py',
    pattern: /__version__\s*=\s*"\d+\.\d+\.\d+"/,
    replacement: `__version__ = "${version}"`,
  },
  // Core markdown (version header)
  {
    file: 'jarvis/core/JARVIS_CORE_BRIEF.md',
    pattern: /> 版本：v\d+\.\d+\.\d+/,
    replacement: `> 版本：v${version}`,
  },
  {
    file: 'jarvis/core/JARVIS_CORE.md',
    pattern: /> 版本：v\d+\.\d+\.\d+/,
    replacement: `> 版本：v${version}`,
  },
  {
    file: 'jarvis/core/JARVIS_BOOTSTRAP.md',
    pattern: /> 状态：Jarvis v\d+\.\d+\.\d+ bootstrap/,
    replacement: `> 状态：Jarvis v${version} bootstrap`,
  },
  {
    file: 'jarvis/core/JARVIS_CORE_FULL.md',
    pattern: /> 版本：v\d+\.\d+\.\d+/,
    replacement: `> 版本：v${version}`,
  },
  // AGENT_v3.4 historical reference
  {
    file: 'jarvis/AGENT_v3.4.md',
    pattern: /当前 v\d+\.\d+\.\d+/,
    replacement: `当前 v${version}`,
  },
  // Plugin manifest
  {
    file: '.claude-plugin/plugin.json',
    pattern: /"version":\s*"\d+\.\d+\.\d+"/,
    replacement: `"version": "${version}"`,
  },
];

// ---------------------------------------------------------------------------
// 3. 注入
// ---------------------------------------------------------------------------
let count = 0;

for (const { file, pattern, replacement } of targets) {
  const filePath = path.join(ROOT, file);
  if (!fs.existsSync(filePath)) {
    console.warn(`[prepack] WARN: skip ${file} (not found)`);
    continue;
  }
  const before = fs.readFileSync(filePath, 'utf-8');
  if (!pattern.test(before)) {
    console.warn(`[prepack]   WARN: ${file} — no version pattern found`);
    continue;
  }
  const after = before.replace(pattern, replacement);
  if (after !== before) {
    fs.writeFileSync(filePath, after, 'utf-8');
    console.log(`[prepack]   injected ${file}`);
    count++;
  } else {
    console.log(`[prepack]   skip ${file} (already ${version})`);
  }
}

// ---------------------------------------------------------------------------
// 4. 清理 __pycache__
// ---------------------------------------------------------------------------
function cleanPyCache(dir) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory() && e.name === '__pycache__') {
      fs.rmSync(full, { recursive: true, force: true });
      console.log(`[prepack]   cleaned ${path.relative(ROOT, full)}`);
    } else if (e.isDirectory() && e.name !== 'node_modules' && !e.name.startsWith('.')) {
      cleanPyCache(full);
    }
  }
}
cleanPyCache(path.join(ROOT, 'jarvis'));

// ---------------------------------------------------------------------------
// 5. 验证
// ---------------------------------------------------------------------------
for (const { file, pattern } of targets) {
  const filePath = path.join(ROOT, file);
  if (!fs.existsSync(filePath)) continue;
  const content = fs.readFileSync(filePath, 'utf-8');
  if (!pattern.test(content)) {
    console.error(`[prepack] ERROR: version pattern not found in ${file} after injection`);
    process.exit(1);
  }
  // Check that the file has the current version
  const versionPattern = new RegExp(version.replace(/\./g, '\\.'));
  if (!versionPattern.test(content)) {
    console.error(`[prepack] ERROR: version ${version} not found in ${file} after injection`);
    process.exit(1);
  }
}

console.log(`[prepack] Done — ${count} files updated, all files verified.`);
