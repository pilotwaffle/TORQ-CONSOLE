# PRD: TORQ Console Dashboard — Unified Agent Interface

**Version:** 1.0.0
**Date:** 2026-02-16
**Status:** Draft
**Author:** Claude Code Analysis
**Stakeholder:** pilotwaffle

---

## 1. Executive Summary

TORQ Console has a powerful Python backend (107K+ lines) with multi-LLM orchestration, 8 specialized AI agents, web search synthesis, spec-driven development, semantic code search, and agent memory — but the frontend exposes less than 30% of these capabilities. The existing UI is split across three incomplete dashboard prototypes with no single version ready for end users.

This PRD defines a unified dashboard that combines the best elements of all three prototypes, informed by patterns from Cursor, Bolt.new, and Antigravity, to create a production-ready frontend for TORQ Console and the Prince Flowers agent system.

### Goal

Ship a single React dashboard that:

1. Exposes all TORQ Console backend capabilities through a coherent UI
2. Deploys on Vercel as a serverless frontend (API via `/api/*`)
3. Provides a chat-first experience with multi-agent orchestration visibility
4. Supports model switching across all 6 LLM providers
5. Integrates web search, code rendering, spec-kit, and agent memory

### Non-Goals

- Native mobile app
- Self-hosted LLM training UI
- Real-time collaborative editing (Phase 2 consideration)
- Admin/billing dashboard

---

## 2. Problem Statement

### Current State

| Dimension | Dashboard 1 (Existing) | Dashboard 2 | Dashboard 3 |
|---|---|---|---|
| Backend integration | Partial (~60%) | None (0%) | None (0%) |
| Code rendering | Monaco + diff viewer | None | None |
| Analytics | None | Static fake charts | Static fake charts |
| Navigation | Single-view | 5-page sidebar | 5-page sidebar + 3 tabs |
| Model routing | None | Wrong providers (2) | Better providers (4) |
| Agent model | 8 real agents | 4 generic names | 4 role-based names |
| Web search | None | None | None |
| Spec-Kit | None | None | None |
| Agent memory | None | None | None |
| Orchestration modes | None | None | None |
| Semantic code search | None | None | None |
| Export | TODO stub | None | None |

### Backend Capabilities Not Exposed in Any Dashboard

1. **Multi-LLM routing** — 6 providers (Anthropic, OpenAI, DeepSeek, GLM/Z.AI, Ollama, llama.cpp)
2. **Web search synthesis** — Perplexity, Brave, Google, DuckDuckGo with content synthesis pipeline
3. **Agent orchestration** — 4 modes (Single, Multi, Pipeline, Parallel)
4. **Spec-Kit workflow** — Constitution → Specification → Plan → Tasks → Implement
5. **Semantic code search** — Vector embeddings, function/class-level, <500ms
6. **Agent memory** — Interaction history, user preferences, feedback-driven learning
7. **Query routing** — Intent classification with confidence scoring
8. **Benchmarking** — TTFUO, token usage, cost estimation, SLO tracking
9. **Export** — CSV, JSON, Markdown, PDF
10. **Content synthesis** — Multi-source aggregation with source attribution
11. **Swarm system** — Multi-agent coordination with feedback loops

---

## 3. Design Principles (Informed by Research)

### From Cursor 2.0

- **Chat as primary interface** — the main interaction point is a chat panel, not a traditional form-based UI
- **Inline context** — show code blocks, diffs, and file references directly in the conversation stream
- **Agent mode visibility** — when an agent takes action, show what it's doing (searching, generating, reviewing) with live progress indicators
- **Cmd+K command palette** — fast fuzzy search across all features, commands, files, and agents
- **Tab-based sessions** — multiple concurrent conversations/tasks in tabs

### From Bolt.new

- **Artifact panel** — when the agent produces code, show it in a split panel with live preview capability
- **One-click deploy** — surface deployment status and quick actions prominently
- **Streaming first** — every AI response streams token-by-token; never show a loading spinner for the full response
- **Minimal chrome** — maximize the content area; controls appear contextually, not permanently

### From Antigravity

- **Multi-model switching** — model selector is always visible and switching is instant (no page reload)
- **Artifact system** — generated code/documents persist as referenceable artifacts in the sidebar
- **Provider status** — show which providers are connected/available with live health indicators
- **Context window visibility** — show token usage and remaining context budget

### Synthesis: TORQ Console Design Rules

