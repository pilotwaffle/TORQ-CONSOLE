"""
Marvin Integration Examples for TORQ Console

Practical examples showing how to use Marvin-powered features:
- Specification analysis
- Query routing
- Agent orchestration
- Code generation
- Memory and learning
"""

import asyncio
from pathlib import Path


# Example 1: Specification Analysis with Marvin
async def example_spec_analysis():
    """
    Example: Analyze a specification using Marvin-powered analyzer.
    """
    print("\n" + "=" * 70)
    print("Example 1: Specification Analysis")
    print("=" * 70)

    from torq_console.spec_kit import marvin_analyze_spec
    from torq_console.spec_kit.rl_spec_analyzer import SpecificationContext

    # Sample specification
    spec_text = """
    User Authentication System

    Requirements:
    - Users can register with email and password
    - Users can login securely with JWT tokens
    - Password reset functionality via email
    - Multi-factor authentication (MFA) support
    - Session management with automatic expiry

    Acceptance Criteria:
    - All passwords must be hashed with bcrypt
    - Sessions expire after 24 hours of inactivity
    - MFA codes expire after 5 minutes
    - Email verification required for new accounts

    Tech Stack:
    - Python FastAPI backend
    - PostgreSQL database
    - Redis for session storage
    - SendGrid for email
    """

    # Create context
    context = SpecificationContext(
        domain="authentication",
        tech_stack=["python", "fastapi", "postgresql", "redis", "sendgrid"],
        project_size="medium",
        team_size=3,
        timeline="6-weeks",
        constraints=["security-critical", "GDPR-compliance"]
    )

    print("\nAnalyzing specification...")

    try:
        # Analyze with Marvin (requires API key)
        result = await marvin_analyze_spec(spec_text, context)

        print("\n✓ Analysis Complete!")
        print(f"  Quality Score: {result['quality_score']['overall_score']:.2f}")
        print(f"  Quality Level: {result['quality_score']['quality_level']}")
        print(f"  Recommendations: {len(result['quality_score']['improvement_suggestions'])}")
        print(f"  Extracted Requirements: {len(result['extracted_requirements'])}")

    except Exception as e:
        print(f"\n⚠ Analysis requires API key: {type(e).__name__}")
        print("  Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")


# Example 2: Query Routing
async def example_query_routing():
    """
    Example: Route queries to appropriate agents.
    """
    print("\n" + "=" * 70)
    print("Example 2: Intelligent Query Routing")
    print("=" * 70)

    from torq_console.agents import create_query_router

    router = create_query_router()

    # Sample queries
    queries = [
        "Help me write a function to parse JSON",
        "Review this code for security issues",
        "Research best practices for API design",
        "Create a task plan for user authentication feature",
    ]

    print("\nRouting queries...")

    for query in queries:
        try:
            routing = await router.route_query(query)
            print(f"\n  Query: {query[:50]}...")
            print(f"  → Routed to: {routing.primary_agent}")
            print(f"    Complexity: {routing.estimated_complexity.value}")
            print(f"    Capabilities: {', '.join(c.value for c in routing.capabilities_needed[:2])}")

        except Exception as e:
            print(f"\n  Query: {query[:50]}...")
            print(f"  ⚠ Routing requires API key: {type(e).__name__}")
            break


# Example 3: Enhanced Prince Flowers Agent
async def example_prince_flowers():
    """
    Example: Use enhanced Prince Flowers for conversation.
    """
    print("\n" + "=" * 70)
    print("Example 3: Enhanced Prince Flowers Agent")
    print("=" * 70)

    from torq_console.agents import create_prince_flowers_agent

    agent = create_prince_flowers_agent(personality="helpful and enthusiastic")

    # Sample conversation
    messages = [
        "Hi! Can you help me with Python?",
        "How do I read a CSV file?",
        "What about error handling?",
    ]

    print("\nConversation with Prince Flowers...")

    for msg in messages:
        try:
            response = await agent.chat(msg)
            print(f"\n  User: {msg}")
            print(f"  Prince Flowers: {response[:100]}...")

        except Exception as e:
            print(f"\n  User: {msg}")
            print(f"  ⚠ Chat requires API key: {type(e).__name__}")
            break

    # Show conversation summary
    print(f"\n  Conversation Summary: {agent.get_conversation_summary()}")


# Example 4: Specialized Workflow Agents
async def example_workflow_agents():
    """
    Example: Use specialized agents for specific tasks.
    """
    print("\n" + "=" * 70)
    print("Example 4: Specialized Workflow Agents")
    print("=" * 70)

    from torq_console.agents import get_workflow_agent, WorkflowType

    # Code Generation
    print("\n4a. Code Generation Agent")
    code_gen = get_workflow_agent(WorkflowType.CODE_GENERATION)

    try:
        result = await code_gen.generate_code(
            requirements="Function to validate email addresses using regex",
            language="python"
        )
        print(f"  ✓ Generated code")
        print(f"    Success: {result.success}")
        print(f"    Recommendations: {len(result.recommendations)}")

    except Exception as e:
        print(f"  ⚠ Requires API key: {type(e).__name__}")

    # Debugging
    print("\n4b. Debugging Agent")
    debugger = get_workflow_agent(WorkflowType.DEBUGGING)

    buggy_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
