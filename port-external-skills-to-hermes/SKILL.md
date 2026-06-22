---
title: Port External Skills to Hermes
skill: port-external-skills-to-hermes
name: port-external-skills-to-hermes
description: Systematic workflow for copying and adapting external skills (from LobeHub, OpenClaw, WorkBuddy, GitHub, etc.) into Hermes-compatible skills in the quanyuanai category. Covers credential reuse from Hermes model config, API endpoint discovery, and skill validation.
version: 1.0.0
category: quanyuanai
tags: [skill-porting, hermes, external-skills, migration, quanyuanai, api-adaptation]
author: quanyuanai
---

# Port External Skills to Hermes

Systematic workflow for copying and adapting external AI agent skills into Hermes-compatible format.

## When to Use

- User has skills from LobeHub, OpenClaw, WorkBuddy, Claude Code, or other agent platforms
- User wants to reuse those skills in Hermes
- User wants the ported skill to automatically use Hermes model credentials (API keys/tokens)
- User wants skills placed in the `quanyuanai` category

## Prerequisites

- Source skill files accessible (local path or downloadable)
- Hermes configured with at least one model provider (the skill will reuse its credentials)

## Workflow

### Step 1 — Analyze Source Skill

Read the source skill's:
1. `SKILL.md` or `skill.md` — understand purpose, commands, parameters
2. Scripts in `scripts/` or `src/scripts/` — identify the credential mechanism
3. Check if it uses API keys, access tokens, OAuth, or other auth

Key questions:
- What credential does it need? (API key, access token, OAuth token)
- How is the credential currently provided? (env var, config file, CLI arg, interactive prompt)
- What API endpoint(s) does it call?
- What dependencies does it need? (stdlib only, or pip packages)

### Step 2 — Determine Credential Mapping

**Critical decision**: Can the skill reuse Hermes' existing model credentials?

| Source Credential | Hermes Equivalent | Compatible? | Action |
|--------------------|-------------------|-------------|--------|
| Kimi Code Token (`KIMI_CODE_TOKEN`) | `KIMI_API_KEY` in Hermes `.env` | ✅ Usually same token | Map `KIMI_API_KEY` → `KIMI_CODE_TOKEN` in script |
| Moonshot API Key (`MOONSHOT_API_KEY`) | `KIMI_API_KEY` in Hermes `.env` | ⚠️ May be different key | Test first; if fails, require separate config |
| OpenAI API Key (`OPENAI_API_KEY`) | `OPENAI_API_KEY` in Hermes `.env` | ✅ Usually same | Direct pass-through |
| Custom provider key | Check Hermes `.env` | Varies | Inspect Hermes config first |

**How to inspect Hermes credentials**:
```bash
# Check what API keys Hermes has configured
grep -n "API_KEY\|api_key" ~/AppData/Local/hermes/.env 2>/dev/null | head -20

# Check Hermes config for provider settings
grep -n "provider\|api_key" ~/AppData/Local/hermes/config.yaml | head -20
```

### Step 3 — Copy and Transform

1. **Create target directory**:
   ```bash
   mkdir -p ~/AppData/Local/hermes/skills/quanyuanai/<skill-name>/scripts
   ```

2. **Copy source files**. Choose the method based on what's available:

   **Method A — Direct file copy (if source is local)**:
   ```bash
   cp -r /path/to/source/* ~/AppData/Local/hermes/skills/quanyuanai/<skill-name>/
   ```

   **Method B — ZIP archive download (if GitHub raw URLs fail due to network)**:
   When `raw.githubusercontent.com` or `git clone` fail with SSL/connection errors (common on some networks), download the entire repo as a ZIP:
   ```bash
   curl -L "https://github.com/<owner>/<repo>/zipball/main" -o /tmp/repo.zip
   unzip -q /tmp/repo.zip -d /tmp/repo-extracted
   # Copy only the skill subdirectory
   cp -r /tmp/repo-extracted/*/skills/<skill-name>/* ~/AppData/Local/hermes/skills/quanyuanai/<skill-name>/
   ```
   This is more reliable than fetching individual raw files when the network is unstable.

   **Method C — GitHub API recursive tree (for many small files)**:
   Use the GitHub API to list all files recursively, then batch-download:
   ```bash
   curl -sL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" > tree.json
   # Parse tree.json for blob paths under skills/<skill-name>/, then download each via raw.githubusercontent.com
   ```
   Add small delays between requests to avoid rate limiting.

   **⚠️ Important**: Do NOT use `execute_code` for file writes that need to persist. The `execute_code` sandbox runs in an isolated temp directory — files written there do NOT appear on the host filesystem. Use `write_file` tool or `terminal` commands for actual filesystem writes.

