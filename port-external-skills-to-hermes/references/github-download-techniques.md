# GitHub Download Techniques for Skill Porting

When porting skills from GitHub repos, the network environment may block or throttle `raw.githubusercontent.com` and `git clone`. Here are proven fallback techniques.

## Technique 1: ZIP Archive (Most Reliable)

Download the entire repo as a ZIP, then extract only the skill subdirectory.

```bash
# Download ZIP
curl -L "https://github.com/<owner>/<repo>/zipball/main" -o /tmp/repo.zip

# Extract
unzip -q /tmp/repo.zip -d /tmp/repo-extracted

# The extracted folder has a name like "Owner-Repo-CommitSHA"
ls /tmp/repo-extracted/

# Copy only the skill files
cp -r /tmp/repo-extracted/Owner-Repo-*/skills/<skill-name>/* \
  ~/AppData/Local/hermes/skills/quanyuanai/<skill-name>/
```

**Pros:** Single download, bypasses raw URL issues, works through most firewalls.
**Cons:** Downloads entire repo (may be large), need to locate correct subdirectory after extraction.

## Technique 2: GitHub API Recursive Tree

For repos where you need selective file downloading or want to see the full structure first.

```bash
# Get recursive file tree
curl -sL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" > tree.json

# Parse for files under the skill directory
# Each blob entry has: path, type, size, url, download_url
# Download each file via: https://raw.githubusercontent.com/<owner>/<repo>/main/<path>
```

**Pros:** Full visibility of repo structure, can filter before downloading.
**Cons:** Many individual HTTP requests (rate limiting risk), need delays between requests.

## Technique 3: Git Clone (When Network Allows)

```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/repo
cp -r /tmp/repo/skills/<skill-name>/* ~/AppData/Local/hermes/skills/quanyuanai/<skill-name>/
```

**Pros:** Clean, gets exactly what's in the repo.
**Cons:** Often blocked by firewalls; `git://` and `https://` may both fail.

## Choosing a Technique

| Situation | Recommended Technique |
|-----------|----------------------|
| Network unstable, raw URLs fail | ZIP archive (Technique 1) |
| Need to inspect structure first | GitHub API tree (Technique 2) |
| Network is open, git works | Git clone (Technique 3) |
| Only a few files needed | Direct raw URL fetch |
| Many small files in subdirectories | ZIP archive or API tree |

## Windows-Specific Notes

- Use `/c/tmp/` or `$HOME/AppData/Local/Temp/` for temp files in MSYS bash.
- `unzip` is available in git-bash; if not, use `python -m zipfile`.
- The extracted ZIP folder name includes the commit SHA prefix (e.g., `JimLiu-baoyu-design-edde718`).

## execute_code Sandbox Warning

**Never use `execute_code` for file writes that need to persist.** The sandbox runs in an isolated temp directory (`C:\Users\...\AppData\Local\Temp\hermes_sandbox_...\`). Files written there are discarded when the script exits. Always use:
- `write_file` tool for creating/updating files
- `terminal` commands for bulk copy/move operations
