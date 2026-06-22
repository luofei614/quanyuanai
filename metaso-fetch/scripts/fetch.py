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
METASO_API_URL = "https://metaso.cn/api/v1/reader"


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
def fetch_url(url: str) -> dict:
    """
    调用 metaso.cn API 抓取网页内容
    
    Args:
        url: 要抓取的网页 URL
        
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
    
    payload = {"url": url}
    
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
                "该 URL 可能无法被抓取，或您的 API Key 权限不足。"
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
            "目标网页加载缓慢或网络不稳定，正在重试..."
        )
    except requests.ConnectionError:
        raise requests.ConnectionError(
            "网络连接失败。\n"
            "请检查网络连接，正在重试..."
        )


def main():
    parser = argparse.ArgumentParser(description='Metaso 网页抓取工具')
    parser.add_argument('url', help='要抓取的网页 URL')
    parser.add_argument('--pretty', '-p', action='store_true', default=True, help='美化输出')
    
    args = parser.parse_args()
    
    try:
        # 检查配置
        check_config()
        
        print(f"正在抓取: {args.url}")
        print("-" * 50)
        
        # 调用 API
        result = fetch_url(args.url)
        
        # 格式化输出
        if args.pretty:
            output = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            output = json.dumps(result, ensure_ascii=False)
        
        print(output)
        
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
