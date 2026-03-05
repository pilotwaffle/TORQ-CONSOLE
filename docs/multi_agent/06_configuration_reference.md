# Configuration Reference

Complete reference for all configuration options in the TORQ Multi-Agent System.

## Environment Variables

### Required Variables

```bash
# At least one LLM provider is required
ANTHROPIC_API_KEY=sk-ant-xxxxx        # Recommended: Anthropic Claude
OPENAI_API_KEY=sk-xxxxx                # Alternative: OpenAI GPT
DEEPSEEK_API_KEY=sk-xxxxx              # Alternative: DeepSeek
```

### Database Configuration

```bash
# Supabase (Primary Database)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxxxx          # Service role key (server-side)
SUPABASE_ANON_KEY=eyJxxxxx             # Anonymous key (client-side)

# Optional: PostgreSQL (Direct connection)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Web Search Configuration

```bash
# Brave Search (2,000 free queries/month)
BRAVE_SEARCH_API_KEY=BSxxxxx

# Tavily Search (1,000 free queries/month)
TAVILY_API_KEY=tvly-xxxxx

# Google Search API
GOOGLE_SEARCH_API_KEY=xxxxx
GOOGLE_SEARCH_ENGINE_ID=xxxxx
```

### Railway Configuration

```bash
# Service Configuration
RAILWAY_ENVIRONMENT=production
RAILWAY_PUBLIC_DOMAIN=torq-console.up.railway.app
RAILWAY_SERVICE_NAME=torq-console
PORT=8000

# Performance
RAILWAY_CPU_REQUEST=250m
RAILWAY_MEMORY_REQUEST=512Mi
RAILWAY_MAX_REQUEST_CONCURRENCY=10
```

### Vercel Configuration

```bash
# Backend Proxy
TORQ_BACKEND_URL=https://torq-console.up.railway.app
TORQ_PROXY_SHARED_SECRET=xxxxx              # Random secret for proxy auth
TORQ_PROXY_TIMEOUT_MS=25000                  # Proxy timeout

# Feature Flags
TORQ_STREAMING_ENABLED=false                # SSE streaming
TORQ_TELEMETRY_ENABLED=true                 # Metrics collection
```

### Agent Configuration

```bash
# Default Models
ANTHROPIC_MODEL=claude-sonnet-4-20250514    # Default Anthropic model
OPENAI_MODEL=gpt-4-turbo                     # Default OpenAI model
DEFAULT_MODEL=anthropic/claude-sonnet-4-20250514

# Agent Behavior
AGENT_TIMEOUT=300                            # 5 minutes max per agent
AGENT_MAX_RETRIES=3                          # Retry failed requests
AGENT_MAX_HANDOFFS=10                        # Max agent handoffs per query

# Memory System
MEMORY_ENABLED=true                          # Enable persistent memory
MEMORY_MAX_ITEMS=50                          # Items to keep in memory
MEMORY_RETENTION_DAYS=30                     # Days to keep old memories
```

### Orchestration Configuration

```bash
# Orchestration Modes
ORCHESTRATION_DEFAULT_MODE=multi_agent       # single_agent, multi_agent, pipeline, parallel
ORCHESTRATION_MAX_AGENTS=5                   # Max agents in multi-agent mode
ORCHESTRATION_TIMEOUT=300                    # Total timeout

# Routing
ROUTING_ENABLED=true                         # Enable intelligent routing
ROUTING_CONFIDENCE_THRESHOLD=0.5            # Minimum confidence for auto-routing
```

### RL Learning Configuration

```bash
# Reinforcement Learning
RL_ENABLED=true                              # Enable RL learning
RL_EXPLORATION_RATE=0.1                      # Epsilon for epsilon-greedy
RL_LEARNING_RATE=0.001                       # Learning rate for policy updates
RL_REWARD_DECAY=0.95                         # Discount factor
RL_EXPERIENCE_REPLAY_SIZE=1000              # Experience buffer size
```

### Logging Configuration

```bash
# Logging
LOG_LEVEL=INFO                               # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                              # json or text
LOG_TO_FILE=false                            # Enable file logging
LOG_FILE_PATH=/var/log/torq/console.log

# Structured Logging
STRUCTURED_LOGGING=true                      # Enable structured logs
LOG_REQUEST_ID=true                          # Include request IDs
LOG_TIMING=true                              # Include timing information
```

### Telemetry Configuration

```bash
# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.collector.endpoint
OTEL_SERVICE_NAME=torq-console
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer xxxx

