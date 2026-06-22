---
title: Kimi 联网搜索（Code API）
skill: kimi-search-v2
description: 通过 Kimi 服务端搜索服务进行联网搜索，返回结构化结果（标题、URL、摘要、可选完整页面内容）。与官方 Kimi Code CLI 的 WebSearch 工具使用相同后端。纯 Python 实现，无需额外依赖。支持中文和英文搜索查询。
version: 1.0.0
category: quanyuanai
tags: [kimi, search, web-search, internet-search, code-api, agent]
author: quanyuanai
---

# Kimi 联网搜索（Code API）

## 概述

搜索网页并获取**结构化结果** — 标题、URL、摘要，以及可选的完整页面内容。基于 Kimi 服务端搜索服务（`POST https://api.kimi.com/coding/v1/search`），与官方 Kimi Code CLI 的 `WebSearch` 工具使用相同后端。纯 Python 实现，无需额外依赖。

服务器自动处理：
- 执行网页搜索
- 从每个结果页面提取摘要
- 可选的完整页面爬取（使用 `--content` 时）

## 何时使用

- 用户要求搜索网页 / 在线查找信息
- 用户需要超出训练数据的当前信息
- 用户明确提到 "kimi search" / "web search" / "搜索" / "联网搜索"
- 需要为某个主题查找特定 URL 或来源
- 需要最新数据（新闻、价格、最新文档）进行分析
- 与 `kimi-fetch` 配合使用：先搜索找到 URL，再抓取完整内容

## 前置要求

### 自动配置（推荐）

本 skill 会自动检测并使用 Hermes 配置中的 Kimi 凭证，无需手动配置。

Token 检测优先级：
1. `--token` 参数
2. 本地 `.env` 文件中的 `KIMI_CODE_TOKEN`
3. **Hermes `.env` 文件中的 `KIMI_API_KEY`**（兼容映射）
4. 环境变量 `KIMI_CODE_TOKEN`
5. 环境变量 `KIMI_API_KEY`（兼容映射）
6. `~/.kimi-code/credentials/kimi-code.json`（OAuth 登录凭证）

### 手动配置（如需覆盖）

如需使用不同的 Token，可创建 skill 本地配置：

```bash
# 在当前 skill 目录创建 .env
cd ~/AppData/Local/hermes/skills/quanyuanai/kimi-search-v2
echo "KIMI_CODE_TOKEN=*** > .env
```

### 配置检查

```bash
python scripts/kimi_search.py "test query"
```

如果未配置 Token，会提示错误信息并显示自动检测到的配置来源。

**注意**：Kimi Code access token 与 Moonshot API Key 可能不同。如果 `KIMI_API_KEY` 认证失败（401），请使用 `KIMI_CODE_TOKEN`。

## 使用方法

### 命令行直接调用

```bash
# 基本搜索（5 个结果，仅摘要）
python scripts/kimi_search.py "人工智能最新新闻"

# 更多结果
python scripts/kimi_search.py "人工智能最新新闻" --limit 10

# 包含完整页面内容（更慢但更全面）
python scripts/kimi_search.py "人工智能最新新闻" --content

# 输出原始 JSON
python scripts/kimi_search.py "人工智能最新新闻" --format json --out results.json

# 或使用环境变量（无需每次传 --token）
export KIMI_CODE_TOKEN=*** scripts/kimi_search.py "人工智能最新新闻"
```

### 在 Hermes 中使用

当用户需要搜索时，使用 `execute_code` 或 `terminal` 工具运行 Python 脚本：

```python
from hermes_tools import terminal

# 基本搜索
result = terminal(
    'python scripts/kimi_search.py "人工智能最新新闻"',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-search-v2"
)
print(result['output'])

# 搜索并保存 JSON
result = terminal(
    'python scripts/kimi_search.py "人工智能最新新闻" --format json --out /tmp/search_results.json',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-search-v2"
)
print(result['output'])

# 搜索 + 抓取完整内容
result = terminal(
    'python scripts/kimi_search.py "人工智能最新新闻" --content --limit 3',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-search-v2"
)
print(result['output'])
```

## 工作流程

### 步骤 1 — 获取 Token

Skill 会自动检测 Hermes 配置中的凭证。如需手动提供：

```bash
export KIMI_CODE_TOKEN=*** 步骤 2 — 执行搜索

```bash
python "<skill_dir>/scripts/kimi_search.py" "搜索关键词"
```

脚本会：
- 发送 `POST` 到 `https://api.kimi.com/coding/v1/search`，携带 `Authorization: Bearer *** 请求体为 `{"text_query": "...", "limit": 5, "enable_page_crawling": false, "timeout_seconds": 30}`
- 服务器搜索网页并返回结构化 JSON 结果
- 结果格式化为可读文本，输出到 stdout

### 步骤 3 — 调整搜索参数

控制结果数量和内容深度：

