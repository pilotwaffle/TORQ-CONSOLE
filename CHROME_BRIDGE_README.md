# TORQ Chrome Bridge - Complete Setup Guide

## Overview

The TORQ Chrome Bridge enables **Prince Flowers Agent** to control your browser for:
- Deployment verification (Railway, Vercel, etc.)
- Screenshot capture and visual regression testing
- Console log inspection
- Form filling and UI automation
- Multi-step workflow execution

### Architecture

```
┌─────────────────────────┐         ┌──────────────────────┐
│  Prince Flowers Agent   │────────▶│  Chrome Bridge API   │
│  (Railway / FastAPI)    │  HTTP   │  (localhost:4545)    │
└─────────────────────────┘         └──────────────────────┘
                                               │
                                               │ Native Messaging
                                               ▼
                                        ┌──────────────┐
                                        │   Chrome     │
                                        │  Extension   │
                                        └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │  Browser     │
                                        │  (Chrome)    │
                                        └──────────────┘
```

### Features

| Feature | Status |
|---------|--------|
| Navigation | ✅ |
| Click / Type / Extract | ✅ |
| Screenshots | ✅ |
| Wait for elements | ✅ |
| Approval gates | ✅ |
| Audit logging (Supabase) | ✅ |
| Console logs | ⏳ v2 |
| Network events | ⏳ v2 |

---

## Installation

### Prerequisites

- **Python 3.10+**
- **Google Chrome** (not Chromium, not Edge)
- **Admin privileges** (for native messaging registration)

### Step 1: Install the Bridge

#### Windows
```powershell
cd E:\TORQ-CONSOLE\chrome_bridge
.\install.bat
```

#### Linux/Mac
```bash
cd /path/to/TORQ-CONSOLE/chrome_bridge
chmod +x install.sh
./install.sh
```

This will:
1. Install Python dependencies (fastapi, uvicorn, pydantic)
2. Create the native messaging manifest
3. Register with Chrome (creates registry key/symlink)
4. Create a desktop shortcut
5. Generate a random API key

### Step 2: Load the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Toggle **Developer mode** (top right)
3. Click **Load unpacked**
4. Select: `E:\TORQ-CONSOLE\chrome_extension`
5. Copy the extension ID (looks like: `abcdefghijklmnopabcdefgh...`)

### Step 3: Update the Manifest (if needed)

If you see connection errors, update the native host manifest:

**Windows** (`E:\TORQ-CONSOLE\chrome_bridge\com.torq.chrome_bridge.json`):
```json
{
  "allowed_origins": ["chrome-extension://YOUR_COPIED_EXTENSION_ID/"]
}
```

Then re-run `install.bat` to update the registry.

### Step 4: Start the Bridge

Double-click the desktop shortcut **OR** run:
```powershell
cd E:\TORQ-CONSOLE\chrome_bridge
.\run_host.bat
```

You should see:
```
[TORQ Bridge] Starting TORQ Native Chrome Bridge
[TORQ Bridge] API: http://127.0.0.1:4545
[TORQ Bridge] Native message loop started
```

### Step 5: Verify Connection

1. Click the Chrome extension icon (popup opens)
2. Status should show **"Connected to TORQ Bridge"**

---

## Usage

### From Prince Flowers Agent

```python
from torq_console.tools.chrome_operator import ChromeOperator

# Create operator
chrome = ChromeOperator()

# Create session
session = await chrome.create_session(metadata={"task": "verify_railway"})

# User approves in extension popup...

# Execute actions
result = await chrome.act(session.session_id, actions=[
    {"op": "navigate", "url": "https://web-production-74ed0.up.railway.app/health"},
    {"op": "wait", "ms": 1500},
    {"op": "screenshot"}
])

# Check result
if result.ok:
    print(f"Screenshot captured: {bool(result.artifacts)}")
```

### Deployment Verification

```python
from torq_console.tools.chrome_operator import verify_deployment

result = await verify_deployment(
    url="https://web-production-74ed0.up.railway.app/health",
    expected_sha="c12b9f86",
    screenshot=True
)

if result.verification_passed:
    print("Deployment verified!")
```

### Via HTTP API

```bash
# Create session
curl -X POST http://127.0.0.1:4545/v1/session \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"task": "test"}}'

# Execute actions
curl -X POST http://127.0.0.1:4545/v1/act \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "require_approval": false,
    "actions": [
      {"op": "navigate", "url": "https://example.com"},
      {"op": "screenshot"}
    ]
  }'
```

