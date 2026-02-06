# TokenTotem

TokenTotem is a macOS menu bar plugin that keeps an eye on OpenAI and Anthropic spend so you do not get surprised by costs.

## Screenshot
![TokenTotem menu bar screenshot](docs/screenshot.png?v=20260206)

## Quick start (5 minutes)
1. Install SwiftBar.
2. Copy the plugin:
   - `cp bin/tokentotem.py ~/Library/Application\ Support/SwiftBar/Plugins/`
3. Make it executable:
   - `chmod +x ~/Library/Application\ Support/SwiftBar/Plugins/tokentotem.py`
4. Open SwiftBar (or restart it if it is already running).
5. In the menu, use the actions to set your keys and budget.
6. Click "Refresh now" in the menu to pull fresh data.

SwiftBar auto-loads the plugin once it is in the Plugins folder. TokenTotem relies on the in-menu "Refresh now" action (no filename-based interval).

## What you get
- Today (UTC) spend
- Month-to-date (UTC) spend
- Budget progress and warnings
- Rate limits (when response headers are available)

## Requirements
- macOS
- SwiftBar
- Python 3
- Admin API keys for OpenAI and Anthropic (billing endpoints)

## First-time setup
In the menu, set:
- OpenAI admin key
- Anthropic admin key
- Monthly budget
- Warning thresholds
- (Optional) manual rate limits

## Where your data lives
### Secrets (Keychain)
- OpenAI: service `tokentotem.openai.admin`, account `openai_admin`
- Anthropic: service `tokentotem.anthropic.admin`, account `anthropic_admin`

### Config and cache
- Config: `~/.config/tokentotem/config.json` (example in `docs/config.example.json`)
- Cache: `~/.cache/tokentotem/cache.json`

## Notes and behavior
- Provider cost APIs are org-level (not per-API-key).
- OpenAI can be filtered by project IDs via `providers.openai.project_ids`.
- Anthropic cost amounts are returned in lowest currency units (cents) and are converted to USD.
- Daily totals use UTC day boundaries.
- Rate limits use response headers when available; otherwise manual config is used.

## Troubleshooting
See `docs/troubleshooting.md`.

## Uninstall
1. Remove the plugin file from SwiftBar:
   - `rm ~/Library/Application\ Support/SwiftBar/Plugins/tokentotem.py`
2. (Optional) Remove config and cache:
   - `rm ~/.config/tokentotem/config.json`
   - `rm ~/.cache/tokentotem/cache.json`
3. (Optional) Remove Keychain items:
   - `tokentotem.openai.admin`
   - `tokentotem.anthropic.admin`

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

## Credits
Shipped by Codex.
