# 🚀 TORQ CONSOLE - Complete Setup & Testing Guide

## **Prerequisites**

### 1. Check Your System
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.10+ required
- **Git**: For repository operations
- **Node.js**: For MCP server integration (optional)

### 2. Verify Prerequisites

```bash
# Check Python (Windows)
python --version
# OR
py --version
# OR
python3 --version

# Check Git
git --version

# Check Node.js (optional)
node --version
```

**If Python is missing:**
- Windows: Download from https://python.org or `winget install Python.Python.3.11`
- macOS: `brew install python3`
- Linux: `sudo apt install python3 python3-pip`

## **Step 1: Install TORQ CONSOLE**

### Navigate to TORQ CONSOLE Directory
```bash
cd E:\TORQ-CONSOLE
```

### Install Dependencies
```bash
# Basic installation
pip install -e .

# OR with all optional features
pip install -e ".[voice,visual,dev]"

# OR install individual features
pip install -e ".[voice]"    # Voice commands
pip install -e ".[visual]"   # Enhanced visual tools
pip install -e ".[dev]"      # Development tools
```

### Install External Tools (Optional but Recommended)
```bash
# Install git-delta for enhanced diffs
winget install dandavison.delta
# OR download from: https://github.com/dandavison/delta

# Install bat for syntax highlighting
winget install sharkdp.bat
# OR download from: https://github.com/sharkdp/bat
```

## **Step 2: Basic Configuration**

### Initialize Configuration
```bash
# Windows
python -m torq_console.cli config-init

# OR
py -m torq_console.cli config-init
```

### Check Installation
```bash
# Show help
python -m torq_console.cli --help

# Check version
python -m torq_console.cli --version
```

## **Step 3: Run Tests**

### Basic Integration Test
```bash
# Run integration tests
python test_integration.py

# Expected output: Test results with ✅ or ❌
```

### Run Demo
```bash
# Experience TORQ CONSOLE capabilities
python demo.py

# This will show:
# - Architecture overview
# - Feature demonstrations
# - MCP integration examples
```

## **Step 4: Start TORQ CONSOLE**

### Method 1: Interactive CLI
```bash
# Start interactive shell
python -m torq_console.cli --interactive

# Commands to try:
torq> help
torq> status
torq> diff
torq> edit "add a comment to README.md"
torq> exit
```

### Method 2: Web UI
```bash
# Start web interface
python -m torq_console.cli --web

# Then open: http://localhost:8080
```

### Method 3: Direct Commands
```bash
# Direct file editing
python -m torq_console.cli edit "improve the README file"

# Show repository diff
python -m torq_console.cli diff --tool delta

# Generate project plan
python -m torq_console.cli edit "plan a new feature" --plan
```

## **Step 5: Connect MCP Infrastructure**

### Start Your Existing MCP Servers
```bash
# In separate terminals, start your MCP infrastructure:

# Terminal 1: Start Hybrid MCP Server
E:\start_hybrid_mcp.bat

# Terminal 2: Start Enhanced N8N MCP
cd E:\enhanced-n8n-mcp
npm start

# Terminal 3: Start Claude Memory MCP
cd E:\claude-memory-mcp
python -m memory_mcp
```

### Connect TORQ CONSOLE to MCP Servers
```bash
# Connect to Hybrid MCP Server
python -m torq_console.cli mcp --endpoint http://localhost:3100

# Connect to N8N MCP Server
python -m torq_console.cli mcp --endpoint http://localhost:3101

# Connect to Memory MCP Server
python -m torq_console.cli mcp --endpoint stdio://claude-memory-mcp

# Test MCP connectivity
python -m torq_console.cli --interactive
torq> connect http://localhost:3100
```

## **Step 6: Test Enhanced Features**

### Test Visual Diffs
```bash
# Make a small change to a file first
echo "# TORQ CONSOLE Test" >> test_file.md

# View with different tools
python -m torq_console.cli diff --tool delta
python -m torq_console.cli diff --tool bat
python -m torq_console.cli diff --tool rich
```

### Test AI-Assisted Editing with MCP
```bash
# With MCP context (requires connected servers)
python -m torq_console.cli edit "create a simple Python function" --ideate

# With planning mode
python -m torq_console.cli edit "design a REST API" --plan

# Multiple file editing
python -m torq_console.cli edit "refactor the configuration system" --files config.py,main.py
```

