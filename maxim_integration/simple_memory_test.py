"""
Simple Test for Memory Systems Integration
Tests whether enhanced Prince Flowers agent uses memory systems
"""

import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_memory_integration():
    """Test memory integration with enhanced Prince Flowers."""
    print("Memory Integration Test for Enhanced Prince Flowers")
    print("=" * 60)

    results = {}

    try:
        # Test 1: Marvin Agent Memory
        print("\n1. Testing Marvin Agent Memory...")

        from torq_console.agents.marvin_memory import MarvinAgentMemory, InteractionType

        memory = MarvinAgentMemory()

        # Record interaction
        interaction_id = memory.record_interaction(
            user_input="How do I implement async/await in Python?",
            agent_response="Async/await in Python allows you to write asynchronous code...",
            agent_name="prince_flowers_enhanced",
            interaction_type=InteractionType.GENERAL_CHAT,
            success=True
        )

        print(f"   [OK] Recorded interaction: {interaction_id}")

        # Add feedback
        memory.add_feedback(interaction_id, score=0.9)
        print("   [OK] Added feedback to interaction")

        # Get memory snapshot
        snapshot = memory.get_memory_snapshot()
        print(f"   [OK] Memory snapshot: {snapshot['total_interactions']} interactions, "
              f"{snapshot['success_rate']:.1%} success rate")

        results['marvin_memory'] = True

    except Exception as e:
        print(f"   [FAILED] Marvin memory test failed: {e}")
        results['marvin_memory'] = False

    try:
        # Test 2: Supabase Memory Integration
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
            results['supabase_memory'] = True
        else:
            print("   [CONFIG] Supabase memory not available (expected if not configured)")
            results['supabase_memory'] = False

    except Exception as e:
        print(f"   [FAILED] Supabase memory test failed: {e}")
        results['supabase_memory'] = False

    try:
        # Test 3: Enhanced Prince Flowers Agent
        print("\n3. Testing Enhanced Prince Flowers Agent...")

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
            results['agent_memory_integrated'] = True
        else:
            print("   [MISSING] Agent does not have integrated memory system")
            results['agent_memory_integrated'] = False

        results['agent_processing'] = result.success

    except Exception as e:
        print(f"   [FAILED] Agent test failed: {e}")
        results['agent_processing'] = False
        results['agent_memory_integrated'] = False

    try:
        # Test 4: Memory Retrieval
        print("\n4. Testing Memory Retrieval...")

        if 'mem_integration' in locals() and mem_integration.enabled:
            context = await mem_integration.get_relevant_context(
                query="database differences",
                limit=3,
                threshold=0.7
            )

            memories = context.get('memories', [])
            patterns = context.get('patterns', [])

            print(f"   [OK] Retrieved {len(memories)} relevant memories")
            print(f"   [OK] Found {len(patterns)} relevant patterns")

            # Format context for prompt
            formatted_context = mem_integration.format_context_for_prompt(context)
            if formatted_context:
                print(f"   [OK] Formatted context for prompt ({len(formatted_context)} chars)")

            results['memory_retrieval'] = True
        else:
            print("   [CONFIG] Memory retrieval not available")
            results['memory_retrieval'] = False

    except Exception as e:
        print(f"   [FAILED] Memory retrieval test failed: {e}")
        results['memory_retrieval'] = False

    return results