3. **Transform credential resolution** in the script:

3. **Transform credential resolution** in the script:
   - Add `find_hermes_env_path()` function (Windows + Linux/macOS paths)
   - Add `parse_env_file()` function to read `.env` key=value pairs
   - Modify credential resolver to check Hermes `.env` as fallback
   - Priority order:
     1. CLI argument (`--token`, `--api-key`)
     2. Local skill `.env` file (skill-specific override)
     3. **Hermes `.env` file** (auto-detected)
     4. Environment variables
     5. Default credential files (`~/.kimi-code/credentials/`, etc.)

4. **Write Hermes-format `SKILL.md`**:
   - Frontmatter with `title`, `skill`, `description`, `version`, `category: quanyuanai`, `tags`
   - Chinese documentation (user preference)
   - "自动配置" section explaining Hermes credential reuse
   - "手动配置" section for overrides
   - Command examples for both CLI and Hermes `execute_code` usage
   - Error handling table

5. **Create `.env.example`** and `.gitignore`

### Step 4 — Test and Validate

1. **Test credential auto-detection**:
   ```bash
   cd ~/AppData/Local/hermes/skills/quanyuanai/<skill-name>
   python scripts/<script>.py --help  # or status command
   ```
   Look for: `[SkillName] Token/API Key 来源: Hermes .env: ...`

2. **Test actual functionality**:
   - Run a simple query/command
   - Verify output format
   - Check error messages are helpful

3. **Verify Hermes recognition**:
   ```bash
   hermes skills list  # or check skills_list tool output
   ```
   Should appear under `quanyuanai` category.

### Step 5 — Handle API Endpoint Issues

If the skill fails with auth errors:

1. **Check if the API endpoint is correct**:
   - Kimi Code API: `https://api.kimi.com/coding/v1/...` (for CodePlan tokens)
   - Moonshot API: `https://api.moonshot.cn/v1/...` (for Moonshot API keys)
   - These are DIFFERENT platforms with different capabilities

2. **Test endpoint capabilities**:
   ```python
   # Try to discover available methods/endpoints
   import urllib.request, json
   # POST to endpoint with various method names
   ```

3. **Document endpoint limitations** in the skill's `SKILL.md`:
   - What works with Kimi Code tokens
   - What requires Moonshot API keys
   - What features are unavailable

## Credential Resolver Template (Python)

Add this pattern to ported scripts:

