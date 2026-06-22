# Kimi 内置数据源参考

> 7 个数据源，每个的 API 列表由后端动态维护，**始终先 `desc` 拿最新文档再 `call`**。
> 以下是各数据源的覆盖范围和常见用法提示，具体 `api_name` / 参数以 `desc` 输出为准。

## 调用流程（铁律）

```
desc  →  拿到 Markdown API 文档（含 api_name 列表 + 参数 schema）
call  →  按 api_name 和参数构造请求，结果 CSV 落到 params['file_path']
```

**永远不要凭记忆写 `api_name`**，后端会随时更新。

---

## 1. stock_finance_data — A股/港股/美股行情与财务

- 行情：日/周/月 K 线、实时行情、分时
- 财务：资产负债表、利润表、现金流量表
- 宏观：CPI、PPI、PMI、社融、M2 等
- 代码格式：A股 `600519.SH` / `000001.SZ`；港股 `00700.HK`；美股 `AAPL.O`
- 常见参数：`ticker`、`start_date`、`end_date`、`file_path`、`freq`（日/周/月）

## 2. yahoo_finance — Yahoo Finance 全球行情

- 全球股票、ETF、指数、外汇、加密货币
- 代码格式：`AAPL`、`^GSPC`（标普500）、`BTC-USD`
- 常见参数：`symbol`、`period`（1d/5d/1mo/…）、`interval`（1m/5m/1h/1d/…）

## 3. world_bank_open_data — 世界银行开放数据

- 国别指标：GDP、人均GNI、人口、预期寿命、CO₂排放…
- 国家代码：`CHN`、`USA`、`JPN`（ISO-3166 alpha-3）
- 指标代码：如 `NY.GDP.MKTP.KD.ZG`（GDP增长率）
- 年份格式：`"2020:2023"` 表示 2020–2023 区间

## 4. tianyancha — 天眼查企业工商信息

- 企业基本信息、股东、对外投资、分支机构、法律诉讼
- 查询方式：企业名称或统一社会信用代码
- 注意：返回的是文本摘要，通常不需要 `file_path`

## 5. arxiv — arXiv 学术预印本

- 检索物理/数学/CS/统计等领域的预印本论文
- 参数：`query`（关键词）、`max_results`、`sort_by`（relevance/date）
- 返回：标题、作者、摘要、arXiv ID、PDF 链接

## 6. scholar — 学术文献检索

- 跨库学术文献搜索
- 参数：`query`、`max_results`
- 返回：标题、作者、年份、引用数、摘要、DOI/链接

## 7. yuandian_law — 华宇元典法律数据

- 中国裁判文书案例检索
- 法律法规条文检索
- 参数：`query`（关键词）、`case_type`、`court_level`、`date_range`
- 返回：案例摘要、法条引用

---

## 通用注意事项

- **file_path**：凡是返回表格数据（CSV）的 API，必须传 `file_path` 指定落盘路径。脚本会自动创建父目录。
- **错误处理**：`is_success: false` 时，响应里的 `error.assistant[0].text` 是人类可读的错误说明。
- **额度**：每次 `call` 消耗 Kimi Code 账号的数据源调用额度。
- **超时**：网关超时 30 秒；大批量数据建议拆分多次调用。
