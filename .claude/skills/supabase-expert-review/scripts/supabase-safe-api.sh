#!/usr/bin/env bash
set -euo pipefail

# Supabase Safe API Wrapper
# - Defaults to anon key, optional user JWT
# - Requires explicit --admin to use service_role
#
# Usage:
#   ./scripts/supabase-safe-api.sh get  rest     "/my_table?select=*" --anon
#   ./scripts/supabase-safe-api.sh post rest     "/my_table" --anon --data '{"name":"x"}'
#   ./scripts/supabase-safe-api.sh get  auth     "/user" --user
#   ./scripts/supabase-safe-api.sh get  storage  "/object/mybucket/path.png" --anon
#   ./scripts/supabase-safe-api.sh post functions "/my-fn" --user --data '{"x":1}'
#
# Required:
#   SUPABASE_URL
#   SUPABASE_ANON_KEY
# Optional:
#   SUPABASE_ACCESS_TOKEN   (user JWT)
# Admin:
#   SUPABASE_SERVICE_ROLE_KEY (only with --admin)

METHOD="${1:-}"
API="${2:-}"
PATH_QS="${3:-}"
shift 3 || true

if [[ -z "${SUPABASE_URL:-}" ]]; then
  echo "Missing SUPABASE_URL" >&2
  exit 1
fi

# Defaults
MODE="anon"  # anon | user | admin
DATA=""
CONTENT_TYPE="application/json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --anon) MODE="anon"; shift ;;
    --user) MODE="user"; shift ;;
    --admin) MODE="admin"; shift ;;
    --data) DATA="${2:-}"; shift 2 ;;
    --content-type) CONTENT_TYPE="${2:-}"; shift 2 ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

# Determine keys/tokens
ANON_KEY="${SUPABASE_ANON_KEY:-}"
USER_TOKEN="${SUPABASE_ACCESS_TOKEN:-}"
SERVICE_KEY="${SUPABASE_SERVICE_ROLE_KEY:-}"

if [[ -z "$ANON_KEY" ]]; then
  echo "Missing SUPABASE_ANON_KEY (safe default required)" >&2
  exit 1
fi

case "$API" in
  rest) BASE="${SUPABASE_URL%/}/rest/v1" ;;
  auth) BASE="${SUPABASE_URL%/}/auth/v1" ;;
  storage) BASE="${SUPABASE_URL%/}/storage/v1" ;;
  functions) BASE="${SUPABASE_URL%/}/functions/v1" ;;
  realtime) BASE="${SUPABASE_URL%/}/realtime/v1" ;;
  *)
    echo "Unknown API: $API (use rest|auth|storage|functions|realtime)" >&2
    exit 1
    ;;
esac

URL="${BASE}${PATH_QS}"

# Header rules:
# - Always send apikey (anon or service) for Supabase gateway
# - Authorization Bearer determines RLS / user context
# Supabase notes RLS enforced based on Authorization header;
# service_role as Bearer bypasses RLS.
# (So admin mode is explicit only.)
case "$MODE" in
  anon)
    APIKEY="$ANON_KEY"
    AUTH_BEARER="$ANON_KEY"
    ;;
  user)
    if [[ -z "$USER_TOKEN" ]]; then
      echo "Missing SUPABASE_ACCESS_TOKEN for --user mode" >&2
      exit 1
    fi
    APIKEY="$ANON_KEY"
    AUTH_BEARER="$USER_TOKEN"
    ;;
  admin)
    if [[ -z "$SERVICE_KEY" ]]; then
      echo "Missing SUPABASE_SERVICE_ROLE_KEY for --admin mode" >&2
      exit 1
    fi
    echo "WARNING: Using service_role key. RLS will be BYPASSED." >&2
    APIKEY="$SERVICE_KEY"
    AUTH_BEARER="$SERVICE_KEY"
    ;;
esac

CURL_ARGS=(-sS -X "$METHOD" "$URL"
  -H "apikey: ${APIKEY}"
  -H "Authorization: Bearer ${AUTH_BEARER}"
)

if [[ -n "$DATA" ]]; then
  CURL_ARGS+=(-H "Content-Type: ${CONTENT_TYPE}" --data "$DATA")
fi

curl "${CURL_ARGS[@]}"
