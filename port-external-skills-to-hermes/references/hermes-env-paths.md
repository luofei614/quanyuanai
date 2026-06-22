# Hermes Environment Paths

Standard paths for Hermes configuration files across operating systems.

## Windows

- Config: `~/AppData/Local/hermes/config.yaml`
- Environment/credentials: `~/AppData/Local/hermes/.env`
- Skills: `~/AppData/Local/hermes/skills/`
- Fallback: `~/.hermes/.env`

## Linux / macOS

- Config: `~/.hermes/config.yaml`
- Environment/credentials: `~/.hermes/.env`
- Skills: `~/.hermes/skills/` (but on Windows use system dir above)
- Fallback: `~/.config/hermes/.env`

## Credential Keys in .env

Common keys found in Hermes `.env`:
- `KIMI_API_KEY` — Kimi Code / Moonshot token (depends on provider config)
- `OPENAI_API_KEY` — OpenAI API key
- `OPENROUTER_API_KEY` — OpenRouter key
- Various provider-specific keys

## How to Inspect

```bash
# List env file contents (keys only, not values)
grep "=" ~/AppData/Local/hermes/.env | cut -d= -f1

# Check config
cat ~/AppData/Local/hermes/config.yaml | grep -E "provider|api_key|default"
```
