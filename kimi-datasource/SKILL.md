---
title: Kimi 数据源查询
skill: kimi-datasource
description: 查询 Kimi 的 7 个内置数据源（A股/美股行情、Yahoo Finance、世界银行、天眼查、arXiv、学术文献、法律案例）。用于获取金融市场数据、宏观经济指标、企业工商信息、学术论文或法律案例信息。无需安装 Kimi Code CLI，纯 Python 实现。
version: 1.0.0
category: quanyuanai
tags: [kimi, datasource, finance, stock, arxiv, academic, law, tianyancha, yahoo-finance, world-bank]
author: quanyuanai
---

# Kimi 数据源查询

## 概述

通过 Kimi 后端网关直接查询 7 个内置数据源，无需安装 Kimi Code CLI、Node 或 MCP server。脚本 `scripts/kimi_datasource.py` 完全复刻官方插件的功能——相同的 endpoint、相同的请求头、相同的响应解析。

## 何时使用

- 用户询问 A股/港股/美股 行情或财务数据
- 用户询问全球股票/ETF/指数数据（Yahoo Finance）
- 用户询问世界银行宏观经济指标（GDP、人口等）
- 用户询问中国企业工商信息（天眼查）
- 用户要求搜索 arXiv 或学术论文
- 用户要求查询中国法律案例/法规（元典法律）
- 用户明确提到 "Kimi 数据源" / "kimi datasource"

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
cd ~/AppData/Local/hermes/skills/quanyuanai/kimi-datasource
echo "KIMI_CODE_TOKEN=your-token-here" > .env
```

### 配置检查

```bash
python scripts/kimi_datasource.py status
```

如果未配置 Token，会提示错误信息并显示自动检测到的配置来源。

**注意**：Kimi Code access token 与 Moonshot API Key 可能不同。如果 `KIMI_API_KEY` 认证失败（401），请使用 `KIMI_CODE_TOKEN`。

## 使用方法

### 命令行直接调用

```bash
# 列出所有支持的数据源
python scripts/kimi_datasource.py list

# 查看数据源 API 文档（调用前必须先 desc）
python scripts/kimi_datasource.py desc --name stock_finance_data

# 执行查询（示例：查询贵州茅台 2024 年行情）
python scripts/kimi_datasource.py call \
  --source stock_finance_data \
  --api get_stock_daily \
  --params '{"ticker":"600519.SH","start_date":"2024-01-01","end_date":"2024-12-31","file_path":"/tmp/600519.csv"}'

# 验证 token 是否有效
python scripts/kimi_datasource.py status
```

### 在 Hermes 中使用

当用户需要查询数据源时，使用 `execute_code` 或 `terminal` 工具运行 Python 脚本：

```python
from hermes_tools import terminal

# 列出数据源
result = terminal(
    'python scripts/kimi_datasource.py list',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-datasource"
)
print(result['output'])

# 查询数据源 API 文档
result = terminal(
    'python scripts/kimi_datasource.py desc --name stock_finance_data',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-datasource"
)
print(result['output'])

# 执行查询（A股行情）
result = terminal(
    'python scripts/kimi_datasource.py call --source stock_finance_data --api get_stock_daily --params \'{"ticker":"600519.SH","start_date":"2024-01-01","end_date":"2024-12-31","file_path":"/tmp/600519.csv"}\'',
    workdir="~/AppData/Local/hermes/skills/quanyuanai/kimi-datasource"
)
print(result['output'])
```

## 工作流程（必须遵循）

### 步骤 0 — 确定数据源

将用户需求映射到以下 7 个数据源之一：

| 数据源 | 覆盖范围 |
|--------|----------|
| `stock_finance_data` | A股/港股/美股 行情、财务报表、宏观经济 |
| `yahoo_finance` | 全球股票/ETF/指数/外汇/加密货币 |
| `world_bank_open_data` | 世界银行 GDP/人口/社会指标 |
| `tianyancha` | 天眼查企业工商信息 |
| `arxiv` | arXiv 学术预印本 |
| `scholar` | 学术文献检索 |
| `yuandian_law` | 华宇元典法律案例/法规 |

### 步骤 1 — 获取 Token

Skill 会自动检测 Hermes 配置中的凭证。如需手动提供：

```bash
export KIMI_CODE_TOKEN="<your-token>"
```

### 步骤 2 — 必须先 desc

**永远不要凭记忆写 `api_name`**，后端会动态更新 API 列表。

```bash
python scripts/kimi_datasource.py desc --name <source>
```

阅读返回的 Markdown 文档，获取可用的 `api_name` 和参数 schema。

### 步骤 3 — 构造并执行查询

根据 desc 输出构建参数 JSON，执行 call：

```bash
python scripts/kimi_datasource.py call \
  --source <source> \
  --api <api_name_from_desc> \
  --params '{"param1":"value1","file_path":"out.csv"}' \
  --out /tmp/result.csv
