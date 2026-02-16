#!/usr/bin/env bash
set -euo pipefail

# Safe gh API wrapper:
# - Checks gh auth status (best effort)
# - Offers a quick rate-limit peek
#
# Usage:
#   ./scripts/gh-safe.sh GET /repos/OWNER/REPO
#   ./scripts/gh-safe.sh GET /rate_limit

METHOD="${1:-}"
ENDPOINT="${2:-}"

if [[ -z "$METHOD" || -z "$ENDPOINT" ]]; then
  echo "Usage: $0 <METHOD> <ENDPOINT>" >&2
  exit 1
fi

# Best-effort auth check
if ! gh auth status >/dev/null 2>&1; then
  echo "gh not authenticated. Run: gh auth login" >&2
  exit 1
fi

# Check core rate limit before making calls
RATE_INFO=$(gh api -H "Accept: application/vnd.github+json" /rate_limit 2>/dev/null || true)
if [[ -n "$RATE_INFO" ]]; then
  REMAINING=$(echo "$RATE_INFO" | jq -r '.resources.core.remaining // "unknown"' 2>/dev/null || echo "unknown")
  if [[ "$REMAINING" != "unknown" && "$REMAINING" -lt 10 ]]; then
    echo "WARNING: Only $REMAINING API calls remaining. Consider waiting." >&2
  fi
fi

gh api -H "Accept: application/vnd.github+json" "$ENDPOINT"
