#!/bin/bash
# TORQ Chrome Bridge - HTTP-Only Mode Launcher
#
# Use this mode when:
# - Testing the HTTP API without Chrome extension
# - Running with a tunnel (Cloudflare, ngrok) for Railway access
# - The extension is NOT needed for basic HTTP testing

set -e

# Enable HTTP-only mode
export NO_NATIVE_MESSAGING=1

# Use a strong API key for production
export CHROME_BRIDGE_API_KEY="${CHROME_BRIDGE_API_KEY:-torq-bridge-change-me}"

# Listen on all interfaces (required for tunnel)
export CHROME_BRIDGE_HOST="0.0.0.0"

export CHROME_BRIDGE_PORT="${CHROME_BRIDGE_PORT:-4545}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/..:${PYTHONPATH}"

echo "=========================================="
echo "TORQ Chrome Bridge - HTTP-Only Mode"
echo "=========================================="
echo ""
echo "This mode runs the HTTP API server without"
echo "Chrome Native Messaging. Use this for:"
echo "  - Railway tunnel connections"
echo "  - API testing without extension"
echo "  - Headless browser operations"
echo ""
echo "Server: http://${CHROME_BRIDGE_HOST}:${CHROME_BRIDGE_PORT}"
echo ""
echo "To connect Railway:"
echo "  1. Start a tunnel (cloudflared, ngrok, etc.)"
echo "     cloudflared tunnel --url http://127.0.0.1:4545"
echo "  2. Copy the tunnel URL"
echo "  3. Set Railway env: CHROME_BRIDGE_URL=https://your-tunnel-url"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Launch the host
python3 "${SCRIPT_DIR}/host.py"
