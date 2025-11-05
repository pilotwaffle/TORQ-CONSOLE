# Marvin Integration Quick Start Guide

## Overview

TORQ Console now features **Marvin 3.0 integration** providing AI-powered specification analysis, intelligent agent routing, and specialized workflow agents.

## Setup

### 1. Install Dependencies

Marvin and dependencies are already installed if you have TORQ Console set up:

```bash
pip install marvin pydantic
```

### 2. Configure API Key

Set your API key for the LLM provider:

```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY=your_key_here

# Or for OpenAI
export OPENAI_API_KEY=your_key_here
```

### 3. Verify Installation

```python
import marvin
print(f"Marvin version: {marvin.__version__}")  # Should be 3.2.3+
```

## Quick Start Examples

### Example 1: Analyze a Specification

```python
import asyncio
from torq_console.spec_kit import marvin_analyze_spec
from torq_console.spec_kit.rl_spec_analyzer import SpecificationContext

async def analyze_spec():
    spec_text = """
    User Authentication System

    Requirements:
    - User registration with email
    - Secure login with JWT
    - Password reset via email

    Tech Stack: Python, FastAPI, PostgreSQL
    """

    context = SpecificationContext(
        domain="authentication",
        tech_stack=["python", "fastapi", "postgresql"],
        project_size="medium",
        team_size=3,
        timeline="4-weeks",
        constraints=["security-critical"]
    )

    result = await marvin_analyze_spec(spec_text, context)

    print(f"Quality Score: {result['quality_score']['overall_score']:.2f}")
    print(f"Quality Level: {result['quality_score']['quality_level']}")
    print(f"Recommendations: {len(result['quality_score']['improvement_suggestions'])}")

asyncio.run(analyze_spec())
```

### Example 2: Route Queries to Agents

```python
import asyncio
from torq_console.agents import create_query_router

async def route_query():
    router = create_query_router()

    routing = await router.route_query(
        "Help me write a function to validate email addresses"
    )

    print(f"Routed to: {routing.primary_agent}")
    print(f"Complexity: {routing.estimated_complexity.value}")
    print(f"Capabilities needed: {routing.capabilities_needed}")

asyncio.run(route_query())
```

### Example 3: Use Enhanced Prince Flowers

```python
import asyncio
from torq_console.agents import create_prince_flowers_agent

async def chat_with_prince():
    agent = create_prince_flowers_agent()

    response = await agent.chat("How do I use async/await in Python?")
    print(response)

    # Get conversation summary
    print(agent.get_conversation_summary())

asyncio.run(chat_with_prince())
```

### Example 4: Generate Code

```python
import asyncio
from torq_console.agents import get_workflow_agent, WorkflowType

async def generate_code():
    agent = get_workflow_agent(WorkflowType.CODE_GENERATION)

    result = await agent.generate_code(
        requirements="Function to validate email addresses",
        language="python"
    )

    if result.success:
        print(result.output)
        print(f"\nRecommendations: {result.recommendations}")

asyncio.run(generate_code())
```

### Example 5: Debug Code

```python
import asyncio
from torq_console.agents import get_workflow_agent, WorkflowType

async def debug_code():
    agent = get_workflow_agent(WorkflowType.DEBUGGING)

    buggy_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
"""

    result = await agent.debug_issue(
        code=buggy_code,
        error_message="ZeroDivisionError: division by zero",
        language="python"
    )

    if result.success:
        print(result.output)

asyncio.run(debug_code())
```

### Example 6: Orchestrate Multiple Agents

```python
import asyncio
from torq_console.agents import get_orchestrator, OrchestrationMode

async def orchestrate():
    orchestrator = get_orchestrator()

    result = await orchestrator.process_query(
        "Generate a sorting function and write tests for it",
        mode=OrchestrationMode.MULTI_AGENT
    )

    print(f"Primary response: {result.primary_response}")
    print(f"Agents used: {result.metadata.get('agents_used')}")

asyncio.run(orchestrate())
```

### Example 7: Use Agent Memory