1. **Chat-first, dashboard-second** — the default view is the chat with Prince Flowers; analytics/settings are secondary pages
2. **Show the routing** — every response shows which agent handled it, which model was used, and confidence scores
3. **Search is visible** — web search has an explicit toggle with provider selection and source attribution
4. **Code is native** — Monaco editor, syntax highlighting, diff viewer, copy/download are standard
5. **Orchestration is transparent** — when multi-agent pipelines run, users see the workflow graph
6. **Memory is accessible** — users can see what the agent has learned and correct it
7. **Spec-Kit is integrated** — the specification workflow is a first-class page, not hidden behind CLI

---

## 4. Information Architecture

```
TORQ Console Dashboard
│
├── [Chat] (default view, always accessible)
│   ├── Chat Input
│   │   ├── Message textarea
│   │   ├── Model selector (provider + model dropdowns)
│   │   ├── Search toggle (ON/OFF + provider picker)
│   │   ├── Mode selector (Single / Multi / Pipeline / Parallel)
│   │   └── Send button
│   ├── Conversation Stream
│   │   ├── User messages
│   │   ├── Agent responses (with routing badge, model badge)
│   │   ├── Code blocks (Monaco, copy, download)
│   │   ├── Diff blocks (side-by-side)
│   │   ├── Search results (collapsible sources)
│   │   ├── Error messages (styled)
│   │   └── System messages (agent transitions, pipeline progress)
│   ├── Artifact Panel (split-right, shows generated code/docs)
│   └── Orchestration Progress (bottom bar when pipeline/multi runs)
│
├── [Agents] (sidebar page)
│   ├── Agent List (real agents from backend)
│   │   ├── Prince Flowers (primary)
│   │   ├── Code Generator
│   │   ├── Debug Assistant
│   │   ├── Documentation
│   │   ├── Test Engineer
│   │   └── Architect
│   ├── Agent Details (capabilities, status, model assignment)
│   ├── Provider Status (connected/disconnected per provider)
│   └── Query Router Decisions (recent routing log)
│
├── [Specifications] (sidebar page)
│   ├── Constitutions List
│   ├── Specifications List (with quality scores)
│   ├── Specification Detail
│   │   ├── Quality bars (clarity, completeness, feasibility, testability, maintainability)
│   │   ├── Risk assessment badges
│   │   ├── Recommendations
│   │   └── Actions (Generate Plan, Start Implementation)
│   ├── Plans List
│   └── Task Tracking
│
├── [Search] (sidebar page)
│   ├── Web Search (multi-provider)
│   │   ├── Provider picker (Perplexity, Brave, Google, DDG)
│   │   ├── Results with source cards
│   │   └── AI synthesis summary
│   └── Code Search (semantic)
│       ├── Natural language query input
│       ├── Results ranked by relevance
│       └── Function/class previews
│
├── [Analytics] (sidebar page)
│   ├── Metrics cards (active agents, interactions, response time, cost)
│   ├── Execution velocity chart (interactions over time)
│   ├── Agent distribution chart (routing decisions by agent)
│   ├── Model usage breakdown
│   ├── Search provider usage
│   └── Token/cost tracking
│
├── [Memory] (sidebar page)
│   ├── Interaction History (searchable, filterable)
│   ├── Learned Preferences (editable)
│   ├── Feedback Scores (average, trend)
│   └── Actions (export, clear, correct)
│
└── [Settings] (sidebar page)
    ├── API Keys (Anthropic, OpenAI, DeepSeek, GLM, Brave, Google — status indicators)
    ├── Default Model Selection
    ├── Search Provider Preference
    ├── Agent Memory Controls
    ├── Connection Status (Ollama, WebSocket, MCP)
    └── Theme (dark/light — dark default)
```

---

## 5. Technical Architecture

### Stack