```bash
# 更多结果
python "<skill_dir>/scripts/kimi_search.py" "query" --limit 10

# 包含每个结果的完整页面内容（更慢但更全面）
python "<skill_dir>/scripts/kimi_search.py" "query" --content

# 输出原始 JSON 用于编程
python "<skill_dir>/scripts/kimi_search.py" "query" --format json --out results.json
```

### 步骤 4 — 展示结果

- 以清晰格式总结搜索结果给用户
- 如果某个结果看起来很有价值，使用 `kimi-fetch` 获取完整页面内容
- 如果保存为 JSON，按需解析和提取特定字段

## 命令参考

```bash
# 基本搜索（5 个结果，仅摘要）
python scripts/kimi_search.py "搜索关键词" --token <KEY>

# 10 个结果 + 完整页面内容
python scripts/kimi_search.py "搜索关键词" --token <KEY> --limit 10 --content

# 保存原始 JSON 响应
python scripts/kimi_search.py "搜索关键词" --token <KEY> --format json --out results.json

# 或设置 token 后省略 --token
export KIMI_CODE_TOKEN=*** scripts/kimi_search.py "搜索关键词"
```

## 输出格式

### 文本模式（默认）

```
======================================================================
[1] 结果标题
    Date: 2024-01-15
    URL:  https://example.com/article
    搜索结果的摘要文本...

======================================================================
[2] 另一个结果
    ...
```

### JSON 模式（`--format json`）

```json
{
  "search_results": [
    {
      "title": "...",
      "url": "...",
      "snippet": "...",
      "content": "...",  // 仅当使用 --content 时
      "date": "...",
      "icon": "...",
      "media": "..."
    }
  ]
}
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词 | 必填 |
| `--token` | Kimi Code access token | 自动检测 |
| `--limit` | 结果数量 | 5 |
| `--content` | 启用页面爬取获取完整内容 | false |
| `--timeout` | 服务器端超时（秒） | 30 |
| `--out`, `-o` | 保存原始 JSON 到文件 | 无 |
| `--format` | 输出格式（text/json） | text |
| `--max-content-chars` | 每个结果的最大内容字符数 | 2000 |

## 错误处理

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| 未找到 Token | 找不到 KIMI_CODE_TOKEN / KIMI_API_KEY | 提示自动检测路径和手动配置方法 |
| HTTP 401 | Token 过期/无效 | 提示用户提供新的 Kimi Code Token |
| HTTP 402/403 | CodePlan 订阅问题 | 提示用户检查订阅状态 |
| HTTP 5xx | 服务器错误 | 等待后重试 |
| 超时 (45s) | 服务器慢 | 尝试减少结果数或简化查询 |
| 无结果 | 查询无匹配 | 尝试重新表述查询或换语言搜索 |

## 使用技巧

- `--content` 显著更慢（服务器爬取每个页面）但提供更完整文本
- 大多数情况下默认摘要已足够；对特定 URL 使用 `kimi-fetch` 获取完整内容
- 用最可能有结果的语言搜索（中文查询适合中文主题，英文适合国际主题）
- `--limit` 超过 10 可能降低响应速度

## Token 安全

- Token 通过 `--token` 或 `$KIMI_CODE_TOKEN` 传入，不要写入会被提交的文件
- 脚本会在 `~/.kimi-code/device_id` 存储稳定的设备 ID（与官方 CLI 一致）

## 资源

### scripts/kimi_search.py

纯 Python（仅标准库）客户端。接受搜索查询作为第一个位置参数。无需 pip 安装。

## 示例

### 搜索最新新闻

```bash
python scripts/kimi_search.py "人工智能最新新闻 2025"
```

### 搜索技术文档

```bash
python scripts/kimi_search.py "Python asyncio tutorial" --limit 10
```

### 搜索并获取完整内容

```bash
python scripts/kimi_search.py "快手最新财报" --content --limit 3
```

### 搜索并保存 JSON

```bash
python scripts/kimi_search.py "特斯拉股价" --format json --out /tmp/tesla_search.json
```

## 注意事项

1. **搜索质量**：结果质量取决于 Kimi 的搜索索引
2. **内容提取**：`--content` 模式可能无法提取所有页面的完整内容
3. **频率限制**：频繁搜索可能触发频率限制
4. **语言支持**：中文查询对中文内容效果较好，英文查询对国际内容效果较好

## 与其他 skill 的配合

| 场景 | 使用 Skill |  workflow |
|------|-----------|-----------|
| 搜索 + 阅读全文 | `kimi-search-v2` → `kimi-fetch` | 先搜索找到 URL，再抓取完整内容 |
| 搜索 + 数据分析 | `kimi-search-v2` → `kimi-datasource` | 先搜索找到股票/公司，再查询数据源 |
| 快速搜索 | `kimi-search-v2` | 直接获取摘要结果 |

## 更新日志

### v1.0.0 (2024-06-19)
- 初始版本
- 支持 Kimi Code API 联网搜索
- 自动检测 Hermes 配置的 KIMI_API_KEY（兼容映射为 Kimi Code Token）
- 纯 Python 标准库实现，无需额外依赖
- 支持文本和 JSON 两种输出格式
- 支持页面内容爬取（--content）