```python
from torq_console.agents import get_agent_memory, InteractionType

memory = get_agent_memory()

# Record interaction
interaction_id = memory.record_interaction(
    user_input="How do I use decorators?",
    agent_response="Decorators are a way to modify functions...",
    agent_name="prince_flowers",
    interaction_type=InteractionType.GENERAL_CHAT,
    success=True
)

# Add feedback
memory.add_feedback(interaction_id, score=0.9)

# Get snapshot
snapshot = memory.get_memory_snapshot()
print(f"Total interactions: {snapshot.total_interactions}")
print(f"Success rate: {snapshot.success_rate:.2%}")
```

## Available Components

### Phase 1: Foundation
- **TorqMarvinIntegration**: Core integration layer
- **Structured Outputs**: extract, cast, classify, generate
- **Base Agents**: Spec analyzer, code reviewer, research agent

### Phase 2: Spec-Kit Enhancement
- **MarvinSpecAnalyzer**: AI-powered specification analysis
- **MarvinQualityEngine**: Multi-dimensional quality assessment
- **MarvinSpecKitBridge**: Integration with Spec-Kit workflow

### Phase 3: Agent Enhancement
- **MarvinQueryRouter**: Intelligent query routing
- **MarvinPrinceFlowers**: Enhanced conversational agent
- **Workflow Agents**: Code, debugging, docs, testing, architecture
- **MarvinAgentOrchestrator**: Multi-agent coordination
- **MarvinAgentMemory**: Persistent memory and learning

## Common Patterns

### Pattern 1: Specification Quality Check

```python
from torq_console.spec_kit import create_marvin_spec_analyzer

async def check_spec_quality(spec_text):
    analyzer = create_marvin_spec_analyzer()

    # Analyze
    analysis = await analyzer.analyze_specification(spec_text, context)

    # Extract requirements
    requirements = await analyzer.extract_requirements(spec_text)

    # Generate acceptance criteria
    criteria = await analyzer.generate_acceptance_criteria(spec_text)

    return {
        'analysis': analysis,
        'requirements': requirements,
        'criteria': criteria
    }
```

### Pattern 2: Smart Query Handling

```python
from torq_console.agents import get_orchestrator

async def handle_user_query(query):
    orchestrator = get_orchestrator()

    # Orchestrator automatically:
    # 1. Routes to appropriate agent
    # 2. Provides context
    # 3. Records interaction

    result = await orchestrator.process_query(query)
    return result.primary_response
```

### Pattern 3: Code Generation Pipeline

```python
from torq_console.agents import get_workflow_agent, WorkflowType

async def full_code_pipeline(requirements):
    # Generate code
    code_gen = get_workflow_agent(WorkflowType.CODE_GENERATION)
    code_result = await code_gen.generate_code(requirements)

    # Generate tests
    test_gen = get_workflow_agent(WorkflowType.TESTING)
    test_result = await test_gen.generate_tests(code_result.output)

    # Generate docs
    doc_gen = get_workflow_agent(WorkflowType.DOCUMENTATION)
    doc_result = await doc_gen.generate_documentation(code_result.output)

    return {
        'code': code_result.output,
        'tests': test_result.output,
        'docs': doc_result.output
    }
```

## Troubleshooting

### API Key Issues

```python
# Check if API key is set
import os
api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
```

### Import Errors

```python
# If you get import errors, ensure you're importing from correct paths:
from torq_console.marvin_integration import TorqMarvinIntegration  # Phase 1
from torq_console.spec_kit import marvin_analyze_spec             # Phase 2
from torq_console.agents import get_orchestrator                  # Phase 3
```

### Performance

```python
# For better performance, reuse instances:
from torq_console.agents import get_orchestrator

orchestrator = get_orchestrator()  # Singleton
# Use orchestrator multiple times without recreating
```

## Next Steps

1. **Run Examples**: `python examples/marvin_integration_examples.py`
2. **Read Full Docs**: See `CLAUDE.md` for complete documentation
3. **Explore Source**: Browse `torq_console/marvin_integration/`, `torq_console/spec_kit/`, `torq_console/agents/`
4. **Build Your Own**: Use the patterns above to create custom integrations

## Support

- **Documentation**: See `CLAUDE.md` and code docstrings
- **Examples**: Check `examples/` directory
- **Tests**: Review test files for usage patterns

## Version Info

- **Marvin**: 3.2.3
- **TORQ Console**: 0.80.0
- **Phase 1**: Complete (Foundation)
- **Phase 2**: Complete (Spec-Kit)
- **Phase 3**: Complete (Agents)
