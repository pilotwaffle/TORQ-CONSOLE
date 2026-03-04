# Chrome Bridge - Correct Startup Sequence

## The "It Exits Immediately" is NORMAL! ✅

When you run `host.py` directly, it exits because:
- Native Messaging reads from stdin
- Without Chrome attached, stdin closes immediately
- Bridge detects EOF → clean exit

## Correct Startup Methods

### Method 1: Let Chrome Launch It (Recommended)

1. Install the bridge:
   ```powershell
   cd E:\TORQ-CONSOLE\chrome_bridge
   .\install.bat
   ```

2. Load the extension in Chrome:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `E:\TORQ-CONSOLE\chrome_extension`

3. Click the extension icon → Chrome launches the bridge automatically

### Method 2: Run HTTP Server Standalone (For API Testing)

If you want to run the API server without Native Messaging (for HTTP-only testing):

```powershell
# Set environment variable to disable stdin reading
set NO_NATIVE_MESSAGING=1
python host.py
```

Then the API server at `http://127.0.0.1:4545` will stay running.

### Method 3: Desktop Shortcut

After running `install.bat`, use the desktop shortcut "TORQ Chrome Bridge":
- Opens a command window with the bridge running
- Stays open for manual testing
- Extension can connect to it

## Verification

1. Click the extension icon
2. Should show: **"Connected to TORQ Bridge"**
3. If it shows "Disconnected", the bridge isn't running

## For Railway Integration

Since Railway needs to reach your local bridge, you must use a tunnel:

```powershell
# In one terminal, start the bridge with NO_NATIVE_MESSAGING=1
set NO_NATIVE_MESSAGING=1
python host.py

# In another terminal, start the tunnel
cloudflared tunnel --url http://127.0.0.1:4545
```

Then set Railway's `CHROME_BRIDGE_URL` to the tunnel URL.
