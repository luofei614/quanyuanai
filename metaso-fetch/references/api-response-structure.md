# Metaso API Response Structure

## Reader API (`/api/v1/reader`)

**Request:**
```json
{"url": "https://example.com/article"}
```

**Response fields:**
- `title` - 文章标题
- `url` - 原始 URL
- `author` - 作者
- `date` - 发布日期
- `markdown` - 正文内容（Markdown 格式）
- `credits` - 消耗的积分

## Search API (`/api/v1/search`)

**Request:**
```json
{
  "q": "搜索关键词",
  "scope": "webpage",
  "includeSummary": false,
  "size": "10",
  "includeRawContent": false,
  "conciseSnippet": false
}
```

**Response fields:**
- `credits` - 消耗的积分
- `searchParameters` - 实际使用的搜索参数
- `total` - 总结果数
- `webpages` - 网页结果列表（scope=webpage 时）
- `news` - 新闻结果列表（scope=news 时）
- `academic` - 学术结果列表（scope=academic 时）

**Result item fields:**
- `title` - 结果标题
- `link` - 结果链接（注意：是 `link` 不是 `url`）
- `snippet` - 内容摘要
- `score` - 相关性评分（high/medium/low）
- `position` - 排名位置
- `date` - 发布日期
- `authors` - 作者列表（可选）

## Common Pitfalls

1. **Field name mismatch:** Search API uses `link` not `url` for result URLs. Reader API uses `url`.
2. **Result key varies by scope:** `webpages` vs `news` vs `academic`, not a generic `results` key.
3. **Size is string:** API expects `"size": "10"` (string) not `10` (number) in JSON payload.
4. **Credits consumption:** Each call consumes credits (usually 3). Monitor usage if quota is limited.