```python
import os
import platform
from pathlib import Path

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
    """Token 解析优先级（Hermes 兼容）"""
    detected_sources: list[str] = []
    token: str | None = None

    # 1. CLI argument
    if cli_token and cli_token.strip():
        return cli_token.strip()

    # 2. Local skill .env
    skill_dir = Path(__file__).parent.parent
    local_env = skill_dir / ".env"
    if local_env.exists():
        env_vars = parse_env_file(local_env)
        token = env_vars.get("EXPECTED_TOKEN_KEY", "").strip()
        if token:
            detected_sources.append(f"本地 .env: {local_env}")

    # 3. Hermes .env (auto-detect)
    if not token:
        hermes_env = find_hermes_env_path()
        if hermes_env:
            env_vars = parse_env_file(hermes_env)
            token = env_vars.get("KIMI_API_KEY", "").strip()  # or other key
            if token:
                detected_sources.append(f"Hermes .env: {hermes_env}")

    # 4. Environment variables
    if not token:
        token = os.environ.get("EXPECTED_TOKEN_KEY", "").strip()
        if token:
            detected_sources.append("环境变量")

    # 5. Default credential files
    if not token:
        # Check ~/.kimi-code/credentials/kimi-code.json etc.
        pass

    if not token:
        print("Error: 未找到 Token/API Key。", file=sys.stderr)
        print("自动检测路径：...", file=sys.stderr)
        raise SystemExit(1)

    if detected_sources:
        print(f"[Skill] Token 来源: {detected_sources[0]}", file=sys.stderr)
    return token
```

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Kimi Code vs Moonshot confusion | 401/403 errors | Check which platform the skill was designed for |
| Shell quote escaping in curl | `unexpected EOF` | Use Python `urllib` instead of curl for complex requests |
| Missing dependencies | `ImportError` | Check if source skill needs `pip install`; prefer stdlib-only scripts |
| Windows path issues | File not found | Use `Path.home() / "AppData" / "Local" / "hermes"` pattern |
| Skill not recognized by Hermes | Missing from `skills_list` | Ensure `SKILL.md` has correct frontmatter with `skill:` field |
| GitHub raw download fails (SSL/timeout) | `Recv failure`, `SSLEOFError`, curl timeout | Use ZIP archive fallback: `curl -L <repo>/zipball/main -o repo.zip` then unzip |
| `execute_code` writes not persisting | Files missing after sandbox exit | Use `write_file` tool or `terminal` for actual filesystem writes |
| GitHub API rate limiting | 403 errors from API | Add small delays between requests; use ZIP archive for bulk downloads |
| GitHub raw + git clone both fail | SSL EOF errors on all direct connections | ZIP archive is the only reliable method; `curl -L <repo>/zipball/main` works when everything else fails |
| GitHub raw works for API but fails for raw content | API tree JSON downloads fine, but raw.githubusercontent.com times out | Use API tree to get file list, then download ZIP archive and extract selectively |

## References

- `references/github-download-techniques.md` — Fallback download methods when GitHub raw URLs fail (ZIP archive, API tree, git clone).
- `references/kimi-code-api-endpoints.md`

Documented Kimi Code API endpoints discovered through testing:

- `POST /coding/v1/search` — Web search (returns structured results)
- `POST /coding/v1/fetch` — URL content extraction (returns Markdown)
- `POST /coding/v1/tools` — Data source tools (finance, arxiv, tianyancha, etc.)
  - Method: `get_data_source_desc` — Get API docs for a data source
  - Method: `call_data_source_tool` — Execute a data source query

**Important**: These endpoints require Kimi Code access tokens (not Moonshot API keys). The same token may work for both platforms if the user has a CodePlan subscription.

- `references/hermes-baoyu-design-usage.md` — Hermes 桌面 GUI 环境下使用 baoyu-design skill 的注意事项和变通方案（浏览器工具不可用、HTTP 服务器启动问题、文件交付方式）。

Hermes configuration paths by OS:

- **Windows**: `~/AppData/Local/hermes/.env`, `~/AppData/Local/hermes/config.yaml`
- **Linux/macOS**: `~/.hermes/.env`, `~/.hermes/config.yaml`

## Examples

### Example 1: Port a Kimi Code skill (kimi-search)

Source: `~/.workbuddy/skills/kimi-search/scripts/kimi_search.py`
- Already had Hermes-compatible token resolver
- Just needed Hermes-format `SKILL.md` and `.env.example`
- Test: `python scripts/kimi_search.py "test query"`

### Example 2: Port a skill needing dependency installation (metaso-search)

Source: External skill requiring `pip install requests`
- Added `requirements.txt`
- Used `uv pip install` or `python -m pip install`
- Created `.env` with `METASO_API_KEY`

### Example 3: Port a skill with different credential name (kimi-datasource)

Source: Used `KIMI_CODE_TOKEN`, Hermes has `KIMI_API_KEY`
- Added mapping logic in `resolve_token()`
- Added fallback: if `KIMI_CODE_TOKEN` not found, try `KIMI_API_KEY`
- Documented the difference in `SKILL.md`

## Version History

### v1.0.0 (2024-06-19)
- Initial version
- Documented workflow from porting 4 skills: kimi-search, kimi-search-v2, kimi-fetch, kimi-datasource
- Discovered Kimi Code API endpoints through active testing
- Established credential reuse pattern for Hermes model config
