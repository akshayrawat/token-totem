# TokenTotem

TokenTotem is your friendly guardian spirit for LLM spend and limits. It lives in your macOS menu bar and keeps an eye on OpenAI and Anthropic usage so you do not get surprised by costs.

## For users (product setup)
### What you get
- Today (UTC) spend
- Month-to-date (UTC) spend
- Budget progress and warnings
- Rate limits (when response headers are available)

### Requirements
- macOS
- SwiftBar
- Python 3
- Admin API keys for OpenAI and Anthropic (billing endpoints)

### Install
1. Install SwiftBar.
2. Copy `bin/tokentotem.py` to `~/Library/Application Support/SwiftBar/Plugins/`.
3. Make it executable:
   - `chmod +x ~/Library/Application\ Support/SwiftBar/Plugins/tokentotem.py`

SwiftBar will auto-load the plugin. Use the in-menu "Refresh now" action when you want an update.

### First-time setup
Use the menu actions to set:
- OpenAI admin key
- Anthropic admin key
- Monthly budget
- Warning thresholds
- (Optional) manual rate limits

Keys are stored in macOS Keychain:
- `tokentotem.openai.admin`
- `tokentotem.anthropic.admin`

Non-secret config lives at `~/.config/tokentotem/config.json`. Example: `docs/config.example.json`.

### Notes
- Provider cost APIs are org-level (not per-API-key).
- OpenAI can be filtered by project IDs via `providers.openai.project_ids`.
- Anthropic cost amounts are returned in lowest currency units (cents) and are converted to USD.
- Daily totals use UTC day boundaries.

## For engineers (development)
### Tooling (uv)
```
uv venv
uv sync --dev
uv run ruff check bin/tokentotem.py
```

### Files to know
- Plugin: `bin/tokentotem.py`
- Docs: `docs/`
- Config: `~/.config/tokentotem/config.json`
- Cache: `~/.cache/tokentotem/cache.json`

## Troubleshooting
See `docs/troubleshooting.md`.
