#!/bin/bash
# Claude Code PostToolUse Hook - Verify Deployment After Changes
#
# This script runs after Edit/Write tools to verify deployments
# when deployment-related files are modified.
#
# Usage: Configure in ~/.claude/settings.json or .claude/settings.local.json
#
# {
#   "hooks": {
#     "PostToolUse": [
#       {
#         "matcher": "Edit|Write",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "/path/to/TORQ-CONSOLE/scripts/verify_deployment.sh \"$FILE_PATH\"",
#             "timeout": 60000
#           }
#         ]
#       }
#     ]
#   }
# }

set -e

FILE_PATH="${1:-}"
BRIDGE_URL="${CHROME_BRIDGE_URL:-http://127.0.0.1:4545}"
API_KEY="${CHROME_BRIDGE_API_KEY:-}"

# Deployment URLs to verify (configure these)
RAILWAY_URL="${RAILWAY_DEPLOY_URL:-https://web-production-74ed0.up.railway.app/health}"
VERCEL_URL="${VERCEL_DEPLOY_URL:-}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[Deployment Verify]${NC} $1"; }
log_error() { echo -e "${RED}[Deployment Verify]${NC} $1" >&2; }
log_warn() { echo -e "${YELLOW}[Deployment Verify]${NC} $1"; }
log_deploy() { echo -e "${BLUE}[Deployment Verify]${NC} $1"; }

# Check if file is deployment-related
is_deployment_file() {
    local file="$1"
    local filename=$(basename "$file")

    # Deployment-related files
    case "$filename" in
        railway.json|Dockerfile|vercel.json|.railwayignore)
            return 0
            ;;
        requirements*.txt|package.json|pyproject.toml)
            return 0
            ;;
        *_deployment.py|deploy*.py)
            return 0
            ;;
        *.yml|*.yaml)
            # CI/CD files
            return 0
            ;;
        *)
            return 1
            esac
}

# Verify Railway deployment
verify_railway() {
    log_deploy "Verifying Railway deployment at $RAILWAY_URL"

    # Create session
    local response
    response=$(curl -s -X POST "$BRIDGE_URL/v1/session" \
        -H "Content-Type: application/json" \
        ${API_KEY:+-H "Authorization: Bearer $API_KEY"} \
        -d '{"metadata": {"trigger": "verify_railway"}}')

    local session_id
    session_id=$(echo "$response" | jq -r '.session_id // empty')

    if [ -z "$session_id" ]; then
        log_error "Failed to create session"
        return 1
    fi

    # Execute verification
    response=$(curl -s -X POST "$BRIDGE_URL/v1/act" \
        -H "Content-Type: application/json" \
        ${API_KEY:+-H "Authorization: Bearer $API_KEY"} \
        -d "{
            \"session_id\": \"$session_id\",
            \"actions\": [
                {\"op\": \"navigate\", \"url\": \"$RAILWAY_URL\"},
                {\"op\": \"wait\", \"ms\": 2000},
                {\"op\": \"screenshot\"},
                {\"op\": \"extract\", \"selector\": \"body\", \"mode\": \"text\"}
            ],
            \"require_approval\": false
        }")

    local ok
    ok=$(echo "$response" | jq -r '.ok // false')

    if [ "$ok" = "true" ]; then
        log_info "Railway deployment verified"

        # Extract git_sha from response
        local body_text
        body_text=$(echo "$response" | jq -r '.results[] | select(.op == "extract") | .data.text // empty')

        if echo "$body_text" | grep -q '"git_sha"'; then
            local git_sha
            git_sha=$(echo "$body_text" | grep -o '"git_sha":"[^"]*"' | cut -d'"' -f4)
            log_info "Deployed SHA: $git_sha"
        fi
    else
        local needs_approval
        needs_approval=$(echo "$response" | jq -r '.needs_approval // false')

        if [ "$needs_approval" = "true" ]; then
            log_warn "Railway verification requires approval in Chrome extension"
        else
            log_error "Railway verification failed"
        fi
    fi
}

# Verify Vercel deployment
verify_vercel() {
    if [ -z "$VERCEL_URL" ]; then
        return
    fi

    log_deploy "Verifying Vercel deployment at $VERCEL_URL"

    # Similar to Railway verification
    local response
    response=$(curl -s -X POST "$BRIDGE_URL/v1/session" \
        -H "Content-Type: application/json" \
        ${API_KEY:+-H "Authorization: Bearer $API_KEY"} \
        -d '{"metadata": {"trigger": "verify_vercel"}}')

    local session_id
    session_id=$(echo "$response" | jq -r '.session_id // empty')

    if [ -z "$session_id" ]; then
        log_error "Failed to create session"
        return 1
    fi

    response=$(curl -s -X POST "$BRIDGE_URL/v1/act" \
        -H "Content-Type: application/json" \
        ${API_KEY:+-H "Authorization: Bearer $API_KEY"} \
        -d "{
            \"session_id\": \"$session_id\",
            \"actions\": [
                {\"op\": \"navigate\", \"url\": \"$VERCEL_URL\"},
                {\"op\": \"wait\", \"ms\": 2000},
                {\"op\": \"screenshot\"}
            ],
            \"require_approval\": false
        }")

    local ok
    ok=$(echo "$response" | jq -r '.ok // false')

    if [ "$ok" = "true" ]; then
        log_info "Vercel deployment verified"
    else
        log_warn "Vercel verification pending approval"
    fi
}

# Main
main() {
    # Check if bridge is running
    if ! curl -s -f "$BRIDGE_URL/health" > /dev/null 2>&1; then
        log_warn "Chrome Bridge not running, skipping verification"
        exit 0
    fi

    # Check if file is deployment-related
    if [ -n "$FILE_PATH" ] && is_deployment_file "$FILE_PATH"; then
        log_info "Deployment file modified: $FILE_PATH"
        verify_railway
        verify_vercel
    fi
}

main "$@"
