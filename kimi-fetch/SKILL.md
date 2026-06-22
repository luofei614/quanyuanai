---
title: Kimi 网页抓取
skill: kimi-fetch
description: 通过 Kimi 服务端提取服务抓取任意 URL，将网页主要内容提取为干净的 Markdown 格式。无需 HTML 解析，服务器自动去除导航、广告、侧边栏、页脚，返回可直接阅读的文本。适用于获取文章、文档、博客、新闻等网页内容。
version: 1.0.0
category: quanyuanai
tags: [kimi, fetch, web-scrape, markdown, url, content-extraction]
author: quanyuanai
---

# Kimi 网页抓取

## 概述

抓取任意 URL 并获取其**主要内容提取为干净的 Markdown** — 不是原始 HTML。基于 Kimi 服务端提取服务（`POST https://api.kimi.com/coding/v1/fetch`），与官方 Kimi Code CLI 的 `FetchURL` 工具使用相同后端。纯 Python 实现，无需额外依赖。

服务器自动处理：
- 抓取页面
- 去除导航、广告、侧边栏、页脚
- 将主要文章文本转换为 Markdown

## 何时使用

- 用户要求抓取/读取/提取特定 URL 的内容
- 用户需要网页的文本内容（文章、文档、博客、新闻）
- 用户想从 URL 提取主要内容，无需 HTML 噪音
- 用户明确提到 "kimi fetch" / "fetch url" / "抓取网页"
- 需要干净的页面文本用于摘要或分析

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
cd ~/AppData/Local/hermes/skills/quanyuanai/kimi-fetch
echo "KIMI_CODE_TOKEN=*** > .env
```

### 配置检查

```bash
python scripts/kimi_fetch.py "https://example.com"
```

如果未配置 Token，会提示错误信息并显示自动检测到的配置来源。

**注意**：Kimi Code access token 与 Moonshot API Key 可能不同。如果 `KIMI_API_KEY` 认证失败（401），请使用 `KIMI_CODE_TOKEN`。

## 使用方法

### 命令行直接调用

```bash
# 抓取 URL（输出 Markdown 到 stdout）
python scripts/kimi_fetch.py "https://example.com/article"

# 保存完整内容到文件，stdout 只显示前 5000 字符
python scripts/kimi_fetch.py "https://example.com/long-article" \
  --out /tmp/page.md \
  --max-chars 5000

# 或使用环境变量（无需每次传 --token）
export KIMI_CODE_TOKEN="<KEY>"
python scripts/kimi_fetch.py "https://example.com"
```

### 在 Hermes 中使用

当用户需要抓取网页时，使用 `execute_code` 或 `terminal` 工具运行 Python 脚本：

```python
from hermes_tools import terminal

# 抓取网页内容
result = terminal(
    'python scripts/kimi_fetch.py "https://example.com/article"',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-fetch"
)
print(result['output'])

# 抓取长文章，保存到文件并限制输出长度
result = terminal(
    'python scripts/kimi_fetch.py "https://example.com/long-article" --out /tmp/page.md --max-chars 8000',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-fetch"
)
print(result['output'])
# 然后读取保存的文件
result2 = terminal('cat /tmp/page.md')
print(result2['output'])
```

## 工作流程

### 步骤 1 — 获取 Token

Skill 会自动检测 Hermes 配置中的凭证。如需手动提供：

```bash
export KIMI_CODE_TOKEN="<you...n### 步骤 2 — 抓取 URL

```bash
python "<skill_dir>/scripts/kimi_fetch.py" "https://example.com/article"
```

脚本会：
- 发送 `POST` 到 `https://api.kimi.com/coding/v1/fetch`，携带 `Authorization: Bearer ***
- 请求体为 `{"url": "https://..."}`
- 服务器抓取页面、提取主要内容、返回 Markdown 文本
- Markdown 文本输出到 stdout

### 步骤 3 — 处理长页面

对于长页面，使用 `--max-chars` 截断 stdout，并可选 `--out` 保存完整内容：

```bash
python "<skill_dir>/scripts/kimi_fetch.py" "https://example.com/long-article" \
  --out /tmp/page.md \
  --max-chars 8000
```

这会输出前 8000 字符到 stdout，并将完整内容保存到 `/tmp/page.md`。

### 步骤 4 — 展示结果

- 读取并总结提取的 Markdown 内容给用户
- 如果保存到文件，使用 Read 工具分析特定部分
- 提取的内容已经是干净的 Markdown — 无需进一步 HTML 解析

## 命令参考

```bash
# 抓取 URL（输出 Markdown 到 stdout）
python scripts/kimi_fetch.py "https://example.com" --token <KEY>

# 保存完整内容到文件，stdout 只显示前 5000 字符
python scripts/kimi_fetch.py "https://example.com" --token <KEY> --out page.md --max-chars 5000

# 或设置 token 后省略 --token
export KIMI_CODE_TOKEN="<KEY>"
python scripts/kimi_fetch.py "https://example.com"
```

> 注意：`--token` 是全局选项。或设置 `$KIMI_CODE_TOKEN` 后省略。

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 要抓取的 URL | 必填 |
| `--token` | Kimi Code access token | 自动检测 |
| `--out`, `-o` | 保存完整 Markdown 到文件 | 无 |
| `--max-chars` | stdout 截断字符数 | 无（完整输出）|

## 错误处理

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| 未找到 Token | 找不到 KIMI_CODE_TOKEN / KIMI_API_KEY | 提示自动检测路径和手动配置方法 |
| HTTP 401 | Token 过期/无效 | 提示用户提供新的 Kimi Code Token |
| HTTP 402/403 | CodePlan 订阅问题 | 提示用户检查订阅状态 |
| HTTP 5xx | 服务器错误 | 等待后重试 |
| 超时 (60s) | 页面过大或服务器慢 | 尝试不同 URL 或重试 |

## Token 安全

- Token 通过 `--token` 或 `$KIMI_CODE_TOKEN` 传入，不要写入会被提交的文件
- 脚本会在 `~/.kimi-code/device_id` 存储稳定的设备 ID（与官方 CLI 一致）

## 资源

### scripts/kimi_fetch.py

纯 Python（仅标准库）客户端。接受 URL 作为第一个位置参数。无需 pip 安装。

## 示例

### 抓取新闻文章

```bash
python scripts/kimi_fetch.py "https://news.example.com/article/12345"
```

### 抓取技术文档

```bash
python scripts/kimi_fetch.py "https://docs.python.org/3/tutorial/" --out /tmp/python_tutorial.md --max-chars 5000
```

### 抓取博客内容

```bash
python scripts/kimi_fetch.py "https://blog.example.com/post-title"
```

## 注意事项

1. **内容提取质量**：服务器会尽力提取主要内容，但某些复杂页面可能提取不完整
2. **动态页面**：对于 JavaScript 渲染的页面，提取效果可能不佳
3. **付费墙**：如果页面需要登录或付费，可能无法提取内容
4. **频率限制**：频繁抓取可能触发频率限制

## 更新日志

### v1.0.0 (2024-06-19)
- 初始版本
- 支持 Kimi 服务端网页提取
- 自动检测 Hermes 配置的 KIMI_API_KEY（兼容映射为 Kimi Code Token）
- 纯 Python 标准库实现，无需额外依赖
