#!/usr/bin/env python3
"""
Core Agent Usage Examples

Demonstrates how to use the new consolidated TORQ Console agent architecture
to replace the scattered agent files with unified, composable agents.
"""

import asyncio
import logging
from typing import Dict, List, Any

# Import the new core agent architecture
from torq_console.agents.core import (
    get_agent_registry,
    register_agent,
    AgentCapability,
    AgentContext
)

# Import specific core agents
from torq_console.agents.core import (
    ConversationalAgent,
    WorkflowAgent,
    ResearchAgent,
    OrchestrationAgent
)

# Import interfaces and types
from torq_console.agents.core.interfaces import (
    ConversationMode,
    WorkflowType,
    SearchScope
)

# Import base types
from torq_console.agents.core.base_agent import AgentResult


async def example_basic_agent_usage():
    """Example of basic agent usage."""
    print("=== Basic Agent Usage Example ===")

    # Get the agent registry
    registry = get_agent_registry()

    # Find available agents
    print("Available agents:")
    agents = registry.list_agents()
    for agent in agents:
        print(f"  - {agent['agent_name']}: {agent['capabilities']}")

    # Get a specific agent
    conversational_agent = await registry.get_agent_instance("conversational_agent")

    if conversational_agent:
        # Process a simple request
        result = await conversational_agent.process_request(
            "Hello, can you help me understand how agent orchestration works?"
        )

        print(f"Agent response: {result.content}")
        print(f"Success: {result.success}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Execution time: {result.execution_time:.2f}s")


async def example_conversation_session():
    """Example of using the conversational agent with session management."""
    print("\n=== Conversation Session Example ===")

    # Get the conversational agent
    registry = get_agent_registry()
    agent = await registry.get_agent_instance("conversational_agent")

    if not agent:
        print("Conversational agent not available")
        return

    # Start a conversation
    session_id = await agent.start_conversation(
        initial_message="I want to learn about Python decorators",
        mode=ConversationMode.MULTI_TURN
    )

    print(f"Started conversation session: {session_id}")

    # Continue the conversation
    questions = [
        "Can you show me a simple example?",
        "How do decorators work with function arguments?",
        "What are some common use cases for decorators?"
    ]

    for question in questions:
        result = await agent.continue_conversation(session_id, question)
        print(f"\nQ: {question}")
        print(f"A: {result.content[:200]}...")

    # Get conversation history
    history = await agent.get_conversation_history(session_id)
    print(f"\nConversation has {len(history)} turns")

    # End the conversation
    await agent.end_conversation(session_id)
    print("Conversation ended")


async def example_workflow_execution():
    """Example of using the workflow agent for different tasks."""
    print("\n=== Workflow Execution Example ===")

    # Get the workflow agent
    registry = get_agent_registry()
    agent = await registry.get_agent_instance("workflow_agent")

    if not agent:
        print("Workflow agent not available")
        return

    # Code generation workflow
    print("1. Code Generation Workflow:")
    result = await agent.execute_workflow(
        workflow_type=WorkflowType.CODE_GENERATION,
        parameters={
            "request": "Create a function to validate email addresses",
            "language": "python"
        }
    )

    if result.success:
        print("✅ Code generated successfully")
        print(f"Execution time: {result.execution_time:.2f}s")
    else:
        print("❌ Code generation failed")
        print(f"Error: {result.error}")

    # Debugging workflow
    print("\n2. Debugging Workflow:")
    buggy_code = """
def divide_numbers(a, b):
    return a / b

result = divide_numbers(10, 0)
"""

    result = await agent.execute_workflow(
        workflow_type=WorkflowType.DEBUGGING,
        parameters={
            "request": "Debug this code that causes division by zero",
            "code": buggy_code,
            "error_message": "ZeroDivisionError: division by zero",
            "language": "python"
        }
    )

    if result.success:
        print("✅ Debugging completed successfully")
        print(f"Analysis: {result.content[:300]}...")
    else:
        print("❌ Debugging failed")

    # Documentation workflow
    print("\n3. Documentation Workflow:")
    result = await agent.execute_workflow(
        workflow_type=WorkflowType.DOCUMENTATION,
        parameters={
            "request": "Document this function with API documentation",
            "content": buggy_code,
            "doc_type": "api",
            "audience": "developers"
        }
    )

    if result.success:
        print("✅ Documentation generated successfully")
    else:
        print("❌ Documentation generation failed")


