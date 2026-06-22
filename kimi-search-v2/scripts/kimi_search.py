#!/usr/bin/env python3
"""
kimi_search.py — Web search via Kimi's server-side search service.

Pure Python (stdlib only). No Node, no Kimi Code CLI.
Calls the same backend the official WebSearch tool uses:
    POST https://api.kimi.com/coding/v1/search
    Authorization: Bearer <token>
    Body: {"text_query": "...", "limit": 5, "enable_page_crawling": false, "timeout_seconds": 30}

The server searches the web and returns structured results (title, url, snippet,
and optionally full page content if enable_page_crawling is true).

Usage:
  python kimi_search.py "search query" --token <KEY>
  python kimi_search.py "search query" --token <KEY> --limit 10
  python kimi_search.py "search query" --token <KEY> --content          # crawl full page content
  python kimi_search.py "search query" --token <KEY> --out results.json # save raw JSON
  python kimi_search.py "search query" --token <KEY> --format json      # output as JSON

Token resolution order: --token > local .env > hermes .env KIMI_API_KEY > $KIMI_CODE_TOKEN > $KIMI_API_KEY > ~/.kimi-code/credentials/kimi-code.json
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

VERSION = "1.0.0"

# --- Endpoint ---
DEFAULT_BASE_URL = "https://api.kimi.com/coding/v1"
REQUEST_TIMEOUT = 45  # seconds


# ---------- paths ----------
def kimi_home() -> Path:
    explicit = os.environ.get("KIMI_CODE_HOME", "").strip()
    return Path(explicit) if explicit else Path.home() / ".kimi-code"


def credentials_path() -> Path:
    return kimi_home() / "credentials" / "kimi-code.json"


def device_id_path() -> Path:
    return kimi_home() / "device_id"


def search_url() -> str:
    explicit = os.environ.get("KIMI_SEARCH_API_URL", "").strip()
    if explicit:
        return explicit
    base = (os.environ.get("KIMI_CODE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return f"{base}/search"


# ---------- token ----------
def find_hermes_env_path() -> Path | None:
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
    Token resolution priority:
    1. --token argument
    2. Local .env KIMI_CODE_TOKEN
    3. Hermes .env KIMI_API_KEY
    4. Env var KIMI_CODE_TOKEN
    5. Env var KIMI_API_KEY
    6. ~/.kimi-code/credentials/kimi-code.json
    """
    # 1. --token
    if cli_token and cli_token.strip():
        return cli_token.strip()

    # 2. Local .env
    skill_dir = Path(__file__).parent.parent
    local_env = skill_dir / ".env"
    if local_env.exists():
        env_vars = parse_env_file(local_env)
        token = env_vars.get("KIMI_CODE_TOKEN", "").strip()
        if token:
            return token

    # 3. Hermes .env KIMI_API_KEY
    hermes_env = find_hermes_env_path()
    if hermes_env:
        env_vars = parse_env_file(hermes_env)
        token = env_vars.get("KIMI_API_KEY", "").strip()
        if token:
            return token

    # 4. Env var KIMI_CODE_TOKEN
    token = os.environ.get("KIMI_CODE_TOKEN", "").strip()
    if token:
        return token

    # 5. Env var KIMI_API_KEY
    token = os.environ.get("KIMI_API_KEY", "").strip()
    if token:
        return token

    # 6. Credentials file
    path = credentials_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            token = data.get("access_token", "").strip()
            if token:
                return token
        except (json.JSONDecodeError, OSError):
            pass

    print("Error: No Kimi Code access token found.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Set it via one of:", file=sys.stderr)
    print("  1. --token <KEY> on the command line", file=sys.stderr)
    print("  2. export KIMI_CODE_TOKEN=\"<KEY>\"", file=sys.stderr)
    print(f"  3. Credentials file: {credentials_path()}", file=sys.stderr)
    raise SystemExit(1)


# ---------- device id ----------
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


# ---------- headers ----------
def ascii_header(value: str, fallback: str = "unknown") -> str:
    cleaned = "".join(c for c in str(value) if " " <= c <= "~").strip()
    return cleaned if cleaned else fallback


def device_model() -> str:
    os_name = platform.system()
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
        "Accept": "application/json",
        "X-Msh-Tool-Call-Id": str(uuid.uuid4()),
        "X-Msh-Platform": ascii_header(os.environ.get("KIMI_MSH_PLATFORM", "kimi-search-skill")),
        "X-Msh-Version": ascii_header(os.environ.get("KIMI_MSH_VERSION", VERSION)),
        "X-Msh-Device-Name": ascii_header(os.environ.get("KIMI_MSH_DEVICE_NAME", socket.gethostname())),
        "X-Msh-Device-Model": ascii_header(os.environ.get("KIMI_MSH_DEVICE_MODEL", device_model())),
        "X-Msh-Os-Version": ascii_header(os.environ.get("KIMI_MSH_OS_VERSION", platform.release())),
        "X-Msh-Device-Id": ascii_header(get_device_id()),
        "User-Agent": f"kimi-search-skill/{VERSION}",
    }


