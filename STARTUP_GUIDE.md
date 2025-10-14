# TORQ Console Startup Guide

## Issue Fixed: ModuleNotFoundError

**Problem**: `ModuleNotFoundError: __path__ attribute not found on 'torq_console.cli' while trying to find 'torq_console.cli.main'`

**Root Cause**: The command `python -m torq_console.cli.main` was incorrect because `cli` is a **file** (`cli.py`), not a **directory/package**. Python's `-m` flag expects packages (directories with `__init__.py`) when using dotted paths like `package.subpackage.module`.

**Solution**: Use `python -m torq_console.cli` (without `.main`)

---

## Startup Methods

### Method 1: Command Line Interface (CLI) - Interactive Mode
**Recommended for: Terminal-based workflows, scripting, automation**

```bash
cd E:\TORQ-CONSOLE
python -m torq_console.cli -i
```

Or use the provided batch script:
```bash
start_torq_cli.bat
```

**Features**:
- Interactive shell with guided prompts
- Full command palette
- Git integration
- MCP server connections
- Voice commands (optional)

---

### Method 2: Web User Interface (Web UI)
**Recommended for: Visual workflows, browser-based interaction**

```bash
cd E:\TORQ-CONSOLE
python torq_console\ui\main.py
```

Or use the existing batch script:
```bash
start_torq.bat
```

**Features**:
- Web-based interface at http://localhost:8899
- Visual file browser
- Chat interface
- Code editor integration
- Real-time collaboration

---

### Method 3: Direct Python Module Execution
**For advanced users and custom configurations**

```bash
# CLI without interactive mode (shows help)
python -m torq_console.cli --help

# CLI with web interface
python -m torq_console.cli --web

# CLI with specific model
python -m torq_console.cli -m claude-3-5-sonnet-20241022

# CLI with MCP server connection
python -m torq_console.cli --mcp-connect stdio://path/to/server

# Web UI with custom port
python -m torq_console.cli serve --port 8080 --host 0.0.0.0
```

---

## Available Commands

### CLI Commands
```bash
# Configuration
python -m torq_console.cli config-init     # Initialize configuration

# File editing
python -m torq_console.cli edit "Fix bug in auth.py" -f auth.py

# MCP management
python -m torq_console.cli mcp -e stdio://path/to/server

# Visual diffs
python -m torq_console.cli diff --tool delta

# Web server
python -m torq_console.cli serve --port 8899
```

---

## Environment Configuration

### Required Environment Variables (from .env)
```env
# Claude API Configuration
ANTHROPIC_API_KEY=your_key_here

# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_key_here

# Google Search API (optional)
GOOGLE_API_KEY=your_key_here
GOOGLE_SEARCH_ENGINE_ID=your_id_here

# Brave Search API (optional)
BRAVE_API_KEY=your_key_here
```

### GPU Acceleration (Optional)
The startup scripts automatically add CUDA DLLs to PATH for GPU acceleration:
```bash
set PATH=E:\Python\Python311\Lib\site-packages\nvidia\cuda_runtime\bin;...
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: __path__ attribute not found"
**Solution**: Use `python -m torq_console.cli` (NOT `torq_console.cli.main`)

### Issue: "Could not import local torq_prince_flowers.py"
**Status**: Warning only, not critical. This refers to an optional local agent file that doesn't exist at the root level. The agent is available in `torq_console/agents/torq_prince_flowers.py`.

### Issue: Import errors for dependencies
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
# or
pip install click rich anthropic openai asyncio pathlib
```

### Issue: Web UI not accessible
**Solution**: Check firewall settings and verify the port is not in use
```bash
netstat -an | findstr 8899
```

---

## Quick Start Workflow

### 1. First Time Setup
```bash
# Navigate to project directory
cd E:\TORQ-CONSOLE

# Initialize configuration
python -m torq_console.cli config-init

# Verify environment variables
python -c "import os; print('API Key:', os.getenv('ANTHROPIC_API_KEY')[:10] + '...')"
```

### 2. Launch TORQ Console
```bash
# Option A: CLI Interactive Mode
start_torq_cli.bat

# Option B: Web UI
start_torq.bat
```

### 3. Start Working
```bash
# In CLI mode:
# - Type your commands or questions
# - Use /help for command reference
# - Press Ctrl+C to exit

# In Web UI:
# - Open browser to http://localhost:8899
# - Use chat interface for AI assistance
# - Browse and edit files in the UI
```

---

## Performance Notes

- **Startup Time**: ~3-5 seconds (loading models and configuration)
- **GPU Acceleration**: Enabled by default (28 layers)
- **Memory Usage**: ~2-4GB RAM (depending on loaded models)
- **Concurrent Sessions**: Supported for collaborative work

---

## Advanced Configuration

### Custom Model Configuration
Edit `config.json` (created after first run):
```json
{
  "default_model": "claude-3-5-sonnet-20241022",
  "diff_tool": "delta",
  "voice_enabled": false,
  "mcp_endpoints": []
}
```

### MCP Server Integration
```bash
# Connect to MCP server during startup
python -m torq_console.cli --mcp-connect stdio://path/to/server

# Or add to config.json
"mcp_endpoints": ["stdio://path/to/server"]
```

---

## File Structure Reference

```
E:\TORQ-CONSOLE\
├── torq_console\
│   ├── __init__.py              # Package initialization
│   ├── cli.py                   # CLI entry point (HAS main() function)
│   ├── agents\
│   │   └── torq_prince_flowers.py  # Prince Flowers agent
│   ├── core\
│   │   ├── console.py           # Core console logic
│   │   └── config.py            # Configuration management
│   ├── ui\
│   │   ├── main.py              # Web UI entry point
│   │   ├── web.py               # Web server
│   │   └── shell.py             # Interactive shell
│   └── ...
├── start_torq.bat               # Web UI launcher (WORKING)
├── start_torq_cli.bat           # CLI launcher (FIXED)
└── .env                         # Environment variables
```

---

## Success Verification

Run these commands to verify everything works:

```bash
# 1. Check module structure
python -c "import torq_console; print('Version:', torq_console.__version__)"

# 2. Test CLI help
python -m torq_console.cli --help

# 3. Test configuration
python -m torq_console.cli config-init

# 4. Quick test (exits after banner)
python -m torq_console.cli
```

Expected output:
```
[OK] Environment variables loaded from .env
[WARN] Could not import local torq_prince_flowers.py
+-----------------------------------------------------------------------------+
|                                                                             |
|  TORQ CONSOLE                                                               |
|  Enhanced AI pair programmer with MCP + Claude Code integration             |
|  v0.70.0                                                                    |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Version Information
- **TORQ Console Version**: v0.70.0
- **Python Version**: 3.11.9
- **Fixed Issue**: ModuleNotFoundError with cli.main
- **Fix Date**: 2025-10-14

---

*For more information, see CLAUDE.md for feature documentation.*
