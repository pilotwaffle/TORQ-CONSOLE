# Troubleshooting Guide

Common issues and solutions for the TORQ Multi-Agent Orchestration System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [API Key Issues](#api-key-issues)
- [Agent Issues](#agent-issues)
- [Memory Issues](#memory-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [Database Issues](#database-issues)

---

## Installation Issues

### Issue: Import Errors

**Symptom:**
```python
ImportError: No module named 'torq_console'
```

**Solution:**
```bash
# Install in development mode
cd TORQ-CONSOLE
pip install -e .

# Or install with extras
pip install -e ".[agents,mcp]"
```

### Issue: Dependency Conflicts

**Symptom:**
```
ERROR: pip's dependency resolver does not currently take into account...
```

**Solution:**
```bash
# Create a fresh virtual environment
python -m venv torq-env
source torq-env/bin/activate  # On Windows: torq-env\Scripts\activate

# Install with pip resolved
pip install --upgrade pip
pip install torq-console
```

### Issue: Marvin Not Found

**Symptom:**
```python
ModuleNotFoundError: No module named 'marvin'
```

**Solution:**
```bash
# Install Marvin with the correct extras
pip install marvin[anthropic]  # For Anthropic
# OR
pip install marvin[openai]     # For OpenAI
```

---

## API Key Issues

### Issue: Invalid API Key

**Symptom:**
```
anthropic.AuthenticationError: Invalid API key
```

**Solution:**
```bash
# Verify the API key is set
echo $ANTHROPIC_API_KEY

# Test the API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Issue: API Key Not Loaded

**Symptom:**
```python
ValueError: No API key found. Please set ANTHROPIC_API_KEY
```

**Solution:**
```python
# Option 1: Set in environment
import os
os.environ['ANTHROPIC_API_KEY'] = 'your-key-here'

# Option 2: Pass directly
from torq_console.marvin_integration import TorqMarvinIntegration
marvin = TorqMarvinIntegration(api_key='your-key-here')

# Option 3: Use .env file
# Create a .env file with: ANTHROPIC_API_KEY=your-key-here
pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
```

### Issue: Rate Limiting

**Symptom:**
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solution:**
```python
# Implement exponential backoff
import time
import asyncio

async def query_with_backoff(agent, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await agent.process_query(query)
        except Exception as e:
            if "rate limit" in str(e).lower():
                wait_time = 2 ** attempt  # 1, 2, 4 seconds
                await asyncio.sleep(wait_time)
            else:
                raise
```

---

## Agent Issues

### Issue: Agent Selection Fails

**Symptom:**
```python
ValueError: No suitable agent found for query
```

**Solution:**
```python
# Specify agent explicitly
from torq_console.agents import MarvinAgentOrchestrator

orchestrator = MarvinAgentOrchestrator()

# Instead of automatic routing, specify agent
result = await orchestrator.process_query(
    query,
    agent_id="prince_flowers"  # Use specific agent
)
```

### Issue: Agent Timeout

**Symptom:**
```
asyncio.TimeoutError: Agent execution timed out
```

**Solution:**
```python
# Increase timeout
import asyncio

from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent

agent = PrinceFlowersAgent()

# Process with custom timeout
result = await asyncio.wait_for(
    agent.process_query(query),
    timeout=600.0  # 10 minutes
)
```

### Issue: Agent Returns Poor Results

**Symptom:**
Agent responses are irrelevant or low quality.

**Solution:**
```python
# Provide more context
result = await agent.process_query(
    "Explain this code",
    context={
        "code": "...",
        "language": "python",
        "expertise_level": "intermediate",
        "focus": "best practices"
    }
)

# Or use more specific agent
from torq_console.agents import get_workflow_agent, WorkflowType

code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
result = await code_agent.generate_code(
    requirements="Explain this Python code...",
    language="python"
)
```

### Issue: Agent Handoff Fails

**Symptom:**
```
Agent handoff failed: Agent 'xxx' not found
```

**Solution:**
```python
# Verify available agents
from torq_console.agents import MarvinAgentOrchestrator

orchestrator = MarvinAgentOrchestrator()
status = await orchestrator.get_status()

print("Available agents:", status['agents_available'])

# Use only available agents
result = await orchestrator.process_query(
    query,
    mode=OrchestrationMode.SINGLE_AGENT  # Avoid handoffs
)
```

---

## Memory Issues

### Issue: Memory Not Persisting

**Symptom:**
```python
Agent memory not found in database
```

**Solution:**
```python
# Check Supabase connection
import os
assert os.getenv('SUPABASE_URL'), "SUPABASE_URL not set"
assert os.getenv('SUPABASE_SERVICE_KEY'), "SUPABASE_SERVICE_KEY not set"

# Test connection
from torq_console.agents import MarvinAgentMemory

memory = MarvinAgentMemory()

# Record test interaction
interaction_id = memory.record_interaction(
    user_input="Test",
    agent_response="Test response",
    agent_name="test",
    interaction_type="general_chat"
)

# Verify retrieval
context = memory.get_context("Test")
assert len(context) > 0, "Memory retrieval failed"
```

### Issue: Memory Retrieval Returns Empty

**Symptom:**
```python
get_context() returns empty list
```

**Solution:**
```python
# Check if memory exists
snapshot = memory.get_memory_snapshot()
print(f"Total interactions: {snapshot['total_interactions']}")

# If 0, record some interactions
# Or lower the similarity threshold
context = memory.get_context(
    query="your query",
    limit=10  # Increase limit
)
```

---

## Performance Issues

### Issue: Slow Response Times

**Symptom:**
Agent responses take >10 seconds.

**Solution:**
```python
# Enable caching
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_query(query: str):
    return await agent.process_query(query)

# Use faster model
from torq_console.marvin_integration import TorqMarvinIntegration

marvin = TorqMarvinIntegration(
    model="anthropic/claude-haiku-4-20250514"  # Faster than Sonnet
)

# Reduce max tokens
agent = MarvinAgentOrchestrator(
    model="anthropic/claude-sonnet-4-20250514",
    max_tokens=1024  # Reduce from 2048
)
```

### Issue: High Memory Usage

**Symptom:**
Process consuming >1GB RAM.

**Solution:**
```python
# Limit memory items
memory = MarvinAgentMemory(max_items=50)  # Default is 50

# Clear old interactions
memory.clear_old_interactions(days=7)

# Disable memory if not needed
orchestrator = MarvinAgentOrchestrator(
    memory_enabled=False
)
```

### Issue: High API Costs

**Symptom:**
Unexpectedly high API usage.

**Solution:**
```python
# Monitor usage
from torq_console.marvin_integration import TorqMarvinIntegration

marvin = TorqMarvinIntegration()
metrics = marvin.get_metrics()
print(metrics)
# {'extractions': 100, 'casts': 50, ...}

# Use cheaper models for simple tasks
# Haiku for simple queries
# Sonnet for complex tasks
# Opus for critical tasks

# Enable caching to reduce redundant calls
```

---

## Deployment Issues

### Issue: Railway Deployment Fails

**Symptom:**
Build fails on Railway.

**Solution:**
```bash
# Check build logs in Railway dashboard

# Verify requirements.txt
cat requirements.txt

# Test locally with same environment
docker build -t torq-console .

# Common fixes:
# 1. Pin Python version: python-version = "3.11"
# 2. Fix requirements.txt versions
# 3. Add missing build dependencies
```

### Issue: Vercel Proxy Errors

**Symptom:**
```
502 Bad Gateway from Railway
```

**Solution:**
```bash
# Check Railway service is running
curl https://your-app.up.railway.app/health

# Verify proxy configuration
echo $TORQ_BACKEND_URL
echo $TORQ_PROXY_SHARED_SECRET

# Test proxy directly
curl -X POST https://your-vercel-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Issue: Database Connection Refused

**Symptom:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```python
# Verify Supabase credentials
import os
import supabase

client = supabase.create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# Test connection
try:
    response = client.table('agent_memory').select('*').limit(1).execute()
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## Database Issues

### Issue: Table Does Not Exist

**Symptom:**
```
relation "agent_memory" does not exist
```

**Solution:**
```sql
-- Run in Supabase SQL Editor
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    user_input TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    success BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Issue: RLS Policy Errors

**Symptom:**
```
ERROR: new row violates row-level security policy
```

**Solution:**
```sql
-- Disable RLS temporarily for testing
ALTER TABLE agent_memory DISABLE ROW LEVEL SECURITY;

-- Or add appropriate policies
CREATE POLICY "Allow all inserts"
ON agent_memory FOR INSERT
WITH CHECK (true);
```

---

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or via environment
# export LOG_LEVEL=DEBUG
```

### Trace Agent Execution

```python
from torq_console.infrastructure.tracing import trace_execution

@trace_execution
async def traced_query(agent, query):
    return await agent.process_query(query)
```

### Health Check

```python
async def health_check():
    """Comprehensive health check."""
    checks = {
        "orchestrator": False,
        "memory": False,
        "database": False,
        "llm": False
    }

    # Check orchestrator
    try:
        from torq_console.agents import MarvinAgentOrchestrator
        orchestrator = MarvinAgentOrchestrator()
        await orchestrator.get_status()
        checks["orchestrator"] = True
    except Exception as e:
        print(f"Orchestrator check failed: {e}")

    # Check memory
    try:
        from torq_console.agents import MarvinAgentMemory
        memory = MarvinAgentMemory()
        memory.get_memory_snapshot()
        checks["memory"] = True
    except Exception as e:
        print(f"Memory check failed: {e}")

    # Check database
    try:
        # Test database connection
        checks["database"] = True
    except Exception as e:
        print(f"Database check failed: {e}")

    # Check LLM
    try:
        from torq_console.marvin_integration import TorqMarvinIntegration
        marvin = TorqMarvinIntegration()
        marvin.run("test", result_type=str)
        checks["llm"] = True
    except Exception as e:
        print(f"LLM check failed: {e}")

    return checks
```

---

## Getting Help

If you're still stuck:

1. **Check the logs** - Enable debug logging
2. **Search issues** - Check GitHub issues
3. **Verify environment** - Run health checks
4. **Test components** - Isolate the failing component
5. **Report bugs** - Include reproducible steps

**Useful Commands:**

```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -i torq

# Run tests
pytest tests/

# Check environment
env | grep TORQ

# Verify API keys
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages
```
