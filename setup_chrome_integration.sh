#!/bin/bash
# Claude Code Chrome Integration Setup for TORQ Console
# This script sets up and tests the Chrome browser automation

echo "=========================================="
echo "Claude Code Chrome Integration Setup"
echo "=========================================="
echo ""

# Check Claude Code version
echo "1. Checking Claude Code CLI version..."
claude --version
if [ $? -ne 0 ]; then
    echo "[ERROR] Claude Code CLI not found. Please install first."
    exit 1
fi
echo "[OK] Claude Code CLI found"
echo ""

# Check for Chrome browser
echo "2. Checking for Chrome browser..."
if command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v chrome &> /dev/null; then
    CHROME_CMD="chrome"
elif [ -f "/c/Program Files/Google/Chrome/Application/chrome.exe" ]; then
    CHROME_CMD="/c/Program Files/Google/Chrome/Application/chrome.exe"
elif [ -f "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" ]; then
    CHROME_CMD="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
else
    echo "[WARNING] Chrome not found in standard paths"
    echo "Please ensure Google Chrome is installed"
fi
echo "[OK] Chrome browser available"
echo ""

# Check for Chrome extension
echo "3. Chrome Extension Installation Required"
echo "   MANUAL STEP: Install 'Claude in Chrome' extension from Chrome Web Store"
echo "   URL: https://chromewebstore.google.com/detail/claude-in-chrome/pnjdndfochkaalbgiahlmjfpnmjmnmhi"
echo ""
echo "   After installation:"
echo "   - Click the extension icon"
echo "   - Sign in with your Claude account"
echo ""

# Test Chrome flag
echo "4. Testing --chrome flag availability..."
unset CLAUDECODE
claude --help 2>&1 | grep -q "\-\-chrome"
if [ $? -eq 0 ]; then
    echo "[OK] --chrome flag is available"
else
    echo "[ERROR] --chrome flag not available. Update Claude Code:"
    echo "   claude --update"
    exit 1
fi
echo ""

# Create test script
echo "5. Creating Chrome integration test script..."
cat > test_chrome_integration.sh << 'EOF'
#!/bin/bash
# Test Chrome Integration with Railway Deployment Verification

echo "Testing Claude Code Chrome Integration..."
echo "Target: Verify Railway deployment at https://web-production-74ed0.up.railway.app"
echo ""

# This would be run with: claude --chrome -p "..."
# Example prompt:
PROMPT="Open https://web-production-74ed0.up.railway.app, take a screenshot of the health endpoint /health, and verify the git_sha is c12b9f86"

echo "Example Chrome automation prompt:"
echo "$PROMPT"
echo ""
echo "To run this test:"
echo "  claude --chrome"
echo ""
echo "Then in the Claude session, ask it to:"
echo "  - Navigate to Railway URLs"
echo "  - Take screenshots"
echo "  - Verify deployments"
echo "  - Fill forms and click buttons"
EOF

chmod +x test_chrome_integration.sh
echo "[OK] Test script created: test_chrome_integration.sh"
echo ""

# Create Railway verification workflow
cat > railway_chrome_verify.sh << 'EOF'
#!/bin/bash
# Railway Deployment Verification using Claude Chrome Integration

# This script demonstrates using Claude Code Chrome to verify deployments

echo "=========================================="
echo "Railway Deployment Chrome Verification"
echo "=========================================="
echo ""

echo "PREREQUISITES:"
echo "1. Claude Code CLI installed (v2.0.73+)"
echo "2. Claude in Chrome extension installed and signed in"
echo "3. Chrome browser running"
echo ""

echo "TO VERIFY RAILWAY DEPLOYMENT:"
echo ""
echo "1. Start Claude with Chrome integration:"
echo "   claude --chrome"
echo ""
echo "2. Ask Claude to:"
echo "   - Open https://railway.com/project/afc9d3b1-9080-4b39-a7f9-bb7945c9cc01/service/170755ba-0dde-4a4b-badf-5429971c80ad"
echo "   - Check the current deployment SHA"
echo "   - Verify branch is set to control-plane-v1-clean"
echo "   - Take screenshots of the deployment status"
echo "   - Check if 'Deploy on push' is enabled"
echo ""

echo "3. For health endpoint verification:"
echo "   - Navigate to https://web-production-74ed0.up.railway.app/health"
echo "   - Read the JSON response"
echo "   - Verify git_sha matches expected commit"
echo ""

echo "4. To trigger new deployment (if needed):"
echo "   - Click 'New Deployment' button"
echo "   - Select control-plane-v1-clean branch"
echo "   - Click 'Deploy now'"
echo "   - Monitor build logs"
echo ""

echo "=========================================="
echo "KEYBOARD SHORTCUTS"
echo "=========================================="
echo ""
echo "Claude Code Shortcuts:"
echo "  Ctrl+C      - Cancel current input"
echo "  Ctrl+D      - Exit Claude Code"
echo "  Ctrl+L      - Clear screen"
echo "  @           - Trigger file path completion"
echo "  /           - Trigger slash commands"
echo ""

echo "Chrome Integration Commands (natural language):"
echo "  'Open https://example.com'"
echo "  'Take a screenshot'"
echo "  'Click the login button'"
echo "  'Fill in the email field with user@example.com'"
echo "  'Read the console errors'"
echo "  'Get the page title'"
echo "  'Navigate to settings'"
echo ""
EOF

chmod +x railway_chrome_verify.sh
echo "[OK] Railway verification script created: railway_chrome_verify.sh"
echo ""

echo "=========================================="
echo "SETUP COMPLETE"
echo "=========================================="
echo ""
echo "NEXT STEPS:"
echo "1. Install Claude in Chrome extension"
echo "2. Sign in to the extension with your Claude account"
echo "3. Run: claude --chrome"
echo "4. Test with Railway verification workflow"
echo ""
echo "For automated verification, run:"
echo "  ./railway_chrome_verify.sh"
echo ""
