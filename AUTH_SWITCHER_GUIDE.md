# Claude Code Authentication Switcher

Easily toggle between **API Key** and **Claude Pro Subscription** authentication.

## Quick Start

### Windows (PowerShell)

```powershell
# Switch to Claude Pro Subscription
python E:\TORQ-CONSOLE\torq_console\mcp\auth_switcher.py sub

# Switch to API Key
python E:\TORQ-CONSOLE\torq_console\mcp\auth_switcher.py api

# Check current mode
python E:\TORQ-CONSOLE\torq_console\mcp\auth_switcher.py status
```

### Linux/Mac

```bash
# Switch to Claude Pro Subscription
bash /e/TORQ-CONSOLE/claude-auth.sh sub

# Switch to API Key
bash /e/TORQ-CONSOLE/claude-auth.sh api

# Check current mode
bash /e/TORQ-CONSOLE/claude-auth.sh status
```

## Setup (One-Time)

### 1. Save Your API Configuration

Currently using api.z.ai? Save those credentials first:

```powershell
# Edit your settings.json and add these values for API mode:
# - ANTHROPIC_AUTH_TOKEN: your-api-key
# - ANTHROPIC_BASE_URL: https://api.z.ai/api/anthropic
```

Then create the backup:

```python
import json
from pathlib import Path

# Save current settings as API backup
settings_file = Path.home() / '.claude' / 'settings.json'
api_backup = Path.home() / '.claude' / 'settings.json.api_backup'

with open(settings_file, 'r') as f:
    settings = json.load(f)

# ADD YOUR API CONFIG HERE
settings.setdefault('env', {})['ANTHROPIC_AUTH_TOKEN'] = 'your-api-key-here'
settings.setdefault('env', {})['ANTHROPIC_BASE_URL'] = 'https://api.z.ai/api/anthropic'

with open(api_backup, 'w') as f:
    json.dump(settings, f, indent=2)

print("API configuration saved")
```

### 2. Create Aliases

Add to your PowerShell profile (`$PROFILE`):

```powershell
# Auth switcher aliases
function claude-sub { python E:\TORQ-CONSOLE\torq_console\mcp\auth_switcher.py sub }
function claude-api { python E:\TORQ-CONSOLE\torq_console\mcp\auth_switcher.py api }
function claude-auth { python E:\TORQ-CONSOLE\torq_console\mcp\auth_switcher.py status }
```

## Modes

| Mode | Use Case | Features |
|------|----------|----------|
| **Subscription** | Latest models, Remote Control | Opus 4.6, Sonnet 4.5, Haiku 4.5, Mobile control |
| **API Key** | Custom endpoints, Cost control | api.z.ai, Other providers, Spend limits |

## What Gets Saved

When switching, the following is preserved:

- **API backup**: `~/.claude/settings.json.api_backup`
- **Credentials backup**: `~/.claude/.credentials.json.api_backup`
- **Permissions**: Always preserved
- **Hooks**: Always preserved

## Troubleshooting

### "No saved API configuration found"

Means you haven't saved your API config yet. See Setup step 1 above.

### "Still using old mode after switch"

Restart Claude Code completely (close all windows).

### "Can't login after switching to subscription"

1. Clear credentials: `rm ~/.claude/.credentials.json`
2. Restart Claude Code
3. Login when prompted

## Files

| File | Purpose |
|------|---------|
| `torq_console/mcp/auth_switcher.py` | Python module (cross-platform) |
| `claude-auth.sh` | Bash script (Linux/Mac) |
| `claude-auth.bat` | Batch script (Windows) |
| `~/.claude/settings.json.api_backup` | API mode configuration |
| `~/.claude/.credentials.json.api_backup` | API credentials backup |

## API Reference

```python
from torq_console.mcp.auth_switcher import switch_auth, AuthMode, get_status

# Switch modes
switch_auth(AuthMode.SUBSCRIPTION)
switch_auth(AuthMode.API_KEY)

# Get current status
status = get_status()
print(f"Current mode: {status['mode']}")
```
