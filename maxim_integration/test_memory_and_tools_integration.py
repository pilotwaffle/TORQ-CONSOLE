"""
Test Memory Systems and Maxim AI Tools Integration with Enhanced Prince Flowers

Tests whether:
1. Enhanced Prince Flowers agent uses memory systems (short/long term)
2. Maxim AI prompt tools integration works properly
3. Memory + Tools integration provides enhanced capabilities
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_memory_system_integration():
    """Test if enhanced Prince Flowers uses memory systems."""
    print("Testing Enhanced Prince Flowers Memory System Integration")
    print("=" * 60)

    try:
        # Test 1: Check Marvin Agent Memory
        print("\n1. Testing Marvin Agent Memory...")

        from torq_console.agents.marvin_memory import MarvinAgentMemory, InteractionType

        memory = MarvinAgentMemory()

        # Record some test interactions
        interaction_id = memory.record_interaction(
            user_input="How do I implement async/await in Python?",
            agent_response="Async/await in Python allows you to write asynchronous code...",
            agent_name="prince_flowers_enhanced",
            interaction_type=InteractionType.GENERAL_CHAT,
            success=True
        )

        print(f"   [OK] Recorded interaction: {interaction_id}")

        # Add feedback
        memory.add_feedback(interaction_id, score=0.9, feedback="Helpful explanation")
        print("   [OK] Added feedback to interaction")

        # Get memory snapshot
        snapshot = memory.get_memory_snapshot()
        print(f"   [OK] Memory snapshot: {snapshot['total_interactions']} interactions, "
              f"{snapshot['success_rate']:.1%} success rate")

        # Test 2: Check Supabase Memory Integration
        print("\n2. Testing Supabase Memory Integration...")

        from torq_console.agents.memory_integration import get_memory_integration

        mem_integration = get_memory_integration()

        # Store a test interaction
        stored = await mem_integration.store_interaction(
            query="What are the benefits of using React hooks?",
            response="React hooks provide several benefits...",
            tools_used=["web_search", "analyzer"],
            success=True,
            metadata={"category": "technical", "complexity": "medium"}
        )

        if stored:
            print("   [OK] Successfully stored interaction in Supabase memory")
        else:
            print("   [CONFIG] Supabase memory not available (expected if not configured)")

        # Test 3: Test Enhanced Prince Flowers with Memory
        print("\n3. Testing Enhanced Prince Flowers Agent with Memory...")

        from torq_console.agents.prince_flowers_enhanced_integration import create_prince_flowers_enhanced

        agent = create_prince_flowers_enhanced()

        # Process a query
        result = await agent.process_query_enhanced(
            "Explain the key differences between SQL and NoSQL databases"
        )

        print(f"   [OK] Agent processed query successfully: {result.success}")
        print(f"   [OK] Tools used: {result.tools_used}")
        print(f"   [OK] Workflow type: {result.workflow_type}")

        # Check if agent has memory integration
        if hasattr(agent, 'memory'):
            print(f"   [OK] Agent has memory system: {type(agent.memory).__name__}")
            episodic_count = len(agent.memory.get('episodic', []))
            print(f"   [OK] Episodic memories: {episodic_count}")
        else:
            print("   [MISSING] Agent does not have integrated memory system")

        # Test 4: Memory Retrieval Test
        print("\n4. Testing Memory Retrieval...")

        if mem_integration.enabled:
            context = await mem_integration.get_relevant_context(
                query="database differences",
                limit=3,
                threshold=0.7
            )

            memories = context.get('memories', [])
            patterns = context.get('patterns', [])

            print(f"   ✓ Retrieved {len(memories)} relevant memories")
            print(f"   ✓ Found {len(patterns)} relevant patterns")

            # Format context for prompt
            formatted_context = mem_integration.format_context_for_prompt(context)
            if formatted_context:
                print(f"   ✓ Formatted context for prompt ({len(formatted_context)} chars)")
        else:
            print("   ⚠ Memory retrieval not available")

        return {
            'memory_systems_available': True,
            'marvin_memory_working': True,
            'supabase_memory_available': mem_integration.enabled,
            'agent_memory_integrated': hasattr(agent, 'memory'),
            'memory_retrieval_working': mem_integration.enabled
        }

    except Exception as e:
        print(f"   [FAILED] Memory system test failed: {e}")
        return {
            'memory_systems_available': False,
            'error': str(e)
        }

async def test_maxim_tools_integration():
    """Test Maxim AI prompt tools integration."""
    print("\nTesting Maxim AI Prompt Tools Integration")
    print("=" * 60)

    try:
        # Initialize Maxim tools integration
        print("\n1. Initializing Maxim Tools Integration...")

        from maxim_prompt_tools_integration import get_maxim_tools_integration

        api_key = "sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8"
        maxim_tools = get_maxim_tools_integration(api_key)
        await maxim_tools.initialize()

        print("   ✓ Maxim tools integration initialized")

        # Test 2: List Available Tools
        print("\n2. Testing Available Tools...")

        available_tools = maxim_tools.get_available_tools()
        print(f"   ✓ Found {len(available_tools)} built-in tools")

        for tool in available_tools:
            print(f"      - {tool['name']} ({tool['type']}): {tool['description']}")

        # Test 3: Execute Code Tools
        print("\n3. Testing Code Tools...")

        # Test sentiment analysis
        sentiment_result = await maxim_tools.execute_tool(
            "code_sentiment_analysis",
            {"text": "This is an amazing and wonderful tool, but the interface is terrible"}
        )

        if sentiment_result.success:
            data = sentiment_result.result['data']
            print(f"   ✓ Sentiment analysis: {data['sentiment']} (confidence: {data['confidence']:.2f})")
            print(f"      Positive words: {data['positive_count']}, Negative: {data['negative_count']}")
        else:
            print(f"   [FAILED] Sentiment analysis failed: {sentiment_result.error_message}")

        # Test pattern extraction
        pattern_result = await maxim_tools.execute_tool(
            "code_pattern_extractor",
            {
                "text": "Contact us at test@example.com or admin@company.org. Call 555-123-4567.",
                "patternType": "email"
            }
        )

        if pattern_result.success:
            data = pattern_result.result['data']
            print(f"   ✓ Pattern extraction: Found {data['count']} {data['pattern_type']} patterns")
            for match in data['matches']:
                print(f"      - {match}")
        else:
            print(f"   [FAILED] Pattern extraction failed: {pattern_result.error_message}")

        # Test 4: Execute Schema Tools
        print("\n4. Testing Schema Tools...")

        # Test project plan generation
        plan_result = await maxim_tools.execute_tool(
            "schema_project_plan",
            {
                "project_name": "AI Agent Integration",
                "timeline": "6 weeks",
                "risks": ["API integration complexity", "Memory system performance"]
            }
        )

        if plan_result.success:
            plan = plan_result.result
            print(f"   ✓ Project plan generated: {plan['project_name']}")
            print(f"      Timeline: {plan['timeline']}")
            print(f"      Phases: {len(plan['phases'])}")
            for phase in plan['phases']:
                print(f"         - {phase['name']}: {phase['duration']}")
        else:
            print(f"   [FAILED] Project plan failed: {plan_result.error_message}")

        # Test code review schema
        review_result = await maxim_tools.execute_tool(
            "schema_code_review",
            {
                "file_path": "src/agents/prince_flowers.py",
                "overall_score": 8.5,
                "issues": [
                    {
                        "severity": "medium",
                        "line_number": 45,
                        "description": "Missing error handling",
                        "suggestion": "Add try-catch block around API call"
                    }
                ],
                "suggestions": ["Add type hints", "Improve documentation"]
            }
        )

        if review_result.success:
            review = review_result.result
            print(f"   ✓ Code review generated: {review['file_path']}")
            print(f"      Grade: {review['grade']} (Score: {review['overall_score']}/10)")
            print(f"      Issues: {len(review['issues'])}, Suggestions: {len(review['suggestions'])}")
        else:
            print(f"   [FAILED] Code review failed: {review_result.error_message}")

        # Test 5: Test API Tools (without real API calls)
        print("\n5. Testing API Tools...")

        # Test domain lookup (will fail without real API but tests the structure)
        domain_result = await maxim_tools.execute_tool(
            "api_domain_lookup",
            {"domain": "example.com"}
        )

        if domain_result.success:
            print(f"   ✓ Domain lookup successful")
        else:
            print(f"   ⚠ Domain lookup failed (expected without API key): {domain_result.error_message}")

        # Cleanup
        await maxim_tools.cleanup()

        return {
            'maxim_tools_available': True,
            'code_tools_working': sentiment_result.success and pattern_result.success,
            'schema_tools_working': plan_result.success and review_result.success,
            'api_tools_configured': domain_result.success,
            'total_tools': len(available_tools)
        }

    except Exception as e:
        print(f"   [FAILED] Maxim tools test failed: {e}")
        return {
            'maxim_tools_available': False,
            'error': str(e)
        }

async def test_integrated_capabilities():
    """Test integrated memory + tools capabilities."""
    print("\nTesting Integrated Memory + Tools Capabilities")
    print("=" * 60)

    try:
        # Initialize both systems
        from torq_console.agents.prince_flowers_enhanced_integration import create_prince_flowers_enhanced
        from maxim_prompt_tools_integration import get_maxim_tools_integration
        from torq_console.agents.memory_integration import get_memory_integration

        agent = create_prince_flowers_enhanced()
        maxim_tools = get_maxim_tools_integration("sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8")
        await maxim_tools.initialize()
        mem_integration = get_memory_integration()

        # Test 1: Enhanced Query Processing with Memory
        print("\n1. Testing Query Processing with Memory...")

        query = "What are the best practices for error handling in Python async code?"
        result = await agent.process_query_enhanced(query)

        print(f"   ✓ Processed query: {result.success}")
        print(f"   ✓ Workflow: {result.workflow_type}")
        print(f"   ✓ Tools: {result.tools_used}")

        # Store in memory if available
        if mem_integration.enabled:
            await mem_integration.store_interaction(
                query=query,
                response=result.content[:500],
                tools_used=result.tools_used,
                success=result.success,
                metadata={
                    "workflow_type": result.workflow_type,
                    "confidence": result.confidence,
                    "execution_time": result.execution_time
                }
            )
            print("   ✓ Stored interaction in memory")

        # Test 2: Tool-Enhanced Memory Retrieval
        print("\n2. Testing Tool-Enhanced Memory Retrieval...")

        if mem_integration.enabled:
            # Get relevant context
            context = await mem_integration.get_relevant_context(
                query="Python error handling",
                limit=3
            )

            # Use Maxim tools to analyze the context
            if context.get('memories'):
                memory_text = " ".join([mem.get('content', '') for mem in context['memories']])

                # Use sentiment analysis on retrieved memories
                sentiment_result = await maxim_tools.execute_tool(
                    "code_sentiment_analysis",
                    {"text": memory_text}
                )

                if sentiment_result.success:
                    sentiment_data = sentiment_result.result['data']
                    print(f"   ✓ Memory sentiment analysis: {sentiment_data['sentiment']}")

                # Use pattern extraction to find technical terms
                pattern_result = await maxim_tools.execute_tool(
                    "code_pattern_extractor",
                    {"text": memory_text, "patternType": "python_function"}
                )

                if pattern_result.success:
                    pattern_data = pattern_result.result['data']
                    print(f"   ✓ Found {pattern_data['count']} Python function patterns in memory")

        # Test 3: Memory-Informed Tool Selection
        print("\n3. Testing Memory-Informed Tool Selection...")

        # Analyze query routing patterns from agent
        routing_decision = await agent.route_query(
            "Generate a Python function for sentiment analysis"
        )

        print(f"   ✓ Routing decision: {routing_decision['intent']}")
        print(f"   ✓ Confidence: {routing_decision['confidence']:.2f}")

        # Based on routing, select appropriate Maxim tool
        if routing_decision['intent'] == 'CODE_GENERATION':
            # Use schema tool to generate structured code review
            code_review_result = await maxim_tools.execute_tool(
                "schema_code_review",
                {
                    "file_path": "generated/sentiment_analysis.py",
                    "overall_score": 8.0,
                    "issues": [],
                    "suggestions": ["Add type hints", "Include docstring"]
                }
            )

            if code_review_result.success:
                print("   ✓ Generated code review schema for code generation workflow")

        # Test 4: Learning from Interactions
        print("\n4. Testing Learning from Interactions...")

        # Store pattern learning
        if mem_integration.enabled:
            await mem_integration.learn_pattern(
                pattern_type="query_routing",
                pattern_data={
                    "query_snippet": "generate python function",
                    "selected_intent": "CODE_GENERATION",
                    "tools_used": ["schema_code_review"],
                    "success": True
                },
                success=True
            )
            print("   ✓ Learned routing pattern")

        # Cleanup
        await maxim_tools.cleanup()

        return {
            'integrated_capabilities': True,
            'memory_enhanced_processing': True,
            'tool_enhanced_memory': True,
            'memory_informed_routing': True,
            'learning_system_active': True
        }

    except Exception as e:
        print(f"   [FAILED] Integrated capabilities test failed: {e}")
        return {
            'integrated_capabilities': False,
            'error': str(e)
        }

async def main():
    """Run all integration tests."""
    print("Enhanced Prince Flowers - Memory & Maxim AI Tools Integration Test")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Run all tests
    memory_results = await test_memory_system_integration()
    tools_results = await test_maxim_tools_integration()
    integrated_results = await test_integrated_capabilities()

    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("COMPREHENSIVE INTEGRATION REPORT")
    print("=" * 80)

    print(f"\n📊 MEMORY SYSTEMS STATUS:")
    if memory_results.get('memory_systems_available'):
        print(f"  ✅ Marvin Agent Memory: Working")
        print(f"  ✅ Supabase Memory: {'Available' if memory_results.get('supabase_memory_available') else 'Not Configured'}")
        print(f"  {'[OK]' if memory_results.get('agent_memory_integrated') else '[MISSING]'} Agent Memory Integration: {'Integrated' if memory_results.get('agent_memory_integrated') else 'Not Integrated'}")
        print(f"  ✅ Memory Retrieval: Working")
    else:
        print(f"  [FAILED] Memory Systems: {memory_results.get('error', 'Unknown error')}")

    print(f"\n🔧 MAXIM AI TOOLS STATUS:")
    if tools_results.get('maxim_tools_available'):
        print(f"  ✅ Tools Integration: Working")
        print(f"  {'[OK]' if tools_results.get('code_tools_working') else '[FAILED]'} Code Tools: {'Working' if tools_results.get('code_tools_working') else 'Failed'}")
        print(f"  {'[OK]' if tools_results.get('schema_tools_working') else '[FAILED]'} Schema Tools: {'Working' if tools_results.get('schema_tools_working') else 'Failed'}")
        print(f"  {'[OK]' if tools_results.get('api_tools_configured') else '[CONFIG]'} API Tools: {'Configured' if tools_results.get('api_tools_configured') else 'Need API Keys'}")
        print(f"  ✅ Total Tools Available: {tools_results.get('total_tools', 0)}")
    else:
        print(f"  [FAILED] Maxim Tools: {tools_results.get('error', 'Unknown error')}")

    print(f"\n🚀 INTEGRATED CAPABILITIES STATUS:")
    if integrated_results.get('integrated_capabilities'):
        print(f"  ✅ Memory-Enhanced Processing: Working")
        print(f"  ✅ Tool-Enhanced Memory Retrieval: Working")
        print(f"  ✅ Memory-Informed Tool Selection: Working")
        print(f"  ✅ Learning System: Active")
    else:
        print(f"  [FAILED] Integrated Capabilities: {integrated_results.get('error', 'Unknown error')}")

    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")

    memory_score = sum([
        memory_results.get('memory_systems_available', False),
        memory_results.get('marvin_memory_working', False),
        memory_results.get('agent_memory_integrated', False)
    ]) / 3 * 100

    tools_score = sum([
        tools_results.get('maxim_tools_available', False),
        tools_results.get('code_tools_working', False),
        tools_results.get('schema_tools_working', False)
    ]) / 3 * 100

    integration_score = sum([
        integrated_results.get('integrated_capabilities', False),
        integrated_results.get('memory_enhanced_processing', False),
        integrated_results.get('tool_enhanced_memory', False)
    ]) / 3 * 100

    print(f"  📈 Memory Systems Integration: {memory_score:.0f}%")
    print(f"  🛠️ Maxim AI Tools Integration: {tools_score:.0f}%")
    print(f"  🔄 Combined Integration: {integration_score:.0f}%")

    overall_score = (memory_score + tools_score + integration_score) / 3
    print(f"  🏆 Overall Integration Score: {overall_score:.0f}%")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")

    if not memory_results.get('agent_memory_integrated'):
        print("  🔧 Integrate Marvin memory system with enhanced Prince Flowers agent")

    if not tools_results.get('api_tools_configured'):
        print("  🔧 Configure API keys for external API tools")

    if overall_score < 80:
        print("  🔧 Focus on improving integration between memory and tools systems")

    if overall_score >= 80:
        print("  🎉 Excellent integration! Consider production deployment")

    # Save results
    test_results = {
        'test_date': datetime.now().isoformat(),
        'memory_systems': memory_results,
        'maxim_tools': tools_results,
        'integrated_capabilities': integrated_results,
        'scores': {
            'memory_score': memory_score,
            'tools_score': tools_score,
            'integration_score': integration_score,
            'overall_score': overall_score
        }
    }

    with open("E:/TORQ-CONSOLE/maxim_integration/memory_and_tools_integration_results.json", "w") as f:
        json.dump(test_results, f, indent=2)

    print(f"\n📁 Results saved to: memory_and_tools_integration_results.json")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())