async def test_maxim_tools():
    """Test Maxim AI prompt tools integration."""
    print("\nMaxim AI Prompt Tools Integration Test")
    print("=" * 60)

    results = {}

    try:
        # Initialize Maxim tools integration
        print("\n1. Initializing Maxim Tools Integration...")

        from maxim_prompt_tools_integration import get_maxim_tools_integration

        api_key = "sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8"
        maxim_tools = get_maxim_tools_integration(api_key)
        await maxim_tools.initialize()

        print("   [OK] Maxim tools integration initialized")
        results['tools_initialized'] = True

        # Test 2: List Available Tools
        print("\n2. Testing Available Tools...")

        available_tools = maxim_tools.get_available_tools()
        print(f"   [OK] Found {len(available_tools)} built-in tools")

        for tool in available_tools:
            print(f"      - {tool['name']} ({tool['type']}): {tool['description']}")

        results['tools_available'] = len(available_tools)

        # Test 3: Execute Code Tools
        print("\n3. Testing Code Tools...")

        # Test sentiment analysis
        sentiment_result = await maxim_tools.execute_tool(
            "code_sentiment_analysis",
            {"text": "This is an amazing and wonderful tool, but the interface is terrible"}
        )

        if sentiment_result.success:
            data = sentiment_result.result
            print(f"   [OK] Sentiment analysis: {data['sentiment']} (confidence: {data['confidence']:.2f})")
            print(f"      Positive words: {data['positive_count']}, Negative: {data['negative_count']}")
            results['sentiment_analysis'] = True
        else:
            print(f"   [FAILED] Sentiment analysis failed: {sentiment_result.error_message}")
            results['sentiment_analysis'] = False

        # Test pattern extraction
        pattern_result = await maxim_tools.execute_tool(
            "code_pattern_extractor",
            {
                "text": "Contact us at test@example.com or admin@company.org. Call 555-123-4567.",
                "patternType": "email"
            }
        )

        if pattern_result.success:
            data = pattern_result.result
            print(f"   [OK] Pattern extraction: Found {data['count']} {data['pattern_type']} patterns")
            for match in data['matches']:
                print(f"      - {match}")
            results['pattern_extraction'] = True
        else:
            print(f"   [FAILED] Pattern extraction failed: {pattern_result.error_message}")
            results['pattern_extraction'] = False

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
            print(f"   [OK] Project plan generated: {plan['project_name']}")
            print(f"      Timeline: {plan['timeline']}")
            print(f"      Phases: {len(plan['phases'])}")
            for phase in plan['phases']:
                print(f"         - {phase['name']}: {phase['duration']}")
            results['project_plan_schema'] = True
        else:
            print(f"   [FAILED] Project plan failed: {plan_result.error_message}")
            results['project_plan_schema'] = False

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
            print(f"   [OK] Code review generated: {review['file_path']}")
            print(f"      Grade: {review['grade']} (Score: {review['overall_score']}/10)")
            print(f"      Issues: {len(review['issues'])}, Suggestions: {len(review['suggestions'])}")
            results['code_review_schema'] = True
        else:
            print(f"   [FAILED] Code review failed: {review_result.error_message}")
            results['code_review_schema'] = False

        # Cleanup
        await maxim_tools.cleanup()

        results['maxim_tools_working'] = True

    except Exception as e:
        print(f"   [FAILED] Maxim tools test failed: {e}")
        results['maxim_tools_working'] = False

    return results

