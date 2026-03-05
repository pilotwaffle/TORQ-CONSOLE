# Agent Registry

This document provides a comprehensive registry of all available agents in the TORQ Multi-Agent System, including their capabilities, configuration options, and usage examples.

## Agent Categories

1. **Conversational Agents** - General-purpose dialogue and assistance
2. **Workflow Agents** - Specialized task execution
3. **Swarm Agents** - Collaborative search and analysis
4. **ControlFlow Agents** - Structured, type-safe workflows

---

## Conversational Agents

### Prince Flowers

**ID:** `prince_flowers`
**Location:** `torq_console/agents/prince_flowers_agent.py`
**Status:** Active

#### Description
Prince Flowers is TORQ's primary conversational agent with advanced agentic RL capabilities. It features persistent memory, learning from feedback, and sophisticated query routing.

#### Capabilities
- `web_search` - Real-time web search integration
- `research` - Comprehensive research workflows
- `analysis` - Content analysis and synthesis
- `planning` - Adaptive strategy selection
- `memory` - Conversation memory with retrieval
- `learning` - RL-based performance improvement
- `tool_composition` - Multi-tool workflow orchestration
- `error_recovery` - Graceful error handling

#### Performance Metrics
| Metric | Value |
|--------|-------|
| Avg Response Time | 2.0s |
| Success Rate | 85% |
| Confidence Avg | 78% |
| Tools per Query | 1.5 |

#### Usage Example

```python
from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent

agent = PrinceFlowersAgent()

result = await agent.process_query(
    "What are the latest developments in quantum computing?",
    context={'urgency': 'normal'}
)

print(result.content)
print(f"Strategy: {result.metadata['strategy']}")
print(f"Tools used: {result.tools_used}")
```

#### Configuration
```python
# Environment variables
ANTHROPIC_API_KEY=sk-ant-xxx  # Required for Claude
OPENAI_API_KEY=sk-xxx          # Alternative: GPT models
```

---

## Workflow Agents

### Code Generation Agent

**ID:** `code_generation`
**Type:** `WorkflowType.CODE_GENERATION`
**Location:** `torq_console/agents/marvin_workflow_agents.py`

#### Description
Specializes in generating clean, well-documented code with best practices, error handling, and usage examples.

#### Capabilities
- Multi-language code generation
- Best practices enforcement
- Error handling patterns
- Type hints and documentation
- Usage examples
- Test suggestions

#### Supported Languages
- Python
- JavaScript/TypeScript
- Go
- Rust
- Java
- C#

#### Usage Example

```python
from torq_console.agents import get_workflow_agent, WorkflowType

agent = get_workflow_agent(WorkflowType.CODE_GENERATION)

result = await agent.generate_code(
    requirements="Create a binary search tree with insert, search, and delete operations",
    language="python"
)

print(result.output)
# Returns: Complete code + explanation + examples
```

#### Output Format
```python
WorkflowResult(
    workflow_type=WorkflowType.CODE_GENERATION,
    success=True,
    output="<complete code with documentation>",
    metadata={
        'language': 'python',
        'requirements': 'binary search tree...'
    },
    recommendations=[
        "Review the generated code",
        "Add comprehensive tests",
        "Consider edge cases"
    ]
)
```

---

### Debugging Agent

**ID:** `debugging`
**Type:** `WorkflowType.DEBUGGING`

#### Description
Expert at identifying root causes of bugs and providing fixes with explanations.

#### Capabilities
- Root cause analysis
- Stack trace interpretation
- Fix generation with explanation
- Prevention strategies
- Code improvement suggestions

#### Usage Example

```python
agent = get_workflow_agent(WorkflowType.DEBUGGING)

result = await agent.debug_issue(
    code="""
def divide(a, b):
    return a / b

print(divide(10, 0))
    """,
    error_message="ZeroDivisionError: division by zero",
    language="python"
)

print(result.output)
# Returns: Root cause + fixed code + explanation
```

---

### Documentation Agent

**ID:** `documentation`
**Type:** `WorkflowType.DOCUMENTATION`

#### Description
Generates comprehensive technical documentation for code and APIs.

