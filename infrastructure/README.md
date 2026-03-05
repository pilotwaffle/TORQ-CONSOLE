# TORQ Console - OpenTelemetry Distributed Tracing

## Step 2: Infrastructure Upgrades - PRD Implementation

This module implements **distributed tracing** for all major system actions in the TORQ Console platform.

### Features

- **Automatic span creation** for all HTTP requests via FastAPI middleware
- **Decorator-based tracing** for functions (sync/async)
- **Trace context propagation** across service boundaries
- **OpenTelemetry compliant** - works with Grafana Tempo, Jaeger, Datadog
- **Fallback console logging** for local development

### Installation

```bash
pip install -r infrastructure/requirements.txt
```

### Quick Start

#### 1. Initialize tracing in your FastAPI app

```python
from fastapi import FastAPI
from infrastructure import init_tracing, add_tracing_middleware

app = FastAPI()

# Initialize tracing
tracer = init_tracing(
    service_name="torq-console-api",
    otlp_endpoint="http://localhost:4317",  # Your OTLP endpoint
    enable_console=True
)

# Add middleware
add_tracing_middleware(app)
```

#### 2. Use decorators to trace functions

```python
from infrastructure import traced, traced_db, traced_llm, SpanKind

@traced(name="user.login", kind=SpanKind.AGENT_ACT)
async def login(username: str):
    # Your code here
    pass

@traced_db(operation="select")
async def get_user(user_id: str):
    # Database operation
    pass

@traced_llm(provider="openai", model="gpt-4")
async def call_llm(prompt: str):
    # LLM call
    pass
```

#### 3. Verify traces are being emitted

```bash
python infrastructure/tracing_test.py
```

### Required Span Names (from PRD)

| Span Name | Description |
|-----------|-------------|
| `api.request` | Incoming HTTP requests |
| `agent.reason` | Agent reasoning steps |
| `agent.retrieve` | Knowledge retrieval |
| `agent.act` | Agent actions |
| `agent.evaluate` | Outcome evaluation |
| `database.query` | Database operations |
| `redis.lookup` | Redis cache operations |

### Each Span Includes

- `trace_id` - Unique trace identifier
- `span_id` - Unique span identifier
- `parent_span_id` - Parent span for hierarchy
- `attributes` - Key-value metadata
- `events` - Timed events within span
- `status` - Final span status

### Tracing Backend Options

**Grafana Tempo (Recommended)**
```python
tracer = init_tracing(
    service_name="torq-console",
    otlp_endpoint="http://tempo:4317"
)
```

**Jaeger**
```python
tracer = init_tracing(
    service_name="torq-console",
    otlp_endpoint="http://jaeger:4317"
)
```

**Console Only (Development)**
```python
tracer = init_tracing(
    service_name="torq-console",
    enable_console=True
)
```

### Railway Deployment

Set environment variables:

```bash
OTEL_EXPORTER_ENDPOINT=http://your-tempo-endpoint:4317
TORQ_TRACING_ENABLED=true
```

### Files

- `tracing.py` - Core tracer implementation
- `tracing_middleware.py` - FastAPI middleware
- `tracing_decorator.py` - Python decorators
- `tracing_fastapi.py` - Complete example
- `tracing_test.py` - Verification script

### Verification

Before completing Step 2, verify:

1. [ ] Traces are being created for API requests
2. [ ] Decorator-traced functions emit spans
3. [ ] Trace context propagates between services
4. [ ] Spans include required fields (trace_id, span_id, parent_span_id)
5. [ ] Tracing backend receives and displays traces

Run `python infrastructure/tracing_test.py` to verify.

### Next Steps

After Step 2 is complete:
- **Step 3**: API gateway middleware
- **Step 4**: CI/CD pipeline integration
- **Step 5**: Cost monitoring

---

**Status**: Ready for deployment to Railway
**Version**: 1.0.0
**PRD Reference**: `C:\Users\asdasd\Downloads\torq_infrastructure_upgrades_prd.md`
