# Troubleshooting

## I see "Missing admin key"
TokenTotem uses the provider billing/usage APIs, which require admin-level API keys. Use the menu actions to set them in Keychain.

## I see "HTTP 401" or "HTTP 403"
Your admin key may not have access to billing endpoints, or the key may be expired or revoked. Recheck the key and org permissions.

## I see "Stale" data
The latest request failed, so TokenTotem is showing cached values. Check your network connection or API status, then refresh.

## The menu bar title shows $0.00
If your account has no usage for the current local day or month, totals will show 0.00. Also confirm you are in the correct org/account.