### Test Web UI Features
```bash
# Start web UI
python -m torq_console.cli --web --port 8080

# In browser (http://localhost:8080):
# 1. Browse files in left sidebar
# 2. View syntax-highlighted code
# 3. Generate diffs
# 4. Use AI chat interface
# 5. Connect MCP servers via UI
```

## **Step 7: Integration with Claude Code**

### Use TORQ CONSOLE within Claude Code Sessions
1. **Start TORQ CONSOLE web UI** in background
2. **Use Claude Code** as normal for editing
3. **TORQ CONSOLE enhances** with:
   - Visual diff viewing
   - MCP context gathering
   - Multi-file planning
   - Enhanced syntax highlighting

### Claude Code + TORQ CONSOLE Workflow
```bash
# 1. Start TORQ CONSOLE web UI
python -m torq_console.cli --web &

# 2. Connect MCP servers
python -m torq_console.cli mcp --endpoint http://localhost:3100

# 3. Use Claude Code with enhanced capabilities:
#    - File editing gets MCP context
#    - Diffs are visually enhanced
#    - Planning uses repository analysis
#    - Voice commands available (if configured)
```

## **Step 8: Troubleshooting**

### Common Issues & Solutions

#### Issue: "Module not found"
```bash
# Solution: Reinstall in development mode
pip uninstall torq-console
pip install -e .
```

#### Issue: "MCP connection failed"
```bash
# Solution: Check MCP server status
# 1. Verify server is running
# 2. Check port availability
netstat -an | findstr 3100

# 3. Test direct connection
curl http://localhost:3100
```

#### Issue: "Visual tools not found"
```bash
# Solution: Install external tools
winget install dandavison.delta
winget install sharkdp.bat

# OR use built-in rich renderer
python -m torq_console.cli diff --tool rich
```

#### Issue: "Permission denied"
```bash
# Solution: Run as administrator or fix permissions
# Windows: Run PowerShell as Administrator
# Linux/macOS: Check file permissions
```

### Debug Mode
```bash
# Enable debug logging
export TORQ_DEBUG=true
python -m torq_console.cli --interactive

# Check logs
cat ~/.config/torq-console/logs/torq.log
```

## **Step 9: Advanced Configuration**

### Custom Configuration
```bash
# Edit configuration file
notepad ~/.config/torq-console/config.json

# Key settings:
{
  "ai_models": [
    {
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "api_key": "your-key-here"
    }
  ],
  "mcp_servers": [
    {
      "endpoint": "http://localhost:3100",
      "name": "Hybrid MCP Server"
    }
  ]
}
```

### Voice Commands Setup (Optional)
```bash
# Install voice dependencies
pip install SpeechRecognition pyttsx3 pyaudio

# Enable voice mode
python -m torq_console.cli --voice --interactive
```

## **Step 10: Verification Checklist**

### ✅ Basic Functionality
- [ ] TORQ CONSOLE starts without errors
- [ ] Configuration loads successfully
- [ ] Help commands work
- [ ] Interactive shell responds

### ✅ Core Features
- [ ] File editing with AI assistance
- [ ] Visual diffs display correctly
- [ ] Git operations work
- [ ] Session management functions

### ✅ MCP Integration
- [ ] MCP servers connect successfully
- [ ] Tools are discovered and listed
- [ ] Context gathering works
- [ ] Claude Code bridge functions

### ✅ UI Interfaces
- [ ] Interactive CLI launches
- [ ] Web UI loads at localhost:8080
- [ ] File browser works
- [ ] Real-time updates via WebSocket

### ✅ Advanced Features
- [ ] Multi-file editing
- [ ] Planning mode generates plans
- [ ] Ideation mode gathers context
- [ ] Visual tools (delta/bat) work

## **🎉 Success! You're Ready**

If all steps completed successfully, you now have:

- **TORQ CONSOLE** fully installed and configured
- **Enhanced Claude Code** capabilities with visual diffs and MCP integration
- **Connected MCP infrastructure** for rich AI context
- **Modern web UI** for intuitive interaction
- **Production-ready setup** for AI pair programming

### Next Steps:
1. **Integrate with your daily workflow**
2. **Connect additional MCP servers** as needed
3. **Explore voice commands** and advanced features
4. **Customize configuration** for your preferences
5. **Share feedback** and contribute improvements

---

**Need help?** Check the troubleshooting section or review the logs for detailed error information.