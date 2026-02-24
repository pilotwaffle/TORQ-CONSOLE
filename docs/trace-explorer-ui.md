# Trace Explorer UI - Data Model & Component Layout

## API Contracts

### GET /api/traces
List traces with filtering and pagination.

**Query Params:**
- `session_id`: Filter by session
- `user_id`: Filter by user
- `limit`: Max results (default 100)
- `offset`: Pagination offset
- `start_date`: ISO date filter
- `end_date`: ISO date filter

**Response:**
```typescript
interface TracesResponse {
  traces: Trace[];
  count: number;
  limit: number;
  offset: number;
  filters: Record<string, unknown>;
}

interface Trace {
  id: string;                    // UUID (Supabase primary key)
  trace_id: string;              // Business trace ID
  session_id: string;            // Session identifier
  agent_name: string | null;     // Agent that processed this
  agent_type: string | null;
  workflow_type: string | null;
  started_at: string;            // ISO timestamp
  ended_at: string | null;       // ISO timestamp
  duration_ms: number | null;    // Total duration
  total_spans: number;           // Number of child spans
  total_tokens: number;          // Tokens used
  total_cost_usd: number;        // Cost in USD
  status: "ok" | "error";
  metadata: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
  meta: Record<string, unknown>;
  user_id: string | null;
  error_code: string | null;
  error_message: string | null;

  // Deploy Identity (for correlation)
  deploy_platform: string;       // "vercel" | "railway" | "local"
  deploy_git_sha: string;        // Git commit SHA
  deploy_app_version: string;    // Version string
  deploy_version_source: string; // "package" | "git" | "env"
}
```

### GET /api/traces/{trace_id}
Get single trace with full details.

**Response:** `Trace` (same as above)

### GET /api/traces/{trace_id}/spans
Get spans for a trace with tree structure.

**Response:**
```typescript
interface TraceSpansResponse {
  trace_id: string;
  spans: Span[];
  root_spans: Span[];      // Top-level spans (no parent)
  count: number;
  limit: number;
  offset: number;
}

interface Span {
  id: string;
  span_id: string;         // Business span ID
  trace_id: string;
  parent_span_id: string | null;
  name: string;
  kind: string;            // "llm" | "tool" | "agent" | "internal"
  start_ms: number;        // Epoch milliseconds
  duration_ms: number;
  metadata: Record<string, unknown>;
  tags: string[];
  children: Span[];        // Populated by backend for tree rendering

  // Deploy Identity
  deploy_platform: string;
  deploy_git_sha: string;
  deploy_app_version: string;
  deploy_version_source: string;
}
```

---

## Component Layout (React/TypeScript)

```
TraceExplorerPage
├── TraceFiltersBar
│   ├── DeploySHAFilter (dropdown of unique SHAs)
│   ├── AgentFilter (multiselect)
│   ├── DateRangePicker
│   ├── StatusFilter (ok/error)
│   └── RefreshButton
│
├── TracesTable
│   ├── Column: Trace ID (link to detail)
│   ├── Column: Deploy Badge (SHA + platform icon)
│   ├── Column: Agent
│   ├── Column: Started At
│   ├── Column: Duration (ms)
│   ├── Column: Status (green/red badge)
│   ├── Column: Token Count
│   └── Column: Cost (USD)
│
├── Pagination (prev/next, page numbers)
│
└── TraceDetailModal (when trace clicked)
    ├── Header
    │   ├── Trace ID + Copy button
    │   ├── Deploy Badge (click to open GitHub commit)
    │   ├── Status Badge
    │   └── Close button
    │
    ├── MetadataPanel
    │   ├── Grid: Agent, Session, User, Workflow
    │   ├── Grid: Timing (start, end, duration)
    │   └── Grid: Deploy Identity
    │
    ├── SpanTree (Timeline visualization)
    │   ├── For each span:
    │   │   ├── SpanName + Duration
    │   │   ├── Timing bar (width = duration % of parent)
    │   │   ├── Expand/collapse children
    │   │   └── Click to show SpanDetail
    │   └── Y-axis: time, X-axis: parallel flows
    │
    └── SpanDetailPanel (when span clicked)
        ├── Properties (name, kind, parent)
        ├── Timing (start_ms, duration_ms)
        ├── Metadata JSON viewer
        └── Tags list
```

---

## State Management (Zustand)

```typescript
interface TraceExplorerStore {
  // Filters
  filters: {
    deploySha: string | null;
    agent: string | null;
    status: "ok" | "error" | null;
    dateRange: { start: Date; end: Date } | null;
  };

  // Data
  traces: Trace[];
  selectedTrace: Trace | null;
  spans: Span[];

  // UI State
  loading: boolean;
  error: string | null;
  pagination: { page: number; pageSize: number; total: number };
  spanTreeExpanded: Set<string>;

  // Actions
  setFilter: (key: string, value: unknown) => void;
  fetchTraces: () => Promise<void>;
  selectTrace: (traceId: string) => Promise<void>;
  toggleSpanExpansion: (spanId: string) => void;
  refresh: () => Promise<void>;
}
```

---

## Key UX Interactions

### 1. Deploy SHA Correlation
- Click deploy badge → opens GitHub commit page
- Filter by deploy SHA to see traces from specific version
- Badge color: green = current, yellow = old, red = unknown

### 2. Trace Timeline
- Waterfall visualization of spans
- Hover span → tooltip with duration
- Click span → detail panel slides in
- Parallel flows shown side-by-side

### 3. Status Indicators
- `status: "ok"` → green checkmark
- `status: "error"` → red X with error_message
- Error traces show at top when sorting by status

### 4. Performance Insights
- Highlight slow spans (> 1s = yellow, > 5s = red)
- Show token count and cost per trace
- Sort by duration, tokens, or cost

---

## Implement Priority Order

1. **Phase 1: Traces Table**
   - Fetch and display traces
   - Deploy badge with GitHub link
   - Basic filters (SHA, status)

2. **Phase 2: Trace Detail**
   - Modal with full trace info
   - Metadata panel
   - Deploy identity section

3. **Phase 3: Span Tree**
   - Timeline visualization
   - Expand/collapse
   - Span detail panel

4. **Phase 4: Advanced Filters**
   - Date range picker
   - Agent multiselect
   - Export traces as JSON

---

## Color Scheme

```css
--trace-status-ok: #10b981;      /* green */
--trace-status-error: #ef4444;    /* red */
--deploy-badge-current: #10b981;  /* green */
--deploy-badge-old: #f59e0b;      /* yellow */
--span-llm: #8b5cf6;             /* purple */
--span-tool: #06b6d4;            /* cyan */
--span-agent: #f59e0b;           /* amber */
--span-slow: #f97316;            /* orange */
--span-very-slow: #dc2626;       /* red */
```
