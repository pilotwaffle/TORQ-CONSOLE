# TORQ Console - Multi-Agent System User Guide

**Date:** 2026-03-05
**Status:** ✅ Operational

---

## How Users Access Agents

### Method 1: Frontend Web UI (Primary)

**URL:** https://torq-console.vercel.app

The frontend has a **sidebar** on the left that displays all available agents. Users can:

1. **Click on any agent** in the sidebar to select it
2. **Start chatting** with the selected agent in the chat window
3. **See agent status** (idle, thinking, active, error) as a badge

### Method 2: Direct API Calls

Developers can call agents directly via API:

```bash
# Chat with auto-routing (system selects best agent)
curl -X POST https://web-production-74ed0.up.railway.app/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Your question here", "session_id": "my-session"}'

# Orchestrate multiple agents
curl -X POST https://web-production-74ed0.up.railway.app/api/agent/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"query": "Complex task", "mode": "parallel"}'

# List all agents
curl https://web-production-74ed0.up.railway.app/api/agent/registry
```

---

## Available Agents (Backend)

These agents are registered in Supabase and available for orchestration:

| Agent ID | Name | Type | Capabilities |
|----------|------|------|--------------|
| `conversational_agent` | Conversational Agent | core | Conversation, memory, learning |
| `workflow_agent` | Workflow Agent | core | Code generation, debugging, testing, architecture |
| `research_agent` | Research Agent | core | Research, analysis |
| `orchestration_agent` | Orchestration Agent | core | Orchestration, coordination |
| `torq_prince_flowers` | Prince Flowers | enhanced | AI Search, Web Research, Orchestration, Code |

---

## Frontend Sidebar (Current State)

The frontend (`App.tsx`) currently shows **hardcoded fallback agents**:

```
🌸 Prince Flowers (orchestrator)
💻 Code Generator (code)
🐛 Debug Assistant (debug)
📚 Documentation (docs)
🧪 Test Engineer (test)
🏗️ Architecture (architecture)
```

### How This Works:

1. **On page load**, the frontend tries to load agents from the backend
2. **After 3 seconds**, if backend agents aren't loaded, it merges with fallback agents
3. **Prince Flowers is always first** in the list
4. **Clicking an agent** makes it active and creates/opens a chat session

---

## How Agent Selection Works

### Automatic Routing (Intelligent)

When you send a message through `/api/agent/chat` without specifying an agent:

1. **Task Router analyzes your query** for keywords:
   - `"research"`, `"find"`, `"search"` → Research Agent
   - `"code"`, `"implement"`, `"debug"` → Workflow Agent
   - `"workflow"`, `"automate"` → Orchestration Agent
   - `"hello"`, `"help"`, `"explain"` → Conversational Agent

2. **Best agent is selected** based on:
   - Query intent classification
   - Agent capabilities
   - Agent availability/status

3. **Response includes routing info**:
   ```json
   {
     "response": "Agent's answer...",
     "agent_id": "research_agent",
     "routing": {
       "selected_agent": "research_agent",
       "confidence": 0.85
     }
   }
   ```

### Manual Selection

Users can click any agent in the sidebar to:
1. Make it the active agent
2. Start a dedicated chat session with that agent
3. All messages go to that specific agent

---

## Orchestration Modes

For complex tasks, users can orchestrate multiple agents:

| Mode | Description | Use Case |
|------|-------------|----------|
| `single` | One best agent | Quick questions, simple tasks |
| `sequential` | Agents work in order | Each agent builds on previous output |
| `parallel` | Agents work simultaneously | Get multiple perspectives quickly |
| `hierarchical` | Lead delegates to others | Complex project coordination |
| `consensus` | Agents vote on best answer | Critical decision making |

### Example: Parallel Orchestration

```json
POST /api/agent/orchestrate
{
  "query": "Analyze market trends for EV stocks",
  "mode": "parallel",
  "agents": ["research_agent", "workflow_agent"]
}
```

**Result:** Both agents work simultaneously, responses are synthesized.

---

## Current Gaps & What's Needed

### Gap 1: Frontend Not Loading Backend Agents

**Issue:** The frontend (`App.tsx`) has hardcoded fallback agents instead of loading from Supabase/registry.

**Fix Needed:** Update frontend to call `/api/agent/registry` on load.

**Current Code:**
```tsx
// App.tsx lines 59-96 - Hardcoded fallback agents
const fallbackAgents: Agent[] = [
  { id: 'prince_flowers', name: 'Prince Flowers', ... },
  { id: 'agent_code', name: 'Code Generator', ... },
  // ...
];
```

**Should Be:**
```tsx
// Load from backend API
const response = await fetch('/api/agent/registry');
const backendAgents = await response.json();
setAgents(backendAgents);
```

### Gap 2: No Orchestration UI

**Issue:** Users can't select orchestration modes in the UI.

**Current State:** Orchestration is only available via direct API calls.

**Fix Needed:** Add a mode selector in the chat interface:
- [ ] Single Agent (default)
- [ ] Sequential
- [ ] Parallel
- [ ] Hierarchical

### Gap 3: Agent ID Mismatch

**Issue:** Frontend uses IDs like `agent_code` but backend uses `workflow_agent`.

**Frontend IDs:**
- `prince_flowers`
- `agent_code`
- `agent_debug`
- `agent_docs`
- `agent_test`
- `agent_arch`

**Backend IDs:**
- `torq_prince_flowers`
- `workflow_agent`
- `research_agent`
- `conversational_agent`
- `orchestration_agent`

**Fix Needed:** Align IDs between frontend and backend.

---

## How to Use Agents Right Now

### Via Web UI (https://torq-console.vercel.app)

1. **Open the site**
2. **See the sidebar** with agent cards on the left
3. **Click an agent** (e.g., "Prince Flowers")
4. **Type your message** in the chat input
5. **Press Enter** to send

### Via API

```bash
# Simple chat with routing
curl -X POST https://web-production-74ed0.up.railway.app/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "session_id": "test-session"
  }'

# Specific agent
curl -X POST https://web-production-74ed0.up.railway.app/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me debug this code",
    "session_id": "test-session",
    "agent_id": "workflow_agent"
  }'

# Multi-agent orchestration
curl -X POST https://web-production-74ed0.up.railway.app/api/agent/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Research and summarize AI trends",
    "mode": "sequential"
  }'
```

---

## Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Backend API** | ✅ Complete | 5 agents registered, orchestration working |
| **Frontend UI** | ⚠️ Partial | Sidebar exists, but uses hardcoded agents |
| **Agent Routing** | ✅ Working | Auto-selects best agent based on query |
| **Orchestration** | ✅ API Ready | UI controls not implemented yet |
| **Agent Sync** | ⚠️ Misaligned | Frontend/backend IDs don't match |

**Users CAN:**
- Chat with agents via web UI
- Call agents directly via API
- Orchestrate multi-agent workflows via API

**Users CANNOT YET:**
- Select orchestration mode in UI
- See real-time backend agents in sidebar
- Choose collaboration patterns in UI

---

## Next Steps to Improve UX

1. **Update frontend** to load agents from `/api/agent/registry`
2. **Add orchestration controls** to the chat interface
3. **Align agent IDs** between frontend and backend
4. **Show agent status** in real-time from backend
5. **Add collaboration panel** for multi-agent workflows