---

## Supported Actions

| Action | Parameters | Description |
|--------|-----------|-------------|
| `navigate` | `url` (string) | Navigate to URL |
| `click` | `selector`, `by` (css/id/xpath) | Click element |
| `type` / `input` | `selector`, `text`, `by` | Type into input |
| `extract` | `selector`, `mode`, `by` | Extract text/html/value |
| `screenshot` | none | Capture visible tab |
| `wait` | `ms` (int) or `selector` (string) | Wait for time or element |
| `get_title` | none | Get page title |
| `get_url` | none | Get current URL |
| `reload` | none | Reload page |
| `go_back` | none | Navigate back |
| `go_forward` | none | Navigate forward |

---

## Safety & Approval

### Automatic Approval Required For:

- Password fields (`input[type=password]`)
- Financial domains (bank, crypto, wallet, payment, etc.)
- Destructive actions (delete, purchase, transfer)

### Approval Flow

1. Prince calls `chrome_act()` with actions
2. Bridge returns `needs_approval: true`
3. User opens Chrome extension popup
4. User pastes `session_id` and clicks **Approve**
5. Prince retries `chrome_act()` → executes

---

## Railway Integration

### Environment Variables (Railway)

```bash
# On Railway, set these to connect Prince to your local bridge:
CHROME_BRIDGE_URL=https://your-tunnel-url.railway.app
CHROME_BRIDGE_API_KEY=your-api-key
```

### Tunneling (Required for Railway → Local)

Since Railway can't reach `127.0.0.1`, use a tunnel:

**Option 1: Cloudflare Tunnel (Recommended)**
```bash
cloudflared tunnel --url http://127.0.0.1:4545
```

**Option 2: Tailscale Funnel**
```bash
tailscale funnel 4545
```

**Option 3: ngrok**
```bash
ngrok http 4545
```

Then update Railway's `CHROME_BRIDGE_URL` to the tunnel URL.

---

## Troubleshooting

### "Failed to connect to native host"

1. Verify bridge is running (`run_host.bat`)
2. Check registry key exists:
   ```
   HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.torq.chrome_bridge
   ```
3. Verify manifest path is correct

### "Extension shows Disconnected"

1. Restart the bridge process
2. Reload the extension in `chrome://extensions/`
3. Check browser console for errors

### "Session requires approval"

1. Copy the `session_id` from the error
2. Paste into Chrome extension popup
3. Click **Approve**
4. Retry the request

### "Timeout waiting for extension result"

1. Check if Chrome has a visible window (not minimized)
2. Verify extension is enabled
3. Check bridge logs for errors

---

## File Structure

```
TORQ-CONSOLE/
├── chrome_bridge/
│   ├── host.py              # Native messaging host + FastAPI
│   ├── run_host.bat         # Windows launcher
│   ├── run_host.sh          # Linux/Mac launcher
│   ├── install.bat          # Windows installer
│   ├── install.sh           # Linux/Mac installer
│   ├── com.torq.chrome_bridge.json  # Native host manifest
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # API key (generated)
│
├── chrome_extension/
│   ├── manifest.json        # Extension manifest
│   ├── background.js        # Service worker + action runner
│   ├── popup.html           # Approval UI
│   ├── popup.js             # Popup logic
│   └── icons/               # Extension icons
│
└── torq_console/
    ├── tools/
    │   └── chrome_operator.py   # Python client for Prince
    └── api/
        └── chrome_tools.py      # FastAPI router
```

---

## Development

### Running Tests

```bash
cd E:\TORQ-CONSOLE\chrome_bridge
python host.py
```

### Checking Logs

Bridge logs are printed to stderr. To capture:
```powershell
.\run_host.bat 2>bridge.log
```

### Adding New Actions

1. Add action type to `chrome_extension/background.js` in `executeAction()`
2. Add handler in `domOperation()` function
3. Document in `torq_console/api/chrome_tools.py`

---

## Security Considerations

1. **API Key**: Always set `CHROME_BRIDGE_API_KEY` in production
2. **Tunnel Auth**: Use IP allowlist on your tunnel service
3. **Approval Gates**: Never disable approval for sensitive operations
4. **Audit Logs**: All actions are logged to Supabase
5. **Local Only**: Bridge only binds to `127.0.0.1` by default

---

## License

MIT License - Part of TORQ Console

---

**Status**: ✅ Ready for Production
