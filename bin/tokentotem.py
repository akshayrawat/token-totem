#!/usr/bin/env python3
"""SwiftBar plugin: TokenTotem."""

import argparse
import datetime as dt
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request

APP_NAME = "TokenTotem"
USER_AGENT = "TokenTotem/0.1"

SERVICE_OPENAI = "tokentotem.openai.admin"
ACCOUNT_OPENAI = "openai_admin"
SERVICE_ANTHROPIC = "tokentotem.anthropic.admin"
ACCOUNT_ANTHROPIC = "anthropic_admin"

# Local config + cache live outside the repo.
CONFIG_DIR = os.path.expanduser("~/.config/tokentotem")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.expanduser("~/.cache/tokentotem")
CACHE_PATH = os.path.join(CACHE_DIR, "cache.json")

DEFAULT_CONFIG = {
    "monthly_budget_usd": None,
    "warning_thresholds": [0.5, 0.8, 0.95],
    "providers": {
        "openai": {
            "enabled": True,
            "project_ids": [],
        },
        "anthropic": {
            "enabled": True,
        },
    },
    "currency": "USD",
}


class FetchError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


def merge_defaults(defaults, data):
    if not isinstance(data, dict):
        return defaults
    merged = dict(defaults)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_defaults(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config():
    ensure_dirs()
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return merge_defaults(DEFAULT_CONFIG, data)
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_CONFIG)


def save_config(config):
    ensure_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, sort_keys=True)


def load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    ensure_dirs()
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=2, sort_keys=True)


def keychain_get(service, account):
    # Read from macOS Keychain using the security CLI.
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                service,
                "-a",
                account,
                "-w",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def keychain_set(service, account, value):
    # Store/overwrite entry in Keychain.
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-s",
            service,
            "-a",
            account,
            "-w",
            value,
            "-U",
        ],
        check=True,
    )


def osascript_text(prompt, title, default=""):
    prompt = prompt.replace("\"", "\\\"")
    title = title.replace("\"", "\\\"")
    default = default.replace("\"", "\\\"")
    script = (
        f'text returned of (display dialog "{prompt}" '
        f'default answer "{default}" with title "{title}")'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def osascript_notify(message, title):
    message = message.replace("\"", "\\\"")
    title = title.replace("\"", "\\\"")
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], check=False)