```

脚本会：
- 发送 POST 到网关，携带 `Authorization: Bearer ***`
- 解析响应（从 `result.assistant[]` 提取文本）
- 将返回的 CSV 文件写入 `params['file_path']`（或 `--out`）
- 打印文本摘要 + trace ID（用于调试）

### 步骤 4 — 读取并展示结果

- **CSV 输出**：用 pandas 或 Read 工具读取，总结关键发现，以表格或图表展示
- **文本输出**（天眼查、arXiv、学术、法律）：打印的文本就是结果，解析并格式化后展示给用户

## 命令参考

```bash
# 列出所有支持的数据源
python scripts/kimi_datasource.py list

# 获取数据源的 API 文档（调用前必须执行）
python scripts/kimi_datasource.py desc --name <source>

# 执行查询
python scripts/kimi_datasource.py call --source <source> --api <api> --params '<json>' --out <path>

# 验证 token
python scripts/kimi_datasource.py status
```

> 注意：`--token` 是全局选项，放在子命令之前。或设置 `$KIMI_CODE_TOKEN` 后省略 `--token`。

## Token 安全

- Token 通过 `--token` 或 `$KIMI_CODE_TOKEN` 传入，不要写入会被提交的文件
- 脚本会在 `~/.kimi-code/device_id` 存储稳定的设备 ID（与官方 CLI 一致）
- 如果 `status` 返回 HTTP 401/402/403，说明 token 已过期或无效，请用户提供新的 token

## 错误处理

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| 未找到 Token | 找不到 KIMI_CODE_TOKEN / KIMI_API_KEY | 提示自动检测路径和手动配置方法 |
| HTTP 401/402/403 | Token 过期或无效 | 提示用户提供新的 Kimi Code Token |
| `is_success: false` | 后端拒绝查询 | 读取响应中的错误文本，修正参数后重试 |
| HTTP 5xx | 网关问题 | 等待后重试 |
| 超时 (30s) | 查询过大 | 拆分为更小的日期范围多次调用 |

## 资源

### scripts/kimi_datasource.py

纯 Python（仅标准库）客户端。支持 `list`, `desc`, `call`, `status` 子命令。无需 pip 安装。

### references/datasources.md

7 个数据源的详细覆盖范围和常见参数模式。不确定使用哪个数据源或传什么参数时加载此文件。

## 数据源详细说明

### 1. stock_finance_data — A股/港股/美股行情与财务

- 行情：日/周/月 K 线、实时行情、分时
- 财务：资产负债表、利润表、现金流量表
- 宏观：CPI、PPI、PMI、社融、M2 等
- 代码格式：A股 `600519.SH` / `000001.SZ`；港股 `00700.HK`；美股 `AAPL.O`
- 常见参数：`ticker`、`start_date`、`end_date`、`file_path`、`freq`（日/周/月）

### 2. yahoo_finance — Yahoo Finance 全球行情

- 全球股票、ETF、指数、外汇、加密货币
- 代码格式：`AAPL`、`^GSPC`（标普500）、`BTC-USD`
- 常见参数：`symbol`、`period`（1d/5d/1mo/…）、`interval`（1m/5m/1h/1d/…）

### 3. world_bank_open_data — 世界银行开放数据

- 国别指标：GDP、人均GNI、人口、预期寿命、CO₂排放…
- 国家代码：`CHN`、`USA`、`JPN`（ISO-3166 alpha-3）
- 指标代码：如 `NY.GDP.MKTP.KD.ZG`（GDP增长率）
- 年份格式：`"2020:2023"` 表示 2020–2023 区间

### 4. tianyancha — 天眼查企业工商信息

- 企业基本信息、股东、对外投资、分支机构、法律诉讼
- 查询方式：企业名称或统一社会信用代码
- 注意：返回的是文本摘要，通常不需要 `file_path`

### 5. arxiv — arXiv 学术预印本

- 检索物理/数学/CS/统计等领域的预印本论文
- 参数：`query`（关键词）、`max_results`、`sort_by`（relevance/date）
- 返回：标题、作者、摘要、arXiv ID、PDF 链接

### 6. scholar — 学术文献检索

- 跨库学术文献搜索
- 参数：`query`、`max_results`
- 返回：标题、作者、年份、引用数、摘要、DOI/链接

### 7. yuandian_law — 华宇元典法律数据

- 中国裁判文书案例检索
- 法律法规条文检索
- 参数：`query`（关键词）、`case_type`、`court_level`、`date_range`
- 返回：案例摘要、法条引用

## 通用注意事项

- **file_path**：凡是返回表格数据（CSV）的 API，必须传 `file_path` 指定落盘路径。脚本会自动创建父目录。
- **错误处理**：`is_success: false` 时，响应里的 `error.assistant[0].text` 是人类可读的错误说明。
- **额度**：每次 `call` 消耗 Kimi Code 账号的数据源调用额度。
- **超时**：网关超时 30 秒；大批量数据建议拆分多次调用。

## 更新日志

### v1.0.0 (2024-06-19)
- 初始版本
- 支持 7 个 Kimi 内置数据源
- 自动检测 Hermes 配置的 KIMI_API_KEY（兼容映射为 Kimi Code Token）
- 纯 Python 标准库实现，无需额外依赖
