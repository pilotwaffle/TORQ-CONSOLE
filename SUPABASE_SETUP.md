# TORQ Console - Supabase Setup Guide

## Quick Setup (5 minutes)

### 1. Get Your Supabase Credentials

1. Go to https://supabase.com/dashboard/project/lkaddjvuptwboaytruiz
2. Navigate to **Settings > API**
3. Copy these values:
   - `Project URL` → SUPABASE_URL
   - `anon/public` key → SUPABASE_ANON_KEY
   - `service_role` key → SUPABASE_SERVICE_ROLE_KEY

### 2. Update Your .env File

```bash
# Edit E:/TORQ-CONSOLE/.env
SUPABASE_URL=https://lkaddjvuptwboaytruiz.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Run the SQL Schema

1. Go to https://supabase.com/dashboard/project/lkaddjvuptwboaytruiz
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `supabase_learning_schema.sql`
4. Click **Run**

### 4. Verify Setup

```bash
cd E:/TORQ-CONSOLE
python -c "
import asyncio
from torq_console.telemetry.storage import get_telemetry_health

async def check():
    health = await get_telemetry_health()
    print('Supabase Health:', health)

asyncio.run(check())
"
```

Expected output:
```json
{
  "configured": true,
  "backend": "supabase",
  "tables": ["telemetry_traces", "telemetry_spans"]
}
```

## What Gets Stored in Supabase

| Table | Description |
|-------|-------------|
| `learning_events` | Agent interactions, rewards, outcomes |
| `telemetry_traces` | Request traces with deploy identity |
| `telemetry_spans` | Span timing for performance analysis |

## SQL Schema Summary

```sql
-- Enable vector search for semantic learning
CREATE EXTENSION IF NOT EXISTS vector;

-- Learning events with embeddings
CREATE TABLE learning_events (
    id UUID PRIMARY KEY,
    event_id TEXT UNIQUE,
    query TEXT,
    query_embedding VECTOR(1536),  -- OpenAI embeddings
    reward DECIMAL(5,4),
    metadata JSONB
);

-- Telemetry traces
CREATE TABLE telemetry_traces (
    trace_id TEXT PRIMARY KEY,
    session_id TEXT,
    agent_name TEXT,
    deploy_git_sha TEXT,
    deploy_app_version TEXT,
    created_at TIMESTAMP
);

-- Telemetry spans
CREATE TABLE telemetry_spans (
    span_id TEXT PRIMARY KEY,
    trace_id TEXT,
    parent_span_id TEXT,
    start_ms BIGINT,
    duration_ms BIGINT
);
```

## Troubleshooting

### "Supabase not configured"
- Check that `.env` has all three variables set
- Restart your terminal/application after updating `.env`

### "Permission denied"
- Use `SUPABASE_SERVICE_ROLE_KEY` for admin operations
- Use `SUPABASE_ANON_KEY` for client operations

### "Table not found"
- Run the SQL schema in Supabase SQL Editor
- Check that tables exist in Table Editor

## Web Search Fix Summary

The browser automation agent fixed web search by:

1. **Created `websearch_fixed.py`** - Multi-provider search with fallback:
   - Tavily (best for AI/crypto)
   - Brave Search (2,000 free/month)
   - Google Custom Search
   - DuckDuckGo (fallback)

2. **Updated `WebSearchTool`** - Now uses fixed provider

3. **Configuration** - Add these APIs to `.env`:
   ```bash
   TAVILY_API_KEY=tvly-...  # Get from https://tavily.com
   BRAVE_SEARCH_API_KEY=...  # Get from https://brave.com/search/api
   GOOGLE_SEARCH_API_KEY=...
   GOOGLE_SEARCH_ENGINE_ID=...
   ```

### Test Web Search

```bash
python -c "
import asyncio
from torq_console.llm.providers.websearch import WebSearchProvider

async def test():
    provider = WebSearchProvider()
    result = await provider.search('BTC price today', max_results=3)
    print('Results:', result['results'])

asyncio.run(test())
"
```

---

**Status**:
- ✅ Schema file created: `E:/TORQ-CONSOLE/supabase_learning_schema.sql`
- ✅ .env template added
- ⚠️ Needs actual API keys from Supabase dashboard
