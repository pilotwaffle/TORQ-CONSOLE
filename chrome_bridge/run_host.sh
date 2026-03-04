#!/bin/bash
# TORQ Chrome Bridge - Linux/Mac Launcher
# This script launches the native messaging host for Chrome
#
# Modes:
#   Normal (default): Native messaging + HTTP API (launched by Chrome extension)
#   HTTP-only: Set NO_NATIVE_MESSAGING=1 for Railway/tunnel testing

set -e

# Configuration
export CHROME_BRIDGE_API_KEY="${CHROME_BRIDGE_API_KEY:-torq-bridge-change-me}"
export CHROME_BRIDGE_HOST="${CHROME_BRIDGE_HOST:-127.0.0.1}"
export CHROME_BRIDGE_PORT="${CHROME_BRIDGE_PORT:-4545}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Add to Python path
export PYTHONPATH="${SCRIPT_DIR}/..:${PYTHONPATH}"

# Check for HTTP-only mode
if [ "${NO_NATIVE_MESSAGING}" = "1" ]; then
    echo "Starting TORQ Chrome Bridge [HTTP-ONLY MODE]..."
    echo "This mode is for Railway/tunnel testing (no Chrome extension connection)"
else
    echo "Starting TORQ Chrome Bridge [NATIVE MESSAGING MODE]..."
    echo "Chrome extension will connect automatically when clicked"
fi

echo "Host: ${CHROME_BRIDGE_HOST}:${CHROME_BRIDGE_PORT}"
echo ""

# Launch the host
python3 "${SCRIPT_DIR}/host.py"
