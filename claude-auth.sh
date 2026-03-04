#!/bin/bash
# Claude Code Authentication Switcher
# Easily toggle between API key and Claude Pro subscription

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

CONFIG_DIR="$HOME/.claude"
SETTINGS_FILE="$CONFIG_DIR/settings.json"
CREDENTIALS_BACKUP="$CONFIG_DIR/.credentials.json.api_backup"
API_SETTINGS_BACKUP="$CONFIG_DIR/settings.json.api_backup"

log_info() { echo -e "${GREEN}[Auth Switcher]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[Auth Switcher]${NC} $1"; }
log_error() { echo -e "${RED}[Auth Switcher]${NC} $1"; }

show_status() {
    echo ""
    echo "=========================================="
    echo "  Claude Code Authentication Status"
    echo "=========================================="
    echo ""

    if [ -f "$SETTINGS_FILE" ]; then
        if grep -q '"forceLoginMethod": "claudeai"' "$SETTINGS_FILE" 2>/dev/null; then
            echo -e "Current Mode: ${GREEN}Claude Pro Subscription${NC}"
        elif grep -q '"ANTHROPIC_AUTH_TOKEN"' "$SETTINGS_FILE" 2>/dev/null; then
            echo -e "Current Mode: ${BLUE}API Key${NC}"

            # Show API endpoint
            API_URL=$(grep '"ANTHROPIC_BASE_URL"' "$SETTINGS_FILE" | sed 's/.*: "\(.*\)".*/\1/')
            if [ -n "$API_URL" ]; then
                echo "API Endpoint: $API_URL"
            fi
        else
            echo -e "Current Mode: ${YELLOW}Default/Unknown${NC}"
        fi
    else
        echo -e "Status: ${RED}No settings file found${NC}"
    fi

    echo ""
    echo "=========================================="
    echo ""
}

save_api_config() {
    # Save current API configuration
    if grep -q '"ANTHROPIC_AUTH_TOKEN"' "$SETTINGS_FILE" 2>/dev/null; then
        cp "$SETTINGS_FILE" "$API_SETTINGS_BACKUP"
        log_info "API configuration saved"
    fi
}

restore_api_config() {
    if [ -f "$API_SETTINGS_BACKUP" ]; then
        cp "$API_SETTINGS_BACKUP" "$SETTINGS_FILE"

        # Restore credentials if backed up
        if [ -f "$CREDENTIALS_BACKUP" ]; then
            cp "$CREDENTIALS_BACKUP" "$CONFIG_DIR/.credentials.json"
        fi

        log_info "API configuration restored"
        return 0
    else
        log_error "No API configuration backup found"
        return 1
    fi
}

switch_to_subscription() {
    log_info "Switching to Claude Pro Subscription..."

    # Save current API config first
    save_api_config

    # Remove API key from settings
    python3 << 'PYTHON'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")

with open(settings_file, 'r') as f:
    settings = json.load(f)

# Remove API-related env vars
env = settings.get('env', {})
api_keys_to_remove = [
    'ANTHROPIC_AUTH_TOKEN',
    'ANTHROPIC_BASE_URL',
    'ANTHROPIC_DEFAULT_OPUS_MODEL',
    'ANTHROPIC_DEFAULT_SONNET_MODEL',
    'ANTHROPIC_DEFAULT_GLM_MODEL',
    'ANTHROPIC_AVAILABLE_MODELS',
    'ANTHROPIC_DEFAULT_GLM_47_MODEL',
    'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC'
]

for key in api_keys_to_remove:
    env.pop(key, None)

# Set subscription mode
settings['forceLoginMethod'] = 'claudeai'
settings['model'] = 'claude-opus-4-6'

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("Settings updated for subscription mode")
PYTHON

    # Clear credentials to force login
    mv -f "$CONFIG_DIR/.credentials.json" "$CREDENTIALS_BACKUP" 2>/dev/null || true

    log_info "Switched to Claude Pro Subscription"
    echo ""
    log_warn "Please restart Claude Code and login with your Claude account"
}

switch_to_api() {
    log_info "Switching to API Key..."

    if ! restore_api_config; then
        log_error "No saved API configuration found"
        echo ""
        echo "To set up API authentication:"
        echo "  1. Get your API key from https://console.anthropic.com/"
        echo "  2. Run: claude auth"
        echo "  3. Or manually add ANTHROPIC_AUTH_TOKEN to settings.json"
        return 1
    fi

    # Remove forceLoginMethod to allow API key
    python3 << 'PYTHON'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")

with open(settings_file, 'r') as f:
    settings = json.load(f)

# Remove subscription mode
settings.pop('forceLoginMethod', None)

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print("Settings updated for API mode")
PYTHON

    log_info "Switched to API Key"
    echo ""
    log_warn "Please restart Claude Code"
}

# Main
case "${1:-status}" in
    "sub"|"subscription"|"pro"|"claudeai")
        switch_to_subscription
        ;;
    "api"|"key"|"apikey")
        switch_to_api
        ;;
    "status"|"--status"|"-s")
        show_status
        ;;
    "help"|"--help"|"-h")
        echo "Claude Code Authentication Switcher"
        echo ""
        echo "Usage: claude-auth [mode]"
        echo ""
        echo "Modes:"
        echo "  sub, pro, subscription  Switch to Claude Pro Subscription"
        echo "  api, key               Switch to API Key"
        echo "  status, --status       Show current authentication mode"
        echo ""
        echo "Examples:"
        echo "  claude-auth sub         Switch to subscription"
        echo "  claude-auth api         Switch to API key"
        echo "  claude-auth status      Show current mode"
        ;;
    *)
        show_status
        echo ""
        echo "Usage: claude-auth [mode]"
        echo ""
        echo "Available modes:"
        echo "  sub, pro     - Switch to Claude Pro Subscription"
        echo "  api, key     - Switch to API Key"
        echo "  status       - Show current status (default)"
        echo ""
        echo "Run 'claude-auth help' for more information"
        ;;
esac
