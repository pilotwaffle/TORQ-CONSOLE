# TORQ Knowledge Plane Railway Deployment Guide

## Overview

This guide covers deploying the TORQ Knowledge Plane backend to Railway. The Knowledge Plane provides semantic knowledge storage, retrieval, and management for TORQ agents.

## Target Service

- **Railway Service**: web-production-74ed0.up.railway.app
- **API Type**: FastAPI backend
- **Version**: 1.1.0-knowledge-plane

## Prerequisites

1. Railway account (https://railway.app)
2. Railway CLI installed: `npm install -g @railway/cli`
3. Supabase project with credentials
4. OpenAI API key (for embeddings)

## Environment Variables Required

| Variable | Description | Source |
|----------|-------------|--------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | OpenAI Dashboard |
| `SUPABASE_URL` | Supabase project URL | Supabase Dashboard |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Supabase Dashboard |
| `TORQ_BRAIN_KEY` | TORQ Brain API key | Can use OPENAI_API_KEY |
| `REDIS_URL` | Redis URL for caching (optional) | Railway or Redis Cloud |

## API Endpoints

### POST /api/knowledge/store
Store a knowledge entry.

**Request:**
```json
{
  "content": "The knowledge content to store",
  "title": "Optional title",
  "category": "code|documentation|concept|best_practice|troubleshooting|architecture|configuration|workflow|other",
  "tags": ["tag1", "tag2"],
  "source": "agent_or_user",
  "metadata": {"key": "value"}
}
```

**Response:**
```json
{
  "success": true,
  "id": "uuid",
  "message": "Knowledge stored successfully",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### POST /api/knowledge/search
Search the knowledge base.

**Request:**
```json
{
  "query": "search query",
  "category": "code (optional)",
  "tags": ["tag1"] (optional),
  "limit": 10,
  "threshold": 0.7
}
```

**Response:**
```json
{
  "query": "search query",
  "total": 5,
  "results": [
    {
      "id": "uuid",
      "content": "matching content",
      "title": "title",
      "category": "code",
      "tags": ["tag1"],
      "source": "user",
      "created_at": "2024-01-01T00:00:00Z",
      "similarity": 0.95
    }
  ],
  "execution_time_ms": 150
}
```

### GET /api/knowledge/recent
Get recent knowledge entries.

**Parameters:**
- `limit`: Number of entries (1-100, default: 20)

**Response:**
```json
{
  "total": 20,
  "results": [...]
}
```

### GET /api/knowledge/stats
Get knowledge base statistics.

**Response:**
```json
{
  "total_entries": 100,
  "by_category": {"code": 50, "documentation": 30},
  "by_source": {"agent": 80, "user": 20},
  "oldest_entry": "2024-01-01T00:00:00Z",
  "newest_entry": "2024-12-31T23:59:59Z",
  "total_tags": 50,
  "unique_tags": ["python", "fastapi", "docker"]
}
```

### GET /api/knowledge/health
Knowledge Plane health check.

**Response:**
```json
{
  "status": "healthy",
  "supabase_configured": true,
  "openai_configured": true,
  "redis_configured": false,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Deployment Steps

### Option 1: Using Railway CLI

1. **Login to Railway:**
   ```bash
   railway login
   ```

2. **Link your Railway project:**
   ```bash
   cd /e/TORQ-CONSOLE
   railway link
   ```

3. **Set environment variables:**
   ```bash
   railway variables set OPENAI_API_KEY="your-key"
   railway variables set SUPABASE_URL="your-url"
   railway variables set SUPABASE_SERVICE_ROLE_KEY="your-key"
   railway variables set TORQ_BRAIN_KEY="your-key"
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

5. **Get service URL:**
   ```bash
   railway domain
   ```

### Option 2: Using Railway Browser UI

1. **Open Railway:** https://railway.app

2. **Create New Project or Select Existing**

3. **Deploy from GitHub:**
   - Click "New Service" > "Deploy from GitHub repo"
   - Select your TORQ-CONSOLE repository
   - Railway will auto-detect the Python project

4. **Configure Environment Variables:**
   - Go to service settings > Variables
   - Add all required variables

5. **Deploy:**
   - Click "Deploy" button
   - Railway will build and deploy

## Health Checks

After deployment, verify the service:

```bash
# Basic health check
curl https://your-service.railway.app/health

# Knowledge Plane health check
curl https://your-service.railway.app/api/knowledge/health

# List all endpoints
curl https://your-service.railway.app/
```

## Testing API Endpoints

### Store Knowledge
```bash
curl -X POST https://your-service.railway.app/api/knowledge/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "FastAPI is a modern, fast web framework for building APIs with Python.",
    "title": "FastAPI Overview",
    "category": "documentation",
    "tags": ["python", "fastapi", "web"],
    "source": "user"
  }'
```

### Search Knowledge
```bash
curl -X POST https://your-service.railway.app/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FastAPI",
    "limit": 5
  }'
```

### Get Recent
```bash
curl https://your-service.railway.app/api/knowledge/recent?limit=10
```

### Get Stats
```bash
curl https://your-service.railway.app/api/knowledge/stats
```

## Troubleshooting

### Build Failures

If the build fails:
1. Check `requirements-railway.txt` has all dependencies
2. Verify Python version (3.11)
3. Check Railway build logs

### Runtime Errors

If endpoints return errors:
1. Verify environment variables are set
2. Check Supabase connection
3. Verify table exists in Supabase

### Database Initialization

If the `torq_knowledge` table doesn't exist, run this SQL in Supabase:

```sql
CREATE TABLE IF NOT EXISTS torq_knowledge (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    title TEXT,
    category TEXT DEFAULT 'other',
    tags TEXT[] DEFAULT '{}',
    source TEXT,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON torq_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON torq_knowledge USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_knowledge_created ON torq_knowledge(created_at DESC);
```

## Monitoring

- **Railway Logs**: View in Railway Dashboard > Service > Logs
- **Health Endpoint**: `/api/knowledge/health`
- **Stats Endpoint**: `/api/knowledge/stats`

## Files Changed

1. `railway_app.py` - Added Knowledge Plane routes
2. `railway.json` - Updated start command
3. `.nixpacks.toml` - Updated start command
4. `torq_console/knowledge_plane/` - New module
   - `__init__.py` - Module init
   - `api.py` - Full Knowledge Plane API
   - `railway_integration.py` - Lightweight Railway integration
5. `requirements-railway.txt` - Existing dependencies sufficient

## Support

For issues or questions:
- Check Railway build logs
- Verify environment variables
- Test endpoints manually with curl
- Check Supabase table exists
