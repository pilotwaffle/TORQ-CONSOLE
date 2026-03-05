# Architecture Overview

## System Architecture

The TORQ Multi-Agent Orchestration System is built on a layered architecture that provides flexibility, scalability, and intelligence in agent coordination.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WebApp[Web Application]
        CLI[CLI Interface]
        API[REST API]
    end

    subgraph "Orchestration Layer"
        QueryRouter[Query Router]
        MarvinOrchestrator[Marvin Orchestrator]
        SwarmOrchestrator[Swarm Orchestrator]
        ControlFlowInt[ControlFlow Integration]
    end

    subgraph "Agent Layer"
        PrinceFlowers[Prince Flowers]
        CodeAgent[Code Generation Agent]
        DebugAgent[Debugging Agent]
        DocAgent[Documentation Agent]
        TestAgent[Testing Agent]
        ArchAgent[Architecture Agent]
        N8NAgent[N8N Architect Agent]
        SearchAgent[Search Agent]
        AnalysisAgent[Analysis Agent]
        SynthesisAgent[Synthesis Agent]
        ResponseAgent[Response Agent]
    end

    subgraph "Capability Layer"
        LLMProviders[LLM Providers]
        WebSearch[Web Search]
        MemorySystem[Memory System]
        RLSystem[RL Learning System]
        ToolRegistry[Tool Registry]
    end

    subgraph "Infrastructure Layer"
        Supabase[(Supabase)]
        Railway[Railway Backend]
        Vercel[Vercel Frontend]
    end

    WebApp --> QueryRouter
    CLI --> QueryRouter
    API --> QueryRouter

    QueryRouter --> MarvinOrchestrator
    QueryRouter --> SwarmOrchestrator
    QueryRouter --> ControlFlowInt
    QueryRouter --> PrinceFlowers

    MarvinOrchestrator --> CodeAgent
    MarvinOrchestrator --> DebugAgent
    MarvinOrchestrator --> DocAgent
    MarvinOrchestrator --> TestAgent
    MarvinOrchestrator --> ArchAgent
    MarvinOrchestrator --> N8NAgent

    SwarmOrchestrator --> SearchAgent
    SwarmOrchestrator --> AnalysisAgent
    SwarmOrchestrator --> SynthesisAgent
    SwarmOrchestrator --> ResponseAgent

    ControlFlowInt --> WebSearch
    ControlFlowInt --> AnalysisAgent

    CodeAgent --> LLMProviders
    DebugAgent --> LLMProviders
    DocAgent --> LLMProviders
    TestAgent --> LLMProviders
    ArchAgent --> LLMProviders
    N8NAgent --> LLMProviders
    SearchAgent --> WebSearch
    AnalysisAgent --> LLMProviders
    SynthesisAgent --> LLMProviders
    ResponseAgent --> LLMProviders

    PrinceFlowers --> MemorySystem
    MarvinOrchestrator --> MemorySystem
    SwarmOrchestrator --> MemorySystem

    PrinceFlowers --> RLSystem
    MarvinOrchestrator --> ToolRegistry

    MemorySystem --> Supabase
    LLMProviders --> Railway
    WebSearch --> Railway
```

## Core Components

### 1. Query Router

The Query Router is the entry point for all agent requests. It uses AI-powered intent classification to determine the best agent or orchestrator for each request.

**Location:** `torq_console/agents/marvin_query_router.py`

**Key Responsibilities:**
- Intent classification
- Agent selection based on capabilities
- Routing decision logging
- Performance tracking

**Configuration:**
```python
from torq_console.agents import MarvinQueryRouter

router = MarvinQueryRouter(model="anthropic/claude-sonnet-4-20250514")

