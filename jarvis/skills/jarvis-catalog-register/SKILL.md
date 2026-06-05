---
name: jarvis-catalog-register
description: 发现/创建内容目录 → 与用户确认用途和写入权限 → 注册到 jarvis.yaml。用于“建个目录叫 X”“以后 X 类内容都放这里”“把这个分析存到 X/”等目录注册场景。
---

# jarvis-catalog-register

## 定位

Jarvis 通过 `jarvis.yaml` 的 `catalogs` 段感知项目中的内容目录。自动发现的目录默认为只读（只搜索、不写入）。用户需要创建或注册新目录时，由本 skill 完成确认和注册。

## 流程

### Step 1: 探测当前状态

使用 `jarvis.lib` 函数判断：

```python
from jarvis.lib import resolve_catalog, load_catalogs, unregistered_catalogs

existing = resolve_catalog(name, root)
```

| 状态 | 下一步 |
|---|---|
| 目录不存在 | → **分支 A**（创建 + 注册） |
| 存在但 `auto_discovered=True`（未注册） | → **分支 B**（只注册） |
| 存在且 `writable=False`（注册为只读） | → **分支 C**（变更权限） |
| 存在且 `writable=True` | → 告知用户已就绪，无需操作 |

### Step 2: 一次性确认（最多 1 个问题）

不要分两次问。一次确认两个决策点：

1. **用途描述**：这个目录放什么？一句话即可
2. **写入权限**：
   - A. 可写入 — 以后知识萃取、文件落档、分析文档都可以往里存
   - B. 只读 — Jarvis 只搜索和引用，不往里写任何东西

用户如已明确表达意图（如"建个设计文档目录放方案"），直接按意图执行，不需追问。

### Step 3: 执行

```python
from pathlib import Path
from jarvis.lib import register_catalog

root = Path.cwd()

# 分支 A：目录不存在 → 先创建
target_dir = root / catalog_name
target_dir.mkdir(parents=True, exist_ok=True)

# 注册
register_catalog(root, catalog_name, writable=True_or_False, description="用户的描述")
```

### Step 4: 验证

读回 `jarvis.yaml`，确认新条目已写入。告知用户：
- 目录路径
- 写入权限状态
- 生效说明：当前会话的 hook 注入是静态的，catalog 列表在下次新会话的 SessionStart 时生效。当前会话中 Jarvis 知道这个目录，但 path config 不会实时刷新。

### Step 5: 后续联动（可选）

- 如果是从 `jarvis-file-process` 转过来的（"把这个分析存到 X/"），注册完成后继续执行文件写入
- 如果是主动创建目录，询问用户是否要立即往里写东西

## inputs

- 用户指定的目录名称
- 当前项目的 `jarvis.yaml`
- `jarvis.lib` 的 `resolve_catalog()` / `unregistered_catalogs()` / `register_catalog()`

## outputs

- 目录路径（新建或确认已有）
- `jarvis.yaml` 中更新后的 `catalogs` 条目
- 用户确认的用途描述和写入权限

## write_level

- `record_write`：创建目录（`mkdir`）是文件系统操作，不属于内容性写入
- `content_write`：修改 `jarvis.yaml` 属于内容性写入，必须先提案、用户确认后执行

## confirmation_rules
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- 写后验证：读回 `jarvis.yaml` 确认条目存在

## fallback_rules
（通用规则见 JARVIS_CORE §4/§6/§7。以下仅列本 skill 特有规则）
- `jarvis.yaml` 不存在时停止，提示用户先执行 `jarvis init`
- `jarvis.lib` 导入失败时，手工编辑 `jarvis.yaml` 的 `catalogs` 段
- 注册失败时，告知用户具体的失败原因，不要静默跳过

