# TORQ Console: Railway vs Local Deployment Analysis

## Problem Summary

**Issue:** Railway deployment shows only a simple HTML dashboard, while local deployment has full TORQ Console functionality including Prince Flowers agent, MCP integration, command palette, and interactive features.

**Root Cause:** Railway is running a standalone FastAPI app (`torq_console/ui/app.py`) instead of the full TORQ Console application (`torq_console/ui/main.py`).

---

## Deployment Comparison

### 🚂 Current Railway Deployment

**Start Command:**
```bash
uvicorn torq_console.ui.app:app --host 0.0.0.0 --port $PORT
```

**What's Running:**
- File: `E:\TORQ-CONSOLE\torq_console\ui\app.py`
- Simple FastAPI application
- HTML dashboard only
- 3 endpoints: `/`, `/api/health`, `/api/console/info`

**What's MISSING:**
- ❌ Prince Flowers agent (`TORQPrinceFlowersInterface`)
- ❌ Full TORQ Console (`TorqConsole` class)
- ❌ Command Palette
- ❌ Interactive Shell
- ❌ MCP Integration
- ❌ Context Manager
- ❌ Chat Manager
- ❌ Inline Editor
- ❌ Real-time collaboration (Socket.IO)
- ❌ Web UI (`WebUI` class)
- ❌ All agentic features

---

### 🖥️ Local Deployment

**Start Command:**
```bash
python torq_console/ui/main.py --host 127.0.0.1 --port 8899
```

**What's Running:**
- File: `E:\TORQ-CONSOLE\torq_console/ui/main.py`
- Full TORQ Console application
- Web UI with Socket.IO
- Complete interactive interface

**What's AVAILABLE:**
- ✅ Prince Flowers agent with agentic RL
- ✅ Full TORQ Console orchestration
- ✅ Command Palette (Ctrl+Shift+P)
- ✅ Interactive Shell
- ✅ MCP Integration (GitHub, Postgres, Jenkins, etc.)
- ✅ Context Manager (@-symbol parsing)
- ✅ Chat Manager (multi-tab conversations)
- ✅ Inline Editor (Ctrl+K)
- ✅ Real-time collaboration
- ✅ WebUI with modern interface
- ✅ All 80+ agentic features from v0.80.0

---

## Key Components Missing from Railway

### 1. **Prince Flowers Agent**

**Local:**
- File: `examples/torq_prince_flowers_demo.py`
- Features: ARTIST-style agentic RL, web search, multi-turn reasoning, self-correction
- Commands: `prince search`, `prince analyze`, `@prince`
- Integration: Full integration with TORQ Console

**Railway:**
- Not available
- No agent functionality
- No AI capabilities

---

### 2. **TORQ Console Core**

**Local:**
```python
# From torq_console/ui/main.py
config = TorqConfig()
console = TorqConsole(config=config)
web_ui = WebUI(console)
await web_ui.start_server(host=args.host, port=args.port)
```

**Railway:**
```python
# From torq_console/ui/app.py
app = FastAPI(title="TORQ CONSOLE Web UI", version="0.80.0")
# Just a simple API, no console instance
```

---

### 3. **Web UI Features**

**Local (`WebUI` class):**
- Socket.IO real-time communication
- Modern React-like interface
- Panels for files, diffs, chat
- Command execution
- Real-time updates
- Multi-tab chat
- File browser
- Git integration

**Railway:**
- Static HTML dashboard
- No interactivity
- No Socket.IO
- No file operations
- No chat interface

---

### 4. **MCP Integration**

**Local:**
- Native bidirectional MCP integration
- Supports: GitHub, Postgres, Jenkins, Browser Automation, etc.
- `--mcp-connect` for endpoint discovery
- Privacy-first: BYO-API key

**Railway:**
- No MCP integration
- No tool connections
- No external service integration

---

### 5. **Spec-Kit Commands**

**Local:** Complete GitHub Spec-Kit workflow
```bash
/torq-spec constitution create
/torq-spec specify create
/torq-spec plan generate
/torq-spec tasks list
/torq-spec implement start
```

**Railway:**
- Not available
- No spec-driven development
- No RL-powered specification analysis

---

## Why This Happened

### Design Decision
During the Railway deployment debugging process (commits 65e9d1f to 7b5a85d), we encountered:
- Dependency issues (missing aiohttp, numpy, scikit-learn)
- Build timeouts (4GB Docker image)
- ASGI application loading errors
- 502 Bad Gateway errors