#### Documentation Types
- `api` - API reference documentation
- `guide` - User guides and tutorials
- `reference` - Technical reference material

#### Usage Example

```python
agent = get_workflow_agent(WorkflowType.DOCUMENTATION)

result = await agent.generate_documentation(
    code="""
def calculate_fibonacci(n):
    '''Calculate the nth Fibonacci number.'''
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
    """,
    doc_type="api",
    language="python"
)

print(result.output)
# Returns: Complete API documentation
```

---

### Testing Agent

**ID:** `testing`
**Type:** `WorkflowType.TESTING`

#### Description
Generates comprehensive test suites with coverage for edge cases and error conditions.

#### Supported Frameworks
- `pytest` (Python)
- `unittest` (Python)
- `jest` (JavaScript)
- `go test` (Go)

#### Usage Example

```python
agent = get_workflow_agent(WorkflowType.TESTING)

result = await agent.generate_tests(
    code="""
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
    """,
    test_framework="pytest",
    language="python"
)

print(result.output)
# Returns: Complete test suite
```

---

### Architecture Agent

**ID:** `architecture`
**Type:** `WorkflowType.ARCHITECTURE`

#### Description
Designs scalable, maintainable software architectures with trade-off analysis.

#### System Types
- `web_application` - Full-stack web applications
- `microservice` - Microservice architectures
- `api` - API design
- `data_pipeline` - Data processing pipelines

#### Usage Example

```python
agent = get_workflow_agent(WorkflowType.ARCHITECTURE)

result = await agent.design_architecture(
    requirements="""
    Build a real-time chat application with:
    - User authentication
    - Room-based chat
    - Message persistence
    - Online status indicators
    """,
    system_type="web_application"
)

print(result.output)
# Returns: Architecture design with components, data flow, tech stack
```

---

### N8N Workflow Architect Agent

**ID:** `n8n_workflow_architect`
**Type:** `WorkflowType.N8N_WORKFLOW_ARCHITECT`
**Location:** `torq_console/agents/n8n_architect_agent.py`

#### Description
Specialized agent for designing, analyzing, and optimizing n8n workflows.

#### Capabilities
- Workflow design from requirements
- Workflow optimization
- Error handling strategies
- Integration patterns
- Workflow documentation

#### Usage Example

```python
from torq_console.agents.n8n_architect_agent import N8NWorkflowArchitectAgent

agent = N8NWorkflowArchitectAgent()

result = await agent.design_workflow(
    requirements="Create a workflow that monitors RSS feeds and posts to Slack",
    context={"nodes": ["RSS Read", "Slack"]}
)

print(result.output)
# Returns: n8n workflow JSON + documentation
```

---

## Swarm Agents

### Search Agent

**ID:** `search_agent`
**Location:** `torq_console/swarm/agents/search_agent.py`

#### Description
Handles web search operations with query enhancement and result processing.

#### Capabilities
- `web_search` - General web search
- `query_enhancement` - AI-powered query refinement
- `information_retrieval` - Structured data extraction
- `context_gathering` - Context-aware search

#### Search Types
- `ai_news_search` - AI/ML news
- `recent_developments` - Time-bounded search
- `general_search` - General web search

#### Usage Example

```python
from torq_console.swarm.orchestrator import SwarmOrchestrator

orchestrator = SwarmOrchestrator(
    llm_manager=llm_manager,
    web_search_provider=search_provider
)

result = await orchestrator.search_ai_news(
    query="latest transformer models"
)

print(result)
```

---

### Analysis Agent

**ID:** `analysis_agent`
**Location:** `torq_console/swarm/agents/analysis_agent.py`

#### Description
Analyzes search results and content to extract insights and themes.

#### Capabilities
- Content quality assessment
- Key theme extraction
- Source credibility evaluation
- Pattern recognition

---

### Synthesis Agent

**ID:** `synthesis_agent`
**Location:** `torq_console/swarm/agents/synthesis_agent.py`

#### Description
Synthesizes analyzed content into coherent responses.

#### Capabilities
- Multi-source synthesis
- Contradiction resolution
- Coherent narrative generation
- Source attribution

---

### Response Agent

**ID:** `response_agent`
**Location:** `torq_console/swarm/agents/response_agent.py`

