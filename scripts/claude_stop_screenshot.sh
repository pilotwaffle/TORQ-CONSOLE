#!/bin/bash
# Claude Code Stop Hook - Capture Screenshot
#
# This script runs when Claude Code completes a response.
# Captures a screenshot of the current browser state for review.
#
# Usage: Configure in ~/.claude/settings.json or .claude/settings.local.json
#
# {
#   "hooks": {
#     "Stop": [
#       {
#         "matcher": "*",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "/path/to/TORQ-CONSOLE/scripts/claude_stop_screenshot.sh",
#             "timeout": 30000
#           }
#         ]
#       }
#     ]
#   }
# }

set -e

# Configuration
BRIDGE_URL="${CHROME_BRIDGE_URL:-http://127.0.0.1:4545}"
API_KEY="${CHROME_BRIDGE_API_KEY:-}"
SESSION_ID=""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[Claude Stop Hook]${NC} $1"
}

log_error() {
    echo -e "${RED}[Claude Stop Hook]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[Claude Stop Hook]${NC} $1"
}

# Check if bridge is running
check_bridge() {
    if ! curl -s -f "$BRIDGE_URL/health" > /dev/null 2>&1; then
        log_error "Chrome Bridge is not running at $BRIDGE_URL"
        log_info "Start it with: cd chrome_bridge && ./run_http_only.sh"
        exit 1
    fi
}

# Create session
create_session() {
    local response
    response=$(curl -s -X POST "$BRIDGE_URL/v1/session" \
        -H "Content-Type: application/json" \
        ${API_KEY:+-H "Authorization: Bearer $API_KEY"} \
        -d '{"metadata": {"trigger": "claude_stop_hook"}}')

    SESSION_ID=$(echo "$response" | jq -r '.session_id // empty')

    if [ -z "$SESSION_ID" ]; then
        log_error "Failed to create session"
        echo "Response: $response" >&2
        exit 1
    fi

    log_info "Session created: $SESSION_ID"
}

# Capture screenshot
capture_screenshot() {
    log_info "Capturing screenshot..."

    local response
    response=$(curl -s -X POST "$BRIDGE_URL/v1/act" \
        -H "Content-Type: application/json" \
        ${API_KEY:+-H "Authorization: Bearer $API_KEY"} \
        -d "{
            \"session_id\": \"$SESSION_ID\",
            \"actions\": [{\"op\": \"screenshot\"}],
            \"require_approval\": false
        }")

    local ok
    ok=$(echo "$response" | jq -r '.ok // false')

    if [ "$ok" = "true" ]; then
        log_info "Screenshot captured successfully"

        # Check if screenshot data is present
        local has_screenshot
        has_screenshot=$(echo "$response" | jq -r '.artifacts.screenshot_png_data_url // empty')

        if [ -n "$has_screenshot" ]; then
            # Save screenshot to file
            local screenshot_dir="/tmp/claude-screenshots"
            mkdir -p "$screenshot_dir"

            local timestamp=$(date +%Y%m%d_%H%M%S)
            local screenshot_file="$screenshot_dir/claude_stop_$timestamp.png"

            # Extract base64 data and decode
            echo "$has_screenshot" | sed 's/^data:image\/png;base64,//' | base64 -d > "$screenshot_file"

            log_info "Screenshot saved: $screenshot_file"
        fi
    else
        # Check if approval is required
        local needs_approval
        needs_approval=$(echo "$response" | jq -r '.needs_approval // false')

        if [ "$needs_approval" = "true" ]; then
            log_warn "Session requires approval in Chrome extension"
            log_info "Session ID: $SESSION_ID"
            log_info "Open Chrome extension, paste session ID, click Approve"
        else
            log_error "Failed to capture screenshot"
            echo "Response: $response" >&2
            exit 1
        fi
    fi
}

# Main
main() {
    log_info "Starting screenshot capture..."
    check_bridge
    create_session
    capture_screenshot
    log_info "Done"
}

main "$@"
