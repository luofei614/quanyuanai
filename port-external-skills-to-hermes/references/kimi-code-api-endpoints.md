# Kimi Code API Endpoints

Documented endpoints for `api.kimi.com/coding/v1` (requires Kimi Code access token).

## Verified Endpoints

### Search
- `POST /coding/v1/search`
- Body: `{"text_query": "...", "limit": 5, "enable_page_crawling": false, "timeout_seconds": 30}`
- Returns: Structured search results with title, URL, snippet, optional content

### Fetch
- `POST /coding/v1/fetch`
- Body: `{"url": "https://..."}`
- Headers: `Accept: text/markdown`
- Returns: Extracted page content as Markdown

### Tools (Data Sources)
- `POST /coding/v1/tools`
- Methods:
  - `get_data_source_desc` — Get API documentation for a data source
    - Params: `{"name": "arxiv"}`
  - `call_data_source_tool` — Execute a data source query
    - Params: `{"data_source_name": "...", "api_name": "...", "params": {...}}`

## Available Data Sources

Full list discovered via error message:
`ifind, arxiv, yahoo_finance, world_bank, google_scholar, binance, tianyancha, qveris, caixin, caidazi, yuandian_law, imf, sec_edgar, gildata, wind, sp_data`

## Important Notes

- These endpoints require Kimi Code access tokens (sk-kimi-...)
- Moonshot API keys (from platform.moonshot.cn) will NOT work here
- The `$web_search` builtin_function is a Moonshot feature, not available on Kimi Code API
- Rate limits and quotas apply based on CodePlan subscription
