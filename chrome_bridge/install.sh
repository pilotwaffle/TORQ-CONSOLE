#!/bin/bash
# TORQ Chrome Bridge - Linux/Mac Installation Script

set -e

echo "=========================================="
echo "TORQ Chrome Bridge - Installation"
echo "=========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found"
    echo "Please install Python 3.10+"
    exit 1
fi

echo "[OK] Python found: $(python3 --version)"
echo ""

# Install dependencies
echo "[1/4] Installing Python dependencies..."
pip3 install -q fastapi uvicorn pydantic
echo "[OK] Dependencies installed"
echo ""

# Create manifest
echo "[2/4] Creating native host manifest..."
MANIFEST_FILE="$SCRIPT_DIR/com.torq.chrome_bridge.json"

cat > "$MANIFEST_FILE" << EOF
{
  "name": "com.torq.chrome_bridge",
  "description": "TORQ Native Messaging Host for Prince Flowers Agent",
  "path": "$SCRIPT_DIR/run_host.sh",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://*"]
}
EOF

echo "[OK] Manifest created: $MANIFEST_FILE"
echo ""

# Detect Chrome config directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_CONFIG="$HOME/Library/Application Support/Google/Chrome"
else
    # Linux
    CHROME_CONFIG="$HOME/.config/google-chrome"
fi

NM_DIR="$CHROME_CONFIG/NativeMessagingHosts"

# Create directory
mkdir -p "$NM_DIR"

# Create symlink
echo "[3/4] Registering with Chrome..."
ln -sf "$MANIFEST_FILE" "$NM_DIR/com.torq.chrome_bridge.json"
echo "[OK] Registered with Chrome"
echo ""

# Make scripts executable
chmod +x "$SCRIPT_DIR/run_host.sh"
chmod +x "$SCRIPT_DIR/host.py"
echo "[OK] Made scripts executable"
echo ""

# Create .env
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "[4/4] Creating .env file..."
    cat > "$SCRIPT_DIR/.env" << EOF
CHROME_BRIDGE_API_KEY=tork-bridge-$RANDOM-$RANDOM
CHROME_BRIDGE_HOST=127.0.0.1
CHROME_BRIDGE_PORT=4545
EOF
    echo "[OK] Created .env with random API key"
fi
echo ""

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Load the Chrome extension:"
echo "   - Open chrome://extensions/"
echo "   - Enable Developer mode"
echo "   - Click 'Load unpacked'"
echo "   - Select: $SCRIPT_DIR/../chrome_extension"
echo ""
echo "2. Start the bridge:"
echo "   - Run: $SCRIPT_DIR/run_host.sh"
echo ""
echo "3. Test the connection:"
echo "   - Click the extension icon"
echo "   - Status should show 'Connected'"
echo ""
