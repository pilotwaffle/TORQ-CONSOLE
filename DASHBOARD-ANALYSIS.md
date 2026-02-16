# TORQ Console Dashboard Analysis: Which UI Is Best for End Users?

**Date:** 2026-02-16
**Scope:** Comparative analysis of two dashboard approaches for TORQ Console
**Verdict:** Neither dashboard alone is sufficient. A hybrid approach is recommended.

---

## Executive Summary

Two dashboard UIs were evaluated against TORQ Console's actual backend capabilities (6 agents, 5 LLM providers, 20+ API endpoints, real-time WebSocket, semantic search, Spec-Kit, multi-mode orchestration, persistent memory, and web search integrations).

| Criterion | Dashboard 1 (Existing Frontend) | Dashboard 2 (TorqDashboardUI) |
|---|---|---|
| **Backend Integration** | Partially wired (API + WebSocket scaffolded) | Not wired at all (100% static/hardcoded) |
| **Code Experience** | Excellent (Monaco Editor, diff viewer) | None |
| **Analytics / Metrics** | None | Strong shell (recharts, 4 metric cards) |
| **Navigation / Information Architecture** | Single-view (chat + sidebar) | Multi-page (5 views with sidebar nav) |
| **Model/Provider Switching** | Not exposed | UI exists but wrong providers |
| **Agent Orchestration Visibility** | Real-time workflow graph + list view | None |
| **Visual Polish** | Good (Cursor 2.0 style) | Better (modern SaaS dashboard) |
| **Production Readiness** | ~60% (mocked WebSocket, TODO items) | ~10% (nothing functional) |

**Recommendation:** Build the **hybrid dashboard** — use Dashboard 2's navigation shell, multi-page layout, and analytics framework, combined with Dashboard 1's chat engine, Monaco editor, coordination panel, and backend integrations.

---

## Part 1: Dashboard 1 — Existing Frontend