"""

    try:
        result = await debugger.debug_issue(
            code=buggy_code,
            error_message="ZeroDivisionError: division by zero",
            language="python"
        )
        print(f"  ✓ Debugging analysis complete")
        print(f"    Success: {result.success}")

    except Exception as e:
        print(f"  ⚠ Requires API key: {type(e).__name__}")

    # Documentation
    print("\n4c. Documentation Agent")
    doc_gen = get_workflow_agent(WorkflowType.DOCUMENTATION)

    code_to_doc = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

    try:
        result = await doc_gen.generate_documentation(
            code=code_to_doc,
            doc_type="api",
            language="python"
        )
        print(f"  ✓ Documentation generated")
        print(f"    Success: {result.success}")

    except Exception as e:
        print(f"  ⚠ Requires API key: {type(e).__name__}")


# Example 5: Agent Orchestration
async def example_orchestration():
    """
    Example: Orchestrate multiple agents.
    """
    print("\n" + "=" * 70)
    print("Example 5: Agent Orchestration")
    print("=" * 70)

    from torq_console.agents import get_orchestrator, OrchestrationMode

    orchestrator = get_orchestrator()

    query = "Generate a Python function to sort a list, then write tests for it"

    print(f"\nQuery: {query}")

    try:
        # Single agent mode
        print("\n  Mode: SINGLE_AGENT")
        result = await orchestrator.process_query(
            query,
            mode=OrchestrationMode.SINGLE_AGENT
        )
        print(f"  ✓ Processed by: {result.metadata.get('agent_used')}")

        # Multi-agent mode
        print("\n  Mode: MULTI_AGENT")
        result = await orchestrator.process_query(
            query,
            mode=OrchestrationMode.MULTI_AGENT
        )
        print(f"  ✓ Agents used: {result.metadata.get('agents_used')}")

    except Exception as e:
        print(f"  ⚠ Requires API key: {type(e).__name__}")


# Example 6: Agent Memory
async def example_memory():
    """
    Example: Use agent memory for learning.
    """
    print("\n" + "=" * 70)
    print("Example 6: Agent Memory & Learning")
    print("=" * 70)

    from torq_console.agents import get_agent_memory, InteractionType

    memory = get_agent_memory()

    # Record interactions
    print("\nRecording interactions...")

    interaction_id = memory.record_interaction(
        user_input="How do I use async/await in Python?",
        agent_response="Async/await allows you to write asynchronous code...",
        agent_name="prince_flowers",
        interaction_type=InteractionType.GENERAL_CHAT,
        success=True,
        metadata={"topic": "python", "complexity": "beginner"}
    )

    print(f"  ✓ Recorded interaction: {interaction_id}")

    # Add feedback
    memory.add_feedback(interaction_id, score=0.9)
    print(f"  ✓ Added feedback: 0.9")

    # Update preferences
    memory.update_preference("language", "python")
    memory.update_preference("expertise_level", "intermediate")
    print(f"  ✓ Updated preferences")

    # Learn pattern
    memory.learn_pattern(
        "async_questions",
        {"pattern": "Questions about async programming", "frequency": "common"}
    )
    print(f"  ✓ Learned pattern: async_questions")

    # Get memory snapshot
    snapshot = memory.get_memory_snapshot()
    print(f"\n  Memory Snapshot:")
    print(f"    Total interactions: {snapshot.total_interactions}")
    print(f"    Success rate: {snapshot.success_rate:.2%}")
    print(f"    Average feedback: {snapshot.average_feedback:.2f}")
    print(f"    Learned patterns: {len(snapshot.learned_patterns)}")


# Example 7: Complete Workflow
async def example_complete_workflow():
    """
    Example: Complete workflow from query to execution.
    """
    print("\n" + "=" * 70)
    print("Example 7: Complete Workflow")
    print("=" * 70)

    from torq_console.agents import get_orchestrator, get_agent_memory, InteractionType

    orchestrator = get_orchestrator()
    memory = get_agent_memory()

    query = "Help me implement a simple REST API endpoint in FastAPI"

    print(f"\nQuery: {query}")

    try:
        # 1. Process query through orchestrator
        print("\n  Step 1: Processing query...")
        result = await orchestrator.process_query(query)

        # 2. Record interaction
        print("  Step 2: Recording interaction...")
        interaction_id = memory.record_interaction(
            user_input=query,
            agent_response=str(result.primary_response)[:100],
            agent_name=result.metadata.get('agent_used', 'unknown'),
            interaction_type=InteractionType.CODE_GENERATION,
            success=result.success
        )

        # 3. Get metrics
        print("  Step 3: Gathering metrics...")
        metrics = orchestrator.get_comprehensive_metrics()

        print(f"\n  ✓ Workflow complete!")
        print(f"    Interaction ID: {interaction_id}")
        print(f"    Total requests: {metrics['orchestrator']['total_requests']}")
        print(f"    Success rate: {metrics['orchestrator']['success_rate']:.2%}")

    except Exception as e:
        print(f"  ⚠ Requires API key: {type(e).__name__}")


# Run all examples
async def run_all_examples():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MARVIN INTEGRATION EXAMPLES")
    print("=" * 70)
    print("\nThese examples demonstrate the Marvin-powered features in TORQ Console.")
    print("Note: Most examples require an API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)")

    examples = [
        ("Specification Analysis", example_spec_analysis),
        ("Query Routing", example_query_routing),
        ("Prince Flowers Agent", example_prince_flowers),
        ("Workflow Agents", example_workflow_agents),
        ("Orchestration", example_orchestration),
        ("Memory & Learning", example_memory),
        ("Complete Workflow", example_complete_workflow),
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n⚠ {name} failed: {e}")

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Set your API key: export ANTHROPIC_API_KEY=your_key")
    print("  2. Run individual examples to see full results")
    print("  3. Integrate these patterns into your own code")
    print()


if __name__ == "__main__":
    asyncio.run(run_all_examples())