def http_get_json(url, headers):
    # Shared JSON fetch with basic error handling.
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data, resp.headers
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8") if err.fp else ""
        raise FetchError(f"HTTP {err.code}: {body or err.reason}", status=err.code) from err
    except urllib.error.URLError as err:
        raise FetchError(str(err)) from err


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def month_start_utc(now):
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def to_rfc3339(ts):
    return ts.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_rfc3339(value):
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def fetch_openai_costs(admin_key, start, end, project_ids):
    # OpenAI org cost endpoint returns daily buckets.
    params = {
        "start_time": int(start.timestamp()),
        "end_time": int(end.timestamp()),
        "bucket_width": "1d",
        "limit": 31,
    }
    if project_ids:
        params["project_ids"] = project_ids
    url = "https://api.openai.com/v1/organization/costs?" + urllib.parse.urlencode(
        params, doseq=True
    )
    headers = {
        "Authorization": f"Bearer {admin_key}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    data, _resp_headers = http_get_json(url, headers)
    today_date = utc_now().date()
    today = 0.0
    mtd = 0.0
    for bucket in data.get("data", []):
        bucket_total = 0.0
        for result in bucket.get("results", []):
            amount = safe_float(result.get("amount", {}).get("value"))
            bucket_total += amount
        mtd += bucket_total
        start_time = bucket.get("start_time")
        if start_time is None:
            continue
        bucket_date = dt.datetime.fromtimestamp(
            start_time, tz=dt.timezone.utc
        ).date()
        if bucket_date == today_date:
            today += bucket_total
    return {
        "today": today,
        "mtd": mtd,
    }


def fetch_anthropic_costs(admin_key, start, end):
    # Anthropic cost report returns daily buckets in cents.
    params = {
        "starting_at": to_rfc3339(start),
        "ending_at": to_rfc3339(end),
        "bucket_width": "1d",
        "limit": 31,
    }
    url = "https://api.anthropic.com/v1/organizations/cost_report?" + urllib.parse.urlencode(
        params
    )
    headers = {
        "x-api-key": admin_key,
        "anthropic-version": "2023-06-01",
        "User-Agent": USER_AGENT,
    }
    data, _resp_headers = http_get_json(url, headers)
    today_date = utc_now().date()
    today = 0.0
    mtd = 0.0
    for bucket in data.get("data", []):
        bucket_total = 0.0
        for result in bucket.get("results", []):
            amount = safe_float(result.get("amount"))
            # Anthropic cost report returns amounts in lowest currency units (e.g. cents).
            bucket_total += amount / 100.0
        mtd += bucket_total
        start_at = parse_rfc3339(bucket.get("starting_at"))
        if start_at and start_at.date() == today_date:
            today += bucket_total
    return {
        "today": today,
        "mtd": mtd,
    }


def format_money(value):
    return f"${value:,.2f}"


def update_budget_notifications(total_mtd, config, cache):
    # Fire notifications only when crossing new thresholds.
    budget = config.get("monthly_budget_usd")
    if not budget:
        return cache
    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return cache
    if budget <= 0:
        return cache
    thresholds = sorted(config.get("warning_thresholds") or [])
    if not thresholds:
        return cache
    percent = total_mtd / budget
    last_notified = (
        cache.get("budget", {}).get("last_notified_threshold", 0) or 0
    )
    crossed = [t for t in thresholds if percent >= t and t > last_notified]
    if crossed:
        threshold = crossed[-1]
        osascript_notify(
            f"Monthly spend hit {int(threshold * 100)}% of budget ({format_money(total_mtd)} / {format_money(budget)}).",
            APP_NAME,
        )
        cache.setdefault("budget", {})["last_notified_threshold"] = threshold
    return cache


def set_budget(config):
    value = osascript_text("Monthly budget in USD", APP_NAME, "100")
    if value is None:
        return
    try:
        config["monthly_budget_usd"] = float(value)
    except ValueError:
        return
    save_config(config)


def set_thresholds(config):
    value = osascript_text(
        "Warning thresholds (comma separated percentages)",
        APP_NAME,
        "50,80,95",
    )
    if value is None:
        return
    parts = []
    for token in value.split(","):
        token = token.strip().replace("%", "")
        if not token:
            continue
        try:
            parts.append(float(token) / 100.0)
        except ValueError:
            continue
    if parts:
        config["warning_thresholds"] = parts
        save_config(config)


def set_openai_key():
    value = osascript_text("OpenAI admin API key", APP_NAME, "")
    if value:
        keychain_set(SERVICE_OPENAI, ACCOUNT_OPENAI, value)


def set_anthropic_key():
    value = osascript_text("Anthropic admin API key", APP_NAME, "")
    if value:
        keychain_set(SERVICE_ANTHROPIC, ACCOUNT_ANTHROPIC, value)


def open_config_file():
    ensure_dirs()
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    subprocess.run(["open", CONFIG_PATH], check=False)


def render_menu():
    # Main SwiftBar output: title line + menu items.
    config = load_config()
    cache = load_cache()
    now = utc_now()
    start = month_start_utc(now)

    openai_key = keychain_get(SERVICE_OPENAI, ACCOUNT_OPENAI)
    anthropic_key = keychain_get(SERVICE_ANTHROPIC, ACCOUNT_ANTHROPIC)

    provider_results = {}
    errors = {}

    if config["providers"]["openai"]["enabled"] and openai_key:
        try:
            provider_results["openai"] = fetch_openai_costs(
                openai_key,
                start,
                now,
                config["providers"]["openai"].get("project_ids"),
            )
        except FetchError as exc:
            errors["openai"] = str(exc)

    if config["providers"]["anthropic"]["enabled"] and anthropic_key:
        try:
            provider_results["anthropic"] = fetch_anthropic_costs(
                anthropic_key, start, now
            )
        except FetchError as exc:
            errors["anthropic"] = str(exc)

    if errors and cache.get("providers"):
        for provider, err in errors.items():
            if provider not in provider_results and provider in cache.get("providers", {}):
                cached = dict(cache["providers"][provider])
                cached["stale"] = True
                cached["error"] = err
                provider_results[provider] = cached
    for provider, err in errors.items():
        if provider not in provider_results:
            provider_results[provider] = {
                "today": 0.0,
                "mtd": 0.0,
                "error": err,
            }

    total_today = sum(result.get("today", 0.0) for result in provider_results.values())
    total_mtd = sum(result.get("mtd", 0.0) for result in provider_results.values())

    title = f"Today {format_money(total_today)} • MTD {format_money(total_mtd)}"
    print(title)
    print("---")

    for provider in ("openai", "anthropic"):
        if provider not in provider_results:
            continue
        result = provider_results[provider]
        provider_title = "OpenAI" if provider == "openai" else "Anthropic"
        print(f"{provider_title}")
        print(f"Today (UTC): {format_money(result.get('today', 0.0))}")
        print(f"Month-to-date (UTC): {format_money(result.get('mtd', 0.0))}")
        print("Scope: Org-wide spend (provider cost APIs are org-level)")
        if result.get("stale"):
            print("Status: Stale (using cached data)")
        if result.get("error"):
            print(f"Error: {result.get('error')}")
        print("---")

    if config.get("monthly_budget_usd"):
        budget = safe_float(config.get("monthly_budget_usd"))
        if budget > 0:
            percent = (total_mtd / budget) * 100
            print(f"Budget: {format_money(total_mtd)} / {format_money(budget)} ({percent:.1f}%)")
    else:
        print("Budget: Not set")

    last_updated = now.isoformat()
    print(f"Last updated: {last_updated}")
    print("---")

    print("Refresh now | refresh=true")
    print("---")

    script_path = os.path.abspath(__file__)
    print(
        f"Set OpenAI admin key... | bash=\"{script_path}\" param1=--action param2=set_openai_key terminal=false refresh=true"
    )
    print(
        f"Set Anthropic admin key... | bash=\"{script_path}\" param1=--action param2=set_anthropic_key terminal=false refresh=true"
    )
    print(
        f"Set monthly budget... | bash=\"{script_path}\" param1=--action param2=set_budget terminal=false refresh=true"
    )
    print(
        f"Set warning thresholds... | bash=\"{script_path}\" param1=--action param2=set_thresholds terminal=false refresh=true"
    )
    print(
        f"Open config file... | bash=\"{script_path}\" param1=--action param2=open_config terminal=false refresh=false"
    )

    cache["providers"] = provider_results
    cache["last_updated"] = last_updated
    cache = update_budget_notifications(total_mtd, config, cache)
    save_cache(cache)


def handle_action(action):
    config = load_config()
    if action == "set_openai_key":
        set_openai_key()
    elif action == "set_anthropic_key":
        set_anthropic_key()
    elif action == "set_budget":
        set_budget(config)
    elif action == "set_thresholds":
        set_thresholds(config)
    elif action == "open_config":
        open_config_file()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="run a configuration action")
    args = parser.parse_args()

    if args.action:
        handle_action(args.action)
        return

    render_menu()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"{APP_NAME}: Error")
        print("---")
        print(str(exc))