### Solution Implemented
Created a **standalone FastAPI app** (`torq_console/ui/app.py`) to:
- ✅ Get something deployed quickly
- ✅ Minimize dependencies
- ✅ Reduce build time (<3 minutes)
- ✅ Avoid complex TorqConsole initialization issues

### Unintended Consequence
- Lost **ALL** TORQ Console functionality
- Deployed essentially a "hello world" API instead of the actual application

---

## Architecture Files

### Local TORQ Console Architecture

```
E:\TORQ-CONSOLE\
├── torq_console/
│   ├── core/
│   │   ├── console.py           # TorqConsole main class
│   │   ├── config.py            # TorqConfig
│   │   ├── context_manager.py   # @-symbol parsing
│   │   └── chat_manager.py      # Multi-tab chat
│   ├── ui/
│   │   ├── main.py             # ✅ LOCAL: Full app entry point
│   │   ├── app.py              # 🚂 RAILWAY: Standalone API only
│   │   ├── shell.py            # Interactive shell
│   │   ├── inline_editor.py    # Real-time editing
│   │   └── web.py              # WebUI with Socket.IO (MISSING ON RAILWAY)
│   ├── llm/
│   │   └── providers/          # AI model providers
│   ├── mcp/
│   │   ├── client.py           # MCP client
│   │   └── claude_code_bridge.py
│   ├── swarm/
│   │   ├── orchestrator.py     # Agent orchestration
│   │   └── agents/             # Various specialized agents
│   ├── integrations/
│   │   ├── n8n_workflows.py
│   │   └── huggingface_models.py
│   └── utils/
│       ├── web_tools.py
│       ├── search_tools.py
│       └── advanced_web_search.py
├── examples/
│   └── torq_prince_flowers_demo.py  # Prince Flowers agent (MISSING ON RAILWAY)
└── requirements.txt             # Full dependencies
```

---

## Railway Deployment Files

**Files Being Deployed:**
```
E:\TORQ-CONSOLE\
├── torq_console/
│   └── ui/
│       └── app.py              # ONLY THIS FILE IS RUNNING
├── railway.toml                # Points to app.py
└── requirements.txt            # CPU-only PyTorch (optimized for speed)
```

**What Gets Ignored:**
- All other Python files
- Prince Flowers integration
- MCP servers
- Swarm agents
- Full UI components

---

## Detailed Feature Comparison

| Feature | Local | Railway | Status |
|---------|-------|---------|--------|
| **Basic API** | ✅ | ✅ | Working |
| **HTML Dashboard** | ✅ | ✅ | Working |
| **Prince Flowers Agent** | ✅ | ❌ | **MISSING** |
| **Web UI (Socket.IO)** | ✅ | ❌ | **MISSING** |
| **Command Palette** | ✅ | ❌ | **MISSING** |
| **Interactive Shell** | ✅ | ❌ | **MISSING** |
| **MCP Integration** | ✅ | ❌ | **MISSING** |
| **Context Manager** | ✅ | ❌ | **MISSING** |
| **Chat Manager** | ✅ | ❌ | **MISSING** |
| **Inline Editor** | ✅ | ❌ | **MISSING** |
| **GitHub Spec-Kit** | ✅ | ❌ | **MISSING** |
| **Real-time Collaboration** | ✅ | ❌ | **MISSING** |
| **Multi-tab Chat** | ✅ | ❌ | **MISSING** |
| **File Browser** | ✅ | ❌ | **MISSING** |
| **Git Integration** | ✅ | ❌ | **MISSING** |
| **N8N Workflows** | ✅ | ❌ | **MISSING** |
| **HuggingFace Models** | ✅ | ❌ | **MISSING** |
| **Web Search** | ✅ | ❌ | **MISSING** |
| **Browser Automation** | ✅ | ❌ | **MISSING** |
| **Agentic RL** | ✅ | ❌ | **MISSING** |
| **Tool Integration** | ✅ | ❌ | **MISSING** |

---

## Environment Variables

### Local
```env
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=sk-proj-...
# Plus all MCP server configurations
```

### Railway
```env
OPENAI_API_KEY=sk-proj-...  # ✅ Configured
RAILWAY_ENVIRONMENT=production
RAILWAY_PUBLIC_DOMAIN=web-production-1f870.up.railway.app
```

**Missing:**
- ANTHROPIC_API_KEY (for Prince Flowers)
- MCP server URLs
- Other integration keys

