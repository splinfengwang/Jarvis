# Memory Backend Interface

## 目的

Jarvis 的记忆检索（Core §6.3）通过可替换的后端适配器实现。默认使用零依赖的文件系统后端，可选 OpenViking 语义搜索。

## 接口

每个后端实现以下操作：

| 方法 | 签名 | 说明 |
|---|---|---|
| `search(query, scope="memory")` | `list[dict]` | 搜索，返回 `[{key, content, score}]` |
| `read(key)` | `str` | 读取指定 key 的内容 |
| `write(key, content)` | `bool` | 写入内容，返回是否成功 |
| `delete(key)` | `bool` | 删除指定 key |
| `available()` | `bool` | 后端是否可用 |

## 后端配置

在 `jarvis.yaml` 中声明：

```yaml
backend: file          # 默认文件后端
# backend: openviking  # 可选语义搜索后端
```

## File Backend（默认）

- **零依赖**：基于 `grep` + 文件系统
- **搜索范围**：按 scope 限定目录
  - `memory` → `~/.claude/projects/{project}/memory/` 或项目本地 memory 目录
  - `project` → 项目根目录下所有 .md 文件
- **匹配**：关键词 grepping，按修改时间排序
- **写入**：直接写文件

## OpenViking Backend（可选）

- **依赖**：openviking-server 运行中
- **搜索**：语义向量搜索
- **适配器**：`backends/openviking/adapter.py`
- **安装**：`pip install jarvis-agent[openviking]`

## 降级策略

Core §6.3 已定义降级：语义搜索不可用 → 读仪表盘 → 本地 grep → 提示"记忆检索暂不可用"。

后端 `available()` 返回 False 时，自动降级到 file 后端。
