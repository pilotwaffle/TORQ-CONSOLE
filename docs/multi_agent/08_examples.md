# Code Examples

Practical examples for common tasks with the TORQ Multi-Agent System.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Agent Collaboration](#agent-collaboration)
- [Web Search Workflows](#web-search-workflows)
- [Code Workflows](#code-workflows)
- [Memory and Context](#memory-and-context)
- [Custom Agents](#custom-agents)
- [Error Handling](#error-handling)

---

## Basic Usage

### Simple Query

```python
from torq_console.agents import MarvinAgentOrchestrator

orchestrator = MarvinAgentOrchestrator()
result = await orchestrator.process_query("What is async/await?")
print(result.response)
```

### With Context

```python
result = await orchestrator.process_query(
    "How do I fix this?",
    context={
        "error": "ZeroDivisionError: division by zero",
        "code": "result = x / y",
        "language": "python"
    }
)
```

### Specific Agent

```python
from torq_console.agents import get_workflow_agent, WorkflowType

code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
result = await code_agent.generate_code(
    requirements="Create a REST API with FastAPI",
    language="python"
)
print(result.output)
```

---

## Agent Collaboration

### Multi-Agent Research

```python
async def research_topic(topic: str):
    """Research a topic using multiple agents."""
    orchestrator = MarvinAgentOrchestrator()

    # Multi-agent mode for complex research
    result = await orchestrator.process_query(
        f"Research {topic} and create a comprehensive report",
        mode=OrchestrationMode.MULTI_AGENT
    )

    print(f"Agents used: {result.agents_used}")
    print(f"Response:\n{result.response}")
    return result
```

### Pipeline Workflow

```python
async def pipeline_workflow(query: str):
    """Execute a sequential pipeline of agents."""
    orchestrator = MarvinAgentOrchestrator()

    result = await orchestrator.process_query(
        query,
        mode=OrchestrationMode.PIPELINE
    )

    # Pipeline: Search -> Analyze -> Synthesize -> Response
    return result
```

### Parallel Processing

```python
async def parallel_analysis(topics: list[str]):
    """Analyze multiple topics in parallel."""
    orchestrator = MarvinAgentOrchestrator()

    tasks = [
        orchestrator.process_query(
            f"Analyze {topic}",
            mode=OrchestrationMode.SINGLE_AGENT
        )
        for topic in topics
    ]

    results = await asyncio.gather(*tasks)
    return results
```

---

## Web Search Workflows

### Basic Web Search

```python
from torq_console.swarm.orchestrator import SwarmOrchestrator

orchestrator = SwarmOrchestrator(
    llm_manager=llm_manager,
    web_search_provider=search_provider
)

result = await orchestrator.general_search(
    "latest developments in AI"
)
print(result)
```

### AI News Search

```python
result = await orchestrator.search_ai_news(
    "GPT-5 release rumors"
)
```

### Recent Developments

```python
result = await orchestrator.search_recent_developments(
    topic="quantum computing",
    days=7
)
```

---

## Code Workflows

### Generate Code

```python
code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)

result = await code_agent.generate_code(
    requirements="""
    Create a binary search tree with:
    - Insert method
    - Search method
    - Delete method
    - In-order traversal
    """,
    language="python"
)

print(result.output)
```

### Debug Code

```python
debug_agent = get_workflow_agent(WorkflowType.DEBUGGING)

result = await debug_agent.debug_issue(
    code="""
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

print(calculate_average([]))
    """,
    error_message="ZeroDivisionError: division by zero",
    language="python"
)

print(result.output)
```

### Generate Documentation

```python
doc_agent = get_workflow_agent(WorkflowType.DOCUMENTATION)

result = await doc_agent.generate_documentation(
    code="""
def fibonacci(n):
    '''Calculate the nth Fibonacci number.'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """,
    doc_type="api",
    language="python"
)

print(result.output)
```

### Generate Tests

```python
test_agent = get_workflow_agent(WorkflowType.TESTING)

result = await test_agent.generate_tests(
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
```

### Architecture Design

```python
arch_agent = get_workflow_agent(WorkflowType.ARCHITECTURE)

result = await arch_agent.design_architecture(
    requirements="""
    Design a real-time chat application with:
    - User authentication
    - Room-based chat
    - Message persistence
    - Online status
    - Typing indicators
    """,
    system_type="web_application"
)

print(result.output)
```

---

## Memory and Context

### Record Interaction

```python
from torq_console.agents import MarvinAgentMemory, InteractionType

memory = MarvinAgentMemory()

interaction_id = memory.record_interaction(
    user_input="How do I implement JWT?",
    agent_response="JWT requires a secret key...",
    agent_name="prince_flowers",
    interaction_type=InteractionType.CODE_HELP,
    success=True
)
```

### Add Feedback

```python
memory.add_feedback(
    interaction_id=interaction_id,
    score=0.9,
    feedback="Very helpful explanation"
)
```

### Get Context

```python
context = memory.get_context(
    query="authentication",
    limit=5,
    agent_name="prince_flowers"
)

for item in context:
    print(f"Q: {item['user_input']}")
    print(f"A: {item['agent_response'][:100]}...")
```

### Conversation Session

```python
class ConversationSession:
    def __init__(self):
        self.memory = MarvinAgentMemory()
        self.orchestrator = MarvinAgentOrchestrator()
        self.session_id = str(uuid.uuid4())

    async def chat(self, message: str) -> str:
        # Get relevant context
        context = self.memory.get_context(message, limit=3)

        # Process with context
        result = await self.orchestrator.process_query(
            message,
            context={"history": context}
        )

        # Record interaction
        self.memory.record_interaction(
            user_input=message,
            agent_response=result.response,
            agent_name=result.agent_id,
            interaction_type=InteractionType.GENERAL_CHAT,
            success=result.success
        )

        return result.response

# Use
session = ConversationSession()
response1 = await session.chat("What's a REST API?")
response2 = await session.chat("Can you give me an example?")
```

---

## Custom Agents

### Create Custom Agent

```python
from torq_console.marvin_integration import TorqMarvinIntegration

class CustomAgent:
    def __init__(self, specialty: str):
        self.marvin = TorqMarvinIntegration()
        self.agent = self.marvin.create_agent(
            name=f"{specialty} Specialist",
            instructions=f"""
            You are a specialist in {specialty}.
            Provide expert-level assistance in this domain.
            """,
            model="anthropic/claude-sonnet-4-20250514"
        )

    async def assist(self, query: str) -> str:
        return await self.agent.run(query)
```

### Register Custom Agent

```python
from torq_console.agents import MarvinAgentOrchestrator

# Create orchestrator
orchestrator = MarvinAgentOrchestrator()

# Create custom agent
custom_agent = CustomAgent("blockchain development")

# Register with orchestrator
orchestrator.register_agent(
    name="blockchain_specialist",
    agent=custom_agent,
    capabilities=["blockchain", "smart_contracts", "web3"]
)
```

### Use Custom Agent

```python
result = await orchestrator.process_query(
    "How do I create a smart contract?",
    agent_id="blockchain_specialist"
)
```

---

## Error Handling

### Basic Error Handling

```python
try:
    result = await agent.process_query(query)
    if result.success:
        print(result.content)
    else:
        print(f"Agent failed: {result.metadata.get('error')}")
except Exception as e:
    print(f"Error: {e}")
```

### Retry with Backoff

```python
async def query_with_retry(agent, query, max_retries=3):
    """Query with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await agent.process_query(query)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"Retry {attempt + 1} after {wait_time}s")
            await asyncio.sleep(wait_time)
```

### Fallback Strategy

```python
async def safe_query(query: str):
    """Query with fallback options."""
    try:
        # Try primary agent
        return await agent.process_query(query)
    except Exception as e:
        print(f"Primary failed: {e}")
        try:
            # Fallback to simpler agent
            simple_agent = PrinceFlowersAgent()
            return await simple_agent.process_query(query)
        except Exception as e2:
            print(f"Fallback failed: {e2}")
            return {"success": False, "error": str(e2)}
```

---

## Advanced Examples

### Multi-Step Code Generation

```python
async def complete_code_workflow(requirements: str):
    """Generate code, tests, and documentation."""
    code_agent = get_workflow_agent(WorkflowType.CODE_GENERATION)
    test_agent = get_workflow_agent(WorkflowType.TESTING)
    doc_agent = get_workflow_agent(WorkflowType.DOCUMENTATION)

    # Generate code
    code_result = await code_agent.generate_code(
        requirements=requirements,
        language="python"
    )

    # Generate tests
    test_result = await test_agent.generate_tests(
        code=code_result.output,
        test_framework="pytest",
        language="python"
    )

    # Generate documentation
    doc_result = await doc_agent.generate_documentation(
        code=code_result.output,
        doc_type="api",
        language="python"
    )

    return {
        "code": code_result.output,
        "tests": test_result.output,
        "docs": doc_result.output
    }
```

### Research and Report

```python
async def research_and_report(topic: str):
    """Research a topic and create a report."""
    orchestrator = MarvinAgentOrchestrator()

    # Step 1: Research
    research = await orchestrator.process_query(
        f"Search for latest information about {topic}",
        mode=OrchestrationMode.SINGLE_AGENT
    )

    # Step 2: Analyze
    analysis = await orchestrator.process_query(
        f"Analyze this research: {research.response[:1000]}...",
        mode=OrchestrationMode.SINGLE_AGENT
    )

    # Step 3: Create report
    report = await orchestrator.process_query(
        f"Create a comprehensive report about {topic} based on the analysis",
        mode=OrchestrationMode.MULTI_AGENT
    )

    return report.response
```

### Batch Processing

```python
async def batch_process(queries: list[str]):
    """Process multiple queries in batch."""
    orchestrator = MarvinAgentOrchestrator()

    # Create tasks
    tasks = [
        orchestrator.process_query(q)
        for q in queries
    ]

    # Execute in parallel with rate limiting
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

    async def bounded_query(query):
        async with semaphore:
            return await orchestrator.process_query(query)

    tasks = [bounded_query(q) for q in queries]
    results = await asyncio.gather(*tasks)

    return results
```

### Streaming Response

```python
async def stream_response(agent, query: str):
    """Stream agent response as it generates."""
    # Note: This requires special setup
    async for chunk in agent.stream_process(query):
        print(chunk, end="", flush=True)
```

---

## CLI Examples

### Command Line

```bash
# Basic query
torq-console agent query "Explain async/await"

# Code generation
torq-console agent code "Create a REST API" --language python

# Debugging
torq-console agent debug "code here" "error message" --language python

# Documentation
torq-console agent docs "code here" --type api --language python

# Architecture
torq-console agent arch "Design a chat app" --type web_application
```

### Python API

```python
# All the above examples work with the Python API
# Just import and use the classes directly
```
