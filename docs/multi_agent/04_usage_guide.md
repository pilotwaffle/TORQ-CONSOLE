# Usage Guide

This guide covers practical usage patterns for the TORQ Multi-Agent Orchestration System.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Orchestration Modes](#orchestration-modes)
- [Agent Collaboration](#agent-collaboration)
- [Memory and Learning](#memory-and-learning)
- [Advanced Patterns](#advanced-patterns)

---

## Quick Start

### Installation

```bash
# Install with agent support
pip install torq-console[agents]

# Set your API key
export ANTHROPIC_API_KEY=your_key_here
```

### First Query

```python
import asyncio
from torq_console.agents import MarvinAgentOrchestrator

async def main():
    orchestrator = MarvinAgentOrchestrator()
    result = await orchestrator.process_query(
        "What are the benefits of async programming?"
    )
    print(result.response)

asyncio.run(main())
```

---

## Basic Usage

### Direct Agent Usage

```python
from torq_console.agents.prince_flowers_agent import PrinceFlowersAgent

# Create agent instance
agent = PrinceFlowersAgent()

# Process a query
result = await agent.process_query(
    "Explain the difference between processes and threads"
)

# Access results
print(result.content)
print(f"Confidence: {result.confidence}")
print(f"Strategy: {result.metadata['strategy']}")
print(f"Tools used: {result.tools_used}")
```

### Using Workflow Agents

```python
from torq_console.agents import get_workflow_agent, WorkflowType

# Code Generation
code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
result = await code_agent.generate_code(
    requirements="Create a REST API with FastAPI",
    language="python"
)
print(result.output)

# Debugging
debug_agent = get_workflow_agent(WorkflowType.DEBUGGING)
result = await debug_agent.debug_issue(
    code="def divide(a, b): return a / b",
    error_message="ZeroDivisionError",
    language="python"
)
print(result.output)

# Documentation
doc_agent = get_workflow_agent(WorkflowType.DOCUMENTATION)
result = await doc_agent.generate_documentation(
    code="your code here",
    doc_type="api",
    language="python"
)
print(result.output)
```

---

## Orchestration Modes

### Single Agent Mode

Best for focused, single-domain tasks.

```python
from torq_console.agents import MarvinAgentOrchestrator, OrchestrationMode

orchestrator = MarvinAgentOrchestrator()

result = await orchestrator.process_query(
    "Explain Python decorators",
    mode=OrchestrationMode.SINGLE_AGENT
)

# Automatically selects the best agent
print(result.response)
print(f"Agent used: {result.agent_id}")
```

### Multi-Agent Mode

Best for complex tasks requiring multiple perspectives.

```python
result = await orchestrator.process_query(
    "Research the latest AI developments and create a summary report",
    mode=OrchestrationMode.MULTI_AGENT
)

# Multiple agents collaborate
print(result.response)
print(f"Agents used: {result.agents_used}")
# Output: ['search_agent', 'analysis_agent', 'synthesis_agent', 'writer_agent']
```

### Pipeline Mode

Best for sequential, multi-step workflows.

```python
result = await orchestrator.process_query(
    "Search for information about quantum computing, analyze it, and write a summary",
    mode=OrchestrationMode.PIPELINE
)

# Agents process in sequence
# SearchAgent -> AnalysisAgent -> SynthesisAgent -> ResponseAgent
```

### Parallel Mode

Best for independent subtasks.

```python
result = await orchestrator.process_query(
    "Compare Python, JavaScript, and Go for web development",
    mode=OrchestrationMode.PARALLEL
)

# Multiple agents work in parallel, results are synthesized
```

---

## Agent Collaboration

### Manual Agent Handoff

```python
from torq_console.agents import get_workflow_agent, WorkflowType

# Start with code generation
code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
code_result = await code_agent.generate_code(
    requirements="Create a user authentication system",
    language="python"
)

# Hand off to testing agent
test_agent = get_workflow_agent(WorkflowType.TESTING)
test_result = await test_agent.generate_tests(
    code=code_result.output,
    test_framework="pytest",
    language="python"
)

# Hand off to documentation agent
doc_agent = get_workflow_agent(WorkflowType.DOCUMENTATION)
doc_result = await doc_agent.generate_documentation(
    code=code_result.output,
    doc_type="api",
    language="python"
)
```

### Swarm Orchestrator

```python
from torq_console.swarm.orchestrator import SwarmOrchestrator

orchestrator = SwarmOrchestrator(
    llm_manager=llm_manager,
    web_search_provider=search_provider
)

# Automatic agent handoff chain
result = await orchestrator.search_ai_news(
    query="latest transformer models"
)

# Chain: SearchAgent -> AnalysisAgent -> SynthesisAgent -> ResponseAgent
```

---

## Memory and Learning

### Recording Interactions

```python
from torq_console.agents import MarvinAgentMemory, InteractionType

memory = MarvinAgentMemory()

# Record an interaction
interaction_id = memory.record_interaction(
    user_input="How do I implement JWT authentication?",
    agent_response="JWT implementation requires...",
    agent_name="prince_flowers",
    interaction_type=InteractionType.CODE_HELP,
    success=True
)
```

### Adding Feedback

```python
# Add feedback for learning
memory.add_feedback(
    interaction_id=interaction_id,
    score=0.9,
    feedback="Very helpful, but I needed more code examples"
)
```

### Retrieving Context

```python
# Get relevant context for a new query
context = memory.get_context(
    query="authentication",
    limit=5,
    agent_name="prince_flowers"
)

for item in context:
    print(f"Q: {item['user_input']}")
    print(f"A: {item['agent_response'][:100]}...")
```

### Memory Statistics

```python
snapshot = memory.get_memory_snapshot()
print(f"Total interactions: {snapshot['total_interactions']}")
print(f"Success rate: {snapshot['success_rate']}")
print(f"Feedback received: {snapshot['feedback_received']}")
```

---

## Advanced Patterns

### Custom Agent with Routing

```python
from torq_console.agents import MarvinQueryRouter, MarvinAgentOrchestrator

async def custom_workflow(query: str):
    # First, route the query
    router = MarvinQueryRouter()
    decision = await router.route_query(query)

    print(f"Query type: {decision.query_type}")
    print(f"Best agent: {decision.best_agent}")

    # Then process with the orchestrator
    orchestrator = MarvinAgentOrchestrator()
    result = await orchestrator.process_query(
        query,
        agent_id=decision.best_agent
    )

    return result
```

### Multi-Step Research Workflow

```python
async def research_workflow(topic: str):
    orchestrator = MarvinAgentOrchestrator()

    # Step 1: Search
    search_result = await orchestrator.process_query(
        f"Search for latest information about {topic}",
        mode=OrchestrationMode.SINGLE_AGENT
    )

    # Step 2: Analyze
    analysis_result = await orchestrator.process_query(
        f"Analyze this information: {search_result.response[:500]}...",
        mode=OrchestrationMode.SINGLE_AGENT
    )

    # Step 3: Synthesize
    synthesis_result = await orchestrator.process_query(
        f"Create a comprehensive report about {topic} based on the analysis",
        mode=OrchestrationMode.MULTI_AGENT
    )

    return synthesis_result
```

### Parallel Code Generation and Testing

```python
import asyncio

async def generate_and_test(requirements: str, language: str):
    code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
    test_agent = get_workflow_agent(WorkflowType.TESTING)

    # Generate code
    code_result = await code_agent.generate_code(
        requirements=requirements,
        language=language
    )

    # Generate tests in parallel
    test_result = await test_agent.generate_tests(
        code=code_result.output,
        test_framework="pytest",
        language=language
    )

    return {
        "code": code_result.output,
        "tests": test_result.output
    }
```

### Error Handling with Fallback

```python
async def safe_query(query: str, max_retries: int = 3):
    orchestrator = MarvinAgentOrchestrator()

    for attempt in range(max_retries):
        try:
            result = await orchestrator.process_query(query)
            if result.success:
                return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")

    # Fallback to simpler agent
    return await orchestrator.process_query(
        query,
        agent_id="prince_flowers"
    )
```

### Streaming Responses

```python
async def stream_query(query: str):
    """Stream responses as they're generated."""
    # Note: Streaming requires special setup
    # This is a placeholder for the pattern

    async for chunk in agent.stream_process(query):
        print(chunk, end="", flush=True)
```

---

## Context Management

### Providing Context

```python
# Provide context for better responses
result = await agent.process_query(
    "How do I fix this error?",
    context={
        "error": "ZeroDivisionError",
        "code": "x = 10 / 0",
        "language": "python",
        "previous_attempts": ["Try-catch", "Input validation"]
    }
)
```

### Session Management

```python
class Session:
    def __init__(self):
        self.memory = MarvinAgentMemory()
        self.orchestrator = MarvinAgentOrchestrator()
        self.session_id = str(uuid.uuid4())

    async def chat(self, message: str):
        # Get context from previous messages
        context = self.memory.get_context(message, limit=3)

        # Process query with context
        result = await self.orchestrator.process_query(
            message,
            context={"session_context": context}
        )

        # Record interaction
        self.memory.record_interaction(
            user_input=message,
            agent_response=result.response,
            agent_name=result.agent_id,
            interaction_type=InteractionType.GENERAL_CHAT,
            success=result.success
        )

        return result

# Use session
session = Session()
response1 = await session.chat("What's async/await?")
response2 = await session.chat("Can you give me an example?")
# Session maintains context between messages
```

---

## Performance Optimization

### Caching

```python
from functools import lru_cache

class CachedAgent:
    def __init__(self):
        self.agent = PrinceFlowersAgent()

    @lru_cache(maxsize=128)
    async def cached_query(self, query: str):
        return await self.agent.process_query(query)
```

### Batch Processing

```python
async def batch_process(queries: List[str]):
    orchestrator = MarvinAgentOrchestrator()

    tasks = [
        orchestrator.process_query(q)
        for q in queries
    ]

    results = await asyncio.gather(*tasks)
    return results
```

---

## Troubleshooting

### Common Issues

#### Issue: Agent Selection

```python
# Force a specific agent
result = await orchestrator.process_query(
    query,
    agent_id="code_generation"  # Use this specific agent
)
```

#### Issue: Timeout

```python
# Set custom timeout
result = await asyncio.wait_for(
    orchestrator.process_query(query),
    timeout=30.0  # 30 seconds
)
```

#### Issue: Poor Results

```python
# Provide more context
result = await orchestrator.process_query(
    query,
    context={
        "domain": "python",
        "expertise_level": "intermediate",
        "include_examples": True
    }
)
```

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Now all agent operations will log detailed information
result = await orchestrator.process_query(query)
```

---

## Best Practices

1. **Choose the right orchestration mode** for your task complexity
2. **Provide context** when available for better results
3. **Use memory** for conversational applications
4. **Handle errors gracefully** with fallback strategies
5. **Monitor performance** through status and metrics
6. **Cache results** for frequently asked questions
7. **Batch operations** when processing multiple queries
8. **Validate agent outputs** before using in production