# Route a query
routing = await router.route_query("Help me debug this Python code")
# Returns: RoutingDecision with best_agent, capabilities, confidence
```

### 2. Marvin Orchestrator

The Marvin Orchestrator provides sophisticated multi-agent coordination using Marvin 3.0's agentic workflow capabilities.

**Location:** `torq_console/agents/marvin_orchestrator.py`

**Orchestration Modes:**

| Mode | Description | Use Case |
|------|-------------|----------|
| `SINGLE_AGENT` | Direct processing by one agent | Simple, focused tasks |
| `MULTI_AGENT` | Collaborative processing | Complex tasks requiring multiple perspectives |
| `PIPELINE` | Sequential processing | Multi-step workflows |
| `PARALLEL` | Concurrent execution | Independent subtasks |

**Architecture:**

```mermaid
graph LR
    Input[Input Query] --> ModeSelector{Mode Selection}

    ModeSelector -->|Single| SingleAgent[Single Agent]
    ModeSelector -->|Multi| MultiAgent[Multi Agent Coordination]
    ModeSelector -->|Pipeline| Pipeline[Sequential Pipeline]
    ModeSelector -->|Parallel| Parallel[Parallel Execution]

    SingleAgent --> Output[Final Response]

    MultiAgent --> Agent1[Agent 1]
    MultiAgent --> Agent2[Agent 2]
    MultiAgent --> Agent3[Agent 3]
    Agent1 --> Synthesize[Synthesize Results]
    Agent2 --> Synthesize
    Agent3 --> Synthesize
    Synthesize --> Output

    Pipeline --> P1[Stage 1]
    P1 --> P2[Stage 2]
    P2 --> P3[Stage 3]
    P3 --> Output

    Parallel --> Par1[Parallel Task 1]
    Parallel --> Par2[Parallel Task 2]
    Parallel --> Par3[Parallel Task 3]
    Par1 --> Gather[Gather & Merge]
    Par2 --> Gather
    Par3 --> Gather
    Gather --> Output
```

### 3. Swarm Orchestrator

The Swarm Orchestrator implements swarm intelligence patterns for coordinated agent behavior, inspired by natural swarm systems and OpenAI Swarm.

**Location:** `torq_console/swarm/orchestrator.py`

**Agent Chain:**

```mermaid
graph LR
    Start[Task] --> Search[Search Agent]
    Search -->|Search Results| Analysis[Analysis Agent]
    Analysis -->|Analyzed Data| Synthesis[Synthesis Agent]
    Synthesis -->|Synthesized Content| Response[Response Agent]
    Response -->|Final Response| End[End]
```

**Key Features:**
- Natural agent handoffs
- Graceful degradation
- Timeout protection
- Execution history tracking

### 4. ControlFlow Integration

The ControlFlow Integration provides structured, type-safe agent orchestration using the ControlFlow framework.

**Location:** `torq_console/orchestration/integration.py`

**Available Agents:**
- Web Search Specialist
- Content Analyst
- Research Writer
- Code Specialist
- General Assistant

## Agent Memory System

The Agent Memory System provides persistent storage and retrieval of agent interactions, enabling context-aware responses and learning from feedback.

```mermaid
graph TB
    subgraph "Memory System"
        InteractionHistory[Interaction History]
        UserPreferences[User Preferences]
        Patterns[Learned Patterns]
        Feedback[Feedback Storage]
    end

    subgraph "Memory Operations"
        Record[Record Interaction]
        Retrieve[Retrieve Context]
        Learn[Learn from Feedback]
        Update[Update Preferences]
    end

    InteractionHistory --> Record
    UserPreferences --> Retrieve
    Patterns --> Learn
    Feedback --> Update

    Record --> Supabase[(Supabase)]
    Retrieve --> Supabase
    Learn --> Supabase
    Update --> Supabase
```

**Memory API:**

```python
from torq_console.agents import MarvinAgentMemory

memory = MarvinAgentMemory()

# Record an interaction
interaction_id = memory.record_interaction(
    user_input="How do I implement JWT?",
    agent_response="JWT implementation involves...",
    agent_name="prince_flowers",
    interaction_type="code_help",
    success=True
)

# Add feedback for learning
memory.add_feedback(interaction_id, score=0.9, feedback="Very helpful")