# Metrics
TELEMETRY_ENABLED=true
TELEMETRY_ENDPOINT=https://metrics.collector
TELEMETRY_API_KEY=xxxxx
```

### Security Configuration

```bash
# Rate Limiting
RATE_LIMITING_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.vercel.app
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE
CORS_ALLOWED_HEADERS=Content-Type,Authorization

# Security Headers
SECURE_HEADERS_ENABLED=true
CONTENT_SECURITY_POLICY=default-src 'self'
```

## Configuration Files

### railway.toml

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -e ."

[deploy]
startCommand = "python -m uvicorn torq_console.railway_app:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[scale]
minReplicas = 1
maxReplicas = 10
targetMemoryPercent = 80
targetCPUUtilization = 80

[service]
name = "torq-console"
```

### .nixpacks.toml

```toml
[phases.setup]
nixPkgs = ["python311", "gcc", "pkg-config"]

[phases.build]
cmds = ["pip install -e ."]

[start]
cmd = "python -m uvicorn torq_console.railway_app:app --host 0.0.0.0 --port $PORT"

[variables]
PORT = "8000"
PYTHON_VERSION = "3.11"
```

### vercel.json

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "env": {
    "TORQ_CONSOLE_PRODUCTION": "true"
  }
}
```

## Python Configuration

### Agent Config

```python
# config/agents.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class AgentConfig:
    """Configuration for individual agents."""

    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 300
    max_retries: int = 3
    capabilities: Optional[list] = None

    # Memory settings
    memory_enabled: bool = True
    memory_max_items: int = 50

    # Learning settings
    learning_enabled: bool = True
    feedback_enabled: bool = True

    # Tool settings
    tools_enabled: bool = True
    tool_timeout: int = 30

# Default configurations
DEFAULT_AGENTS: Dict[str, AgentConfig] = {
    "prince_flowers": AgentConfig(
        name="Prince Flowers",
        model="anthropic/claude-sonnet-4-20250514",
        temperature=0.7,
        capabilities=[
            "web_search", "research", "analysis",
            "planning", "memory", "learning"
        ]
    ),
    "code_generation": AgentConfig(
        name="Code Generation Specialist",
        model="anthropic/claude-sonnet-4-20250514",
        temperature=0.3,
        capabilities=["code_generation", "documentation"]
    ),
    "debugging": AgentConfig(
        name="Debugging Specialist",
        model="anthropic/claude-sonnet-4-20250514",
        temperature=0.2,
        capabilities=["debugging", "code_analysis"]
    ),
}
```

### Orchestrator Config

```python
# config/orchestrator.py
from dataclasses import dataclass
from enum import Enum

class OrchestrationMode(Enum):
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"

@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""

    default_mode: OrchestrationMode = OrchestrationMode.MULTI_AGENT
    max_agents: int = 5
    timeout: int = 300
    enable_routing: bool = True
    enable_memory: bool = True
    enable_learning: bool = True

    # Parallel execution settings
    max_parallel_tasks: int = 5
    parallel_timeout: int = 120

    # Pipeline settings
    pipeline_stages: list = None
    pipeline_timeout_per_stage: int = 60

    # Multi-agent settings
    multi_agent_voting: bool = False
    multi_agent_consensus_threshold: float = 0.6
```

### Memory Config

```python
# config/memory.py
from dataclasses import dataclass

@dataclass
class MemoryConfig:
    """Configuration for the memory system."""

    # Storage
    storage_type: str = "supabase"  # supabase, redis, memory
    connection_string: str = None
    table_name: str = "agent_memory"

    # Retention
    max_items_per_session: int = 100
    max_sessions: int = 1000
    retention_days: int = 30

    # Retrieval
    default_retrieval_limit: int = 5
    similarity_threshold: float = 0.7
    enable_semantic_search: bool = True

    # Learning
    feedback_enabled: bool = True
    learning_rate: float = 0.1
```

## Runtime Configuration

### Updating Configuration at Runtime

```python
from torq_console.agents import MarvinAgentOrchestrator

# Create with custom config
orchestrator = MarvinAgentOrchestrator(
    model="anthropic/claude-opus-4-20250514",
    memory_enabled=True,
    learning_enabled=False
)

# Update agent config
orchestrator.update_agent_config(
    "prince_flowers",
    temperature=0.5,
    max_tokens=4096
)
```

### Configuration Validation

```python
from torq_console.config import validate_config

# Validate environment variables
is_valid, errors = validate_config()

if not is_valid:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
```

## Configuration Best Practices

1. **Use environment variables** for sensitive data
2. **Use config files** for application settings
3. **Validate configuration** at startup
4. **Provide defaults** for all settings
5. **Document all options** clearly
6. **Use type hints** for config classes
7. **Support hot reload** where possible
8. **Log configuration** at startup (without secrets)
