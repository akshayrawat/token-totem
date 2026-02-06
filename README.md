# TokenTotem

TokenTotem is your friendly guardian spirit for LLM spend and limits. It lives in your macOS menu bar and keeps an eye on OpenAI and Anthropic usage so you do not get surprised by costs.

## What it shows
- Today (UTC) spend
- Month-to-date (UTC) spend
- Budget progress and warnings
- Rate limits (from response headers when available)

## Requirements
- macOS
- SwiftBar
- Python 3
- Admin API keys for OpenAI and Anthropic (billing endpoints)

## Optional dev tooling (uv)
If you want a modern Python workflow, use `uv`:
1. `uv venv`
2. `uv sync --dev`
3. `uv run ruff check bin/tokentotem.30m.py`

## Install
1. Install SwiftBar.
2. Copy the plugin script into your SwiftBar plugins folder:
   - `bin/tokentotem.30m.py` -> `~/Library/Application Support/SwiftBar/Plugins/`
3. Ensure the script is executable:
   - `chmod +x ~/Library/Application\ Support/SwiftBar/Plugins/tokentotem.30m.py`
4. SwiftBar will load it automatically (refresh interval is 30 minutes based on file name).

## Setup
Use the menu actions to configure:
- Set OpenAI admin key
- Set Anthropic admin key
- Set monthly budget
- Set warning thresholds
- (Optional) Set manual rate limits

Keys are stored in macOS Keychain under:
- Service: `tokentotem.openai.admin`
- Service: `tokentotem.anthropic.admin`

## Configuration
TokenTotem stores non-secret config at:
- `~/.config/tokentotem/config.json`

Example config lives at `docs/config.example.json`.

OpenAI-only: you can optionally set `providers.openai.project_ids` to filter costs to specific projects.

## Notes and limitations
- Provider cost APIs are org-level. Per-API-key spend is not currently available from those endpoints.
- OpenAI can be filtered by project IDs in config if you use projects to segment usage.
- Anthropic cost amounts are reported in lowest currency units (cents) and are converted to USD for display.
- Daily totals are based on UTC day boundaries.
- Rate limit headers may not be present on all endpoints; if missing, set manual limits.

## Troubleshooting
See `docs/troubleshooting.md`.