### Architecture
- **Stack:** React 18 + TypeScript + Vite + Tailwind CSS + Zustand
- **Layout:** TopNav + AgentSidebar (380px) + ChatWindow (flex) + CoordinationPanel (bottom)
- **Color System:** TORQ Blue (#0078d4) / Green (#10b981), dark theme (#1e1e1e)
- **State:** Two Zustand stores — `agentStore` (agents, sessions, messages) and `coordinationStore` (workflows, view modes)

### Strengths

1. **Real Backend Integration**
   - Axios HTTP client pointed at `localhost:8899/api` with full CRUD for agents, sessions, messages
   - Socket.IO WebSocket manager with reconnection, typing indicators, workflow events
   - `agentService.ts` with typed methods for all 8 agent types (prince_flowers, orchestration, meta, code, debug, docs, test, architecture)

2. **Code-First Experience**
   - Monaco Editor with custom TORQ dark theme, language detection, minimap
   - CodeViewer for read-only display with copy/download
   - DiffViewer with colored addition/removal/modification highlighting
   - DiffStats for change summaries
   - CodeBlock with collapse/expand for long outputs

3. **Multi-Agent Coordination Panel**
   - WorkflowGraph: SVG-based visualization of pipeline/parallel/multi/single execution modes
   - AgentCard: Individual agent progress with status indicators and expandable output
   - Live progress bars, animated edges for active workflows
   - List vs Graph view toggle
   - Cancel workflow capability via WebSocket

4. **Command Palette (Cmd+K)**
   - Full-screen fuzzy search across agents, sessions, and commands
   - Recent command history (localStorage)
   - Keyboard navigation (arrows + Enter + Esc)
   - Categorized results with weighted scoring

5. **Component Library**
   - Button (4 variants, 4 sizes via CVA), Card (6 subcomponents), Badge (6 variants)
   - TorqLogo SVG with size props
   - Consistent design tokens in Tailwind config

### Weaknesses

1. **No Analytics / Metrics Visualization**
   The backend tracks agent metrics, orchestrator metrics, query router metrics, memory metrics, and semantic search performance — none of this is surfaced to the user.

2. **No Model/Provider Switching**
   The backend supports 5 LLM providers (Claude, DeepSeek, Ollama, GLM, llama.cpp) with configurable model selection. Users cannot switch providers or models from the UI.

3. **No Settings Page**
   Logged but not implemented. Users cannot configure API keys, default models, preferences, or workspace settings.

4. **Single-View Architecture**
   Everything lives in one view (sidebar + chat + bottom panel). There's no dedicated page for analytics, team management, specification workflow, or system configuration.

5. **Partially Mocked**
   WebSocket connection is scaffolded but App.tsx uses mock agents with simulated 1-second delays. Real backend calls are TODO.

6. **No Web Search UI**
   Perplexity, Brave, Google Custom Search, and DuckDuckGo are all available in the backend but invisible to users.

7. **No Spec-Kit UI**
   The entire constitution/specification/plan/task workflow has no frontend representation.

8. **No Agent Memory Visibility**
   The backend has persistent interaction history, user preferences, pattern learning, and feedback scoring — none of this is visible.

---

## Part 2: Dashboard 2 — TorqDashboardUI

### Architecture
- **Stack:** Single React component (~500 lines), recharts, inline styles + Tailwind
- **Layout:** Collapsible Sidebar (5 nav items) + TopBar (Ctrl+K search) + Content Area
- **Color System:** Space Cadet (#2b2d42) / Red Pantone (#ef233c)
- **State:** Local React state only (useState hooks)

### Strengths

1. **Multi-Page Navigation**
   Five distinct views — Overview, Agents, Analytics, Team, Settings — with sidebar icons and labels. This is the information architecture TORQ Console needs.

2. **Analytics Framework**
   - 4 metric cards with trend indicators (Active Agents, Tasks Completed, Success Rate, Avg Response)
   - Area chart for "Agent Performance" over time
   - Bar chart for "Tasks by Agent"
   - Both use recharts with responsive containers

3. **Model Routing Panel**
   Provider dropdown + Model dropdown on the Agents page. This exposes a critical backend capability (multi-LLM support) that Dashboard 1 completely ignores.

4. **Visual Design Quality**
   - Radial gradient background gives depth
   - Consistent card styling with backdrop blur
   - Collapsible sidebar with smooth transitions
   - Clean TopBar with user avatar and search

5. **Workspace Tabs**
   Overview page has Workspace / Clients / Automation tabs, suggesting multi-project management capability.

### Weaknesses

1. **Zero Backend Integration**
   No API calls, no WebSocket, no state management library. Everything is hardcoded arrays and objects.

2. **Wrong Data Model**
   - `MODEL_REGISTRY` lists `gpt-4-turbo`, `gpt-3.5-turbo`, `claude-3-opus`, `claude-3-sonnet` — none match TORQ's actual models (`claude-sonnet-4-20250514`, `deepseek-chat`, `glm-4.6`, `deepseek-r1:7b`)
   - `AGENTS` are generic (`Data Analyzer`, `Code Assistant`, `Research Bot`, `Task Manager`) — not TORQ's real agents (Prince Flowers, Query Router, Orchestrator, Code Gen, Debug, Docs, Testing, Architecture)
   - Provider list shows only `openai` and `anthropic` — missing DeepSeek, GLM, Ollama, llama.cpp

3. **No Code Rendering**
   No Monaco Editor, no CodeBlock, no DiffViewer. For a development-focused AI platform, this is a critical gap.

4. **No Orchestration Visibility**
   No workflow graph, no coordination panel, no execution mode selector. The backend's 4 orchestration modes (single/multi/pipeline/parallel) are invisible.

5. **No Real Chat Engine**
   The agent console is a simple input/response box. No message history, no streaming, no typing indicators, no session management.

6. **No Web Search**
   Despite TORQ having Perplexity, Brave, Google CSE, and DuckDuckGo integrations, there's no search interface.

7. **No Spec-Kit Integration**
   No specification workflow UI.

8. **Color System Mismatch**
   Space Cadet / Red Pantone doesn't match TORQ's established brand (Blue / Green). Introducing a second color system creates brand inconsistency.

9. **Placeholder Pages**
   Analytics, Team, and Settings pages show "Coming Soon" messages only.

---

## Part 3: Verdict — Which Is Best for End Users?

### For a Developer User (primary persona)

**Dashboard 1 wins** because:
- Monaco Editor and diff viewing are essential for code-focused AI workflows
- Multi-agent coordination panel shows real-time workflow execution
- WebSocket integration enables streaming responses and live agent status
- Command palette provides fast navigation

### For a Business/Manager User (secondary persona)

**Dashboard 2 wins** because:
- Multi-page navigation organizes information into digestible views
- Analytics charts show team/agent performance at a glance
- Model routing panel gives visibility into LLM provider selection
- Settings page (even if placeholder) signals enterprise readiness

### For the End User (both personas)

**Neither dashboard alone is sufficient.** Here's why:

| Feature Needed | Dashboard 1 | Dashboard 2 | Backend Has It? |
|---|---|---|---|
| Chat with agents | Yes | Partial | Yes |
| Code rendering | Yes (Monaco) | No | Yes |
| Diff viewing | Yes | No | Yes |
| Analytics/metrics | No | Yes (static) | Yes |
| Model switching | No | Yes (wrong data) | Yes |
| Multi-page nav | No | Yes | N/A |
| Orchestration modes | Yes (graph) | No | Yes |
| Web search | No | No | Yes |
| Spec-Kit | No | No | Yes |
| Agent memory | No | No | Yes |
| Settings/config | No | Placeholder | Yes |
| Team features | No | Placeholder | Partial |

---

## Part 4: Recommended Hybrid Dashboard

### Design Principles
1. **Use Dashboard 2's shell** — sidebar navigation, multi-page layout, TopBar
2. **Port Dashboard 1's engines** — chat, Monaco, diff, coordination panel, WebSocket
3. **Wire everything to real APIs** — no hardcoded data
4. **Match TORQ brand** — Blue (#0078d4) / Green (#10b981) color system
5. **Expose hidden capabilities** — search, memory, Spec-Kit, provider switching

### Proposed Page Structure

```
Sidebar Navigation:
├── Overview          → System health, key metrics, recent activity
├── Agents            → Agent chat + model routing + orchestration
├── Specifications    → Spec-Kit workflow (constitution → plan → tasks)
├── Analytics         → Agent metrics, search performance, memory stats
├── Search            → Web search (Perplexity, Brave, Google, DDG)
└── Settings          → API keys, model defaults, preferences, memory
```

### Page Specifications

#### 1. Overview Page
**Source:** Dashboard 2 layout with real data from backend
- **Metric Cards:** Active agents (GET /agents), sessions (GET /sessions), system uptime (GET /status), memory interactions (agent memory API)
- **Performance Chart:** recharts area chart fed by orchestrator metrics (requests by mode, success rate over time)
- **Activity Feed:** Recent agent interactions from memory system
- **Quick Actions:** New chat, run workflow, create specification

#### 2. Agents Page (Primary View)
**Source:** Dashboard 1 chat engine + Dashboard 2 model routing
- **Left Panel:** Agent list from GET /agents (real agents: Prince Flowers, Code Gen, Debug, Docs, Testing, Architecture)
- **Center Panel:** ChatWindow with Monaco CodeBlock rendering, DiffViewer, streaming responses
- **Right Panel (collapsible):**
  - Model Routing: Provider selector (Claude, DeepSeek, Ollama, GLM, llama.cpp) + model dropdown with actual models
  - Orchestration Mode: Single / Multi / Pipeline / Parallel selector
  - Agent Capabilities: List of capabilities for selected agent
- **Bottom Panel:** CoordinationPanel with WorkflowGraph (from Dashboard 1)

#### 3. Specifications Page (New)
**Source:** New page exposing Spec-Kit backend
- **Constitution Panel:** Create/view project constitutions
- **Specification List:** All specs with quality scores, status badges
- **Spec Editor:** Create/edit specifications with real-time Marvin analysis
- **Plan Viewer:** Generated implementation plans with task breakdowns
- **Task Board:** Kanban-style task tracking

#### 4. Analytics Page
**Source:** Dashboard 2 chart framework with real metrics
- **Agent Performance:** Response times, success rates, interaction counts from agent metrics
- **Orchestration Stats:** Requests by mode, pipeline execution times
- **Search Analytics:** Query patterns, citation counts, provider usage
- **Memory Insights:** Learning patterns, preference evolution, feedback scores
- **Semantic Search:** Indexing stats, search latency percentiles (P50/P95/P99)

#### 5. Search Page (New)
**Source:** New page exposing web search integrations
- **Search Bar:** Universal search across Perplexity, Brave, Google CSE, DuckDuckGo
- **Provider Selector:** Choose search backend
- **Results Panel:** Search results with citations, summaries
- **Code Search:** Semantic codebase search with relevance scores
- **History:** Recent searches with re-run capability

#### 6. Settings Page
**Source:** Dashboard 2 placeholder made real
- **API Keys:** Manage Anthropic, DeepSeek, Perplexity, GLM keys (masked display)
- **Default Model:** Set preferred LLM provider and model
- **Agent Preferences:** Default orchestration mode, response style
- **Memory Management:** View/clear interaction history, export patterns
- **Workspace:** Configure codebase path, indexing settings

### Component Reuse Matrix

| Component | From | Modifications Needed |
|---|---|---|
| Sidebar + TopBar | Dashboard 2 | Rebrand to TORQ colors, add real nav items |
| ChatWindow + ChatInput | Dashboard 1 | Already wired, needs session persistence |
| ChatMessage + CodeBlock | Dashboard 1 | Already handles code/diff/error/system types |
| MonacoEditor + CodeViewer | Dashboard 1 | No changes needed |
| DiffViewer + DiffStats | Dashboard 1 | No changes needed |
| CoordinationPanel + WorkflowGraph | Dashboard 1 | Already wired to WebSocket |
| CommandPalette | Dashboard 1 | Extend with spec/search commands |
| Metric Cards | Dashboard 2 | Wire to GET /status and agent metrics |
| Area/Bar Charts | Dashboard 2 | Wire to orchestrator/memory metrics |
| Model Routing Panel | Dashboard 2 | Fix MODEL_REGISTRY to match real providers |
| Button/Card/Badge | Dashboard 1 | Already has CVA variants |
| Agent List | Dashboard 2 sidebar style | Use real agent data from GET /agents |

### Color System (Unified)

```
Primary:     #0078d4 (TORQ Blue)     — CTAs, active states, links
Success:     #10b981 (TORQ Green)    — Success, online, complete
Error:       #ef4444 (TORQ Red)      — Errors, danger, offline
Warning:     #f59e0b (TORQ Orange)   — Warnings, thinking, processing
Background:  #1e1e1e → #252526 → #2d2d30 (3-tier dark)
Text:        #ffffff → #cccccc → #808080 (3-tier text)
Border:      #3e3e42 (default), #0078d4 (focus)
```

**Why not Space Cadet / Red Pantone?**
- Space Cadet (#2b2d42) is close enough to #1e1e1e that switching adds no value
- Red Pantone (#ef233c) as a primary accent is aggressive for a dev tool; blue conveys trust and professionalism
- The existing TORQ brand is already established in the codebase, README, and logo

---

## Part 5: Implementation Priority

### Phase 1 — Foundation (Week 1-2)
1. Replace single-view App.tsx with sidebar + multi-page layout from Dashboard 2
2. Install react-router-dom (already a dependency) and set up 6 routes
3. Move ChatWindow + CodeBlock + CoordinationPanel into Agents page
4. Wire Overview page metric cards to GET /status and GET /agents
5. Fix Dashboard 2's MODEL_REGISTRY to use real TORQ providers/models

### Phase 2 — Analytics & Settings (Week 3)
6. Wire recharts to real agent metrics and orchestrator stats
7. Build Settings page with API key management and model defaults
8. Add orchestration mode selector to Agents page
9. Connect agent memory API for interaction history display

### Phase 3 — New Capabilities (Week 4)
10. Build Specifications page with Spec-Kit API integration
11. Build Search page with Perplexity/Brave/Google/DDG backends
12. Add semantic code search to Search page
13. Surface agent memory insights in Analytics

### Phase 4 — Polish (Week 5)
14. Command palette extensions for new pages
15. Keyboard shortcuts for page navigation
16. Responsive design for tablet/mobile
17. Loading states, error boundaries, empty states for all pages
18. End-to-end testing with real backend

---

## Appendix A: Backend Capabilities Not Exposed by Either Dashboard

These backend features exist and are fully functional but have **zero frontend representation** in either dashboard:

1. **Semantic Codebase Search** — Natural language search over indexed code with relevance scores
2. **Agent Memory System** — Persistent interaction history, user preferences, pattern learning
3. **Perplexity Web Search** — Full web search with citations and domain filtering
4. **Spec-Kit Workflow** — Constitution → Specification → Plan → Tasks → Implementation
5. **Marvin Quality Engine** — 5-dimensional specification quality scoring
6. **Request Cancellation** — Cancel long-running agent requests via WebSocket
7. **Agent Typing Indicators** — Real-time typing status via WebSocket events
8. **LLM Provider Fallback** — Automatic provider switching when primary fails
9. **Interaction Feedback** — Score agent responses (0.0-1.0) for learning
10. **Codebase Indexing Controls** — Start/stop/status of semantic indexing
11. **Orchestration Mode Selection** — User-driven choice of single/multi/pipeline/parallel

## Appendix B: File References

| File | Purpose |
|---|---|
| `frontend/src/App.tsx` | Main app entry, currently single-view |
| `frontend/src/stores/agentStore.ts` | Agent/session Zustand store |
| `frontend/src/stores/coordinationStore.ts` | Workflow Zustand store |
| `frontend/src/services/api.ts` | REST API client (localhost:8899) |
| `frontend/src/services/websocket.ts` | Socket.IO WebSocket manager |
| `frontend/src/services/agentService.ts` | High-level agent orchestration service |
| `frontend/src/components/chat/ChatWindow.tsx` | Main chat interface |
| `frontend/src/components/coordination/WorkflowGraph.tsx` | SVG workflow visualization |
| `frontend/src/components/editor/MonacoEditor.tsx` | Monaco editor wrapper |
| `frontend/src/components/command/CommandPalette.tsx` | Cmd+K command palette |
| `torq_console/console.py` | Main backend console class |
| `torq_console/llm/manager.py` | LLM provider management |
| `torq_console/agents/` | All agent implementations |
| `torq_console/spec_kit/` | Spec-Kit + Marvin integration |
| `api/index.py` | Vercel-compatible API entry point |

---

*This analysis was generated by comparing both dashboard implementations against TORQ Console's full backend capabilities across 6 agents, 5 LLM providers, 20+ API endpoints, and 11 unexposed features.*
