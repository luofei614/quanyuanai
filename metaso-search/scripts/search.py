import os
import sys
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

METASO_API_KEY = os.getenv("METASO_API_KEY")
METASO_API_URL = "https://metaso.cn/api/v1/search"


class MetasoAPIError(Exception):
    """Metaso API 调用错误"""
    pass


class ConfigError(Exception):
    """配置错误"""
    pass


def check_config():
    """检查配置是否完整"""
    if not METASO_API_KEY:
        raise ConfigError(
            "未配置 METASO_API_KEY。\n"
            "请在 https://metaso.cn/search-api/api-keys 获取 API Key，\n"
            "然后写入 .env 文件：METASO_API_KEY=your_key_here"
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=True
)
def search_query(
    q: str,
    scope: str = "webpage",
    size: int = 10,
    include_summary: bool = False,
    include_raw_content: bool = False,
    concise_snippet: bool = False
) -> dict:
    """
    调用 metaso.cn API 搜索

    Args:
        q: 搜索关键词
        scope: 搜索范围 (webpage/news/academic)
        size: 返回结果数量
        include_summary: 是否包含 AI 摘要
        include_raw_content: 是否包含原始网页内容
        concise_snippet: 是否精简摘要

    Returns:
        API 返回的 JSON 数据

    Raises:
        MetasoAPIError: API 返回错误
        requests.RequestException: 网络请求错误
    """
    headers = {
        "Authorization": f"Bearer {METASO_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "q": q,
        "scope": scope,
        "includeSummary": include_summary,
        "size": str(size),
        "includeRawContent": include_raw_content,
        "conciseSnippet": concise_snippet
    }

    try:
        response = requests.post(
            METASO_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        # 处理 HTTP 错误状态码
        if response.status_code == 401:
            raise MetasoAPIError(
                "API Key 无效或已过期 (401)。\n"
                "请检查 .env 文件中的 METASO_API_KEY 是否正确，\n"
                "或前往 https://metaso.cn/search-api/api-keys 重新获取。"
            )
        elif response.status_code == 403:
            raise MetasoAPIError(
                "访问被拒绝 (403)。\n"
                "您的 API Key 权限不足，或该功能未开通。"
            )
        elif response.status_code == 404:
            raise MetasoAPIError(
                "API 端点不存在 (404)。\n"
                "可能是 metaso.cn API 地址已变更，请联系管理员。"
            )
        elif response.status_code == 429:
            raise MetasoAPIError(
                "请求过于频繁 (429)。\n"
                "请稍后再试，或降低请求频率。"
            )
        elif response.status_code >= 500:
            # 5xx 错误会触发重试
            response.raise_for_status()
        elif response.status_code >= 400:
            raise MetasoAPIError(
                f"请求错误 (HTTP {response.status_code}): {response.text}"
            )

        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        raise requests.Timeout(
            "请求超时 (30s)。\n"
            "网络不稳定或目标服务响应缓慢，正在重试..."
        )
    except requests.ConnectionError:
        raise requests.ConnectionError(
            "网络连接失败。\n"
            "请检查网络连接，正在重试..."
        )


def format_table(results: list, query: str, scope: str) -> str:
    """
    将搜索结果格式化为表格

    Args:
        results: 搜索结果列表
        query: 搜索关键词
        scope: 搜索范围

    Returns:
        格式化后的表格字符串
    """
    lines = []
    lines.append(f"🔍 搜索: \"{query}\"")
    lines.append(f"范围: {scope} | 结果数: {len(results)}")
    lines.append("")

    if not results:
        lines.append("未找到相关结果。")
        return "\n".join(lines)

    # 表头
    lines.append("┌────┬─────────────────────────────┬────────────────────────────────────────┐")
    lines.append("│ {:<2} │ {:<27} │ {:<38} │".format("#", "标题", "链接"))
    lines.append("├────┼─────────────────────────────┼────────────────────────────────────────┤")

    # 数据行
    for i, item in enumerate(results, 1):
        title = item.get("title", "")[:27]
        url = item.get("link", "")[:38]
        lines.append("│ {:<2} │ {:<27} │ {:<38} │".format(i, title, url))

    lines.append("└────┴─────────────────────────────┴────────────────────────────────────────┘")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Metaso 搜索工具')
    parser.add_argument('q', help='搜索关键词')
    parser.add_argument('--scope', default='webpage', choices=['webpage', 'news', 'academic'],
                        help='搜索范围 (默认: webpage)')
    parser.add_argument('--size', type=int, default=10, help='返回结果数量 (默认: 10)')
    parser.add_argument('--summary', action='store_true', help='包含 AI 摘要')
    parser.add_argument('--raw', action='store_true', help='包含原始网页内容')
    parser.add_argument('--concise', action='store_true', help='精简摘要')
    parser.add_argument('--json', action='store_true', help='输出原始 JSON 格式')

    args = parser.parse_args()

    try:
        # 检查配置
        check_config()

        # 调用 API
        result = search_query(
            q=args.q,
            scope=args.scope,
            size=args.size,
            include_summary=args.summary,
            include_raw_content=args.raw,
            concise_snippet=args.concise
        )

        # 输出格式
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 提取结果列表 (metaso API 返回 webpages/news/academic 等字段)
            results = []
            if isinstance(result, dict):
                results = result.get("webpages", []) or result.get("news", []) or result.get("academic", []) or []
            print(format_table(results, args.q, args.scope))

    except ConfigError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        sys.exit(1)
    except MetasoAPIError as e:
        print(f"API 错误: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"网络错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
