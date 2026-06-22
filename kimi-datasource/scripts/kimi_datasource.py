#!/usr/bin/env python3
"""
kimi_datasource.py — Query Kimi's built-in data sources with a CodePlan key.

Pure Python (stdlib only). No Node, no Kimi Code CLI, no MCP server process.
Calls the same backend gateway the official plugin uses:
    POST https://api.kimi.com/coding/v1/tools
    Authorization: Bearer <token>

Workflow (ALWAYS in this order):
  1. desc   — pull the API doc for a data source
  2. call   — execute a specific API with params; CSV lands in params['file_path']

Usage:
  python kimi_datasource.py desc   --name stock_finance_data --token <KEY>
  python kimi_datasource.py call   --source stock_finance_data --api <api_name> \
                                   --params '{"ticker":"600519.SH",...,"file_path":"out.csv"}' \
                                   --token <KEY>
  python kimi_datasource.py list                              # list supported sources
  python kimi_datasource.py status --token <KEY>              # verify token works

Token resolution order: --token > $KIMI_CODE_TOKEN > ~/.kimi-code/credentials/kimi-code.json
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

VERSION = "1.0.0"

# --- Endpoint defaults (mirror bin/kimi-datasource.mjs) ---
DEFAULT_OAUTH_HOST = "https://auth.kimi.com"
DEFAULT_BASE_URL = "https://api.kimi.com/coding/v1"
REQUEST_TIMEOUT = 30  # seconds

# --- The 7 built-in data sources (hardcoded enum in the official plugin) ---
DATA_SOURCES = [
    "stock_finance_data",
    "yahoo_finance",
    "world_bank_open_data",
    "tianyancha",
    "arxiv",
    "scholar",
    "yuandian_law",
]

DATA_SOURCE_LABELS = {
    "stock_finance_data": "A股/港股/美股行情、财务、宏观数据",
    "yahoo_finance": "Yahoo Finance 全球行情与指标",
    "world_bank_open_data": "世界银行开放数据（GDP/人口/社会指标）",
    "tianyancha": "天眼查企业工商信息",
    "arxiv": "arXiv 学术预印本",
    "scholar": "学术文献检索",
    "yuandian_law": "华宇元典法律案例/法规",
}


# ---------- paths ----------
def kimi_home() -> Path:
    explicit = os.environ.get("KIMI_CODE_HOME", "").strip()
    return Path(explicit) if explicit else Path.home() / ".kimi-code"


def credentials_path() -> Path:
    return kimi_home() / "credentials" / "kimi-code.json"


def device_id_path() -> Path:
    return kimi_home() / "device_id"


def api_url() -> str:
    explicit = os.environ.get("KIMI_DATASOURCE_API_URL", "").strip()
    if explicit:
        return explicit
    base = (os.environ.get("KIMI_CODE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return f"{base}/tools"


# ---------- token ----------
def find_hermes_env_path() -> Path | None:
    """查找 Hermes 的 .env 文件路径（支持 Windows / Linux / macOS）"""
    home = Path.home()
    if platform.system() == "Windows":
        candidates = [
            home / "AppData" / "Local" / "hermes" / ".env",
            home / ".hermes" / ".env",
        ]
    else:
        candidates = [
            home / ".hermes" / ".env",
            home / ".config" / "hermes" / ".env",
        ]
    for path in candidates:
        if path.exists():
            return path
    return None


def parse_env_file(env_path: Path) -> dict[str, str]:
    """解析 .env 文件，提取 key=value 对"""
    env_vars: dict[str, str] = {}
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    except Exception:
        pass
    return env_vars


def resolve_token(cli_token: str | None) -> str:
    """
    Token 解析优先级（方案 A）：
    1. --token 参数
    2. 本地 .env 的 KIMI_CODE_TOKEN
    3. Hermes .env 的 KIMI_API_KEY（兼容映射）
    4. 环境变量 KIMI_CODE_TOKEN
    5. 环境变量 KIMI_API_KEY（兼容映射）
    6. ~/.kimi-code/credentials/kimi-code.json
    """
    detected_sources: list[str] = []
    token: str | None = None

    # 1. --token 参数
    if cli_token and cli_token.strip():
        return cli_token.strip()

    # 2. 本地 .env 的 KIMI_CODE_TOKEN
    skill_dir = Path(__file__).parent.parent
    local_env = skill_dir / ".env"
    if local_env.exists():
        env_vars = parse_env_file(local_env)
        token = env_vars.get("KIMI_CODE_TOKEN", "").strip()
        if token:
            detected_sources.append(f"本地 .env: {local_env}")

    # 3. Hermes .env 的 KIMI_API_KEY（兼容映射）
    if not token:
        hermes_env = find_hermes_env_path()
        if hermes_env:
            env_vars = parse_env_file(hermes_env)
            token = env_vars.get("KIMI_API_KEY", "").strip()
            if token:
                detected_sources.append(f"Hermes .env: {hermes_env}")

    # 4. 环境变量 KIMI_CODE_TOKEN
    if not token:
        token = os.environ.get("KIMI_CODE_TOKEN", "").strip()
        if token:
            detected_sources.append("环境变量 KIMI_CODE_TOKEN")

    # 5. 环境变量 KIMI_API_KEY（兼容映射）
    if not token:
        token = os.environ.get("KIMI_API_KEY", "").strip()
        if token:
            detected_sources.append("环境变量 KIMI_API_KEY")

    # 6. ~/.kimi-code/credentials/kimi-code.json
    if not token:
        path = credentials_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                token = data.get("access_token", "").strip()
                if token:
                    detected_sources.append(f"凭证文件: {path}")
            except (json.JSONDecodeError, OSError):
                pass

    if not token:
        print("Error: 未找到 Kimi Code access token。", file=sys.stderr)
        print("", file=sys.stderr)
        print("检测路径（按优先级）：", file=sys.stderr)
        print(f"  1. --token 参数", file=sys.stderr)
        print(f"  2. 本地 .env (KIMI_CODE_TOKEN): {local_env}", file=sys.stderr)
        hermes_env = find_hermes_env_path()
        print(f"  3. Hermes .env (KIMI_API_KEY): {hermes_env or '未找到'}", file=sys.stderr)
        print(f"  4. 环境变量 KIMI_CODE_TOKEN", file=sys.stderr)
        print(f"  5. 环境变量 KIMI_API_KEY", file=sys.stderr)
        print(f"  6. 凭证文件: {credentials_path()}", file=sys.stderr)
        print("", file=sys.stderr)
        print("解决方法：", file=sys.stderr)
        print("  1. 在 Hermes 中配置 Kimi provider（会自动设置 KIMI_API_KEY）", file=sys.stderr)
        print("  2. 或设置环境变量: export KIMI_CODE_TOKEN=\"your-token\"", file=sys.stderr)
        print("  3. 或在当前 skill 目录创建 .env 文件覆盖:", file=sys.stderr)
        print(f"     cd {skill_dir}", file=sys.stderr)
        print("     echo KIMI_CODE_TOKEN=your-token > .env", file=sys.stderr)
        print("", file=sys.stderr)
        print("注意：Kimi Code access token 与 Moonshot API Key 不同。", file=sys.stderr)
        print("      如果 KIMI_API_KEY 认证失败，请使用 KIMI_CODE_TOKEN。", file=sys.stderr)
        raise SystemExit(1)

    # 打印检测到的来源（stderr，不影响正常输出）
    if detected_sources:
        print(f"[Kimi Datasource] Token 来源: {detected_sources[0]}", file=sys.stderr)

    return token


# ---------- device id (stable, like the .mjs) ----------
def get_device_id() -> str:
    p = device_id_path()
    try:
        existing = p.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except OSError:
        pass
    new_id = str(uuid.uuid4())
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new_id + "\n", encoding="utf-8")
    except OSError:
        pass
    return new_id


# ---------- headers (mirror buildHeaders in the .mjs) ----------
def ascii_header(value: str, fallback: str = "unknown") -> str:
    cleaned = "".join(c for c in str(value) if " " <= c <= "~").strip()
    return cleaned if cleaned else fallback


def device_model() -> str:
    os_name = platform.system()  # Windows / Darwin / Linux
    os_ver = platform.release()
    arch = platform.machine() or "x86_64"
    if os_name == "Darwin":
        return f"macOS {os_ver} {arch}"
    if os_name == "Windows":
        return f"Windows {os_ver} {arch}"
    return f"{os_name} {os_ver} {arch}".strip()


def build_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Msh-Tool-Call-Id": str(uuid.uuid4()),
        "X-Msh-Platform": ascii_header(os.environ.get("KIMI_MSH_PLATFORM", "kimi-datasource-skill")),
        "X-Msh-Version": ascii_header(os.environ.get("KIMI_MSH_VERSION", VERSION)),
        "X-Msh-Device-Name": ascii_header(os.environ.get("KIMI_MSH_DEVICE_NAME", socket.gethostname())),
        "X-Msh-Device-Model": ascii_header(os.environ.get("KIMI_MSH_DEVICE_MODEL", device_model())),
        "X-Msh-Os-Version": ascii_header(os.environ.get("KIMI_MSH_OS_VERSION", platform.release())),
        "X-Msh-Device-Id": ascii_header(get_device_id()),
        "User-Agent": f"kimi-datasource-skill/{VERSION}",
    }


# ---------- HTTP ----------
def call_gateway(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    """POST {method, params} to the tools gateway. Returns parsed JSON (or text)."""
    url = api_url()
    body = json.dumps({"method": method, "params": params}, ensure_ascii=False).encode("utf-8")
    headers = build_headers(token)
    ctx = ssl.create_default_context()
    last_err: Exception | None = None
    for attempt in range(2):
        req = urllib.request.Request(url, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                trace_id = resp.headers.get("x-request-id") or resp.headers.get("x-trace-id") or ""
            break
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            raise SystemExit(f"HTTP {e.code} from gateway: {raw}") from None
        except (urllib.error.URLError, OSError) as e:
            last_err = e
            if attempt == 0:
                time.sleep(1)  # transient SSL EOF — retry once
                continue
            raise SystemExit(f"Network error reaching {url}: {e}") from None
    else:
        raise SystemExit(f"Network error reaching {url}: {last_err}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw_text": raw, "_trace_id": trace_id}
    if isinstance(parsed, dict):
        parsed.setdefault("_trace_id", trace_id)
    return parsed


# ---------- response parsing (mirror extractText / extractChannelText) ----------
def extract_channel_text(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    for channel in ("assistant", "user"):
        items = value.get(channel)
        if not isinstance(items, list):
            continue
        texts = []
        for item in items:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                if item["text"]:
                    texts.append(item["text"])
        joined = "\n\n".join(texts).strip()
        if joined:
            return joined
    return None


def extract_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    if not isinstance(response, dict):
        return str(response)
    if response.get("is_success") is False:
        msg = extract_channel_text(response.get("error")) or json.dumps(response, ensure_ascii=False)
        raise SystemExit(f"Tool API error: {msg}")
    text = extract_channel_text(response.get("result"))
    if text is not None:
        return text
    return f"Tool API succeeded but returned no text. Raw: {json.dumps(response, ensure_ascii=False)[:2000]}"


def write_response_files(response: Any, expected_path: str | None) -> list[str]:
    """Write any 'files' array entries to disk. Returns warning messages."""
    if not isinstance(response, dict):
        return []
    files = response.get("files")
    if not isinstance(files, list):
        return []
    warnings: list[str] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        name = str(f.get("name", "")).strip()
        content = f.get("content")
        if not name or content is None:
            continue
        # Security: only write if name resolves under the expected output directory
        write_path = _safe_write_path(name, expected_path)
        if write_path is None:
            warnings.append(f"Skipped returned file '{name}' (outside expected output path).")
            continue
        try:
            write_path.parent.mkdir(parents=True, exist_ok=True)
            if f.get("encoding") == "base64":
                import base64
                write_path.write_bytes(base64.b64decode(str(content)))
            else:
                write_path.write_text(str(content), encoding="utf-8")
        except OSError as e:
            warnings.append(f"Failed to write {write_path}: {e}")
    return warnings


def _safe_write_path(name: str, expected: str | None) -> Path | None:
    if expected is None:
        return None
    actual = Path(name).resolve()
    expected_p = Path(expected).resolve()
    if actual == expected_p:
        return actual
    # allow sibling files like "out_1.csv" next to expected "out.csv"
    if actual.parent == expected_p.parent and actual.suffix == expected_p.suffix and actual.stem.startswith(expected_p.stem + "_"):
        return actual
    return None


# ---------- commands ----------
def cmd_list(args: argparse.Namespace) -> None:
    print("Kimi 内置数据源（共 %d 个）:" % len(DATA_SOURCES))
    for s in DATA_SOURCES:
        label = DATA_SOURCE_LABELS.get(s, "")
        print(f"  - {s}" + (f"   ({label})" if label else ""))


def cmd_desc(args: argparse.Namespace) -> None:
    token = resolve_token(args.token)
    if args.name not in DATA_SOURCES:
        print(f"Unknown data source: {args.name}", file=sys.stderr)
        print(f"Valid: {', '.join(DATA_SOURCES)}", file=sys.stderr)
        sys.exit(2)
    resp = call_gateway(token, "get_data_source_desc", {"name": args.name})
    text = extract_text(resp)
    print(text)
    _print_trace(resp)


def cmd_call(args: argparse.Namespace) -> None:
    token = resolve_token(args.token)
    params = json.loads(args.params)
    if args.out:
        params.setdefault("file_path", args.out)
    out = params.get("file_path")
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
    resp = call_gateway(
        token,
        "call_data_source_tool",
        {"data_source_name": args.source, "api_name": args.api, "params": params},
    )
    text = extract_text(resp)
    warnings = write_response_files(resp, out)
    print(text)
    if warnings:
        print("\n" + "\n".join(warnings))
    _print_trace(resp)
    if isinstance(resp, dict) and resp.get("is_success") is False:
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    token = resolve_token(args.token)
    print(f"Gateway: {api_url()}")
    print(f"Token:   {token[:8]}…{token[-4:]}  (len={len(token)})")
    print("Verifying with a lightweight desc call …")
    try:
        resp = call_gateway(token, "get_data_source_desc", {"name": "arxiv"})
        text = extract_text(resp)
        ok = "arxiv" in text.lower() or len(text) > 50
        print(f"Result:  {'✅ token valid — gateway reachable' if ok else '⚠️  unexpected response'}")
        if not ok:
            print(text[:500])
        _print_trace(resp)
    except SystemExit as e:
        print(f"Result:  ❌ {e}")


def _print_trace(resp: Any) -> None:
    if isinstance(resp, dict) and resp.get("_trace_id"):
        print(f"\n[trace] request-id: {resp['_trace_id']}", file=sys.stderr)


# ---------- CLI ----------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Query Kimi built-in data sources with a CodePlan key (no CLI, no Node).",
    )
    p.add_argument("--token", default=None, help="Kimi Code access token / CodePlan key. Falls back to $KIMI_CODE_TOKEN or credentials file.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List supported data sources").set_defaults(func=cmd_list)

    s_desc = sub.add_parser("desc", help="Get API documentation for a data source")
    s_desc.add_argument("--name", required=True, choices=DATA_SOURCES, help="Data source name")
    s_desc.set_defaults(func=cmd_desc)

    s_call = sub.add_parser("call", help="Execute a data-source API query")
    s_call.add_argument("--source", required=True, choices=DATA_SOURCES, help="Data source name")
    s_call.add_argument("--api", required=True, help="API name (from desc output)")
    s_call.add_argument("--params", required=True, help='JSON string, e.g. \'{"ticker":"600519.SH","file_path":"out.csv"}\'')
    s_call.add_argument("--out", default=None, help="Set params['file_path'] to this path (CSV output)")
    s_call.set_defaults(func=cmd_call)

    s_stat = sub.add_parser("status", help="Verify the token works against the gateway")
    s_stat.set_defaults(func=cmd_status)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