async def example_research_operations():
    """Example of using the research agent for information gathering."""
    print("\n=== Research Operations Example ===")

    # Get the research agent
    registry = get_agent_registry()
    agent = await registry.get_agent_instance("research_agent")

    if not agent:
        print("Research agent not available")
        return

    # Web search
    print("1. Web Search:")
    from torq_console.agents.core.interfaces import ResearchQuery

    query = ResearchQuery(
        query="Python best practices for error handling",
        scope=SearchScope.WEB,
        max_results=5
    )

    result = await agent.search(query)

    if result.success:
        print("✅ Search completed successfully")
        print(f"Found {result.metadata.get('results_count', 0)} results")

        # Extract insights
        if "insights" in result.metadata:
            print("Insights:")
            for insight in result.metadata["insights"][:3]:
                print(f"  - {insight}")
    else:
        print("❌ Search failed")

    # Extract insights from text
    print("\n2. Text Analysis:")
    sample_text = """
    Python error handling is crucial for robust applications. Common patterns include:
    1. Always handle specific exceptions
    2. Use finally blocks for cleanup
    3. Consider using context managers
    4. Log errors appropriately
    5. Provide meaningful error messages
    """

    insights = await agent.extract_insights(sample_text, "trends")
    print("Extracted insights:")
    for insight in insights:
        print(f"  - {insight}")


async def example_orchestration():
    """Example of using the orchestration agent to coordinate multiple agents."""
    print("\n=== Orchestration Example ===")

    # Get the orchestration agent
    registry = get_agent_registry()
    orchestration_agent = await registry.get_agent_instance("orchestration_agent")

    if not orchestration_agent:
        print("Orchestration agent not available")
        return

    # Orchestrate multiple agents for a complex task
    print("1. Multi-Agent Orchestration:")

    workflow_definition = {
        "name": "Code Analysis and Improvement",
        "description": "Analyze existing code and suggest improvements",
        "mode": "pipeline",
        "steps": [
            {
                "id": "analyze",
                "agent": "workflow_agent",
                "type": "analysis",
                "parameters": {
                    "request": "Analyze this Python code for quality issues",
                    "analysis_type": "quality"
                }
            },
            {
                "id": "improve",
                "agent": "workflow_agent",
                "type": "refactoring",
                "parameters": {
                    "request": "Improve the code based on the analysis",
                    "goals": ["readability", "performance"]
                }
            },
            {
                "id": "document",
                "agent": "workflow_agent",
                "type": "documentation",
                "parameters": {
                    "request": "Create documentation for the improved code",
                    "doc_type": "api"
                }
            }
        ]
    }

    result = await orchestration_agent.coordinate_workflow(workflow_definition)

    if result.success:
        print("✅ Orchestration completed successfully")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Plan ID: {result.metadata.get('workflow_id', 'unknown')}")
    else:
        print("❌ Orchestration failed")
        print(f"Error: {result.error}")

    # Simple agent orchestration
    print("\n2. Simple Agent Orchestration:")

    agents_to_orchestrate = ["conversational_agent", "research_agent"]

    result = await orchestration_agent.orchestrate_agents(
        agents=agents_to_orchestrate,
        workflow={
            "name": "Research and Discuss",
            "mode": "parallel",
            "task_type": "research",
            "parameters": {
                "topic": "latest Python developments"
            }
        }
    )

    if result.success:
        print("✅ Multi-agent orchestration completed")
    else:
        print("❌ Multi-agent orchestration failed")


async def example_agent_discovery_and_routing():
    """Example of agent discovery and capability-based routing."""
    print("\n=== Agent Discovery and Routing Example ===")

    # Get the registry
    registry = get_agent_registry()

    # Find agents by capability
    print("1. Agents by Capability:")

    capabilities_to_check = [
        AgentCapability.CONVERSATION,
        AgentCapability.CODE_GENERATION,
        AgentCapability.RESEARCH,
        AgentCapability.ORCHESTRATION
    ]

    for capability in capabilities_to_check:
        agents = registry.find_agents_by_capability(capability)
        print(f"  {capability}: {len(agents)} agents")
        for agent_id in agents:
            agent_info = registry.get_agent_info(agent_id)
            print(f"    - {agent_info['agent_name']} ({agent_info['status']})")

    # Find agents with multiple capabilities
    print("\n2. Agents with Multiple Capabilities:")

    all_agents = registry.list_agents()
    multi_capability_agents = [
        agent for agent in all_agents
        if len(agent['capabilities']) > 3
    ]

    for agent in multi_capability_agents:
        print(f"  - {agent['agent_name']}: {len(agent['capabilities'])} capabilities")
        print(f"    Capabilities: {', '.join(agent['capabilities'])}")

    # Get registry statistics
    print("\n3. Registry Statistics:")
    stats = registry.get_registry_stats()
    print(f"  Total agents: {stats['total_agents']}")
    print(f"  Active instances: {stats['active_instances']}")
    print(f"  Status distribution: {stats['status_counts']}")

    # Capability distribution
    print("\n4. Capability Distribution:")
    for capability, count in stats['capability_counts'].items():
        print(f"  {capability}: {count} agents")


