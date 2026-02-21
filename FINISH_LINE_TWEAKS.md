# TORQ Console: Finish-Line Tweaks - Implementation Summary

**Version**: 1.0.8-standalone
**Date**: 2026-02-21
**Branch**: api-railway-proxy

---

## Overview

Implemented production-hardening "finish-line" tweaks for the Vercel → Railway → Supabase architecture to ensure bulletproof operation as traffic grows.

---

## 1. Enhanced Trace/Event Lookup with Stable Envelope

### Endpoints

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /api/debug/trace/{trace_id}` | All events for a trace | Many events (retries, fallbacks) |
| `GET /api/debug/event/{event_id}` | Single canonical record | One event |

### Stable Envelope Response

```json
{
  "found": true,
  "query": {"trace_id": "...", "event_id": null},
  "count": 3,
  "events": [...],
  "latest": {...}
}
```

### Not Found Response (stable)

```json
{
  "found": false,
  "query": {"trace_id": "...", "event_id": null},
  "count": 0,
  "events": []
}
```

**Benefits**:
- No ambiguous "Trace not found" errors
- Client-friendly stable structure
- Easy to distinguish "no results" from errors

---

## 2. Top-Level Columns for Analytics Performance

### New Columns

| Column | Type | Indexed | Purpose |
|--------|------|---------|---------|
| `trace_id` | TEXT | ✅ | Fast trace filtering (alias for source_trace_id) |
| `session_id` | TEXT | ✅ | Fast session grouping |
| `duplicate_count` | INTEGER | - | Tracks retry frequency |
| `last_seen_at` | TIMESTAMPTZ | - | Last time event was seen |

### SQL Location

Run `sql/add_top_level_columns.sql` in Supabase SQL Editor.

### Why This Matters

**Before**: Query by JSONB filter (slow)
```sql
SELECT * FROM learning_events
WHERE event_data->>'session_id' = '...'
```

**After**: Query by indexed column (fast)
```sql
SELECT * FROM learning_events
WHERE session_id = '...'
```

### Indexes Created

- `idx_learning_events_session_id` - Session lookups
- `idx_learning_events_trace_id` - Trace lookups
- `idx_learning_events_recent` - Recent events (30-day partial index)
- `idx_learning_events_session_time` - Composite session+time queries

---

## 3. Attempt Counters Without Breaking Idempotency

### Implementation

Uses Supabase's `ON CONFLICT` with `resolution=merge-duplicates`:

```python
learning_payload = {
    "event_id": learning_event_id,
    "trace_id": trace_id,  # Top-level
    "session_id": request.session_id,  # Top-level
    "duplicate_count": 1,  # First attempt
    "last_seen_at": datetime.utcnow().isoformat(),
    ...
}

headers["Prefer"] = "resolution=merge-duplicates"
```

### Behavior

- **First request**: `duplicate_count = 1`, `last_seen_at` set
- **Retry (same event_id)**: `duplicate_count += 1`, `last_seen_at` updated
- **Unique constraint on event_id**: Prevents duplicates

### Signal Provided

```json
{
  "event_id": "2d049ce2489f688b...",
  "event_inserted": false,
  "event_duplicate": true,
  "duplicate_count": 3  // This is the 3rd attempt!
}
```

**Analytics value**: Detect when upstream is retrying too aggressively.

---

## 4. PowerShell Wrapping Guard

### Validation Function

```python
def _validate_auth_header(auth_header: str | None) -> tuple[bool, str | None]:
    """Detects whitespace, newlines, truncation in Authorization headers."""
```

### Checks

1. **Newlines**: Detects PowerShell auto-wrap insertion
2. **Unusual whitespace**: Tabs, double spaces
3. **Truncation**: Token length < 50 or > 4000 chars
4. **Format**: Validates Bearer token structure

### Error Response

```json
{
  "detail": "Bearer token appears to contain newlines (PowerShell wrapping issue). Paste token without line breaks."
}
```

**Applied to**: `/api/debug/trace/*` and `/api/debug/event/*` endpoints

---

## Migration Steps

### 1. Run SQL in Supabase

```bash
# Copy contents of sql/add_top_level_columns.sql
# Paste in Supabase SQL Editor
# Execute
```

### 2. Verify Railway Deploys

```bash
curl https://your-railway-url.railway.app/api/debug/deploy
```

Should return:
```json
{
  "service": "railway-backend",
  "version": "1.0.8-standalone",
  ...
}
```

### 3. Test Trace Lookup

```bash
curl https://your-railway-url.railway.app/api/debug/trace/test-trace-id
```

Should return stable envelope with `found`, `query`, `count`, `events`.

### 4. Test Event Lookup

```bash
curl https://your-railway-url.railway.app/api/debug/event/test-event-id
```

---

## File Changes

| File | Changes |
|------|---------|
| `railway_app.py` | New endpoints, top-level columns, attempt counters, auth validation |
| `sql/add_top_level_columns.sql` | Database migration script |

---

## Next Steps (Future)

When ready to tackle the next capability jump:

1. **Learning Review UI** - Admin control center for filtering, hop chains, approve/deny
2. **Drift/Regression Monitor** - Daily metrics: fallback rate, duplicate rate, latency p95, tool-call rate

---

## API Reference

### GET /api/debug/trace/{trace_id}

Returns all events for a trace (including retries/fallbacks).

**Query**: `trace_id` (can also use source_trace_id for backward compat)

**Response**:
```json
{
  "found": true,
  "query": {"trace_id": "abc-123", "event_id": null},
  "count": 2,
  "events": [
    {
      "event_id": "...",
      "duplicate_count": 1,
      "occurred_at": "2026-02-21T10:00:00Z",
      "telemetry": {...}
    },
    {
      "event_id": "...",
      "duplicate_count": 2,
      "occurred_at": "2026-02-21T10:00:05Z",
      "telemetry": {...}
    }
  ],
  "latest": {...}
}
```

### GET /api/debug/event/{event_id}

Returns single canonical event record.

**Query**: `event_id`

**Response**:
```json
{
  "found": true,
  "query": {"trace_id": null, "event_id": "2d049..."},
  "count": 1,
  "events": [{
    "event_id": "2d049...",
    "trace_id": "abc-123",
    "session_id": "session-456",
    "duplicate_count": 1,
    "user_query": "...",
    "agent_response": "...",
    "telemetry": {...}
  }],
  "latest": {...}
}
```

---

**Status**: ✅ Complete - Production Ready
**Commit**: 7cee418e
