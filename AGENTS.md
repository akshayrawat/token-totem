# Codex Instructions (TokenTotem)

## Quick overview
- SwiftBar plugin: `bin/tokentotem.30m.py`
- Config: `~/.config/tokentotem/config.json`
- Cache: `~/.cache/tokentotem/cache.json`
- Docs: `README.md`, `docs/`

## How to run locally
- Menu bar output (debug): `python3 bin/tokentotem.30m.py`
- Run ruff: `uv run ruff check bin/tokentotem.30m.py`

## Keychain entries
- OpenAI admin key: service `tokentotem.openai.admin`, account `openai_admin`
- Anthropic admin key: service `tokentotem.anthropic.admin`, account `anthropic_admin`

## Editing guidance
- Keep SwiftBar output format intact (title line, `---` separators, then menu items).
- Menu actions are wired via `param1=--action param2=<action>`; keep names stable.
- Defaults live in `DEFAULT_CONFIG`; merge via `merge_defaults()`.

## API touchpoints
- OpenAI org cost endpoint: `/v1/organization/costs` (project filter supported).
- Anthropic cost report: `/v1/organizations/cost_report`.
- Rate limits are read from response headers if present; otherwise use manual config.

## Common tasks
- Add a new provider: extend `DEFAULT_CONFIG`, add fetch + render block, and update README.
- Change refresh interval: rename the file (e.g. `tokentotem.10m.py`).
- Update docs: keep README install/setup in sync with actual menu actions.

## Notes
- Costs are org-level per provider APIs; per-key spend is not supported.
- Anthropic amounts are in lowest currency units (cents) and are converted to USD.