# ---------- HTTP ----------
def do_search(
    token: str,
    query: str,
    limit: int = 5,
    enable_page_crawling: bool = False,
    timeout_seconds: int = 30,
) -> tuple[dict, str]:
    """
    POST search request to the Kimi search endpoint.
    Returns (parsed_json, trace_id).
    """
    endpoint = search_url()
    payload = {
        "text_query": query,
        "limit": limit,
        "enable_page_crawling": enable_page_crawling,
        "timeout_seconds": timeout_seconds,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = build_headers(token)
    ctx = ssl.create_default_context()
    last_err: Exception | None = None

    for attempt in range(2):
        req = urllib.request.Request(endpoint, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                trace_id = resp.headers.get("x-request-id") or resp.headers.get("x-trace-id") or ""
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                raise SystemExit(f"Server returned non-JSON response: {raw[:500]}") from None
            return data, trace_id
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code == 401:
                raise SystemExit(f"HTTP 401 - token is invalid or expired. {detail}") from None
            if e.code in (402, 403):
                raise SystemExit(f"HTTP {e.code} - access denied (check your CodePlan subscription). {detail}") from None
            raise SystemExit(f"HTTP {e.code} from search service: {detail}") from None
        except (urllib.error.URLError, OSError) as e:
            last_err = e
            if attempt == 0:
                time.sleep(1)  # transient SSL/network - retry once
                continue
            raise SystemExit(f"Network error reaching {endpoint}: {e}") from None

    raise SystemExit(f"Network error reaching {endpoint}: {last_err}")


# ---------- formatting ----------
def format_text(results: list[dict], show_content: bool, max_content_chars: int) -> str:
    """Format search results as human-readable text."""
    if not results:
        return "No search results found."

    lines: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "(no title)")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        date = r.get("date", "")
        content = r.get("content", "")

        lines.append(f"{'=' * 70}")
        lines.append(f"[{i}] {title}")
        if date:
            lines.append(f"    Date: {date}")
        lines.append(f"    URL:  {url}")
        if snippet:
            lines.append(f"    {snippet}")
        if show_content and content:
            truncated = content[:max_content_chars]
            if len(content) > max_content_chars:
                truncated += f"\n    ... [content truncated, {len(content) - max_content_chars} more chars]"
            lines.append(f"    --- Content ---")
            lines.append(f"    {truncated}")
        lines.append("")

    return "\n".join(lines)


def format_json(data: dict) -> str:
    """Output raw JSON response."""
    return json.dumps(data, ensure_ascii=False, indent=2)


# ---------- main ----------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Web search via Kimi's server-side search service.",
        usage="python kimi_search.py QUERY [--token KEY] [--limit N] [--content] [--out FILE] [--format text|json]",
    )
    parser.add_argument("query", help="Search query text")
    parser.add_argument("--token", default=None, help="Kimi Code access token (or set $KIMI_CODE_TOKEN)")
    parser.add_argument("--limit", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument(
        "--content", action="store_true",
        help="Enable page crawling to get full page content for each result (slower)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Server-side timeout per result in seconds (default: 30)",
    )
    parser.add_argument("--out", "-o", default=None, help="Save raw JSON response to this file")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--max-content-chars", type=int, default=2000,
        help="Max chars of page content to show per result when --content is used (default: 2000)",
    )
    args = parser.parse_args()

    token = resolve_token(args.token)

    print(f"[kimi-search] Query: {args.query}", file=sys.stderr)
    print(f"[kimi-search] Limit: {args.limit}, content crawling: {args.content}", file=sys.stderr)

    data, trace_id = do_search(
        token,
        args.query,
        limit=args.limit,
        enable_page_crawling=args.content,
        timeout_seconds=args.timeout,
    )

    if trace_id:
        print(f"[trace] request-id: {trace_id}", file=sys.stderr)

    # Save raw JSON if --out is specified
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(format_json(data), encoding="utf-8")
        print(f"[kimi-search] Saved JSON to {out_path}", file=sys.stderr)

    # Output
    results = data.get("search_results", [])
    print(f"[kimi-search] {len(results)} result(s)", file=sys.stderr)

    if args.format == "json":
        print(format_json(data))
    else:
        print(format_text(results, show_content=args.content, max_content_chars=args.max_content_chars))


if __name__ == "__main__":
    main()