async def example_custom_agent_registration():
    """Example of registering a custom agent."""
    print("\n=== Custom Agent Registration Example ===")

    # Define a custom agent
    from torq_console.agents.core.base_agent import BaseAgent, AgentCapability

    class CustomSecurityAgent(BaseAgent):
        """Custom security-focused agent."""

        def __init__(self, config=None):
            super().__init__(
                agent_id="security_agent",
                agent_name="Security Analysis Agent",
                capabilities=[AgentCapability.SECURITY_ANALYSIS],
                config=config
            )

        async def _execute_request(self, request, context=None):
            """Execute security analysis request."""
            # Simple security analysis
            security_issues = []

            if "password" in request.lower():
                security_issues.append("Potential password handling detected")

            if "sql" in request.lower():
                security_issues.append("Potential SQL injection risk")

            if "eval(" in request:
                security_issues.append("Code execution risk detected")

            result_content = "Security Analysis Complete\n\n"
            if security_issues:
                result_content += "Security Issues Found:\n"
                for issue in security_issues:
                    result_content += f"- {issue}\n"
                result_content += "\nRecommendation: Review and mitigate these security concerns."
            else:
                result_content += "No obvious security issues detected."

            return AgentResult(
                success=True,
                content=result_content,
                confidence=0.8,
                metadata={"issues_found": len(security_issues)}
            )

    # Register the custom agent
    success = register_agent(
        CustomSecurityAgent,
        "security_agent",
        "Security Analysis Agent",
        [AgentCapability.SECURITY_ANALYSIS],
        config={
            "scan_depth": "medium",
            "check_patterns": ["password", "sql", "eval", "exec"]
        }
    )

    if success:
        print("✅ Custom security agent registered successfully")

        # Test the custom agent
        registry = get_agent_registry()
        agent = await registry.get_agent_instance("security_agent")

        if agent:
            test_request = "Analyze this code: user_input = input(); eval(user_input)"
            result = await agent.process_request(test_request)

            print("Security analysis result:")
            print(result.content)
    else:
        print("❌ Failed to register custom agent")


async def example_performance_monitoring():
    """Example of performance monitoring for agents."""
    print("\n=== Performance Monitoring Example ===")

    # Get the registry
    registry = get_agent_registry()

    # Test agents and collect metrics
    agents_to_test = ["conversational_agent", "workflow_agent", "research_agent"]

    for agent_id in agents_to_test:
        agent = await registry.get_agent_instance(agent_id)

        if agent:
            # Get initial metrics
            initial_metrics = agent.get_metrics()

            # Execute some requests
            test_requests = [
                "Hello, how are you?",
                "Can you help me with Python?",
                "What is machine learning?"
            ]

            for request in test_requests:
                await agent.process_request(request)

            # Get updated metrics
            final_metrics = agent.get_metrics()

            print(f"\nAgent: {agent_id}")
            print(f"  Total requests: {final_metrics.total_requests}")
            print(f"  Success rate: {final_metrics.success_rate:.2%}")
            print(f"  Average execution time: {final_metrics.average_execution_time:.3f}s")
            print(f"  Total tokens used: {final_metrics.total_tokens_used}")

            # Agent-specific info
            if hasattr(agent, 'get_agent_info'):
                agent_info = agent.get_agent_info()
                if "active_sessions" in agent_info:
                    print(f"  Active sessions: {agent_info['active_sessions']}")
                if "cache_stats" in agent_info:
                    cache_stats = agent_info['cache_stats']
                    print(f"  Cache hits: {cache_stats.get('active', 0)}")


async def main():
    """Main function to run all examples."""
    print("TORQ Console Core Agent Architecture Usage Examples")
    print("=" * 60)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        # Run all examples
        await example_basic_agent_usage()
        await example_conversation_session()
        await example_workflow_execution()
        await example_research_operations()
        await example_orchestration()
        await example_agent_discovery_and_routing()
        await example_custom_agent_registration()
        await example_performance_monitoring()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("\nKey Benefits of Core Agent Architecture:")
        print("✅ Unified interfaces and consistent APIs")
        print("✅ Modular capabilities and composable agents")
        print("✅ Dynamic agent discovery and routing")
        print("✅ Comprehensive monitoring and metrics")
        print("✅ Easy extension and customization")
        print("✅ Dramatically reduced code duplication")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())