#### Description
Formats and delivers final responses to users.

#### Capabilities
- Response formatting
- Context injection
- Source citation
- Error handling

---

## ControlFlow Agents

### Web Search Specialist

**ID:** `web_search_specialist`
**Location:** `torq_console/orchestration/agents/base_agents.py`

#### Description
ControlFlow-based agent for web search operations.

#### Capabilities
- Multi-provider search (DuckDuckGo, Brave, SearX)
- Query optimization
- Result quality assessment
- Source verification

#### Creation Example

```python
from torq_console.orchestration.agents.base_agents import create_web_search_agent

agent = create_web_search_agent(
    model="anthropic/claude-sonnet-4-20250514"
)
```

---

### Content Analyst

**ID:** `content_analyst`

#### Description
Analyzes content for quality, themes, and credibility.

#### Capabilities
- Quality assessment
- Theme extraction
- Credibility evaluation
- Gap identification

---

### Research Writer

**ID:** `research_writer`

#### Description
Synthesizes research into comprehensive reports.

#### Capabilities
- Multi-source synthesis
- Report structuring
- Source citation
- Objective presentation

---

### Code Specialist

**ID:** `code_specialist`

#### Description
Handles code analysis, generation, and debugging tasks.

#### Capabilities
- Code review
- Code generation
- Debugging
- Documentation

---

### General Assistant

**ID:** `general_assistant`

#### Description
General-purpose helper for miscellaneous tasks.

#### Capabilities
- Intent understanding
- Task breakdown
- Specialized agent delegation
- Context maintenance

---

## Agent Selection Guide

### By Task Type

| Task | Recommended Agent | Mode |
|------|-------------------|------|
| General conversation | Prince Flowers | Single |
| Code generation | Code Agent | Single |
| Bug fixing | Debugging Agent | Single |
| API documentation | Documentation Agent | Single |
| Test writing | Testing Agent | Single |
| System design | Architecture Agent | Single |
| n8n workflow | N8N Architect | Single |
| Web search | Search Agent | Pipeline |
| Research synthesis | Swarm | Pipeline |
| Multi-step workflow | Marvin Orchestrator | Multi-Agent |

### By Complexity

| Complexity | Agent | Strategy |
|------------|-------|----------|
| Low | Prince Flowers | direct_response |
| Medium | Single Workflow Agent | Specialized processing |
| High | Marvin Orchestrator | multi_agent |
| Very High | Swarm Orchestrator | Full pipeline |

---

## Agent Status Matrix

| Agent | Status | Version | Last Updated |
|-------|--------|---------|--------------|
| Prince Flowers | Active | 1.0.0 | 2025-01-11 |
| Code Generation | Active | 1.0.0 | 2025-01-11 |
| Debugging | Active | 1.0.0 | 2025-01-11 |
| Documentation | Active | 1.0.0 | 2025-01-11 |
| Testing | Active | 1.0.0 | 2025-01-11 |
| Architecture | Active | 1.0.0 | 2025-01-11 |
| N8N Architect | Active | 1.0.0 | 2025-01-11 |
| Search Agent | Active | 1.0.0 | 2025-01-11 |
| Analysis Agent | Active | 1.0.0 | 2025-01-11 |
| Synthesis Agent | Active | 1.0.0 | 2025-01-11 |
| Response Agent | Active | 1.0.0 | 2025-01-11 |

---

## Custom Agent Development

### Creating a Custom Agent

```python
from torq_console.marvin_integration import TorqMarvinIntegration

class CustomAgent:
    def __init__(self, model: str = None):
        self.marvin = TorqMarvinIntegration(model=model)
        self.agent = self.marvin.create_agent(
            name="Custom Specialist",
            instructions="You are a specialist in...",
            model=model
        )

    async def process(self, task: str) -> str:
        return await self.agent.run(task)
```

### Registering a Custom Agent

```python
from torq_console.agents import MarvinAgentOrchestrator

orchestrator = MarvinAgentOrchestrator()

# Add custom agent to registry
orchestrator.register_agent(
    name="custom_agent",
    agent=custom_agent_instance,
    capabilities=["capability1", "capability2"]
)
```
