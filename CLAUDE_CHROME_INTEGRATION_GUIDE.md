# Claude Code Chrome Integration - Quick Start Guide

## Overview

Claude Code Chrome Integration enables AI-controlled browser automation. You can ask Claude to navigate websites, click buttons, fill forms, take screenshots, and verify deployments - all from the terminal.

## Prerequisites

| Requirement | Version | Status |
|-------------|---------|--------|
| Claude Code CLI | 2.0.73+ | ✅ 2.1.44 installed |
| Google Chrome | Any recent version | Required |
| Claude for Chrome Extension | 1.0.36+ | Need to install |
| Claude Subscription | Pro/Team/Enterprise | Required |

## Installation Steps

### 1. Install Chrome Extension

Visit Chrome Web Store and install "Claude in Chrome":
```
https://chromewebstore.google.com/detail/claude-in-chrome/pnhdjlaonhjfgfabffncecfnhfgjipm
```

### 2. Sign In

Click the extension icon and sign in with your Claude account.

### 3. Start Claude with Chrome

```bash
claude --chrome
```

## Keyboard Shortcuts

### Claude Code Terminal
| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current input/generation |
| `Ctrl+D` | Exit Claude Code |
| `Ctrl+L` | Clear screen (preserves history) |
| `@` | Trigger file path auto-completion |
| `/` | Trigger slash commands |
| `!` | Run Bash commands directly |

### No Special Chrome Shortcuts
Use natural language to control the browser:
- "Open https://example.com"
- "Click the submit button"
- "Take a screenshot"
- "Read the console logs"

## Usage Examples

### Railway Deployment Verification
```
You: Open https://web-production-74ed0.up.railway.app/health and tell me the git_sha

Claude: [Navigates to URL, reads JSON response]
The current git_sha is 5b9a06aee6eb. This appears to be from the control-plane-v1 branch.
```

### Screenshot Testing
```
You: Navigate to the Railway dashboard, take a screenshot of the deployment logs, and check for errors

Claude: [Opens Railway, navigates to deployments, captures screenshot, analyzes logs]
```

### Form Automation
```
You: Fill in the login form with username@example.com and password Test123, then click submit

Claude: [Locates form fields, enters values, submits]
```

## TORQ Console Use Cases

### 1. Verify Railway Deployments
```bash
claude --chrome
```
Then ask:
- "Open Railway console and check the latest deployment SHA"
- "Verify the branch is set to control-plane-v1-clean"
- "Check if 'Deploy on push' is enabled"
- "Take a screenshot of the deployment status"

### 2. Test Health Endpoints
```
"Open https://web-production-74ed0.up.railway.app/health and verify:
- git_sha is c12b9f86
- supabase_configured is true
- service is torq-console-railway"
```

### 3. Trigger New Deployments
```
"On Railway dashboard, click 'New Deployment', select control-plane-v1-clean branch, and deploy"
```

### 4. Verify Vercel Deployments
```
"Open https://vercel.com/pilotwaffles-projects/torq-console/deployments and check the latest deployment status"
```

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Claude Code    │────────▶│ Chrome Extension │────────▶│   Browser    │
│  (Terminal)     │ Native  │  (Side Panel)    │ Messages │  (Chrome)   │
│                 │ Messaging│                  │         │             │
└─────────────────┘         └──────────────────┘         └─────────────┘
       │                                                        │
       │                                                        │
       ▼                                                        ▼
  Reasoning &                                          Execution &
  Orchestration                                         State Access
```

## Security Considerations

- Claude operates using your authenticated browser sessions
- Be cautious with sensitive operations (deletions, payments)
- Review actions before confirming
- Domain trust scoring helps prevent malicious sites

## Troubleshooting

### Extension Not Connecting
1. Verify Chrome is running
2. Check you're signed in to the extension
3. Try restarting Claude Code with `--chrome` flag

### Actions Not Executing
1. Check browser console for errors
2. Verify page is fully loaded
3. Try more specific selectors (e.g., "Click the button with id 'submit'")

### Nested Session Error
If running Claude within Claude, unset environment variable:
```bash
unset CLAUDECODE
claude --chrome
```

## Advanced: Agentic Automation

For autonomous workflows, combine with TORQ agents:

```python
# Example: Nightly deployment verification agent
task = {
    "type": "chrome_verification",
    "targets": [
        "https://web-production-74ed0.up.railway.app/health",
        "https://vercel.com/pilotwaffles-projects/torq-console/deployments"
    ],
    "verify": {
        "git_sha": "expected_sha",
        "status": "healthy"
    }
}
```

## Resources

- Chrome Extension: https://chromewebstore.google.com/detail/claude-in-chrome
- Claude Code Docs: https://code.claude.com/docs
- Setup Script: `./setup_chrome_integration.sh`
- Railway Verify Script: `./railway_chrome_verify.sh`

---

**Status**: ✅ CLI Ready | ⏳ Extension Pending Install
