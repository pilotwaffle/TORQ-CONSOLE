# Phase 6: Operator Control Surface — PRD

**Version**: 1.0
**Status**: Planning
**Priority**: High (Blocker for Phase 5.2)
**Target Release**: v0.9.1-beta

---

## Executive Summary

The Operator Control Surface is TORQ's **mission command center** — a web-based UI that provides real-time visibility into missions, nodes, workstreams, events, and handoffs. Before adding complexity (Agent Teams, Organizational Learning), we must first make the system **observable**.

**Why This Before Phase 5.2?**

Without this UI, debugging TORQ requires:
- Database queries
- Log file parsing
- Custom scripts

Once Phase 5.2 (Agent Teams) arrives, system complexity increases dramatically. The control surface becomes essential for watching:
- Teams collaborating
- Synthesis happening
- Conflicts emerging
- Quality gates firing

In real time.

---

## Problem Statement

### Current State

TORQ v0.9.0-beta has a validated execution fabric with:
- Mission graph planning
- Idempotent node execution
- Event-driven coordination
- Rich handoff generation
- Workstream health tracking

**But all of this is invisible.**

### Pain Points

1. **No Mission Visibility** — Can't see running missions, their progress, or their state
2. **No Graph Visualization** — Mission graphs exist only as database records
3. **No Event Observability** — Event bus is active but events are hidden
4. **No Handoff Inspection** — Rich handoffs are generated but never displayed
5. **No Workstream Monitoring** — Health tracking exists but isn't exposed
6. **Debugging is Hard** — Understanding failures requires database inspection

### Impact

- Development velocity is slowed by debugging friction
- System behavior is opaque to operators
- Can't demonstrate TORQ's capabilities visually
- Phase 5.2 (Agent Teams) would be un-debuggable

---

## Solution Overview

The Operator Control Surface is a **React-based web UI** that connects to existing TORQ backend APIs. It provides five core views:

### 1. Mission Portfolio Panel
List view of all missions with status indicators

### 2. Mission Graph View
Interactive visualization of mission execution graph

### 3. Workstream Health Dashboard
Health status across parallel workstreams

### 4. Event Stream
Real-time event bus monitor

### 5. Handoff Viewer
Detailed inspection of collaboration packets

---

## User Stories

### As a TORQ Operator...
- I can see all missions in one place so I know what's running
- I can click into a mission to see its graph and understand dependencies
- I can watch events flow in real-time to debug execution issues
- I can inspect handoffs to verify data quality between nodes
- I can monitor workstream health to detect blocked or failing work

### As a TORQ Developer...
- I can visualize mission graphs to understand execution flow
- I can trace events to debug idempotency issues
- I can inspect handoffs to verify rich format compliance
- I can watch workstreams to detect race conditions or deadlocks

---

## Functional Requirements

### FR1: Mission Portfolio Panel

**User Goal**: See all missions at a glance

**Requirements**:
- Display table of all missions with columns:
  - Mission ID
  - Objective (truncated if >60 chars)
  - Status (pending, running, completed, failed)
  - Progress (X/Y nodes complete)
  - Created At
  - Updated At
- Status badges with color coding
- Click row to navigate to Mission Detail view
- Sort by any column
- Filter by status
- Auto-refresh every 5 seconds
- Pagination for >100 missions

**Data Source**:
```
GET /api/missions
→ missions table
```

### FR2: Mission Graph View

**User Goal**: Visualize mission structure and execution state

**Requirements**:
- Interactive node-link diagram using React Flow
- Nodes colored by state:
  - Green: completed
  - Blue: running
  - Yellow: ready to run
  - Gray: pending (blocked by dependency)
  - Red: failed
- Node labels show node type (objective, task, decision, evidence, deliverable)
- Edges show dependencies
- Click node to show detail panel
- Layout algorithm: hierarchical (top-to-bottom)
- Zoom and pan
- Mini-map for large graphs

**Data Source**:
```
GET /api/missions/{id}/graph
→ mission_nodes table, parsed from graph JSON
```

**Node Detail Panel**:
- Node ID and Title
- Node Type
- Current Status
- Agent Used (if applicable)
- Output Summary (truncated, with expand)
- Events Emitted (count, link to Event Stream)
- Handoff Packet (link to Handoff Viewer)
- Created/Updated timestamps

### FR3: Workstream Health Dashboard

**User Goal**: Monitor health of parallel workstreams

**Requirements**:
- Card-based layout, one card per workstream
- Each card shows:
  - Workstream Name
  - Health Status (healthy, at_risk, failed, idle)
  - Progress (X/Y nodes complete)
  - Active Node Count
  - Blocked Node Count
  - Last Activity timestamp