# Get context for new queries
context = memory.get_context("authentication", limit=5)
```

## RL Learning System

The Reinforcement Learning system enables agents to improve their performance through experience.

**Location:** `torq_console/agents/rl_learning_system.py`

**Components:**

| Component | Description |
|-----------|-------------|
| State Representation | Encodes query context and history |
| Action Space | Agent and strategy selections |
| Reward Function | Success/failure signals |
| Policy Network | Learns optimal decisions |

**Learning Flow:**

```mermaid
graph TB
    Query[User Query] --> State[State Representation]
    State --> Policy[Policy Network]
    Policy --> Action[Action Selection]
    Action --> Execution[Agent Execution]
    Execution --> Reward{Success?}
    Reward -->|Yes| Positive[Positive Reward]
    Reward -->|No| Negative[Negative Reward]
    Positive --> Update[Update Policy]
    Negative --> Update
    Update --> Policy
```

## Tool Registry

The Tool Registry manages available tools that agents can use to extend their capabilities.

```mermaid
graph TB
    ToolRegistry[Tool Registry]

    subgraph "Web Tools"
        WebSearch[Web Search]
        WebFetch[Web Fetch]
        Tavily[Tavily Search]
        Brave[Brave Search]
    end

    subgraph "Code Tools"
        Execute[Execute Code]
        Analyze[Analyze Code]
        Format[Format Code]
    end

    subgraph "System Tools"
        FileSystem[File System]
        Terminal[Terminal]
        Browser[Browser Automation]
    end

    ToolRegistry --> WebTools
    ToolRegistry --> CodeTools
    ToolRegistry --> SystemTools
```

## Communication Patterns

### Agent Handoff

```mermaid
sequenceDiagram
    participant User
    participant Router
    participant Agent1
    participant Agent2
    participant Memory

    User->>Router: Query
    Router->>Agent1: Forward with context
    Agent1->>Memory: Retrieve context
    Memory-->>Agent1: Context data
    Agent1->>Router: Handoff with partial result
    Router->>Agent2: Forward with context + partial
    Agent2->>Agent2: Complete task
    Agent2-->>Router: Final result
    Router-->>User: Response
```

### Multi-Agent Collaboration

```mermaid
sequenceDiagram
    participant Orchestrator
    participant Agent1
    participant Agent2
    participant Agent3
    participant Synthesizer

    Orchestrator->>Agent1: Subtask 1
    Orchestrator->>Agent2: Subtask 2
    Orchestrator->>Agent3: Subtask 3

    par Parallel Execution
        Agent1-->>Orchestrator: Result 1
        Agent2-->>Orchestrator: Result 2
        Agent3-->>Orchestrator: Result 3
    end

    Orchestrator->>Synthesizer: All results
    Synthesizer-->>Orchestrator: Synthesized response
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Vercel (Frontend)"
        WebUI[Web UI]
        ProxyAPI[Proxy API]
    end

    subgraph "Railway (Backend)"
        AgentService[Agent Service]
        MarvinService[Marvin Service]
        SwarmService[Swarm Service]
    end

    subgraph "Supabase (Database)"
        AgentMemory[(Agent Memory)]
        UserPrefs[(User Preferences)]
        Interactions[(Interactions)]
    end

    subgraph "External Services"
        Anthropic[Anthropic API]
        OpenAI[OpenAI API]
        Brave[Brave Search]
    end

    WebUI --> ProxyAPI
    ProxyAPI --> AgentService
    AgentService --> MarvinService
    AgentService --> SwarmService
    AgentService --> Supabase
    MarvinService --> Anthropic
    MarvinService --> OpenAI
    SwarmService --> Brave
```

## Performance Considerations

### Caching Strategy
- LLM responses cached by semantic hash
- Search results cached for 5 minutes
- Agent capabilities cached in memory

### Concurrency
- Multi-agent mode uses asyncio for parallel execution
- Maximum 10 concurrent agent operations
- Timeout protection (5 minutes per task)

### Scaling
- Stateless agent design enables horizontal scaling
- Connection pooling for external APIs
- Rate limiting to prevent API exhaustion
