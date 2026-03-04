# Claude Code Remote Control + TORQ Chrome Bridge Integration

## Overview

This integration enables **Claude Code's Remote Control** to utilize the **TORQ Chrome Bridge** for browser automation, allowing Claude to "see" and "control" web browsers while maintaining full safety gates and audit trails.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Claude Code Session                          │
│                    (Local with Remote Control)                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐         ┌──────────────┐         ┌─────────────┐ │
│  │   Claude    │◀────────│   MCP Server │◀────────│  Browser    │ │
│  │   Agent     │  Hooks  │   (Bridge)   │  HTTP   │   Tools     │ │
│  └─────────────┘         └──────────────┘         └─────────────┘ │
│         │                         │                       │        │
└─────────┼─────────────────────────┼───────────────────────┼────────┘
          │                         │                       │
          │                         │                       │
          ▼                         ▼                       ▼
    ┌─────────────┐         ┌──────────────┐         ┌─────────────┐
    │  Remote     │         │   Chrome     │         │   Chrome    │
    │  Control    │         │   Bridge     │         │  Extension  │
    │  (Mobile/   │         │   (Local)    │         │  (Browser)  │
    │   Browser)  │         │   :4545      │         │             │
    └─────────────┘         └──────────────┘         └─────────────┘
```

## Components

### 1. MCP Server: Chrome Bridge Provider

Exposes browser automation tools to Claude Code via MCP.

### 2. Claude Code Hooks

Event-driven automation that triggers browser operations:
- `Stop` hook: Capture screenshot after Claude completes work
- `PostToolUse` hook: Verify deployments after Edit/Write
- `Notification` hook: Send browser notifications to mobile

### 3. Remote Control Integration

Claude can request browser operations from mobile, which execute locally.

## Installation

### Step 1: Install Chrome Bridge

```powershell
cd E:\TORQ-CONSOLE\chrome_bridge
.\install.bat
```

### Step 2: Configure MCP Server

Add to `~/.claude/mcp.json` (global) or `.claude/mcp.json` (project):

```json
{
  "mcpServers": {
    "chrome-bridge": {
      "command": "python",
      "args": [
        "E:/TORQ-CONSOLE/torq_console/mcp/chrome_bridge_server.py"
      ],
      "env": {
        "CHROME_BRIDGE_URL": "http://127.0.0.1:4545",
        "CHROME_BRIDGE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Step 3: Configure Hooks

Add to `~/.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "E:/TORQ-CONSOLE/scripts/claude-stop-screenshot.sh",
            "timeout": 30000
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "E:/TORQ-CONSOLE/scripts/verify-after-change.sh \"$FILE_PATH\"",
            "timeout": 60000
          }
        ]
      }
    ]
  }
}
```

## Usage

### From Claude Code (Local)

```
You: Navigate to Railway and check the deployment status

Claude: [Uses chrome-bridge MCP tool]
      Creates session → Approve in extension → Executes
      [Returns deployment status with screenshot]
```

### From Remote Control (Mobile)

```
You (on phone): Take a screenshot of the current deployment

Claude (local): [Executes browser operation]
                [Sends screenshot to phone]
```

## MCP Tools

The MCP server exposes these tools to Claude:

| Tool | Parameters | Description |
|------|------------|-------------|
| `chrome_navigate` | `url` | Navigate to URL |
| `chrome_click` | `selector`, `by` | Click element |
| `chrome_type` | `selector`, `text` | Type into input |
| `chrome_extract` | `selector`, `mode` | Extract data |
| `chrome_screenshot` | - | Capture screenshot |
| `chrome_verify_deployment` | `url`, `expected` | Verify deployment |

## Hook Scripts

### Stop Hook: Final Screenshot

`scripts/claude-stop-screenshot.sh`:
```bash
#!/bin/bash
# Capture screenshot after Claude completes work
# Useful for seeing the final state after code changes

curl -s -X POST http://127.0.0.1:4545/v1/session \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"trigger": "claude_stop_hook"}}' \
  | jq -r '.session_id' \
  | xargs -I {} curl -s -X POST http://127.0.0.1:4545/v1/act \
      -H "Content-Type: application/json" \
      -d "{\"session_id\": {}, \"actions\": [{\"op\": \"screenshot\"}], \"require_approval\": false}"
```

### PostToolUse Hook: Deployment Verification

`scripts/verify-after-change.sh`:
```bash
#!/bin/bash
# Verify deployment after file changes
# Triggers when Edit/Write tools are used

FILE_PATH="$1"

# Check if this looks like a deployment file
if echo "$FILE_PATH" | grep -qE "(railway\.json|Dockerfile|vercel\.json)"; then
    # Trigger deployment verification
    python -c "
import asyncio
from torq_console.tools.chrome_operator import verify_deployment

async def verify():
    result = await verify_deployment(
        'https://web-production-74ed0.up.railway.app/health',
        screenshot=True
    )
    print(f'Verification: {\"PASS\" if result.ok else \"FAIL\"}')

asyncio.run(verify())
"
fi
```

## Remote Control Workflow

### Complete Remote Deployment Cycle

1. **Start Remote Control**
   ```bash
   claude remote-control
   ```

2. **From Phone, Request Deployment**
   ```
   You: Deploy to Railway and verify it's working

   Claude (local): [Edits files]
                   [Commits to git]
                   [Triggers Railway deploy]
                   [Uses chrome-bridge to verify]
                   [Sends screenshot to phone]
   ```

3. **Approve Browser Session**
   - Phone prompts: "Approve browser session?"
   - You tap "Approve"
   - Chrome extension processes actions

## Safety Configuration

### Auto-Approval for Safe Operations

In `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "chrome_bridge_read_only",
        "hooks": [
          {
            "type": "autoApprove"
          }
        ]
      }
    ]
  }
}
```

### Sensitive Operations Require Approval

Define in `chrome_operator.py`:
```python
AUTO_APPROVE_OPERATIONS = [
    "navigate",
    "extract",
    "get_title",
    "get_url",
    "screenshot"
]

REQUIRE_APPROVE_OPERATIONS = [
    "click",
    "type",
    "submit"
]
```

## Troubleshooting

### MCP Server Not Starting

1. Check Chrome Bridge is running:
   ```powershell
   curl http://127.0.0.1:4545/health
   ```

2. Check MCP server logs:
   ```bash
   cat ~/.claude/mcp-logs/chrome-bridge.log
   ```

### Hooks Not Firing

1. Verify hook configuration:
   ```bash
   claude config hooks
   ```

2. Check script permissions:
   ```bash
   chmod +x scripts/*.sh
   ```

### Remote Control Can't Access Browser

1. Ensure Chrome Bridge is in HTTP-only mode:
   ```powershell
   .\run_http_only.bat
   ```

2. Approve session in Chrome extension popup

## Advanced: Custom MCP Tools

Define custom tools for your workflow:

```python
# In chrome_bridge_server.py
@mcp.tool()
async def verify_railway_deployment(url: str, expected_sha: str = None) -> dict:
    """Verify a Railway deployment is healthy."""
    chrome = ChromeOperator()
    session = await chrome.create_session(metadata{"task": "verify_railway"})

    actions = [
        {"op": "navigate", "url": url},
        {"op": "screenshot"}
    ]

    result = await chrome.act(session.session_id, actions)
    return {"verified": result.ok, "artifacts": result.artifacts}
```

Then Claude can call:
```
You: Verify the Railway deployment at https://web-production-74ed0.up.railway.app

Claude: [Calls verify_railway_deployment tool]
      [Returns verification result]
```

## File Structure

```
TORQ-CONSOLE/
├── torq_console/
│   └── mcp/
│       └── chrome_bridge_server.py    # MCP server for Claude Code
├── scripts/
│   ├── claude-stop-screenshot.sh      # Stop hook script
│   ├── verify-after-change.sh         # PostToolUse hook script
│   └── notify-mobile.sh               # Notification hook script
└── .claude/
    └── mcp.json                        # MCP server configuration
```

## Security Considerations

1. **API Key Protection**: Store `CHROME_BRIDGE_API_KEY` in environment
2. **Approval Gates**: Never auto-approve destructive actions
3. **Audit Logging**: All browser actions logged to Supabase
4. **Local Only**: Chrome Bridge binds to 127.0.0.1 by default
5. **Session Isolation**: Each Claude session gets unique browser session

## Future Enhancements

- [ ] Real-time screenshot streaming to remote
- [ ] Voice commands via mobile for browser control
- [ ] Multi-browser session support
- [ ] Scheduled browser verification tasks
- [ ] Integration with CI/CD pipelines

---

**Status**: ✅ Architecture Complete | ⏳ Implementation In Progress