- Health status color-coded
- Click card to filter Event Stream to this workstream
- Auto-refresh every 5 seconds

**Data Source**:
```
GET /api/missions/{id}/workstreams
→ Derived from mission_nodes.workstream_id
```

**Health Calculation** (from existing `workstream_state.py`):
```
healthy:      no blocked nodes, at least one active
at_risk:      has blocked nodes, but making progress
failed:       has failed nodes, no progress in 5 minutes
idle:         no active nodes, no failed nodes
```

### FR4: Event Stream

**User Goal**: Watch event bus activity in real-time

**Requirements**:
- Scrolling list of events, newest first
- Each event shows:
  - Timestamp (ISO 8601)
  - Event Type (e.g., node.started, node.completed, handoff.created)
  - Entity ID (node_id, mission_id)
  - Severity (info, warning, error)
  - Event Data (collapsed JSON, expandable)
- Color coding by severity
- Auto-scroll to newest (toggleable)
- Filter by:
  - Event type (multi-select)
  - Mission ID
  - Workstream ID
  - Time range
- Real-time updates via Server-Sent Events (SSE)
- Export to JSON/CSV

**Data Source**:
```
GET /api/missions/{id}/events
SSE /api/missions/{id}/events/stream
→ mission_events table
```

### FR5: Handoff Viewer

**User Goal**: Inspect collaboration packets between nodes

**Requirements**:
- List view of all handoffs for a mission
- Each handoff shows:
  - Source Node → Target Node
  - Confidence Score
  - Created At
- Click to expand full handoff detail:
  - Summary (markdown rendered)
  - Artifacts (list, downloadable if stored)
  - Recommendations (bulleted list)
  - Dependencies (links to source nodes)
  - Metadata (JSON viewer)
- Badge for handoff format (rich vs minimal)
- Filter by source or target node

**Data Source**:
```
GET /api/missions/{id}/handoffs
→ mission_handoffs table
```

### FR6: Mission Detail Page

**User Goal**: Single page for all mission information

**Requirements**:
- Header with mission info:
  - Mission ID
  - Objective
  - Status badge
  - Progress bar
  - Created/Updated timestamps
- Tabbed interface:
  - Graph (FR2)
  - Workstreams (FR3)
  - Events (FR4)
  - Handoffs (FR5)
- URL: `/missions/{id}`

---

## Non-Functional Requirements

### NFR1: Performance

- Initial page load: <2 seconds
- Mission list (100 items): <500ms
- Graph rendering (50 nodes): <1 second
- Event stream update latency: <100ms (SSE)
- Auto-refresh: 5 seconds (configurable)

### NFR2: Scalability

- Support missions with 500+ nodes
- Support event streams with 10,000+ events
- Support 100+ concurrent users (future)

### NFR3: Usability

- Responsive design (desktop, tablet)
- Accessible (WCAG 2.1 AA)
- Keyboard navigation
- Loading states for all async operations
- Error handling with user-friendly messages

### NFR4: Reliability

- Graceful degradation if SSE fails (fall back to polling)
- Retry logic for failed API calls
- Client-side caching for static data

---

## Technical Architecture

### Frontend Stack

```
React 18+      # UI framework
Vite           # Build tool
TypeScript     # Type safety
React Flow     # Graph visualization
TailwindCSS    # Styling (if preferred)
Axios          # HTTP client
EventSource    # SSE support
React Query    # Server state management
Zustand        # Client state (if needed)
```

### Backend APIs

All endpoints use existing database tables. No schema changes required.

#### Mission List
```
GET /api/missions

Response:
{
  "missions": [
    {
      "id": "uuid",
      "objective": "string",
      "status": "pending|running|completed|failed",
      "progress": {"completed": 4, "total": 6},
      "created_at": "ISO 8601",
      "updated_at": "ISO 8601"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

#### Mission Detail
```
GET /api/missions/{id}