| Layer | Technology | Rationale |
|---|---|---|
| Framework | React 18 + TypeScript | Already in codebase, widely supported |
| Build | Vite | Already configured, fast HMR |
| Styling | Tailwind CSS + CVA | Already in codebase (tailwind.config.ts exists) |
| Components | Radix UI primitives + custom wrappers | Already installed (@radix-ui/*) |
| State | Zustand | Already in codebase (2 stores exist) |
| Charts | Recharts | Dashboard 3 pattern, lightweight |
| Code Editor | Monaco Editor (@monaco-editor/react) | Already installed |
| Real-time | Socket.IO client | Already installed (socket.io-client) |
| Icons | Lucide React | Already installed |
| Animations | Framer Motion | Already installed |
| HTTP | fetch (native) | No additional dependency |

### New Dependencies Required

```
recharts          # Dashboard 3 pattern — charting
```

All other dependencies are already in `package.json`.

### File Structure

```
frontend/src/
├── App.tsx                          # Root with router
├── main.tsx                         # Entry point
├── lib/
│   ├── api.ts                       # API client (fetch wrapper)
│   ├── websocket.ts                 # Socket.IO connection manager
│   └── utils.ts                     # cn() helper, formatters
├── stores/
│   ├── chatStore.ts                 # Chat state (messages, sessions)
│   ├── agentStore.ts                # Agent state (list, status, routing)
│   ├── settingsStore.ts             # User preferences, API keys
│   └── specStore.ts                 # Spec-Kit state
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx             # Root layout with gradient bg
│   │   ├── Sidebar.tsx              # Collapsible navigation
│   │   ├── TopBar.tsx               # Search, notifications, user
│   │   └── CommandPalette.tsx       # Ctrl+K fuzzy search
│   ├── chat/
│   │   ├── ChatWindow.tsx           # Main conversation view
│   │   ├── ChatInput.tsx            # Input + model/search/mode selectors
│   │   ├── ChatMessage.tsx          # Message renderer (text/code/diff/error/system)
│   │   ├── CodeBlock.tsx            # Monaco-powered code display
│   │   ├── DiffViewer.tsx           # Side-by-side diff
│   │   ├── SearchResults.tsx        # Collapsible source cards
│   │   ├── RoutingBadge.tsx         # Agent + model + confidence display
│   │   └── ArtifactPanel.tsx        # Split-right code/doc panel
│   ├── agents/
│   │   ├── AgentList.tsx            # All agents with status
│   │   ├── AgentCard.tsx            # Single agent detail
│   │   ├── ProviderStatus.tsx       # Provider health indicators
│   │   └── RoutingLog.tsx           # Recent query routing decisions
│   ├── specs/
│   │   ├── SpecList.tsx             # Specifications with quality scores
│   │   ├── SpecDetail.tsx           # Quality bars, risk, recommendations
│   │   ├── ConstitutionList.tsx     # Project constitutions
│   │   └── TaskTracker.tsx          # Implementation progress
│   ├── search/
│   │   ├── WebSearch.tsx            # Multi-provider web search
│   │   ├── CodeSearch.tsx           # Semantic code search
│   │   └── SourceCard.tsx           # Individual search result
│   ├── analytics/
│   │   ├── MetricCards.tsx          # KPI cards
│   │   ├── ExecutionChart.tsx       # Area chart (interactions over time)
│   │   ├── AgentDistribution.tsx    # Bar chart (routing by agent)
│   │   └── TokenUsage.tsx           # Cost/token tracking
│   ├── memory/
│   │   ├── InteractionHistory.tsx   # Searchable history
│   │   ├── Preferences.tsx          # Editable learned preferences
│   │   └── FeedbackStats.tsx        # Score averages and trends
│   ├── settings/
│   │   ├── ApiKeys.tsx              # Key management with status
│   │   ├── ModelDefaults.tsx        # Default model configuration
│   │   └── ConnectionStatus.tsx     # Provider connection health
│   └── ui/                          # Existing + new primitives
│       ├── button.tsx               # (exists)
│       ├── badge.tsx                # (exists)
│       ├── card.tsx                 # (exists — extend)
│       ├── dropdown-menu.tsx        # (new — Radix wrapper)
│       ├── input.tsx                # (new — styled input)
│       ├── tabs.tsx                 # (new — Radix wrapper)
│       ├── select.tsx               # (new — Radix wrapper)
│       ├── toggle.tsx               # (new — search toggle)
│       └── tooltip.tsx              # (new — Radix wrapper)
└── pages/
    ├── ChatPage.tsx                 # Default view
    ├── AgentsPage.tsx               # Agent management
    ├── SpecsPage.tsx                # Spec-Kit workflow
    ├── SearchPage.tsx               # Web + code search
    ├── AnalyticsPage.tsx            # Metrics dashboard
    ├── MemoryPage.tsx               # Agent memory
    └── SettingsPage.tsx             # Configuration
```

### API Contract

The frontend communicates with the backend through these endpoints (some exist, some need creation):

#### Existing Endpoints (from backend)

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | Send message, get agent response |
| GET | `/api/agents` | List all agents with status |
| GET | `/api/status` | System health check |
| GET | `/health` | Simple health ping |
| WebSocket | `/socket.io` | Real-time streaming, agent events |

#### New Endpoints Required

| Method | Path | Description |
|---|---|---|
| GET | `/api/providers` | List LLM providers with connection status and available models |
| GET | `/api/metrics` | Agent metrics (interactions, routing distribution, latency, cost) |
| GET | `/api/memory/snapshot` | Agent memory summary (interaction count, preferences, feedback avg) |
| GET | `/api/memory/history` | Paginated interaction history |
| PUT | `/api/memory/preferences` | Update user preferences |
| DELETE | `/api/memory/clear` | Clear interaction history (with age filter) |
| GET | `/api/specs` | List specifications with quality scores |
| GET | `/api/specs/:id` | Specification detail with full analysis |
| POST | `/api/specs` | Create new specification |
| POST | `/api/specs/:id/plan` | Generate implementation plan |
| POST | `/api/search/web` | Web search with provider selection |
| POST | `/api/search/code` | Semantic code search |
| GET | `/api/search/providers` | Available search providers with status |

#### Chat Request Schema

```typescript
interface ChatRequest {
  message: string;
  model_id?: string;           // e.g., "claude-sonnet-4-20250514"
  provider?: string;           // e.g., "anthropic"
  search_enabled?: boolean;    // trigger web search
  search_provider?: string;    // e.g., "brave"
  mode?: "single" | "multi" | "pipeline" | "parallel";
  agent_id?: string;           // override auto-routing
  session_id?: string;         // conversation thread
}
```

#### Chat Response Schema

```typescript
interface ChatResponse {
  response: string;
  metadata: {
    agent_id: string;
    agent_name: string;
    model_used: string;
    provider: string;
    routing_decision: {
      confidence: number;
      intent: string;
      capabilities_needed: string[];
    };
    tokens_used: number;
    response_time_ms: number;
    search_results?: SearchResult[];
    artifacts?: Artifact[];
  };
}

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  provider: string;
  relevance_score: number;
}

interface Artifact {
  type: "code" | "document" | "diff";
  language?: string;
  content: string;
  filename?: string;
}
```

---

## 6. Component Specifications

### 6.1 Chat Input Bar

The most critical component. Must expose all backend capabilities without visual clutter.

```
┌──────────────────────────────────────────────────────────────────┐
│ [Claude Sonnet 4.5 ▼] [Search: OFF ▼] [Single ▼]               │
│                                                                  │
│ Type your message...                                     [Send] │
│                                                                  │
│ via Prince Flowers · Anthropic                    1,247 tokens  │
└──────────────────────────────────────────────────────────────────┘
```

**Controls (top row):**

1. **Model Selector** — Two-level dropdown: Provider → Model
   - Shows current provider icon + model name
   - Groups by provider: Anthropic, OpenAI, DeepSeek, GLM, Ollama, llama.cpp
   - Grayed out if provider not configured (no API key)
   - Fetched from `GET /api/providers` on mount

2. **Search Toggle** — Pill toggle: OFF / ON with provider submenu
   - OFF (default): no web search
   - ON: opens provider picker (Perplexity, Brave, Google, DuckDuckGo)
   - Shows active provider name when ON

3. **Mode Selector** — Dropdown for orchestration mode
   - Single (default) — one agent handles query
   - Multi-Agent — multiple agents collaborate
   - Pipeline — sequential chain (shows pipeline builder)
   - Parallel — concurrent execution

**Input area:**
- Auto-expanding textarea (1-5 lines)
- Enter to send, Shift+Enter for newline
- Paste detection for code (auto-wraps in code fence)

**Status bar (bottom):**
- Shows which agent will handle the query (live routing preview)
- Token count for current context
- Provider name

### 6.2 Chat Message

Each message in the conversation stream renders based on content type.

**User message:**
```
┌─────────────────────────────────────────── You ──┐
│ How do I implement JWT authentication in Python?  │
└──────────────────────────────────────────────────┘
```

**Agent response (with routing badge):**
```
┌── Code Generator · Claude Sonnet 4.5 · 0.92 ────┐
│                                                   │
│ Here's a JWT implementation using PyJWT:          │
│                                                   │
│ ┌─ python ─────────────── [Copy] [Download] ──┐  │
│ │ import jwt                                   │  │
│ │ from datetime import datetime, timedelta     │  │
│ │                                              │  │
│ │ def create_token(user_id: str) -> str:       │  │
│ │     payload = {                              │  │
│ │         "sub": user_id,                      │  │
│ │         "exp": datetime.utcnow() + ...       │  │
│ │     }                                        │  │
│ │     return jwt.encode(payload, SECRET, ...)  │  │
│ └──────────────────────────────────────────────┘  │
│                                                   │
│ 🔍 Sources (3)                            [v]     │
│  ├─ PyJWT Documentation — pyjwt.readthedocs.io   │
│  ├─ FastAPI Security — fastapi.tiangolo.com       │
│  └─ OWASP JWT Guide — owasp.org                  │
│                                                   │
│ 847 tokens · 1.2s                    [👍] [👎]   │
└───────────────────────────────────────────────────┘
```

**Components used:**
- `RoutingBadge` — agent name, model, confidence
- `CodeBlock` — Monaco-powered with syntax highlighting, copy, download
- `SearchResults` — collapsible source cards
- Feedback buttons (thumbs up/down) feed into agent memory

### 6.3 Orchestration Progress Bar

When pipeline or parallel mode is active, a bottom bar shows live progress:

```
┌─── Pipeline: "Build auth with tests and docs" ──────────────────────┐
│                                                                      │
│  [Code Generator ✓] ──→ [Test Engineer ⟳] ──→ [Documentation ○]    │
│  "JWT implementation"    "Writing tests..."    "Pending"             │
│                                                                      │
│  ████████████████████░░░░░░░░░░  67%                                │
└──────────────────────────────────────────────────────────────────────┘
```

- Clickable nodes to view individual agent output
- Live status updates via WebSocket
- Cancel button to abort pipeline

### 6.4 Sidebar Navigation

Based on Dashboard 3's shell, enhanced with real data:

```
┌─────────────────────────┐
│  [T]  Torq Console      │
│        Dashboard         │
│                    [◀]   │
│─────────────────────────│
│  💬  Chat          (2)  │  ← active sessions count
│  🤖  Agents        (6)  │  ← active agent count
│  📋  Specifications (3) │  ← spec count
│  🔍  Search             │
│  📊  Analytics          │
│  🧠  Memory       (147) │  ← interaction count
│  ⚙️  Settings           │
│─────────────────────────│
│  Quick actions          │
│  [+ New Chat] [Run ▶]  │
└─────────────────────────┘
```

- Collapsible (icon-only mode)
- Counts fetched from backend on mount and updated via WebSocket
- Active page highlighted with accent color

### 6.5 Agent List Page

Shows real TORQ Console agents with live provider status:

```
┌─ Agents ─────────────────────────────────────────────────────────┐
│                                                                   │
│  Provider Status                                                  │
│  [Anthropic ✓] [OpenAI ✓] [DeepSeek ✓] [GLM ○] [Ollama ○]     │
│                                                                   │
│  ┌─ Prince Flowers ──────── Primary ─────── Active ──┐           │
│  │  General conversational agent with memory.         │           │
│  │  Capabilities: chat, code, research, task mgmt     │           │
│  │  Default model: Claude Sonnet 4.5                  │           │
│  │  Interactions: 52 (last 7d)                        │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                   │
│  ┌─ Code Generator ─────── Specialist ─── Active ────┐           │
│  │  Clean, documented code with examples.             │           │
│  │  Capabilities: code generation, refactoring        │           │
│  │  Routes when: code/implement/build detected        │           │
│  │  Interactions: 34 (last 7d)                        │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                   │
│  [Debug Assistant] [Documentation] [Test Engineer] [Architect]    │
│                                                                   │
│  Recent Routing Decisions                                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ "How do I implement JWT?" → Code Generator (0.92)          │   │
│  │ "What's wrong with this code?" → Debug Assistant (0.88)    │   │
│  │ "Explain async patterns" → Prince Flowers (0.95)           │   │
│  └────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### 6.6 Specifications Page

First-ever UI for the Spec-Kit system:

```
┌─ Specifications ──────────────────────────────────────────────────┐
│                                                                    │
│  Constitutions (2)    Specifications (5)    Plans (3)              │
│  ─────────────────────────────────────────────────                 │
│                                                                    │
│  ┌─ User Authentication System ─── In Progress ──────────────┐    │
│  │                                                            │    │
│  │  Quality Scores                                            │    │
│  │  Clarity:        ████████░░  0.85                          │    │
│  │  Completeness:   ███████░░░  0.72                          │    │
│  │  Feasibility:    █████████░  0.91                          │    │
│  │  Testability:    ████████░░  0.80                          │    │
│  │  Maintainability:██████░░░░  0.65                          │    │
│  │                                                            │    │
│  │  Overall: Good (0.79)                                      │    │
│  │                                                            │    │
│  │  Risk: Medium                                              │    │
│  │  • Timeline Risk: 0.40 — tight schedule                    │    │
│  │  • Quality Risk: 0.35 — testing gaps                       │    │
│  │                                                            │    │
│  │  Recommendations (3)                                       │    │
│  │  • Add specific security requirements for password policy  │    │
│  │  • Define performance benchmarks (<2s login)               │    │
│  │  • Specify error handling for token refresh                │    │
│  │                                                            │    │
│  │  [Generate Plan]  [Start Implementation]  [Re-analyze]     │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 7. Color System & Visual Design

### Decision: Dashboard 3's Dark Theme (Modified)

Dashboard 3's color system is the most refined. Adopt it with adjustments:

```typescript
const TORQ = {
  // Backgrounds (dark navy spectrum)
  bg:      "#0f1220",           // Deepest background
  panel:   "#151a2e",           // Sidebar, panels
  card:    "#1b2140",           // Cards, elevated surfaces
  surface: "#212845",           // Inputs, interactive areas

  // Borders
  border:       "rgba(141,153,174,0.22)",   // Default
  borderActive: "rgba(239,35,60,0.35)",     // Active/selected

  // Text
  text:    "#edf2f4",           // Primary text (Antiflash White)
  muted:   "rgba(237,242,244,0.72)",  // Secondary text
  dim:     "rgba(237,242,244,0.45)",  // Tertiary/disabled

  // Brand
  accent:  "#ef233c",           // Red Pantone (primary accent)
  accent2: "#d90429",           // Fire Engine Red (hover/active)
  gray:    "#8d99ae",           // Cool Gray (neutral accent)

  // Semantic
  success: "#10b981",           // Green (connected, success)
  warning: "#f59e0b",           // Amber (warnings)
  error:   "#ef4444",           // Red (errors, critical)
  info:    "#3b82f6",           // Blue (info, links)

  // Provider brand colors (for status indicators)
  anthropic: "#D4A574",         // Anthropic warm
  openai:    "#74AA9C",         // OpenAI green
  deepseek:  "#4B8BF5",        // DeepSeek blue
  ollama:    "#FFFFFF",         // Ollama white
  glm:       "#FF6B35",        // GLM/Z.AI orange
};
```

### Typography

- Font: System font stack (no custom fonts needed for initial release)
- Monospace: `JetBrains Mono` for code blocks (already available via Monaco)
- Sizes: 11px (labels), 13px (body), 14px (headers), 24px (metrics)

### Radii

- Cards: `rounded-2xl` (16px) — Dashboard 3 pattern
- Buttons: `rounded-xl` (12px)
- Inputs: `rounded-xl` (12px)
- Badges: `rounded-full`

---

## 8. State Management

### Zustand Stores

```typescript
// chatStore.ts
interface ChatStore {
  sessions: Session[];
  activeSessionId: string | null;
  messages: Record<string, Message[]>;
  isStreaming: boolean;

  // Actions
  sendMessage: (content: string, options: ChatOptions) => Promise<void>;
  createSession: () => string;
  switchSession: (id: string) => void;
  addMessage: (sessionId: string, message: Message) => void;
  setStreaming: (streaming: boolean) => void;
}

// agentStore.ts
interface AgentStore {
  agents: Agent[];
  providers: Provider[];
  routingLog: RoutingDecision[];

  fetchAgents: () => Promise<void>;
  fetchProviders: () => Promise<void>;
  getProviderStatus: (id: string) => "connected" | "disconnected" | "unknown";
}

// settingsStore.ts
interface SettingsStore {
  defaultProvider: string;
  defaultModel: string;
  searchProvider: string;
  searchEnabled: boolean;
  orchestrationMode: "single" | "multi" | "pipeline" | "parallel";
  theme: "dark" | "light";

  updateSetting: (key: string, value: unknown) => void;
}

// specStore.ts
interface SpecStore {
  constitutions: Constitution[];
  specifications: Specification[];
  plans: Plan[];

  fetchSpecs: () => Promise<void>;
  createSpec: (spec: NewSpec) => Promise<void>;
  generatePlan: (specId: string) => Promise<void>;
}
```

---

## 9. Real-time Communication

### WebSocket Events

```typescript
// Connect
const socket = io(API_BASE_URL, {
  transports: ["websocket"],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5,
});

// Outbound
socket.emit("chat_message", {
  message: string,
  session_id: string,
  model_id?: string,
  search_enabled?: boolean,
  mode?: string,
});

// Inbound
socket.on("agent_typing", (data: { agent_id: string }) => { ... });
socket.on("agent_token", (data: { token: string, session_id: string }) => { ... });
socket.on("agent_response", (data: ChatResponse) => { ... });
socket.on("search_started", (data: { provider: string, query: string }) => { ... });
socket.on("search_results", (data: { results: SearchResult[] }) => { ... });
socket.on("pipeline_progress", (data: { step: number, total: number, agent: string, status: string }) => { ... });
socket.on("agent_status_change", (data: { agent_id: string, status: string }) => { ... });
socket.on("error", (data: { message: string, code: string }) => { ... });
```

---

## 10. Implementation Phases

### Phase 1: Core Chat (Foundation)

**Goal:** A working chat that connects to the real backend with model selection.

**Components:**
- AppShell, Sidebar (navigation only, no counts), TopBar
- ChatWindow, ChatInput (message + model selector only)
- ChatMessage (text rendering)
- CodeBlock (basic syntax highlighting)
- RoutingBadge
- chatStore, agentStore, settingsStore

**API Endpoints Used:**
- `POST /api/chat`
- `GET /api/agents`
- `GET /api/providers` (new)
- `GET /api/status`

**Backend Changes:**
- Add `GET /api/providers` endpoint
- Ensure `/api/chat` returns routing metadata

**Acceptance Criteria:**
- [ ] User can send a message and receive a streamed response
- [ ] Model selector shows real providers from backend (grayed out if unavailable)
- [ ] Response shows routing badge (agent name, model, confidence)
- [ ] Code blocks render with syntax highlighting and copy button
- [ ] Multiple chat sessions in sidebar

### Phase 2: Search + Orchestration

**Goal:** Web search integration and multi-agent pipeline visibility.

**Components:**
- Search toggle in ChatInput
- SearchResults (collapsible source cards)
- Mode selector in ChatInput
- OrchestrationProgress (bottom bar)
- CommandPalette (Ctrl+K)
- WebSocket streaming integration

**API Endpoints Used:**
- `POST /api/search/web` (new)
- `POST /api/search/code` (new)
- `GET /api/search/providers` (new)
- WebSocket events for streaming

**Backend Changes:**
- Add search API endpoints wrapping existing WebSearchProvider
- Add semantic search API endpoint wrapping existing indexer
- Add pipeline progress WebSocket events

**Acceptance Criteria:**
- [ ] Search toggle enables web search with provider selection
- [ ] Search results appear as collapsible cards in conversation
- [ ] Pipeline mode shows real-time progress bar with agent steps
- [ ] Ctrl+K opens command palette with fuzzy search
- [ ] Token streaming works via WebSocket

### Phase 3: Spec-Kit + Analytics

**Goal:** Specification workflow and real metrics.

**Components:**
- SpecsPage (SpecList, SpecDetail, ConstitutionList, TaskTracker)
- AnalyticsPage (MetricCards, ExecutionChart, AgentDistribution, TokenUsage)
- Quality score visualization (bar charts per dimension)
- Risk badges

**API Endpoints Used:**
- `GET /api/specs` (new)
- `GET /api/specs/:id` (new)
- `POST /api/specs` (new)
- `POST /api/specs/:id/plan` (new)
- `GET /api/metrics` (new)

**Backend Changes:**
- Add Spec-Kit REST API wrapping existing SpecKitEngine
- Add metrics aggregation endpoint

**Acceptance Criteria:**
- [ ] Specifications list shows quality scores
- [ ] Specification detail shows 5-dimension quality bars
- [ ] "Generate Plan" creates a plan and shows tasks
- [ ] Analytics page shows real interaction/routing data
- [ ] Charts update when new interactions occur

### Phase 4: Memory + Settings + Polish

**Goal:** Agent memory visibility, settings page, and production polish.

**Components:**
- MemoryPage (InteractionHistory, Preferences, FeedbackStats)
- SettingsPage (ApiKeys, ModelDefaults, ConnectionStatus)
- DiffViewer
- ArtifactPanel
- Export functionality (Markdown, JSON, CSV, PDF)
- Notification system (via WebSocket events)
- Sidebar counts (live from backend)

**API Endpoints Used:**
- `GET /api/memory/snapshot` (new)
- `GET /api/memory/history` (new)
- `PUT /api/memory/preferences` (new)

**Backend Changes:**
- Add memory REST API wrapping existing MarvinAgentMemory
- Add export endpoints

**Acceptance Criteria:**
- [ ] Memory page shows interaction history with search
- [ ] User can edit learned preferences
- [ ] Settings page shows API key status (configured/missing)
- [ ] Export works for Markdown, JSON, CSV
- [ ] Notifications appear when agents complete tasks
- [ ] Sidebar shows live counts

---

## 11. Component Reuse Matrix

Components to port from existing Dashboard 1:

| Component | Source File | Reuse Strategy |
|---|---|---|
| Monaco Editor integration | `frontend/src/components/CodeViewer.tsx` | Port directly, update styling |
| CodeBlock | `frontend/src/components/chat/CodeBlock.tsx` | Port, add download button |
| DiffViewer | `frontend/src/components/chat/DiffMessage.tsx` | Port directly |
| ChatMessage type system | `frontend/src/components/chat/ChatMessage.tsx` | Port message type detection |
| WorkflowGraph SVG | `frontend/src/components/coordination/WorkflowGraph.tsx` | Port for pipeline visualization |
| CoordinationPanel | `frontend/src/components/coordination/CoordinationPanel.tsx` | Port for orchestration progress |
| Agent service | `frontend/src/services/agentService.ts` | Port API methods |
| WebSocket manager | `frontend/src/services/websocketService.ts` | Port connection logic |
| Zustand stores | `frontend/src/stores/` | Extend existing patterns |
| Button (CVA) | `frontend/src/components/ui/button.tsx` | Use directly |
| Badge | `frontend/src/components/ui/badge.tsx` | Use directly |
| Card | `frontend/src/components/ui/card.tsx` | Extend with new variants |

New Radix UI wrappers needed:

| Component | Radix Primitive | Status |
|---|---|---|
| DropdownMenu | `@radix-ui/react-dropdown-menu` | Already installed |
| Tabs | `@radix-ui/react-tabs` | Already installed |
| Dialog | `@radix-ui/react-dialog` | Already installed |
| Select | `@radix-ui/react-select` | Need to install |
| Toggle | `@radix-ui/react-toggle` | Need to install |
| Tooltip | `@radix-ui/react-tooltip` | Need to install |

---

## 12. Vercel Deployment

The dashboard deploys as a Vite static build on Vercel, with API routes handled by the Python serverless function.

### vercel.json

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/index.py" },
    { "src": "/(.*)", "dest": "/frontend/dist/$1" }
  ],
  "functions": {
    "api/index.py": {
      "runtime": "@vercel/python@latest",
      "maxDuration": 30
    }
  }
}
```

### Environment Variables (Vercel Dashboard)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Primary LLM provider |
| `OPENAI_API_KEY` | No | Fallback provider |
| `DEEPSEEK_API_KEY` | No | DeepSeek models |
| `GLM_API_KEY` | No | GLM/Z.AI models |
| `BRAVE_API_KEY` | No | Brave web search |
| `GOOGLE_API_KEY` | No | Google Custom Search |

---

## 13. Success Metrics

| Metric | Target | How Measured |
|---|---|---|
| First message to response | <3s | Frontend performance monitoring |
| Model switch latency | <500ms | No page reload, just API param change |
| Search results display | <2s after toggle | Web search provider response time |
| Pipeline visualization | Real-time | WebSocket event latency |
| Backend capability coverage | >90% | Feature audit against this PRD |
| Lighthouse score | >90 | Vite build optimization |

---

## 14. Risk Register

| Severity | Risk | Mitigation |
|---|---|---|
| High | WebSocket not available on Vercel serverless | Use SSE fallback for streaming; WebSocket for Railway/Docker deploys |
| High | Token streaming adds complexity | Phase 1 uses HTTP polling; Phase 2 adds streaming |
| Medium | Recharts bundle size | Tree-shake; only import used chart types |
| Medium | Monaco Editor bundle size | Lazy-load Monaco only on code-heavy pages |
| Low | Provider API keys exposed in frontend | All API calls go through backend; frontend never touches keys directly |
| Low | Color system inconsistency | Single TORQ theme object used everywhere |

---

## 15. Open Questions

1. **WebSocket on Vercel** — Vercel serverless doesn't support persistent WebSocket connections. Options:
   - Use Server-Sent Events (SSE) for streaming (Vercel supports this)
   - Use a separate WebSocket service (Railway, Fly.io) alongside Vercel frontend
   - Accept HTTP polling for Vercel deploys, WebSocket for self-hosted

2. **Authentication** — This PRD assumes no user authentication. If multi-user support is needed, add Supabase Auth or Clerk integration as Phase 5.

3. **Mobile responsive** — The sidebar collapses on mobile, but the full dashboard experience is desktop-optimized. Mobile-first redesign would be a separate effort.

---

## 16. Summary

This PRD defines a unified TORQ Console dashboard that:

- **Takes Dashboard 3's shell** (sidebar, dark theme, recharts, model routing)
- **Fills it with Dashboard 1's engines** (Monaco, diff viewer, WebSocket, Zustand)
- **Adds what no dashboard has** (search integration, spec-kit, agent memory, orchestration modes)
- **Follows patterns from Cursor/Bolt/Antigravity** (chat-first, streaming, artifacts, multi-model)
- **Deploys on Vercel** with static frontend + Python serverless API
- **Exposes >90% of backend capabilities** that are currently hidden behind CLI-only access

The implementation is 4 phases, with Phase 1 delivering a working chat with real backend integration and model selection.

---

*TORQ Console — Where AI meets industrial-grade software development methodology.*
