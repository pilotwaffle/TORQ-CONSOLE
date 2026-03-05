# API Reference

Complete API documentation for the TORQ Multi-Agent Orchestration System.

## Table of Contents

- [Orchestrator API](#orchestrator-api)
- [Agent API](#agent-api)
- [Memory API](#memory-api)
- [Router API](#router-api)
- [Workflow Agent API](#workflow-agent-api)
- [REST API](#rest-api)

---

## Orchestrator API

### MarvinAgentOrchestrator

Main orchestrator for multi-agent coordination.

```python
from torq_console.agents import MarvinAgentOrchestrator, OrchestrationMode
```

#### Constructor

```python
def __init__(
    model: Optional[str] = None,
    memory_enabled: bool = True,
    learning_enabled: bool = True
)
```

**Parameters:**
- `model` (str, optional): LLM model to use (default: "anthropic/claude-sonnet-4-20250514")
- `memory_enabled` (bool): Enable persistent memory (default: True)
- `learning_enabled` (bool): Enable RL learning (default: True)

#### Methods

##### process_query

Process a query with specified orchestration mode.

```python
async def process_query(
    query: str,
    mode: OrchestrationMode = OrchestrationMode.SINGLE_AGENT,
    context: Optional[Dict[str, Any]] = None,
    agent_id: Optional[str] = None
) -> OrchestrationResult
```

**Parameters:**
- `query` (str): The user query to process
- `mode` (OrchestrationMode): Orchestration mode
  - `OrchestrationMode.SINGLE_AGENT` - Use one best agent
  - `OrchestrationMode.MULTI_AGENT` - Collaborative multi-agent
  - `OrchestrationMode.PIPELINE` - Sequential pipeline
  - `OrchestrationMode.PARALLEL` - Parallel execution
- `context` (dict, optional): Additional context
- `agent_id` (str, optional): Specific agent to use

**Returns:** `OrchestrationResult`

```python
@dataclass
class OrchestrationResult:
    success: bool
    response: str
    agent_id: str
    mode: OrchestrationMode
    metadata: Dict[str, Any]
    execution_time: float
    agents_used: List[str]
```

**Example:**

```python
orchestrator = MarvinAgentOrchestrator()

# Single agent mode
result = await orchestrator.process_query(
    "Explain async/await in Python",
    mode=OrchestrationMode.SINGLE_AGENT
)

# Multi-agent mode
result = await orchestrator.process_query(
    "Research AI trends and create a report",
    mode=OrchestrationMode.MULTI_AGENT
)

print(result.response)
print(f"Agents used: {result.agents_used}")
print(f"Execution time: {result.execution_time}s")
```

##### get_status

Get orchestrator status and metrics.

```python
async def get_status() -> Dict[str, Any]
```

**Returns:** Status dictionary

```python
{
    "status": "active",
    "total_queries": 150,
    "success_rate": 0.92,
    "avg_execution_time": 2.3,
    "agents_available": 11,
    "memory_items": 450,
    "learning_enabled": True
}
```

##### register_agent

Register a custom agent.

```python
def register_agent(
    name: str,
    agent: Any,
    capabilities: List[str]
) -> None
```

**Example:**

```python
from torq_console.marvin_integration import TorqMarvinIntegration

marvin = TorqMarvinIntegration()
custom_agent = marvin.create_agent(
    name="Custom Agent",
    instructions="You specialize in..."
)

orchestrator.register_agent(
    name="custom",
    agent=custom_agent,
    capabilities["capability1", "capability2"]
)
```

---

## Agent API

### PrinceFlowersAgent

Main conversational agent.

```python
from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent
```

#### Constructor

```python
def __init__(llm_provider: Optional[BaseLLMProvider] = None)
```

#### Methods

##### process_query

Process a conversational query.

```python
async def process_query(
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> AgentResult
```

**Returns:** `AgentResult`

```python
@dataclass
class AgentResult:
    success: bool
    content: str
    confidence: float
    tools_used: List[str]
    execution_time: float
    metadata: Dict[str, Any]
```

**Example:**

```python
agent = PrinceFlowersAgent()

result = await agent.process_query(
    "What's the difference between REST and GraphQL?",
    context={'domain': 'technology'}
)

print(result.content)
print(f"Confidence: {result.confidence}")
print(f"Strategy: {result.metadata['strategy']}")
```

##### get_status

Get agent status.

```python
def get_status() -> Dict[str, Any]
```

##### health_check

Perform health check.

```python
async def health_check() -> Dict[str, Any]
```

---

## Memory API

### MarvinAgentMemory

Persistent memory and learning system.

```python
from torq_console.agents import MarvinAgentMemory, InteractionType
```

#### Constructor

```python
def __init__(storage_path: Optional[str] = None)
```

#### Methods

##### record_interaction

Record an agent interaction.

```python
def record_interaction(
    user_input: str,
    agent_response: str,
    agent_name: str,
    interaction_type: InteractionType,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

**Parameters:**
- `user_input` (str): User's input
- `agent_response` (str): Agent's response
- `agent_name` (str): Name of the agent
- `interaction_type` (InteractionType): Type of interaction
  - `InteractionType.GENERAL_CHAT`
  - `InteractionType.CODE_HELP`
  - `InteractionType.RESEARCH`
  - `InteractionType.DEBUGGING`
  - `InteractionType.DOCUMENTATION`
- `success` (bool): Whether the interaction was successful
- `metadata` (dict, optional): Additional metadata

**Returns:** Interaction ID (str)

**Example:**

```python
memory = MarvinAgentMemory()

interaction_id = memory.record_interaction(
    user_input="How do I implement JWT?",
    agent_response="JWT implementation requires...",
    agent_name="prince_flowers",
    interaction_type=InteractionType.CODE_HELP,
    success=True
)
```

##### add_feedback

Add feedback for learning.

```python
def add_feedback(
    interaction_id: str,
    score: float,
    feedback: Optional[str] = None
) -> None
```

**Parameters:**
- `interaction_id` (str): ID of interaction
- `score` (float): Score from 0.0 to 1.0
- `feedback` (str, optional): Textual feedback

**Example:**

```python
memory.add_feedback(
    interaction_id=interaction_id,
    score=0.9,
    feedback="Very helpful explanation"
)
```

##### get_context

Get relevant context for a query.

```python
def get_context(
    query: str,
    limit: int = 5,
    agent_name: Optional[str] = None
) -> List[Dict[str, Any]]
```

**Returns:** List of relevant context items

**Example:**

```python
context = memory.get_context(
    query="authentication",
    limit=5,
    agent_name="prince_flowers"
)

for item in context:
    print(f"{item['user_input']} -> {item['agent_response'][:50]}...")
```

##### get_memory_snapshot

Get memory statistics.

```python
def get_memory_snapshot() -> Dict[str, Any]
```

**Returns:** Memory statistics

```python
{
    "total_interactions": 1250,
    "successful_interactions": 1100,
    "success_rate": 0.88,
    "interaction_types": {
        "general_chat": 500,
        "code_help": 400,
        "research": 250,
        "debugging": 100
    },
    "agent_stats": {
        "prince_flowers": 800,
        "code_agent": 300,
        "debug_agent": 150
    },
    "feedback_received": 350,
    "avg_feedback_score": 0.82
}
```

---

## Router API

### MarvinQueryRouter

Intelligent query routing.

```python
from torq_console.agents import MarvinQueryRouter
```

#### Constructor

```python
def __init__(model: Optional[str] = None)
```

#### Methods

##### route_query

Route a query to the best agent.

```python
async def route_query(
    query: str,
    available_agents: Optional[List[str]] = None
) -> RoutingDecision
```

**Returns:** `RoutingDecision`

```python
@dataclass
class RoutingDecision:
    best_agent: str
    confidence: float
    capabilities_needed: List[str]
    reasoning: str
    alternative_agents: List[str]
    query_type: str
    complexity: float
```

**Example:**

```python
router = MarvinQueryRouter()

decision = await router.route_query(
    "Help me debug this Python code"
)

print(f"Best agent: {decision.best_agent}")
print(f"Confidence: {decision.confidence}")
print(f"Reasoning: {decision.reasoning}")
```

##### classify_query

Classify query intent.

```python
async def classify_query(query: str) -> QueryType
```

**Returns:** `QueryType` enum

```python
class QueryType(Enum):
    GENERAL_CHAT = "general_chat"
    CODE_HELP = "code_help"
    RESEARCH = "research"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
```

---

## Workflow Agent API

### Workflow Agents

Specialized agents for specific workflows.

```python
from torq_console.agents import get_workflow_agent, WorkflowType
```

#### get_workflow_agent

Get a workflow agent by type.

```python
def get_workflow_agent(
    workflow_type: WorkflowType,
    model: Optional[str] = None
) -> Union[
    CodeGenerationAgent,
    DebuggingAgent,
    DocumentationAgent,
    TestingAgent,
    ArchitectureAgent
]
```

**Workflow Types:**

```python
class WorkflowType(str, Enum):
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    N8N_WORKFLOW_ARCHITECT = "n8n_workflow_architect"
```

#### CodeGenerationAgent

```python
agent = get_workflow_agent(WorkflowType.CODE_GENERATION)

result = await agent.generate_code(
    requirements="Create a binary search tree",
    language="python",
    context=None
)
```

#### DebuggingAgent

```python
agent = get_workflow_agent(WorkflowType.DEBUGGING)

result = await agent.debug_issue(
    code="buggy code here",
    error_message="ZeroDivisionError",
    language="python",
    context=None
)
```

#### DocumentationAgent

```python
agent = get_workflow_agent(WorkflowType.DOCUMENTATION)

result = await agent.generate_documentation(
    code="code to document",
    doc_type="api",
    language="python",
    context=None
)
```

#### TestingAgent

```python
agent = get_workflow_agent(WorkflowType.TESTING)

result = await agent.generate_tests(
    code="code to test",
    test_framework="pytest",
    language="python",
    context=None
)
```

#### ArchitectureAgent

```python
agent = get_workflow_agent(WorkflowType.ARCHITECTURE)

result = await agent.design_architecture(
    requirements="Build a real-time chat app",
    system_type="web_application",
    context=None
)
```

---

## REST API

### Endpoints

#### POST /api/chat

Chat with agents.

**Request:**

```http
POST /api/chat HTTP/1.1
Content-Type: application/json

{
  "message": "Explain async/await",
  "context": {},
  "mode": "single_agent",
  "model": null
}
```

**Response:**

```json
{
  "response": "Async/await is a syntax for...",
  "agent_id": "prince_flowers",
  "timestamp": "2025-03-04T20:00:00Z",
  "metadata": {
    "backend": "railway",
    "learning_recorded": true,
    "trace_id": "vercel-1234567890"
  }
}
```

#### GET /api/agents

List all available agents.

**Response:**

```json
[
  {
    "id": "prince_flowers",
    "name": "Prince Flowers",
    "description": "TORQ Business Consulting AI",
    "capabilities": [
      "general_chat",
      "market_research",
      "tax_strategy",
      "business_valuation",
      "portfolio_analysis"
    ],
    "status": "active"
  },
  {
    "id": "query_router",
    "name": "Marvin Query Router",
    "description": "Intelligently routes queries",
    "capabilities": [
      "intent_classification",
      "query_analysis",
      "agent_selection"
    ],
    "status": "active"
  }
]
```

#### GET /api/agents/{agent_id}

Get specific agent information.

**Response:**

```json
{
  "id": "prince_flowers",
  "name": "Prince Flowers",
  "description": "TORQ Business Consulting AI",
  "capabilities": ["general_chat", "research", "analysis"],
  "status": "active",
  "performance": {
    "avg_response_time": 2.0,
    "success_rate": 0.85,
    "total_queries": 150
  }
}
```

#### GET /api/status

Get system status.

**Response:**

```json
{
  "status": "healthy",
  "service": "torq-console",
  "version": "0.91.0",
  "platform": "vercel",
  "agents_active": 11,
  "anthropic_configured": true,
  "openai_configured": true,
  "streaming_enabled": false,
  "timestamp": "2025-03-04T20:00:00Z"
}
```

#### POST /api/sessions

Create a new session.

**Request:**

```http
POST /api/sessions HTTP/1.1
Content-Type: application/json

{
  "agent_id": "prince_flowers"
}
```

**Response:**

```json
{
  "session_id": "vercel-20250304200000",
  "created_at": "2025-03-04T20:00:00Z",
  "agent_id": "prince_flowers",
  "message_count": 0,
  "status": "active"
}
```

#### GET /api/sessions

List sessions.

**Response:**

```json
[
  {
    "session_id": "vercel-20250304200000",
    "agent_id": "prince_flowers",
    "created_at": "2025-03-04T20:00:00Z",
    "message_count": 5
  }
]
```

#### GET /api/traces

List execution traces.

**Query Parameters:**
- `limit` (int): Max traces to return
- `agent_id` (str): Filter by agent
- `status` (str): Filter by status

**Response:**

```json
{
  "traces": [
    {
      "trace_id": "trace-123",
      "agent_id": "prince_flowers",
      "query": "Explain async/await",
      "status": "success",
      "duration_ms": 1234,
      "timestamp": "2025-03-04T20:00:00Z"
    }
  ],
  "total": 150
}
```

#### GET /api/traces/{trace_id}

Get trace details.

**Response:**

```json
{
  "trace_id": "trace-123",
  "agent_id": "prince_flowers",
  "query": "Explain async/await",
  "response": "Async/await is...",
  "status": "success",
  "duration_ms": 1234,
  "metadata": {
    "strategy": "direct_response",
    "tools_used": ["synthesizer"]
  },
  "spans": [
    {
      "span_id": "span-1",
      "name": "query_analysis",
      "duration_ms": 50
    }
  ]
}
```

---

## Error Handling

All API methods follow this error handling pattern:

```python
try:
    result = await agent.process_query(query)
    if result.success:
        print(result.content)
    else:
        print(f"Failed: {result.metadata.get('error')}")
except Exception as e:
    print(f"Error: {e}")
```

### Error Response Format

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {},
  "request_id": "uuid"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `AGENT_NOT_FOUND` | Specified agent not available |
| `INVALID_MODE` | Invalid orchestration mode |
| `TIMEOUT` | Operation timed out |
| `RATE_LIMITED` | Rate limit exceeded |
| `API_KEY_ERROR` | Missing or invalid API key |
