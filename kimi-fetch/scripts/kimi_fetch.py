#!/usr/bin/env python3
"""
kimi_fetch.py — Fetch a URL via Kimi's server-side extraction service.

Pure Python (stdlib only). No Node, no Kimi Code CLI.
Calls the same backend the official FetchURL tool uses:
    POST https://api.kimi.com/coding/v1/fetch
    Authorization: Bearer <token>
    Accept: text/markdown
    Body: {"url": "https://..."}

The server fetches the page, extracts the main content, and returns it as
clean Markdown — no HTML parsing needed on our side.

Usage:
  python kimi_fetch.py "https://example.com/article" --token <KEY>
  python kimi_fetch.py "https://example.com/article" --token <KEY> --out page.md
  python kimi_fetch.py "https://example.com/article" --token <KEY> --max-chars 5000

Token resolution order: --token > $KIMI_CODE_TOKEN > $KIMI_API_KEY > ~/.kimi-code/credentials/kimi-code.json
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
REQUEST_TIMEOUT = 60  # seconds — page fetching can be slower than API calls


# ---------- paths ----------
def kimi_home() -> Path:
    explicit = os.environ.get("KIMI_CODE_HOME", "").strip()
    return Path(explicit) if explicit else Path.home() / ".kimi-code"


def credentials_path() -> Path:
    return kimi_home() / "credentials" / "kimi-code.json"


def device_id_path() -> Path:
    return kimi_home() / "device_id"


def fetch_url() -> str:
    explicit = os.environ.get("KIMI_FETCH_API_URL", "").strip()
    if explicit:
        return explicit
    base = (os.environ.get("KIMI_CODE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return f"{base}/fetch"


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
    detected_sources: list[str] = []

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
        "Accept": "text/markdown",
        "X-Msh-Tool-Call-Id": str(uuid.uuid4()),
        "X-Msh-Platform": ascii_header(os.environ.get("KIMI_MSH_PLATFORM", "kimi-fetch-skill")),
        "X-Msh-Version": ascii_header(os.environ.get("KIMI_MSH_VERSION", VERSION)),
        "X-Msh-Device-Name": ascii_header(os.environ.get("KIMI_MSH_DEVICE_NAME", socket.gethostname())),
        "X-Msh-Device-Model": ascii_header(os.environ.get("KIMI_MSH_DEVICE_MODEL", device_model())),
        "X-Msh-Os-Version": ascii_header(os.environ.get("KIMI_MSH_OS_VERSION", platform.release())),
        "X-Msh-Device-Id": ascii_header(get_device_id()),
        "User-Agent": f"kimi-fetch-skill/{VERSION}",
    }


# ---------- HTTP ----------
def do_fetch(token: str, url: str) -> tuple[str, str]:
    """
    POST {"url": url} to the fetch endpoint.
    Returns (markdown_content, trace_id).
    The server extracts the page's main content and returns it as Markdown text.
    """
    endpoint = fetch_url()
    body = json.dumps({"url": url}, ensure_ascii=False).encode("utf-8")
    headers = build_headers(token)
    ctx = ssl.create_default_context()
    last_err: Exception | None = None

    for attempt in range(2):
        req = urllib.request.Request(endpoint, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                trace_id = resp.headers.get("x-request-id") or resp.headers.get("x-trace-id") or ""
            return content, trace_id
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code == 401:
                raise SystemExit(f"HTTP 401 — token is invalid or expired. {detail}") from None
            if e.code == 402 or e.code == 403:
                raise SystemExit(f"HTTP {e.code} — access denied (check your CodePlan subscription). {detail}") from None
            raise SystemExit(f"HTTP {e.code} from fetch service: {detail}") from None
        except (urllib.error.URLError, OSError) as e:
            last_err = e
            if attempt == 0:
                time.sleep(1)  # transient SSL/network — retry once
                continue
            raise SystemExit(f"Network error reaching {endpoint}: {e}") from None

    raise SystemExit(f"Network error reaching {endpoint}: {last_err}")


# ---------- main ----------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a URL via Kimi's server-side extraction (returns Markdown).",
        usage="python kimi_fetch.py URL [--token KEY] [--out FILE] [--max-chars N]",
    )
    parser.add_argument("url", help="The URL to fetch")
    parser.add_argument("--token", default=None, help="Kimi Code access token (or set $KIMI_CODE_TOKEN)")
    parser.add_argument("--out", "-o", default=None, help="Save full Markdown to this file")
    parser.add_argument(
        "--max-chars", type=int, default=None,
        help="Truncate stdout to N characters (full content still saved to --out if specified)",
    )
    args = parser.parse_args()

    token = resolve_token(args.token)

    # Resolve token printed to stderr
    print(f"[kimi-fetch] Fetching: {args.url}", file=sys.stderr)

    content, trace_id = do_fetch(token, args.url)

    if trace_id:
        print(f"[trace] request-id: {trace_id}", file=sys.stderr)

    # Save full content if --out is specified
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"[kimi-fetch] Saved {len(content)} chars to {out_path}", file=sys.stderr)

    # Print to stdout (optionally truncated)
    if args.max_chars and len(content) > args.max_chars:
        print(content[:args.max_chars])
        print(f"\n... [truncated, {len(content) - args.max_chars} more chars]", file=sys.stderr)
    else:
        print(content)


if __name__ == "__main__":
    main()
