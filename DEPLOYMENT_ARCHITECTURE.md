# TORQ Console Deployment Architecture v2.0

**Last Updated:** 2026-03-04
**Architecture:** Vercel Frontend + Railway Backend + Supabase
**Status:** ✅ Production Active | 🔄 Enterprise Upgrade in Progress

**Document Size:** ~1,550 lines | **Sections:** 15 major topics

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Enhanced Architecture Diagram](#enhanced-architecture-diagram-layered-view)
3. [Security Architecture](#security-architecture)
4. [Active Endpoints](#active-endpoints-railway-backend)
5. [Distributed Tracing System](#distributed-tracing-system-opentelemetry)
6. [Telemetry & Observability](#telemetry--observability)
7. [Multi-LLM Routing Architecture](#multi-llm-routing-architecture)
8. [Caching Strategy](#caching-strategy-planned-implementation)
9. [Environment Variable Governance](#environment-variable-governance)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Versioning Strategy](#versioning-strategy)
12. [Failure Handling Strategy](#failure-handling-strategy)
13. [Disaster Recovery Plan](#disaster-recovery-plan)
14. [Scaling Strategy](#scaling-strategy)
15. [AI Governance System](#ai-governance-system)
16. [Supabase Database Schema](#supabase-database-schema)
17. [Configuration Files](#configuration-files)
18. [URLs & Links](#urls--links)
19. [Health Check Commands](#health-check-commands)
20. [Troubleshooting Guide](#troubleshooting-guide)
21. [Chrome Bridge Integration](#chrome-bridge-integration)
22. [Roadmap](#roadmap)
23. [Quick Reference](#appendix-quick-reference)

---

## Quick Find

| Want to find... | Go to section |
|-----------------|---------------|
| How the system fits together | [Architecture Diagram](#enhanced-architecture-diagram-layered-view) |
| Security model | [Security Architecture](#security-architecture) |
| What endpoints exist | [Active Endpoints](#active-endpoints-railway-backend) |
| How to debug issues | [Distributed Tracing](#distributed-tracing-system-opentelemetry) |
| LLM provider strategy | [Multi-LLM Routing](#multi-llm-routing-architecture) |
| Environment setup | [Environment Governance](#environment-variable-governance) |
| How deployment works | [CI/CD Pipeline](#cicd-pipeline) |
| What happens when things break | [Failure Handling](#failure-handling-strategy) |
| How to recover from disaster | [Disaster Recovery](#disaster-recovery-plan) |
| How to scale up | [Scaling Strategy](#scaling-strategy) |
| AI policy management | [AI Governance](#ai-governance-system) |
| Database schema | [Supabase Schema](#supabase-database-schema) |
| Configuration files | [Configuration Files](#configuration-files) |
| Important URLs | [URLs & Links](#urls--links) |
| Health check commands | [Health Checks](#health-check-commands) |
| Troubleshooting | [Troubleshooting Guide](#troubleshooting-guide) |
| Future plans | [Roadmap](#roadmap) |

---

## Executive Summary

TORQ Console is a production-ready AI consulting platform built on modern serverless architecture:
- **Frontend**: Vercel Edge CDN for global performance
- **Backend**: Railway containerized FastAPI services
- **Database**: Supabase PostgreSQL with pgvector
- **Governance**: Multi-LLM routing with policy enforcement

**Current Status**: Fully operational. Enterprise enhancements in progress.

---

## Enhanced Architecture Diagram (Layered View)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  User Browser (torq-console.vercel.app)                             │  │
│  │  - React/Vite SPA                                                    │  │
│  │  - OpenTelemetry tracing (trace_id propagation)                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTPS + JWT
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EDGE LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Vercel Edge Middleware (FUTURE: API Gateway)                        │  │
│  │  ✓ Rate limiting (by user/session)                                   │  │
│  │  ✓ Request tracing (trace_id injection)                              │  │
│  │  ✓ Bot filtering (user-agent analysis)                               │  │
│  │  ✓ API key enforcement                                               │  │
│  │  ✓ CORS management                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ API Routes (/api/*)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             GATEWAY LAYER (PLANNED)                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  API Gateway (Cloudflare Workers / FastAPI)                         │  │
│  │  - Service discovery & routing                                       │  │
│  │  - Circuit breaker pattern                                           │  │
│  │  - Request/response transformation                                    │  │
│  │  - Unified logging                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ Service Calls
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API SERVICES LAYER                                │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐ │
│  │  Agent Service       │  │  Telemetry Service   │  │  Learning Service │ │
│  │  (FastAPI)           │  │  (FastAPI)           │  │  (FastAPI)        │ │
│  │                      │  │                      │  │                   │ │
│  │  /api/chat           │  │  /api/telemetry/*    │  │  /api/learning/*  │ │
│  │  /api/agents         │  │  /api/traces/*       │  │  policy mgmt      │ │
│  │  Multi-LLM routing   │  │  span aggregation    │  │  RL training      │ │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────┘ │
│                                                                             │
│  All services:                                                              │
│  ✓ OpenTelemetry distributed tracing                                        │
│  ✓ Structured logging (JSON)                                                │
│  ✓ Health check endpoints                                                   │
│  ✓ Graceful shutdown                                                        │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ Data Access
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CACHE LAYER (PLANNED)                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Redis (Upstash / Railway Redis)                                     │  │
│  │  - Agent response caching (TTL: 1hr)                                 │  │
│  │  - Session state (TTL: 24hr)                                         │  │
│  │  - Telemetry buffer (write-behind)                                   │  │
│  │  - Rate limiting counters                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ Persistence
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Supabase PostgreSQL (npukynbaglmcdvzyklqa)                          │  │
│  │                                                                      │  │
│  │  Telemetry:              Learning:              Vector Search:       │  │
│  │  - telemetry_traces      - learning_events     - pgvector extension │  │
│  │  - telemetry_spans       - learning_policies   - similarity search   │  │
│  │                                                                      │  │
│  │  Features:                                                            │  │
│  │  - Row Level Security (RLS)                                          │  │
│  │  - Point-in-time recovery                                            │  │
│  │  - Daily automated backups                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

                     EXTERNAL SERVICES
┌─────────────────────────────────────────────────────────────────────────────┐
│  LLM Providers                Observability              Auth               │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐       │
│  │ Anthropic Claude │   │ Grafana/Prometheus│   │ Supabase Auth    │       │
│  │ OpenAI GPT-4     │   │ Sentry           │   │ JWT Sessions     │       │
│  │ DeepSeek         │   │ OpenTelemetry    │   │                  │       │
│  │ Local Ollama     │   │ Collector        │   │                  │       │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│  Supabase   │────▶│   Vercel    │────▶│   Railway   │
│             │     │    Auth     │     │  Middleware │     │  Backend    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                                        │
                          ▼                                        ▼
                   JWT Token                               Verify JWT
                   + user_id                               + check scope
```

### Authorization Model

| Operation | Auth Mechanism | Required Scope |
|-----------|---------------|----------------|
| **User chat** | JWT Bearer token | `chat:write` |
| **View traces** | JWT Bearer token | `telemetry:read` |
| **Admin policy** | TORQ_ADMIN_TOKEN | `admin:policy` |
| **Service-to-service** | Service role key | `service:full` |
| **Health checks** | None (public) | N/A |

### Security Headers

```http
# All responses include:
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

### Secrets Management

| Secret | Stored In | Access |
|--------|-----------|--------|
| `ANTHROPIC_API_KEY` | Railway Secrets | Backend only |
| `SUPABASE_SERVICE_ROLE_KEY` | Railway Secrets | Backend only |
| `TORQ_ADMIN_TOKEN` | Railway Secrets | Backend only |
| `TORQ_PROXY_SECRET` | Railway + Vercel | Inter-service |
| `SUPABASE_ANON_KEY` | Vercel Env | Frontend (limited) |

### Rate Limiting Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Rate Limits (per user, per window)                         │
├─────────────────────────────────────────────────────────────┤
│  /api/chat          : 100 requests / minute                 │
│  /api/telemetry/*   : 50 requests / minute                  │
│  /api/traces/*      : 200 requests / minute                  │
│  /api/learning/*    : 10 requests / minute (admin only)      │
│  /health            : Unlimited                             │
└─────────────────────────────────────────────────────────────┘

Implementation:
- Redis counters (planned) or in-memory
- Sliding window algorithm
- HTTP 429 response with Retry-After header
```

---

## Active Endpoints (Railway Backend)

| Endpoint | Method | Purpose | Auth | Status |
|----------|--------|---------|------|--------|
| `/health` | GET | Health check | None | ✅ Active |
| `/api/debug/deploy` | GET | Deploy identity (git_sha, version) | None | ✅ Active |
| `/api/learning/status` | GET | Learning system status | JWT | ✅ Active |
| `/api/telemetry/health` | GET | Telemetry diagnostics | JWT | ✅ Active |
| `/api/traces` | GET | List telemetry traces | JWT | ✅ Active |
| `/api/traces/{id}` | GET | Get single trace | JWT | ✅ Active |
| `/api/traces/{id}/spans` | GET | Get trace spans | JWT | ✅ Active |
| `/api/chat` | POST | Agent chat with learning hook | JWT | ✅ Active |
| `/api/telemetry` | POST | Ingest telemetry | Service | ✅ Active |
| `/api/learning/policy/approve` | POST | Approve policy | Admin | ✅ Active |

---

## Distributed Tracing System (OpenTelemetry)

### Trace Correlation Flow

```
Browser Request
    │
    │ trace_id=abc123 (generated or propagated)
    │ request_id=req-abc123-def456
    │ session_id=sess-xyz789
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Vercel Edge Middleware                                         │
│  - Extracts trace_id from headers or generates new              │
│  - Adds to response headers: X-Trace-ID, X-Request-ID          │
└─────────────────────────────────────────────────────────────────┘
    │
    │ trace_id: abc123
    │ parent_span_id: vercel-edge
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Railway Backend (FastAPI)                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Span: http.request (duration: 50ms)                   │   │
│  │  Attributes:                                           │   │
│  │  - http.method: POST                                  │   │
│  │  - http.url: /api/chat                                │   │
│  │  - user.id: usr_abc123                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│    │                                                           │
│    │ Creates child spans:                                      │
│    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Span: agent.process (duration: 2500ms)                 │   │
│  │  │                                                       │   │
│  │  ├─▶ Span: llm.anthropic (duration: 1800ms)            │   │
│  │  │  - tokens_in: 1500                                  │   │
│  │  │  - tokens_out: 450                                  │   │
│  │  │  - model: claude-sonnet-4-6                        │   │
│  │  │                                                      │   │
│  │  ├─▶ Span: tool.web_search (duration: 300ms)           │   │
│  │  │  - search_query: "..."                              │   │
│  │  │                                                      │   │
│  │  └─▶ Span: supabase.learning_write (duration: 50ms)    │   │
│  │     - table: learning_events                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
    │
    │ All spans include:
    │ - trace_id: abc123
    │ - session_id: sess-xyz789
    │ - deploy_git_sha: fe821df71772
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Supabase (telemetry_traces, telemetry_spans)                   │
│  - Complete trace stored with all spans                         │
│  - Queryable by trace_id, session_id, user_id                   │
└─────────────────────────────────────────────────────────────────┘
```

### Trace Header Propagation

```http
# Incoming request headers:
X-Trace-ID: abc123-def456-ghi789
X-Request-ID: req-abc123-456def
X-Session-ID: sess-xyz789-123abc

# Outgoing response headers:
X-Trace-ID: abc123-def456-ghi789
X-Request-ID: req-abc123-456def
X-Span-ID: span-xyz123-789abc
```

### Span Categories

| Span Kind | Name | Example Attributes |
|-----------|------|-------------------|
| `internal` | `agent.process` | `agent_name`, `mode`, `success` |
| `llm` | `llm.anthropic` | `provider`, `model`, `tokens_in`, `tokens_out`, `cost_estimate` |
| `tool` | `tool.web_search` | `tool_name`, `query`, `result_count` |
| `http` | `http.request` | `http.method`, `http.status_code`, `http.route` |
| `db` | `db.supabase_query` | `db.system`, `db.name`, `db.statement` |
| `cache` | `cache.redis_get` | `cache.hit`, `cache.key`, `cache.ttl` |

### Debugging with Traces

```
Problem: "User reports slow response"

1. Get user_id from support ticket
2. Query: SELECT * FROM telemetry_traces WHERE user_id = 'usr_abc' ORDER BY created_at DESC LIMIT 10
3. Find slow trace: duration_ms = 8500
4. Get spans: SELECT * FROM telemetry_spans WHERE trace_id = 'abc123' ORDER BY start_ms
5. Identify bottleneck: llm.anthropic span = 7800ms
6. Check attributes: model='claude-opus-4', tokens_in=15000
7. Solution: Route to faster model or add caching

Problem: "LLM cost spike"

1. Aggregate: SELECT provider, model, SUM(tokens_total), SUM(cost_estimate)
   FROM telemetry_spans WHERE created_at > NOW() - INTERVAL '1 hour'
   GROUP BY provider, model
2. Find culprit: DeepSeek, 5M tokens, $50
3. Investigate: Which agent? Which queries?
4. Action: Add rate limit or routing rule
```

---

## Telemetry & Observability

### Observability Stack (Planned Enhancement)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Grafana Dashboards                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  TORQ Console Operations Dashboard                      │   │
│  │  - Request rate (RPS)                                   │   │
│  │  - P50/P95/P99 latency                                  │   │
│  │  - Error rate (%)                                       │   │
│  │  - LLM token usage (by provider)                        │   │
│  │  - Cost per hour                                        │   │
│  │  - Active sessions                                      │   │
│  │  - Cache hit rate                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Data from
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Prometheus Metrics                            │
│  - torq_request_duration_seconds{endpoint, status}              │
│  - torq_requests_total{endpoint, method, status}                │
│  - torq_llm_tokens_total{provider, model, direction}            │
│  - torq_llm_cost_usd{provider, model}                           │
│  - torq_cache_hits_total{cache, operation}                      │
│  - torq_active_sessions{user_type}                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Stored in
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase (PostgreSQL)                         │
│  - Metrics aggregated from telemetry_spans                      │
│  - Materialized views for dashboards                            │
│  - Retention: 90 days detailed, 1 year aggregated               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Sentry Error Tracking                         │
│  - Uncaught exceptions                                         │
│  - LLM provider failures                                       │
│  - Supabase connection errors                                  │
│  - Performance issues (slow transactions)                       │
└─────────────────────────────────────────────────────────────────┘
```

### Metrics to Track

| Category | Metric | Alert Threshold |
|----------|--------|-----------------|
| **Performance** | P95 latency | > 5 seconds |
| **Performance** | P99 latency | > 10 seconds |
| **Errors** | Error rate | > 5% |
| **Errors** | LLM failures | > 10% in 5min |
| **Cost** | Hourly LLM cost | > $100 |
| **Cost** | Tokens per user | > 100K/hour |
| **Availability** | Health check failures | > 3 consecutive |

---

## Multi-LLM Routing Architecture

### LLM Provider Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TORQ LLM Router                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Route Decision Engine (torq_console/llm_router.py)                  │  │
│  │                                                                      │  │
│  │  Input: query, user_tier, cost_budget, latency_requirement           │  │
│  │  Output: provider, model, fallback_chain                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   REASONING     │ │    EMBEDDING    │ │   COST OPT      │
│   Tier          │ │    Tier         │ │    Tier         │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ Anthropic       │ │ OpenAI          │ │ DeepSeek        │
│ Claude Opus 4   │ │ text-embedding-3│ │ DeepSeek-V3     │
│ Claude Sonnet   │ │                 │ │                 │
│ GPT-4o          │ │                 │ │ Local Ollama    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Routing Rules

| Query Type | Primary Model | Fallback | Criteria |
|------------|---------------|----------|-----------|
| **Complex reasoning** | Claude Opus 4 | Claude Sonnet 4.6 | `complexity > 0.7` |
| **Code generation** | Claude Sonnet 4.6 | GPT-4o | `mode == 'code'` |
| **Simple chat** | Claude Sonnet 4.6 | Haiku 4 | `complexity < 0.4` |
| **Embeddings** | OpenAI text-embedding-3 | - | Always |
| **Offline mode** | Local Ollama (Qwen2.5) | - | `force_local == true` |
| **Cost sensitive** | DeepSeek-V3 | Claude Haiku | `user_tier == 'free'` |
| **Admin/ops** | GPT-4o | Claude Sonnet | `scope == 'admin'` |

### Cost Estimation

```python
# Per-1K token costs (USD, as of 2026-03)
PRICING = {
    "anthropic": {
        "claude-opus-4": {"input": 0.015, "output": 0.075},
        "claude-sonnet-4.6": {"input": 0.003, "output": 0.015},
        "claude-haiku-4": {"input": 0.0008, "output": 0.004},
    },
    "openai": {
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "text-embedding-3-small": {"input": 0.00002, "output": 0},
    },
    "deepseek": {
        "deepseek-v3": {"input": 0.00014, "output": 0.00028},
    },
    "local": {
        "ollama": {"input": 0, "output": 0},  # Free, GPU cost amortized
    },
}

def estimate_cost(provider, model, tokens_in, tokens_out):
    """Estimate request cost in USD."""
    pricing = PRICING[provider][model]
    cost = (tokens_in / 1000) * pricing["input"] + (tokens_out / 1000) * pricing["output"]
    return cost

# Example: Claude Sonnet, 1500 in, 450 out → $0.01275
```

### Cost Monitoring Schema

```sql
-- Add to telemetry_spans
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS cost_estimate DECIMAL(10,6);

-- Materialized view for cost dashboard
CREATE MATERIALIZED VIEW hourly_llm_costs AS
SELECT
    date_trunc('hour', created_at) as hour,
    provider,
    model,
    SUM(tokens_in) as total_tokens_in,
    SUM(tokens_out) as total_tokens_out,
    SUM(cost_estimate) as total_cost_usd,
    COUNT(*) as request_count
FROM telemetry_spans
WHERE kind = 'llm'
GROUP BY 1, 2, 3;

-- Refresh every hour
CREATE INDEX ON hourly_llm_costs (hour DESC);
```

### Cost Alerting

| Metric | Threshold | Action |
|--------|-----------|--------|
| Hourly cost | > $50 | Alert team |
| Per-user cost (day) | > $10 | Soft limit user |
| Per-user cost (month) | > $50 | Hard limit user |
| Provider cost spike | > 200% normal | Investigate |
| Unusual model usage | > 1000 requests/hr | Check for abuse |

---

## Caching Strategy (Planned Implementation)

### Redis Cache Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cache Layer Design                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  L1: Vercel Edge Cache (static assets)                  │   │
│  │  - TTL: 1 hour                                          │   │
│  │  - Purge on deployment                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  L2: Redis (Upstash / Railway Redis)                    │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Agent Response Cache                            │    │   │
│  │  │  Key: agent_response:{query_hash}                │    │   │
│  │  │  TTL: 1 hour                                       │    │   │
│  │  │  Invalidated on: policy update, new learning      │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Session State                                   │    │   │
│  │  │  Key: session:{session_id}                       │    │   │
│  │  │  TTL: 24 hours                                     │    │   │
│  │  │  Contains: context, preferences, history          │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Telemetry Write-Behind Buffer                   │    │   │
│  │  │  Key: telemetry_buffer:{trace_id}                 │    │   │
│  │  │  TTL: 5 minutes (flush interval)                  │    │   │
│  │  │  Purpose: Batch writes to Supabase                │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  Rate Limit Counters                             │    │   │
│  │  │  Key: ratelimit:{user_id}:{endpoint}:{window}    │    │   │
│  │  │  TTL: 1 minute (sliding window)                   │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  L3: Supabase (persistent storage)                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cache Key Patterns

```python
# Agent response cache
cache_key = f"agent_response:{hash(query + str(context) + str(model))}"

# Session cache
cache_key = f"session:{session_id}"

# Rate limit
cache_key = f"ratelimit:{user_id}:{endpoint}:{datetime.now().strftime('%Y%m%d%H%M')}"

# User preferences
cache_key = f"user_prefs:{user_id}"

# Embedding cache
cache_key = f"embedding:{text_hash}"
```

### Cache Invalidation Strategy

| Event | Invalidation Action |
|-------|-------------------|
| New learning policy approved | Flush all `agent_response:*` keys |
| User preference change | Delete `user_prefs:{user_id}` |
| Session timeout | Delete `session:{session_id}` |
| New deployment | Flush all L1 edge caches |
| Emergency stop | Flush all caches |

---

## Environment Variable Governance

### Authority & Sources of Truth

```
┌─────────────────────────────────────────────────────────────────┐
│              Environment Variable Authority Matrix               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRODUCTION ENVIRONMENTS:                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Railway Secrets Manager (Primary for Backend)          │   │
│  │  - https://railway.com/project/.../variables            │   │
│  │  - Encrypted at rest                                     │   │
│  │  - Injected at runtime                                   │   │
│  │  - Audit log of changes                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Vercel Environment Variables (Primary for Frontend)     │   │
│  │  - https://vercel.com/.../settings/environment-variables │   │
│  │  - Environment-scoped (prod, preview, dev)              │   │
│  │  - Redacted in logs                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  LOCAL DEVELOPMENT:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  .env.local (gitignored)                                │   │
│  │  - Template: .env.example                               │   │
│  │  - Never commit actual values                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  STAGING:                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Railway Preview Deployments                            │   │
│  │  - Separate variables per PR                            │   │
│  │  - Shared staging secrets                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Environment Schema Definition

**File:** `config/env.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TORQ Console Environment Variables",
  "type": "object",
  "required": ["ANTHROPIC_API_KEY", "SUPABASE_URL"],
  "properties": {
    "ANTHROPIC_API_KEY": {
      "type": "string",
      "description": "Anthropic Claude API key",
      "pattern": "^sk-ant-",
      "env": ["railway"]
    },
    "OPENAI_API_KEY": {
      "type": "string",
      "description": "OpenAI API key for embeddings",
      "pattern": "^sk-",
      "env": ["railway"]
    },
    "SUPABASE_URL": {
      "type": "string",
      "format": "uri",
      "description": "Supabase project URL",
      "env": ["railway", "vercel"]
    },
    "SUPABASE_SERVICE_ROLE_KEY": {
      "type": "string",
      "description": "Supabase service role key (backend only)",
      "env": ["railway"]
    },
    "SUPABASE_ANON_KEY": {
      "type": "string",
      "description": "Supabase anonymous key (frontend)",
      "env": ["vercel"]
    },
    "TORQ_PROXY_SECRET": {
      "type": "string",
      "minLength": 32,
      "description": "Shared secret for Vercel-Railway proxy",
      "env": ["railway", "vercel"]
    },
    "TORQ_ADMIN_TOKEN": {
      "type": "string",
      "minLength": 32,
      "description": "Admin token for policy operations",
      "env": ["railway"]
    },
    "TORQ_ENV": {
      "type": "string",
      "enum": ["production", "staging", "development"],
      "default": "production",
      "env": ["railway", "vercel"]
    },
    "TORQ_TELEMETRY_ENABLED": {
      "type": "boolean",
      "default": true,
      "env": ["railway"]
    },
    "TORQ_TELEMETRY_STRICT": {
      "type": "boolean",
      "default": false,
      "description": "Fail requests on telemetry errors",
      "env": ["railway"]
    },
    "TORQ_LEARNING_POLICY_VERSION": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "default": "1.0.0",
      "env": ["railway"]
    },
    "REDIS_URL": {
      "type": "string",
      "format": "uri",
      "description": "Redis connection URL (for caching)",
      "env": ["railway"],
      "required": false
    },
    "SENTRY_DSN": {
      "type": "string",
      "format": "uri",
      "description": "Sentry error tracking DSN",
      "env": ["railway", "vercel"],
      "required": false
    }
  }
}
```

### Environment Variable Checklist

| Variable | Railway | Vercel | Required | Description |
|----------|---------|--------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | ❌ | Yes | Claude access |
| `OPENAI_API_KEY` | ✅ | ❌ | No | Embeddings |
| `SUPABASE_URL` | ✅ | ✅ | Yes | Database |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | ❌ | Yes | Backend DB |
| `SUPABASE_ANON_KEY` | ❌ | ✅ | Yes | Frontend DB |
| `TORQ_PROXY_SECRET` | ✅ | ✅ | Yes | Inter-service |
| `TORQ_ADMIN_TOKEN` | ✅ | ❌ | Yes | Admin ops |
| `TORQ_ENV` | ✅ | ✅ | Yes | Environment |
| `REDIS_URL` | ✅ | ❌ | No | Caching |
| `SENTRY_DSN` | ✅ | ✅ | No | Error tracking |

---

## CI/CD Pipeline

### Deployment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Git Push (control-plane-v1-clean)           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflow                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  .github/workflows/deploy.yml                            │   │
│  │                                                           │   │
│  │  Step 1: Pre-flight Checks                               │   │
│  │  ✓ Lint (ruff, eslint)                                   │   │
│  │  ✓ Type check (mypy, tsc)                                │   │
│  │  ✓ Unit tests (pytest, vitest)                           │   │
│  │  ✓ Environment schema validation                         │   │
│  │  ✓ Security scan (snyk, dependabot)                      │   │
│  │                                                           │   │
│  │  Step 2: Build Artifacts                                 │   │
│  │  ✓ Frontend: npm run build                               │   │
│  │  ✓ Backend: docker build (if needed)                     │   │
│  │  ✓ Generate build metadata                               │   │
│  │                                                           │   │
│  │  Step 3: Deploy (parallel)                               │   │
│  │  ├─▶ Railway: Trigger auto-deploy                        │   │
│  │  │   - Health check verification                         │   │
│  │  │   - Smoke tests                                       │   │
│  │  │                                                       │   │
│  │  └─▶ Vercel: Trigger auto-deploy                         │   │
│  │      - Edge function tests                               │   │
│  │      - Screenshot diff (visual)                          │   │
│  │                                                           │   │
│  │  Step 4: Post-deploy Verification                        │   │
│  │  ✓ Health check all services                             │   │
│  │  ✓ Run smoke tests against prod                          │   │
│  │  ✓ Verify telemetry flowing                              │   │
│  │  ✓ Notify team (Slack)                                   │   │
│  │                                                           │   │
│  │  Step 5: Rollback on Failure                             │   │
│  │  ❌ Auto-rollback if health checks fail                   │   │
│  │  🔄 Re-deploy previous commit                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Versioning Strategy

```
MAJOR.MINOR.PATCH

MAJOR: Breaking changes (architecture, API contracts, data schemas)
  Example: 1.0.0 → 2.0.0 (telemetry schema v1 → v2)

MINOR: New features (backward compatible)
  Example: 1.0.0 → 1.1.0 (add new LLM provider)

PATCH: Bug fixes (no behavior change)
  Example: 1.0.0 → 1.0.1 (fix timeout handling)
```

---

## Failure Handling Strategy

### Failure Mode Matrix

| Failure Scenario | Detection | Behavior | Recovery |
|------------------|-----------|----------|----------|
| **Supabase down** | Health check timeout | Telemetry fallback mode | Auto-retry with backoff |
| **LLM provider timeout** | Request > 30s | Fallback to backup model | Return cached if available |
| **Railway container restart** | Health check fails | Drain queue, graceful shutdown | Auto-restart by Railway |
| **High error rate** | > 5% errors in 5min | Circuit breaker opens | Gradual recovery |
| **Rate limit exceeded** | HTTP 429 from LLM | Queue request, retry later | Exponential backoff |
| **Cache failure** | Redis connection error | Bypass cache, hit DB | Auto-reconnect |
| **Frontend build fail** | Vercel deploy error | Keep previous deployment | Manual fix required |

### Circuit Breaker Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    Circuit Breaker States                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CLOSED (Normal)                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Requests pass through                                │   │
│  │  - Track success/failure rate                           │   │
│  │  - If failure rate > 50% → OPEN                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  OPEN (Failing)                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Requests fail fast (no wait)                        │   │
│  │  - Return cached response or degraded message           │   │
│  │  - After timeout (60s) → HALF_OPEN                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  HALF_OPEN (Testing)                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - Allow test request                                  │   │
│  │  - If success → CLOSED                                │   │
│  │  - If failure → OPEN                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Graceful Degradation

```python
# Example: Multi-level fallback
async def get_agent_response(query, session_id):
    try:
        # Primary: Claude Opus
        return await call_claude_opus(query)
    except RateLimitError:
        try:
            # Fallback 1: Claude Sonnet (cheaper, higher limits)
            return await call_claude_sonnet(query)
        except Exception:
            try:
                # Fallback 2: DeepSeek (very cheap)
                return await call_deepseek(query)
            except Exception:
                # Fallback 3: Cached response
                cached = await get_cached_response(query)
                if cached:
                    return cached + "\n\n[Cached response due to service issues]"
                # Fallback 4: Static message
                return "I'm experiencing technical difficulties. Please try again."
    except Exception:
        # Any other error → try cache
        cached = await get_cached_response(query)
        return cached or "Service temporarily unavailable."
```

### Retry Strategy

```python
RETRY_CONFIG = {
    "supabase_write": {"max_attempts": 3, "backoff": "exponential", "base_delay": 1.0},
    "llm_request": {"max_attempts": 2, "backoff": "exponential", "base_delay": 2.0},
    "http_request": {"max_attempts": 5, "backoff": "exponential", "base_delay": 0.5},
    "cache_get": {"max_attempts": 1, "backoff": "none"},  # Fail fast
}
```

---

## Disaster Recovery Plan

### Backup Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                        Backup Matrix                            │
├─────────────────────────────────────────────────────────────────┤
│  Asset                │ Frequency  │ Retention │ Location       │
│  ──────────────────────┼───────────┼──────────┼──────────────│
│  Supabase Database    │ Daily     │ 30 days  │ Supabase auto  │
│  Supabase Point-in-time│ Continuous│ 30 days  │ Supabase WAL   │
│  GitHub Repository    │ Continuous│ Forever   │ GitHub         │
│  Environment Configs  │ Per change│ 90 days  │ Railway/Vercel  │
│  Learning Policies    │ Per write │ Forever   │ Supabase       │
│  Telemetry Data       │ N/A       │ 90 days  │ Supabase       │
│  Redis Cache          │ N/A       │ N/A      │ Ephemeral      │
└─────────────────────────────────────────────────────────────────┘
```

### Recovery Objectives

| Metric | Target | Notes |
|--------|--------|-------|
| **RTO** (Recovery Time Objective) | 15 minutes | Max acceptable downtime |
| **RPO** (Recovery Point Objective) | 5 minutes | Max data loss |
| **Hot Standby** | N/A | Railway auto-restarts |
| **Cold Start** | 10 minutes | Full rebuild from git |

### Recovery Procedures

```bash
# Scenario 1: Supabase outage (read-only mode)
curl -X PATCH https://api.supabase.com/v1/projects/npukynbaglmcdvzyklqa/database/pause

# Mitigation: Enable read-only mode
# - All write operations disabled
# - Telemetry stored locally (buffer)
# - Agent responses still work (read-only)

# Scenario 2: Railway container crash (auto-recovery)
# Railway automatically restarts on failure
# No action needed unless persistent crashes

# Scenario 3: Complete data loss recovery
# Step 1: Create new Supabase project
supabase projects create --name "torq-console-emergency"

# Step 2: Run schema migrations
psql $NEW_DATABASE_URL -f supabase/migrations/99_canonical_telemetry_schema.sql
psql $NEW_DATABASE_URL -f supabase_learning_schema.sql

# Step 3: Update environment variables
railway variables set SUPABASE_URL=$NEW_DATABASE_URL
vercel env add SUPABASE_URL $NEW_DATABASE_URL

# Step 4: Deploy
git commit --allow-empty -m "emergency: switch to new database"
git push

# Scenario 4: Rollback to previous version
git checkout v1.0.9  # Known good version
git push -f origin control-plane-v1-clean  # Force deploy
```

### Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| **Platform Owner** | TBD | Slack @platform |
| **Database Admin** | TBD | Slack @dbadmin |
| **LLM Ops** | TBD | Slack @llm-ops |

---

## Scaling Strategy

### Current Architecture (Single Service)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Current: Monolithic API                      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Railway: 1 container × 512MB RAM                       │   │
│  │  - /api/chat                                            │   │
│  │  - /api/telemetry/*                                     │   │
│  │  - /api/learning/*                                      │   │
│  │  - /api/traces/*                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                     ↓ Handles ~100 concurrent users            │
└─────────────────────────────────────────────────────────────────┘
```

### Scale Path 1: Vertical Scale (Easy)

```
┌─────────────────────────────────────────────────────────────────┐
│              Phase 1: More Resources (Same Service)              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Railway: 1 container × 2GB RAM (+ 4X CPU)              │   │
│  │  - Cost: ~$40/month → ~$120/month                       │   │
│  │  - Handles: ~400 concurrent users                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                     ↓ Change one variable in Railway            │
└─────────────────────────────────────────────────────────────────┘
```

### Scale Path 2: Horizontal Scale (Medium)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Phase 2: Multiple Containers                   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Railway Load Balancer                                   │   │
│  │  - numReplicas: 3                                       │   │
│  │  - Each: 1GB RAM                                        │   │
│  │  - Total: 3GB RAM across 3 containers                   │   │
│  │  - Handles: ~1200 concurrent users                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                     ↓ Change numReplicas in railway.json        │
└─────────────────────────────────────────────────────────────────┘
```

### Scale Path 3: Microservices (Complex)

```
┌─────────────────────────────────────────────────────────────────┐
│                Phase 3: Service Separation                      │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Agent Service  │  │ Telemetry Svc   │  │  Learning Svc   │ │
│  │  2 containers   │  │  1 container    │  │  1 container    │ │
│  │  512MB each     │  │  256MB          │  │  256MB          │ │
│  │  /api/chat      │  │  /api/telemetry │  │  /api/learning  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│          │                     │                     │           │
│          └─────────────────────┼─────────────────────┘           │
│                                ▼                                 │
│                     ┌─────────────────┐                         │
│                     │  Shared Redis   │                         │
│                     │  (state/cache)  │                         │
│                     └─────────────────┘                         │
│                                                                  │
│  Handles: ~2000 concurrent users with better isolation          │
└─────────────────────────────────────────────────────────────────┘
```

### Scale Triggers & Actions

| Metric | Trigger | Action |
|--------|---------|--------|
| CPU usage | > 80% for 5min | Scale up containers |
| Memory usage | > 85% for 5min | Add container or upgrade |
| Response time P95 | > 5s | Scale up or add cache |
| Error rate | > 10% | Investigate + scale |
| Queue depth | > 100 | Add consumer |

---

## AI Governance System

### Policy Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Learning Policy Lifecycle                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. TRAINING                                                     │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  Agent interactions → learning_events table             │ │
│     │  Reward calculation → policy_score                     │ │
│     │  Pattern detection → routing recommendations            │ │
│     └─────────────────────────────────────────────────────────┘ │
│                        │                                         │
│                        ▼                                         │
│  2. VALIDATION                                                  │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  Policy review committee (human + automated)            │ │
│     │  Safety checks (toxicity, bias, hallucination)          │ │
│     │  Performance benchmark (must exceed current)             │ │
│     └─────────────────────────────────────────────────────────┘ │
│                        │                                         │
│                        ▼                                         │
│  3. APPROVAL                                                    │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  POST /api/learning/policy/approve                      │ │
│     │  Requires: TORQ_ADMIN_TOKEN                             │ │
│     │  Stores: learning_policies table                        │ │
│     │  Result: policy_id marked as "approved"                 │ │
│     └─────────────────────────────────────────────────────────┘ │
│                        │                                         │
│                        ▼                                         │
│  4. ROLLOUT                                                     │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  Update TORQ_LEARNING_POLICY_VERSION                    │ │
│     │  Deploy to Railway (auto or manual)                     │ │
│     │  Monitor: A/B testing against old policy                │ │
│     └─────────────────────────────────────────────────────────┘ │
│                        │                                         │
│                        ▼                                         │
│  5. MONITORING                                                  │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  Track: reward scores, user satisfaction, errors        │ │
│     │  Dashboard: policy performance metrics                  │ │
│     │  Alert: if performance drops below threshold           │ │
│     └─────────────────────────────────────────────────────────┘ │
│                        │                                         │
│                        ▼                                         │
│  6. ROLLBACK (if needed)                                        │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │  POST /api/learning/policy/rollback                     │ │
│     │  Reverts to previous approved policy                    │ │
│     │  Emergency stop if critical issues                      │ │
│     └─────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Model Approval Process

| Model | Approval Status | Use Case | Restrictions |
|-------|----------------|----------|--------------|
| Claude Opus 4 | ✅ Approved | Complex reasoning | Cost limit $0.50/req |
| Claude Sonnet 4.6 | ✅ Approved | General purpose | Daily limit 1000 req |
| Claude Haiku 4 | ✅ Approved | Simple queries | None |
| GPT-4o | ✅ Approved | Code generation | None |
| DeepSeek-V3 | ⚠️ Conditional | Cost optimization | Accuracy warning |
| Local Ollama | 🔄 Testing | Offline mode | Not for production |

### Safety Guardrails

```python
# Input sanitization
def sanitize_input(user_input: str) -> str:
    # Remove prompt injection patterns
    # Check for malicious content
    # Enforce length limits
    pass

# Output filtering
def filter_output(agent_response: str) -> str:
    # Check for prohibited content
    # Mask PII
    # Add citations where required
    pass

# Rate limiting by user
def check_user_limits(user_id: str):
    # Daily request count
    # Cost limits
    # Token limits
    pass
```

### Audit Trail

All policy changes are logged:

```sql
CREATE TABLE policy_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    actor TEXT NOT NULL,  -- admin token hash
    action TEXT NOT NULL,  -- approve, rollback, disable
    policy_id TEXT NOT NULL,
    previous_state JSONB,
    new_state JSONB,
    reason TEXT
);
```

### Compliance Checklist

- [x] **Data Retention**: 90 days telemetry, 7 years policies
- [x] **Right to Deletion**: User can request data purge
- [x] **Export Capability**: Users can download their data
- [x] **Consent Management**: Clear opt-in for data collection
- [ ] **SOC 2**: Not certified (can add if enterprise required)
- [ ] **GDPR**: Partially compliant (need full audit)

---

## Supabase Database Schema

### Project Reference
- **Dashboard**: https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa
- **API URL**: https://npukynbaglmcdvzyklqa.supabase.co
- **Region**: Check dashboard

### Tables Overview

#### Telemetry Tables

**`telemetry_traces`**
| Column | Type | Description |
|--------|------|-------------|
| `trace_id` | TEXT | Unique trace identifier |
| `session_id` | TEXT | User session ID |
| `user_id` | TEXT | User identifier |
| `meta` | JSONB | Trace metadata |
| `started_at` | TIMESTAMPTZ | Trace start time |
| `ended_at` | TIMESTAMPTZ | Trace end time |
| `error_code` | TEXT | Error code if failed |
| `error_message` | TEXT | Error message if failed |
| `deploy_git_sha` | TEXT | Git SHA for correlation |

**`telemetry_spans`**
| Column | Type | Description |
|--------|------|-------------|
| `span_id` | TEXT | Unique span identifier |
| `trace_id` | TEXT | Parent trace ID |
| `parent_span_id` | TEXT | Parent span (nested ops) |
| `kind` | TEXT | Span type (internal/llm/tool) |
| `name` | TEXT | Operation name |
| `duration_ms` | INTEGER | Duration in milliseconds |
| `start_ms` | BIGINT | Start timestamp (ms) |
| `end_ms` | BIGINT | End timestamp (ms) |
| `attributes` | JSONB | Span attributes |
| `provider` | TEXT | LLM provider |
| `model` | TEXT | Model name |
| `tokens_in` | INTEGER | Input tokens |
| `tokens_out` | INTEGER | Output tokens |
| `tokens_total` | INTEGER | Total tokens |
| `cost_estimate` | DECIMAL(10,6) | Estimated USD cost |
| `error_code` | TEXT | Error code if failed |
| `error_message` | TEXT | Error message if failed |

#### Learning Tables

**`learning_events`**
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `event_id` | TEXT UNIQUE | Unique event identifier |
| `created_at` | TIMESTAMPTZ | Event timestamp |
| `query` | TEXT | User query |
| `query_embedding` | VECTOR(1536) | OpenAI embedding |
| `mode` | TEXT | Agent mode used |
| `success` | BOOLEAN | Whether outcome was successful |
| `reward` | DECIMAL(5,4) | Calculated reward (0.0-1.0) |
| `execution_time` | DECIMAL(8,3) | Response time |
| `outcome` | TEXT | Outcome description |
| `tools_used` | TEXT[] | Tools used in response |
| `metadata` | JSONB | Additional metadata |

**`learning_policies`**
| Column | Type | Description |
|--------|------|-------------|
| `policy_id` | TEXT | Policy identifier |
| `routing_data` | JSONB | Routing configuration |
| `status` | TEXT | Policy status |
| `approved_at` | TIMESTAMPTZ | Approval timestamp |
| `created_by` | TEXT | Admin who approved |

### Indexes

```sql
-- Telemetry
idx_telemetry_traces_trace_id
idx_telemetry_traces_session_id
idx_telemetry_spans_trace_id
idx_telemetry_spans_span_id
idx_telemetry_spans_parent_span_id
idx_telemetry_spans_start_ms

-- Learning (ivfflat for vector)
idx_learning_events_query_embedding (ivfflat)
idx_learning_events_mode
idx_learning_events_success
idx_learning_events_created_at
```

### Row Level Security (RLS)
- **Enabled** on all tables
- **Service role** has full access for Railway backend
- **Policy**: `"Service role full access"` - Allows `auth.role() = 'service_role'`

---

## Configuration Files

### Vercel Configuration (`vercel.json`)

```json
{
  "name": "torq-console",
  "buildCommand": "cd frontend && test -f src/components/ui/Badge.tsx && npm install && npx vite build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/api/index.py"
    },
    {
      "source": "/health",
      "destination": "/api/index.py"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "env": {
    "TORQ_CONSOLE_PRODUCTION": "true",
    "TORQ_DISABLE_LOCAL_LLM": "true",
    "TORQ_DISABLE_GPU": "true",
    "PYTHON_VERSION": "3.11"
  }
}
```

### Railway Configuration (`railway.json`)

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "deploy": {
    "startCommand": "python -m torq_console.ui.start_railway",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ALWAYS",
    "numReplicas": 1
  },
  "build": {
    "builder": "NIXPACKS"
  }
}
```

### Frontend Vite Configuration (`frontend/vite.config.ts`)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8899',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8899',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

---

## URLs & Links

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | https://torq-console.vercel.app/ | Main UI |
| **Vercel Dashboard** | https://vercel.com/pilotwaffles-projects/torq-console | Deployment settings |
| **Railway Service** | https://railway.com/project/.../service/... | Backend logs & config |
| **Supabase Dashboard** | https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa | Database & SQL |
| **GitHub Repo** | https://github.com/pilotwaffle/TORQ-CONSOLE | Source code |
| **Active Branch** | control-plane-v1-clean | Production branch |

---

## Health Check Commands

### Check Frontend
```bash
curl https://torq-console.vercel.app/
```

### Check Backend (Railway)
```bash
curl https://<your-railway-public-domain>/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "torq-console-railway",
  "git_sha": "fe821df71772",
  "app_version": "1.0.10-standalone",
  "supabase_configured": true,
  "anthropic_configured": true
}
```

### Check Deploy Identity
```bash
curl https://<your-railway-public-domain>/api/debug/deploy
```

Expected response:
```json
{
  "_schema": "torq-deploy-v1",
  "_schema_version": 1,
  "request_id": "req-xxx-yyy",
  "running_file": "torq_console/ui/railway_app.py",
  "git_sha": "fe821df71772",
  "app_version": "1.0.10-standalone",
  "platform": "railway",
  "anthropic_configured": true,
  "supabase_configured": true,
  "learning_hook": "mandatory"
}
```

---

## Troubleshooting Guide

### Frontend Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Blank page | Build failed | Check Vercel logs, rebuild |
| API errors | Backend down | Check Railway health |
| CORS errors | Origin mismatch | Check Vercel domain |
| Old version | Cache stale | Hard refresh (Ctrl+Shift+R) |

### Backend Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| 502 errors | Container crash | Check Railway logs |
| Slow responses | LLM timeout | Check provider status |
| Auth failures | Invalid JWT | Verify token |
| Telemetry errors | Supabase down | Check DB status |

### Database Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Connection refused | Network issue | Check Supabase status |
| RLS errors | Policy mismatch | Verify service role |
| Slow queries | Missing index | Run EXPLAIN ANALYZE |

---

## Chrome Bridge Integration

The **Chrome Bridge** feature (commit `6262c384`) is available but:
- **Not deployed** to Vercel/Railway yet
- Requires local installation for browser automation
- See `CHROME_BRIDGE_README.md` for setup

### Chrome Bridge Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Native Messaging Host | `chrome_bridge/host.py` | Chrome extension backend |
| Chrome Extension | `chrome_extension/` | Browser control UI |
| MCP Server | `torq_console/mcp/chrome_bridge_server.py` | Claude Code integration |
| Python Client | `torq_console/tools/chrome_operator.py` | Agent usage |

---

## Roadmap

### Phase 1: Foundation (✅ Complete)
- ✅ Vercel + Railway + Supabase architecture
- ✅ Multi-LLM routing
- ✅ Telemetry system
- ✅ Learning hooks

### Phase 2: Reliability (🔄 In Progress)
- 🔄 Redis caching layer
- 🔄 Circuit breaker pattern
- 🔄 Improved failure handling
- 🔄 Distributed tracing (OpenTelemetry)

### Phase 3: Observability (📅 Planned)
- ⏳ Grafana dashboards
- ⏳ Prometheus metrics
- ⏳ Sentry error tracking
- ⏳ Cost monitoring

### Phase 4: Scale (📅 Planned)
- ⏳ Microservices architecture
- ⏳ API Gateway
- ⏳ Horizontal scaling
- ⏳ CDN optimization

### Phase 5: Governance (📅 Planned)
- ⏳ Full policy approval workflow
- ⏳ Audit logging
- ⏳ Compliance certification (SOC 2)
- ⏳ Enterprise SSO

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Deploy frontend
git push origin control-plane-v1-clean  # Vercel auto-deploys

# Deploy backend
railway up  # Or git push (auto-deploy)

# Check health
curl https://torq-console.vercel.app/
curl https://<railway-url>/health

# View logs
railway logs  # Backend
vercel logs   # Frontend

# Run locally
cd frontend && npm run dev  # Frontend on :3000
python -m torq_console.ui.start_railway  # Backend on :8899
```

### Important Files

| File | Purpose |
|------|---------|
| `vercel.json` | Vercel deployment config |
| `railway.json` | Railway deployment config |
| `frontend/vite.config.ts` | Frontend build config |
| `torq_console/ui/railway_app.py` | Backend FastAPI app |
| `supabase/migrations/` | Database migrations |
| `.github/workflows/` | CI/CD pipelines |

### Support Resources

- **GitHub Issues**: https://github.com/pilotwaffle/TORQ-CONSOLE/issues
- **Documentation**: `CLAUDE.md` in project root
- **API Docs**: `/docs` endpoint when running locally
- **Telemetry Explorer**: `/traces` when authenticated

---

*Generated: 2026-03-04*
*Architecture Version: 2.0.0*
*Status: Production Active with Enterprise Enhancements Planned*