Response:
{
  "id": "uuid",
  "objective": "string",
  "reasoning_strategy": "string",
  "status": "string",
  "graph": { /* graph JSON */ },
  "context": { /* context JSON */ },
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

#### Mission Graph
```
GET /api/missions/{id}/graph

Response:
{
  "nodes": [
    {
      "id": "uuid",
      "title": "string",
      "type": "objective|task|decision|evidence|deliverable",
      "status": "pending|running|completed|failed|skipped",
      "workstream_id": "uuid|null",
      "position": {"x": 0, "y": 0}  // for layout
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "source": "node_id",
      "target": "node_id",
      "condition": "string|null"  // for decision gates
    }
  ]
}
```

#### Workstreams
```
GET /api/missions/{id}/workstreams

Response:
{
  "workstreams": [
    {
      "id": "uuid",
      "name": "string",
      "health": "healthy|at_risk|failed|idle",
      "progress": {"completed": 5, "total": 8},
      "active_nodes": 2,
      "blocked_nodes": 1,
      "last_activity": "ISO 8601"
    }
  ]
}
```

#### Events
```
GET /api/missions/{id}/events?limit=100&offset=0

Response:
{
  "events": [
    {
      "id": "uuid",
      "event_type": "string",
      "entity_id": "uuid",
      "entity_type": "string",
      "severity": "info|warning|error",
      "event_data": {},
      "created_at": "ISO 8601"
    }
  ],
  "total": 1337,
  "limit": 100,
  "offset": 0
}
```

SSE for real-time:
```
GET /api/missions/{id}/events/stream

Server-Sent Events stream, one event per line:
data: {"id": "...", "event_type": "...", ...}
```

#### Handoffs
```
GET /api/missions/{id}/handoffs

Response:
{
  "handoffs": [
    {
      "id": "uuid",
      "source_node_id": "uuid",
      "target_node_id": "uuid",
      "source_node_title": "string",
      "target_node_title": "string",
      "confidence": 0.95,
      "summary": "string",
      "artifacts": [],
      "recommendations": [],
      "format": "rich|minimal",
      "created_at": "ISO 8601"
    }
  ]
}
```

### Component Architecture

```
App
├── Layout
│   ├── Header
│   ├── Sidebar
│   └── MainContent
├── MissionList
│   ├── MissionTable
│   ├── MissionRow
│   └── StatusBadge
├── MissionDetail
│   ├── MissionHeader
│   ├── TabNavigation
│   ├── GraphView
│   │   ├── GraphCanvas (React Flow)
│   │   ├── NodeDetailPanel
│   │   └── NodeComponent
│   ├── WorkstreamDashboard
│   │   └── WorkstreamCard
│   ├── EventStream
│   │   ├── EventList
│   │   └── EventItem
│   └── HandoffViewer
│       ├── HandoffList
│       └── HandoffDetail
└── Shared
    ├── LoadingSpinner
    ├── ErrorBoundary
    └── Timestamp
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Set up React + Vite + TypeScript project structure
- [ ] Configure React Flow
- [ ] Set up routing (React Router)
- [ ] Create base layout (Header, Sidebar, MainContent)
- [ ] Implement API client with TypeScript types

### Phase 2: Mission Portfolio (Week 1)
- [ ] Implement `/api/missions` backend endpoint
- [ ] Build MissionList component
- [ ] Build MissionTable with sorting/filtering
- [ ] Add status badges and progress indicators
- [ ] Implement auto-refresh

### Phase 3: Mission Graph View (Week 2)
- [ ] Implement `/api/missions/{id}/graph` backend endpoint
- [ ] Set up React Flow canvas
- [ ] Implement node coloring by state
- [ ] Build NodeDetailPanel
- [ ] Add zoom/pan/minimap

### Phase 4: Workstream Dashboard (Week 2)
- [ ] Implement `/api/missions/{id}/workstreams` backend endpoint
- [ ] Calculate health from existing workstream_state.py logic
- [ ] Build WorkstreamDashboard component
- [ ] Build WorkstreamCard with health indicators

### Phase 5: Event Stream (Week 2)
- [ ] Implement `/api/missions/{id}/events` backend endpoint
- [ ] Implement SSE endpoint for real-time updates
- [ ] Build EventStream component
- [ ] Build EventItem with expandable JSON
- [ ] Add filtering by type/entity

### Phase 6: Handoff Viewer (Week 2)
- [ ] Implement `/api/missions/{id}/handoffs` backend endpoint
- [ ] Build HandoffViewer component
- [ ] Build HandoffDetail with full packet display

### Phase 7: Integration & Polish (Week 3)
- [ ] Build MissionDetail page with tabbed interface
- [ ] Connect all views to routing
- [ ] Add loading states and error handling
- [ ] Implement responsive design
- [ ] Performance testing with large missions
- [ ] Documentation

---

## Database Queries

### Mission List Query
```sql
SELECT
  m.id,
  m.objective,
  m.status,
  (SELECT COUNT(*) FROM mission_nodes WHERE mission_id = m.id AND status = 'completed') as completed_nodes,
  (SELECT COUNT(*) FROM mission_nodes WHERE mission_id = m.id) as total_nodes,
  m.created_at,
  m.updated_at
FROM missions m
ORDER BY m.updated_at DESC
LIMIT :limit OFFSET :offset;
```

### Mission Graph Query
```sql
SELECT
  id,
  title,
  type,
  status,
  workstream_id
FROM mission_nodes
WHERE mission_id = :mission_id
ORDER BY sequence_order;
```

### Workstream Health Query
```sql
SELECT
  workstream_id,
  COUNT(*) FILTER (WHERE status = 'running') as active,
  COUNT(*) FILTER (WHERE status = 'completed') as completed,
  COUNT(*) FILTER (WHERE status = 'failed') as failed,
  COUNT(*) FILTER (WHERE status = 'pending') as pending,
  MAX(updated_at) as last_activity
FROM mission_nodes
WHERE mission_id = :mission_id AND workstream_id IS NOT NULL
GROUP BY workstream_id;
```

Health calculated in application layer using `workstream_state.py` logic.

### Event Stream Query
```sql
SELECT
  id,
  event_type,
  entity_id,
  entity_type,
  severity,
  event_data,
  created_at
FROM mission_events
WHERE mission_id = :mission_id
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
```

### Handoff Query
```sql
SELECT
  h.id,
  h.source_node_id,
  h.target_node_id,
  s.title as source_node_title,
  t.title as target_node_title,
  h.confidence,
  h.summary,
  h.artifacts,
  h.recommendations,
  h.format,
  h.created_at
FROM mission_handoffs h
JOIN mission_nodes s ON h.source_node_id = s.id
JOIN mission_nodes t ON h.target_node_id = t.id
WHERE h.mission_id = :mission_id
ORDER BY h.created_at DESC;
```

---

## Success Criteria

### Milestone 1: Basic Visibility
- [ ] Mission Portfolio Panel shows all missions
- [ ] Mission Detail page accessible
- [ ] Graph view renders mission structure

### Milestone 2: Real-Time Observability
- [ ] Event Stream shows live events
- [ ] SSE connection stable
- [ ] Workstream health updates in real-time

### Milestone 3: Full Inspection
- [ ] Handoff Viewer displays rich handoffs
- [ ] Node detail shows all metadata
- [ ] Filtering and sorting work

### Milestone 4: Production Ready
- [ ] Performance requirements met
- [ ] Error handling comprehensive
- [ ] Documentation complete

---

## Open Questions

1. **Authentication**: Should the control surface require auth, or is it dev-only initially?
   - **Recommendation**: Dev-only initially, add auth for v1.0

2. **Deployment**: Should this be a separate service or integrated into existing TORQ frontend?
   - **Recommendation**: Integrate into existing frontend at `/control` path

3. **Event Retention**: How long should events be retained for the stream?
   - **Recommendation**: 30 days default, configurable

4. **Graph Persistence**: Should we save calculated node positions?
   - **Recommendation**: Yes, auto-layout on first render, save positions

5. **Multi-Mission View**: Should we support viewing multiple missions simultaneously?
   - **Recommendation**: Phase 2 feature, not in initial release

---

## Dependencies

### Blocks
- **Phase 5.2 (Agent Teams)**: This must be complete first

### Depends On
- **Phase 5.1 (Execution Fabric)**: Complete ✅
- **Phase 5 (Mission Graph Planning)**: Complete ✅
- **Existing database schema**: No changes required ✅

---

## Timeline Estimate

| Phase | Duration | Target |
|-------|----------|--------|
| Foundation | 3 days | Week 1 |
| Mission Portfolio | 2 days | Week 1 |
| Mission Graph View | 3 days | Week 2 |
| Workstream Dashboard | 2 days | Week 2 |
| Event Stream | 3 days | Week 2 |
| Handoff Viewer | 2 days | Week 2 |
| Integration & Polish | 3 days | Week 3 |

**Total**: ~18 days (3 weeks)

---

## References

- [Phase 5.1 Execution Fabric](../architecture/PHASE_5_1_EXECUTION_FABRIC.md)
- [Phase 5 Mission Graph Planning](../architecture/PHASE_5_MISSION_GRAPH_PLANNING.md)
- [Implementation Status](../current/IMPLEMENTATION_STATUS.md)
- React Flow Documentation: https://reactflow.dev/
- Server-Sent Events (MDN): https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events

---

*This PRD establishes the Operator Control Surface as the essential observability layer that enables all future development, particularly Phase 5.2 (Agent Teams) where system complexity increases dramatically.*
