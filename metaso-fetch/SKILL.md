---
name: metaso-fetch
description: "调用 metaso.cn API 抓取微信公众号、网页内容，支持重试和错误处理"
version: 1.0.0
author: quanyuanai
license: MIT
metadata:
  hermes:
    tags: [web-scraping, metaso, api, curl]
    related_skills: [metaso-search]
---

# Metaso 网页抓取

调用 [metaso.cn](https://metaso.cn) 的 Reader API，抓取微信公众号文章和普通网页内容，返回结构化 JSON 数据。

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
   METASO_API_KEY=mk-xxxxxxxxxxxxxxxx
   ```

### 配置检查

运行以下命令验证配置：
```bash
python scripts/fetch.py --help
```

如果未配置 API Key，会提示错误信息。

## 使用方法

### 命令行直接调用

```bash
# 基本用法：抓取网页并打印 JSON
python scripts/fetch.py "https://www.163.com/news/article/K56809DQ000189FH.html"

# 紧凑输出（不格式化）
python scripts/fetch.py "https://example.com" --pretty=false
```

### 在 Hermes 中使用

当用户需要抓取网页内容时，使用 `execute_code` 工具运行 Python 脚本：

```python
from hermes_tools import terminal

# 单条 URL 抓取
result = terminal(
    'python ~/.hermes/skills/quanyuanai/metaso-fetch/scripts/fetch.py "https://example.com"',
    workdir="~/.hermes/skills/quanyuanai/metaso-fetch"
)
print(result['output'])
```

## 功能特性

- ✅ **智能重试**：网络超时/连接错误自动重试 3 次，指数退避（2s, 4s, 8s）
- ✅ **错误分类**：401/403/404/429 等错误给出清晰中文提示
- ✅ **JSON 输出**：默认格式化输出，可选紧凑模式
- ✅ **环境配置**：API Key 从 `.env` 读取，安全不外泄

## 错误处理

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| 401 | API Key 无效 | 提示重新获取 Key |
| 403 | 访问被拒绝 | 提示 URL 无法抓取或权限不足 |
| 404 | 端点不存在 | 提示 API 地址可能变更 |
| 429 | 请求过于频繁 | 提示降低频率 |
| 5xx | 服务器错误 | 自动重试 3 次 |
| 超时 | 30秒无响应 | 自动重试 3 次 |

## 示例输出

```json
{
  "title": "新闻标题",
  "content": "正文内容...",
  "author": "作者名",
  "publish_time": "2024-01-01",
  "url": "https://www.163.com/..."
}
```

## 注意事项

1. **API Key 安全**：`.env` 文件已加入 `.gitignore`，请勿提交到版本控制
2. **频率限制**：metaso.cn 可能有请求频率限制，遇到 429 请稍后再试
3. **内容版权**：抓取内容仅供个人学习研究，请遵守相关版权法规

## API 参考

详见 `references/api-response-structure.md` 了解 metaso API 的响应字段和常见陷阱。

## 更新日志

### v1.0.0 (2024-06-19)
- 初始版本
- 支持单 URL 抓取
- 支持 JSON 格式化输出
- 实现 3 次自动重试机制