---

## Solution Options

### Option 1: Deploy Full TORQ Console (Recommended)

**Change Railway start command to:**
```bash
python -m torq_console.ui.main --host 0.0.0.0 --port $PORT
```

**Pros:**
- ✅ Full functionality
- ✅ Prince Flowers works
- ✅ All features available
- ✅ True TORQ Console experience

**Cons:**
- ⚠️ Larger dependencies (need to add back to requirements.txt)
- ⚠️ Longer build time (~5-10 minutes)
- ⚠️ Larger Docker image (~2-3GB)
- ⚠️ May need to debug dependency issues again

---

### Option 2: Hybrid Deployment

**Keep current API but add Prince Flowers:**

Modify `torq_console/ui/app.py` to include:
```python
from examples.torq_prince_flowers_demo import TORQPrinceFlowersInterface

prince_agent = TORQPrinceFlowersInterface()

@app.post("/api/prince/query")
async def prince_query(request: dict):
    result = await prince_agent.handle_prince_command(request["query"])
    return {"response": result}
```

**Pros:**
- ✅ Adds Prince Flowers functionality
- ✅ Keeps lightweight deployment
- ✅ Fast builds still work

**Cons:**
- ⚠️ Still missing most TORQ Console features
- ⚠️ No interactive UI
- ⚠️ API-only access

---

### Option 3: Keep Current (Not Recommended)

**Keep the standalone API as-is:**

**Pros:**
- ✅ Fast builds (<3 min)
- ✅ Small image (~1GB)
- ✅ Simple deployment

**Cons:**
- ❌ Not actually TORQ Console
- ❌ No Prince Flowers
- ❌ No useful functionality
- ❌ Just a static dashboard

---

## Recommendations

### Immediate Action (Recommended)

**Deploy Full TORQ Console:**

1. **Update `requirements.txt`** to include all dependencies:
   ```txt
   # Add back full dependencies
   aiohttp>=3.9.0
   numpy>=1.26.0
   scikit-learn>=1.5.0
   sentence-transformers>=3.0.0
   # ... (see full list in README.md)
   ```

2. **Update `railway.toml`**:
   ```toml
   [deploy]
   startCommand = "python -m torq_console.ui.main --host 0.0.0.0 --port $PORT"
   ```

3. **Add all necessary environment variables**:
   ```bash
   railway variables --set ANTHROPIC_API_KEY="your-key"
   ```

4. **Accept longer build time** (5-10 min) for full functionality

5. **Commit and push** - Railway will auto-deploy

---

### Quick Win (Alternative)

**Add Prince Flowers to existing deployment:**

1. Create new file `E:\TORQ-CONSOLE\torq_console\ui\app_with_prince.py`
2. Copy current `app.py` and add Prince Flowers integration
3. Update Railway to use new file
4. Keep fast builds, add core AI functionality

---

## Testing Checklist

Once full deployment is working, verify:

- [ ] Prince Flowers responds: `POST /api/prince/query {"query": "prince help"}`
- [ ] Web UI loads: `GET /` shows interactive interface (not just HTML dashboard)
- [ ] Socket.IO connects: Real-time updates work
- [ ] Command palette: Can access via UI
- [ ] Chat interface: Can send messages
- [ ] File browser: Can navigate files
- [ ] MCP integration: Tools are available
- [ ] Context manager: @-symbol parsing works
- [ ] Spec-Kit: `/torq-spec` commands work
- [ ] Health check: `GET /api/health` passes
- [ ] Logs: No dependency errors

---

## Conclusion

**Current State:**
- Railway deployment is a **minimal API** with no real TORQ Console functionality
- Essentially deployed a "hello world" instead of the actual application

**Reason:**
- Chose fast, simple deployment to fix 502 errors
- Sacrificed all features for quick wins

**Path Forward:**
1. **Best:** Deploy full TORQ Console (accept longer builds)
2. **Good:** Add Prince Flowers to existing deployment (hybrid approach)
3. **Not Recommended:** Keep current minimal deployment

**Decision Point:**
Do you want:
- 🚀 **Full TORQ Console** (longer builds, all features)
- ⚡ **Fast builds** (keep current, limited functionality)
- 🎯 **Hybrid** (add Prince Flowers only, medium builds)

---

**Created:** 2025-10-29
**Status:** Analysis Complete
**Next Steps:** Choose deployment strategy and implement
