---
title: Metaso 搜索
skill: metaso-search
description: 调用 metaso.cn API 搜索网页、新闻、学术内容，支持表格和 JSON 输出
version: 1.0.0
category: quanyuanai
tags: [search, metaso, api, web-search]
author: quanyuanai
---

# Metaso 搜索

调用 [metaso.cn](https://metaso.cn) 的 Search API，搜索网页、新闻或学术内容，返回结构化结果。

## 前置要求

1. Python 3.8+
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置 API Key（见下方配置说明）

## 配置 API Key

### 首次使用

1. 前往 https://metaso.cn/search-api/api-keys 获取 API Key
2. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```
3. 编辑 `.env`，填入你的 API Key：
   ```
   METASO_API_KEY=mk-xxx...xx
   ```

### 配置检查

运行以下命令验证配置：
```bash
python scripts/search.py --help
```

如果未配置 API Key，会提示错误信息。

## 使用方法

### 命令行直接调用

```bash
# 基本用法：搜索网页（默认表格输出）
python scripts/search.py "谁是这个世界上最美丽的女人"

# 指定搜索范围和结果数量
python scripts/search.py "AI教育" --scope webpage --size 20

# 搜索新闻
python scripts/search.py "最新科技动态" --scope news

# 搜索学术内容
python scripts/search.py "深度学习论文" --scope academic

# 包含 AI 摘要
python scripts/search.py "Python教程" --summary

# 输出原始 JSON
python scripts/search.py "元宇宙" --json
```

### 在 Hermes 中使用

当用户需要搜索时，使用 `execute_code` 工具运行 Python 脚本：

```python
from hermes_tools import terminal

# 基本搜索
result = terminal(
    'python scripts/search.py "谁是这个世界上最美丽的女人"',
    workdir="~/.hermes/skills/quanyuanai/metaso-search"
)
print(result['output'])

# 指定参数
result = terminal(
    'python scripts/search.py "AI教育" --scope webpage --size 20',
    workdir="~/.hermes/skills/quanyuanai/metaso-search"
)
print(result['output'])
```

## 功能特性

- ✅ **多范围搜索**：支持 webpage（网页）、news（新闻）、academic（学术）
- ✅ **智能重试**：网络超时/连接错误自动重试 3 次，指数退避（2s, 4s, 8s）
- ✅ **错误分类**：401/403/404/429 等错误给出清晰中文提示
- ✅ **表格输出**：默认表格格式，直观易读
- ✅ **JSON 输出**：`--json` 参数输出原始 JSON 数据
- ✅ **AI 摘要**：`--summary` 参数包含 AI 生成的内容摘要
- ✅ **环境配置**：API Key 从 `.env` 读取，安全不外泄

## 参数说明

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `q` | 搜索关键词 | - | 必填 |
| `--scope` | 搜索范围 | webpage/news/academic | webpage |
| `--size` | 返回结果数量 | 1-50 | 10 |
| `--summary` | 包含 AI 摘要 | - | false |
| `--raw` | 包含原始网页内容 | - | false |
| `--concise` | 精简摘要 | - | false |
| `--json` | 输出 JSON 格式 | - | false |

## 错误处理

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 401 | API Key 无效 | 提示重新获取 Key |
| 403 | 访问被拒绝 | 提示权限不足或功能未开通 |
| 404 | 端点不存在 | 提示 API 地址可能变更 |
| 429 | 请求过于频繁 | 提示降低频率 |
| 5xx | 服务器错误 | 自动重试 3 次 |
| 超时 | 30秒无响应 | 自动重试 3 次 |

## 示例输出

### 表格模式（默认）

```
🔍 搜索: "AI教育"
范围: webpage | 结果数: 10

┌────┬─────────────────────────────┬────────────────────────────────────────┐
│ #  │ 标题                        │ 链接                                   │
├────┼─────────────────────────────┼────────────────────────────────────────┤
│ 1  │ AI教育走出屏幕的第一步...    │ https://mp.weixin.qq.com/s/xxx         │
│ 2  │ 人工智能教育发展趋势...      │ https://www.example.com/ai-edu         │
└────┴─────────────────────────────┴────────────────────────────────────────┘
```

### JSON 模式（--json）

```json
{
  "query": "AI教育",
  "scope": "webpage",
  "results": [
    {
      "title": "AI教育走出屏幕的第一步...",
      "url": "https://mp.weixin.qq.com/s/xxx",
      "snippet": "当AI大模型从云端走向物理世界..."
    }
  ]
}
```

## 注意事项

1. **API Key 安全**：`.env` 文件已加入 `.gitignore`，请勿提交到版本控制
2. **频率限制**：metaso.cn 可能有请求频率限制，遇到 429 请稍后再试
3. **结果质量**：搜索结果质量取决于 metaso.cn 的索引范围

## 更新日志

### v1.0.0 (2024-06-19)
- 初始版本
- 支持 webpage/news/academic 三种搜索范围
- 支持表格和 JSON 两种输出格式
- 实现 3 次自动重试机制