async def main():
    """Run all tests."""
    print("Enhanced Prince Flowers - Memory & Tools Integration Test")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Run tests
    memory_results = await test_memory_integration()
    tools_results = await test_maxim_tools()

    # Generate report
    print("\n" + "=" * 80)
    print("INTEGRATION TEST REPORT")
    print("=" * 80)

    print(f"\nMEMORY SYSTEMS STATUS:")
    memory_score = 0
    max_memory_score = 5

    if memory_results.get('marvin_memory'):
        print("  [OK] Marvin Agent Memory: Working")
        memory_score += 1
    else:
        print("  [FAILED] Marvin Agent Memory: Failed")

    if memory_results.get('supabase_memory'):
        print("  [OK] Supabase Memory: Available")
        memory_score += 1
    else:
        print("  [CONFIG] Supabase Memory: Not Configured")

    if memory_results.get('agent_memory_integrated'):
        print("  [OK] Agent Memory Integration: Integrated")
        memory_score += 1
    else:
        print("  [MISSING] Agent Memory Integration: Not Integrated")

    if memory_results.get('agent_processing'):
        print("  [OK] Agent Processing: Working")
        memory_score += 1
    else:
        print("  [FAILED] Agent Processing: Failed")

    if memory_results.get('memory_retrieval'):
        print("  [OK] Memory Retrieval: Working")
        memory_score += 1
    else:
        print("  [CONFIG] Memory Retrieval: Not Available")

    print(f"\nMAXIM AI TOOLS STATUS:")
    tools_score = 0
    max_tools_score = 6

    if tools_results.get('tools_initialized'):
        print("  [OK] Tools Integration: Working")
        tools_score += 1
    else:
        print("  [FAILED] Tools Integration: Failed")

    if tools_results.get('tools_available', 0) > 0:
        print(f"  [OK] Tools Available: {tools_results.get('tools_available', 0)}")
        tools_score += 1
    else:
        print("  [FAILED] Tools Available: None")

    if tools_results.get('sentiment_analysis'):
        print("  [OK] Sentiment Analysis: Working")
        tools_score += 1
    else:
        print("  [FAILED] Sentiment Analysis: Failed")

    if tools_results.get('pattern_extraction'):
        print("  [OK] Pattern Extraction: Working")
        tools_score += 1
    else:
        print("  [FAILED] Pattern Extraction: Failed")

    if tools_results.get('project_plan_schema'):
        print("  [OK] Project Plan Schema: Working")
        tools_score += 1
    else:
        print("  [FAILED] Project Plan Schema: Failed")

    if tools_results.get('code_review_schema'):
        print("  [OK] Code Review Schema: Working")
        tools_score += 1
    else:
        print("  [FAILED] Code Review Schema: Failed")

    # Calculate overall scores
    memory_percentage = (memory_score / max_memory_score) * 100
    tools_percentage = (tools_score / max_tools_score) * 100
    overall_percentage = (memory_percentage + tools_percentage) / 2

    print(f"\nOVERALL ASSESSMENT:")
    print(f"  Memory Integration: {memory_percentage:.0f}% ({memory_score}/{max_memory_score})")
    print(f"  Maxim Tools Integration: {tools_percentage:.0f}% ({tools_score}/{max_tools_score})")
    print(f"  Overall Integration: {overall_percentage:.0f}%")

    # Key findings
    print(f"\nKEY FINDINGS:")

    # Memory system analysis
    if not memory_results.get('agent_memory_integrated'):
        print("  [IMPORTANT] Enhanced Prince Flowers agent is NOT using Marvin memory system")
        print("             The agent has memory initialization but doesn't integrate with MarvinAgentMemory")
    else:
        print("  [GOOD] Enhanced Prince Flowers agent is using memory system")

    # Tools integration analysis
    if tools_results.get('maxim_tools_working'):
        print("  [GOOD] Maxim AI prompt tools integration is working")
        print(f"         Available tools: {tools_results.get('tools_available', 0)}")
    else:
        print("  [ISSUE] Maxim AI prompt tools integration has problems")

    # Save results
    test_results = {
        'test_date': datetime.now().isoformat(),
        'memory_results': memory_results,
        'tools_results': tools_results,
        'scores': {
            'memory_score': memory_percentage,
            'tools_score': tools_percentage,
            'overall_score': overall_percentage
        },
        'findings': {
            'agent_uses_memory': memory_results.get('agent_memory_integrated', False),
            'maxim_tools_working': tools_results.get('maxim_tools_working', False),
            'memory_integration_complete': memory_score == max_memory_score,
            'tools_integration_complete': tools_score == max_tools_score
        }
    }

    try:
        with open("E:/TORQ-CONSOLE/maxim_integration/simple_memory_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n[OK] Results saved to: simple_memory_test_results.json")
    except Exception as e:
        print(f"\n[FAILED] Could not save results: {e}")

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())