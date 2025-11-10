"""
Test Memory-Enhanced Prince Flowers Agent

Comprehensive test to validate 95%+ performance target with memory integration.
"""

import asyncio
import json
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_memory_enhanced_agent():
    """Test the memory-enhanced Prince Flowers agent."""
    print("Memory-Enhanced Prince Flowers Agent Test")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    try:
        # Initialize the memory-enhanced agent
        print("\n1. Initializing Memory-Enhanced Agent...")

        from memory_enhanced_prince_flowers import create_memory_enhanced_prince_flowers

        agent = create_memory_enhanced_prince_flowers()
        memory_ready = await agent.initialize()

        print(f"   [OK] Agent initialized")
        print(f"   [OK] Memory integration: {'Enabled' if memory_ready else 'Local only'}")

        results['initialization'] = {
            'success': True,
            'memory_enabled': memory_ready
        }

        # Test queries with expected memory improvements
        test_queries = [
            {
                'name': 'Research Query with Memory',
                'query': 'What are the latest developments in quantum computing?',
                'expected_intent': 'RESEARCH',
                'expected_memory_usage': True
            },
            {
                'name': 'Code Generation with Memory',
                'query': 'Generate a Python function for sentiment analysis',
                'expected_intent': 'CODE_GENERATION',
                'expected_memory_usage': True
            },
            {
                'name': 'Web Search with Memory',
                'query': 'Find information about React best practices',
                'expected_intent': 'WEB_SEARCH',
                'expected_memory_usage': True
            },
            {
                'name': 'Similar Query (Memory Test)',
                'query': 'What are the latest developments in quantum computing?',  # Same as first
                'expected_intent': 'RESEARCH',
                'expected_memory_usage': True,
                'expect_improvement': True  # Should use previous context
            },
            {
                'name': 'Complex Research Task',
                'query': 'Compare and contrast machine learning frameworks: TensorFlow vs PyTorch',
                'expected_intent': 'RESEARCH',
                'expected_memory_usage': True
            }
        ]

        print(f"\n2. Testing {len(test_queries)} queries with memory integration...")

        interaction_ids = []
        query_results = []

        for i, test_case in enumerate(test_queries, 1):
            print(f"\n   Test {i}: {test_case['name']}")
            print(f"   Query: {test_case['query']}")

            start_time = time.time()
            result = await agent.process_query_with_memory(test_case['query'])
            execution_time = time.time() - start_time

            print(f"   Success: {result['success']}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Intent: {result.get('intent', 'unknown')}")
            print(f"   Tools Used: {result.get('tools_used', [])}")
            print(f"   Execution Time: {execution_time:.3f}s")

            # Memory integration metrics
            memory_context = result.get('memory_context', {})
            print(f"   Memory Context:")
            print(f"     - Memories Used: {memory_context.get('memories_used', 0)}")
            print(f"     - Patterns Used: {memory_context.get('patterns_used', 0)}")
            print(f"     - Confidence Boost: {memory_context.get('confidence_boost', 0):.3f}")

            # Learning metrics
            learning_applied = result.get('learning_applied', {})
            print(f"   Learning Applied:")
            print(f"     - Routing Optimized: {learning_applied.get('routing_optimized', False)}")
            print(f"     - Tool Selection Optimized: {learning_applied.get('tool_selection_optimized', False)}")
            print(f"     - Response Enhanced: {learning_applied.get('response_enhanced', False)}")

            # Validate expectations
            validation_results = {
                'success': result['success'],
                'confidence_above_threshold': result['confidence'] >= 0.7,
                'memory_used': memory_context.get('memories_used', 0) > 0 or memory_context.get('patterns_used', 0) > 0,
                'execution_reasonable': execution_time < 10.0,
                'intent_correct': result.get('intent') == test_case['expected_intent'],
                'learning_applied': any(learning_applied.values())
            }

            print(f"   Validation:")
            for key, value in validation_results.items():
                status = "[OK]" if value else "[FAIL]"
                print(f"     - {key}: {status}")

            query_results.append({
                'test_case': test_case['name'],
                'result': result,
                'validation': validation_results,
                'execution_time': execution_time
            })

            if 'interaction_id' in result:
                interaction_ids.append(result['interaction_id'])

        # Test feedback learning
        print(f"\n3. Testing feedback learning...")

        if interaction_ids:
            # Provide feedback for first interaction
            feedback_id = interaction_ids[0]
            await agent.learn_from_feedback(
                interaction_id=feedback_id,
                feedback_score=0.9,
                feedback_text="Very helpful and comprehensive response"
            )
            print(f"   [OK] Feedback provided for interaction: {feedback_id}")

            results['feedback_learning'] = True
        else:
            print(f"   [SKIP] No interactions to provide feedback for")
            results['feedback_learning'] = False

        # Get performance metrics
        print(f"\n4. Getting performance metrics...")

        performance_metrics = await agent.get_performance_metrics()
        print(f"   [OK] Performance metrics retrieved")

        print(f"   Session Metrics:")
        session_metrics = performance_metrics.get('session_metrics', {})
        print(f"     - Total Interactions: {session_metrics.get('total_interactions', 0)}")
        print(f"     - Successful Interactions: {session_metrics.get('successful_interactions', 0)}")
        print(f"     - Success Rate: {session_metrics.get('session_success_rate', 0):.1%}")

        print(f"   Memory Performance:")
        memory_perf = performance_metrics.get('memory_performance', {})
        if memory_perf:
            session_metrics_mem = memory_perf.get('session_metrics', {})
            print(f"     - Memory Interactions: {session_metrics_mem.get('total_interactions', 0)}")
            print(f"     - Memory Success Rate: {session_metrics_mem.get('success_rate', 0):.1%}")

        print(f"   Agent Status:")
        print(f"     - Tools Available: {performance_metrics.get('tools_available', 0)}")
        print(f"     - Learning Active: {performance_metrics.get('learning_active', False)}")
        print(f"     - Memory Integration: {performance_metrics.get('memory_integration_enabled', False)}")

        results['performance_metrics'] = performance_metrics

        # Calculate overall success metrics
        print(f"\n5. Calculating overall performance...")

        total_tests = len(query_results)
        successful_tests = sum(1 for qr in query_results if qr['validation']['success'])
        confident_tests = sum(1 for qr in query_results if qr['validation']['confidence_above_threshold'])
        memory_used_tests = sum(1 for qr in query_results if qr['validation']['memory_used'])
        learning_tests = sum(1 for qr in query_results if qr['validation']['learning_applied'])
        fast_tests = sum(1 for qr in query_results if qr['validation']['execution_reasonable'])

        success_rate = successful_tests / total_tests
        confidence_rate = confident_tests / total_tests
        memory_usage_rate = memory_used_tests / total_tests
        learning_rate = learning_tests / total_tests
        performance_rate = fast_tests / total_tests

        print(f"   Test Results:")
        print(f"     - Success Rate: {success_rate:.1%} ({successful_tests}/{total_tests})")
        print(f"     - Confidence Rate: {confidence_rate:.1%} ({confident_tests}/{total_tests})")
        print(f"     - Memory Usage Rate: {memory_usage_rate:.1%} ({memory_used_tests}/{total_tests})")
        print(f"     - Learning Applied Rate: {learning_rate:.1%} ({learning_tests}/{total_tests})")
        print(f"     - Performance Rate: {performance_rate:.1%} ({fast_tests}/{total_tests})")

        # Calculate overall score (targeting 95%+)
        weights = {
            'success': 0.3,
            'confidence': 0.25,
            'memory_usage': 0.2,
            'learning': 0.15,
            'performance': 0.1
        }

        overall_score = (
            success_rate * weights['success'] +
            confidence_rate * weights['confidence'] +
            memory_usage_rate * weights['memory_usage'] +
            learning_rate * weights['learning'] +
            performance_rate * weights['performance']
        )

        results['overall_metrics'] = {
            'total_tests': total_tests,
            'success_rate': success_rate,
            'confidence_rate': confidence_rate,
            'memory_usage_rate': memory_usage_rate,
            'learning_rate': learning_rate,
            'performance_rate': performance_rate,
            'overall_score': overall_score,
            'target_achieved': overall_score >= 0.95
        }

        print(f"\n6. Final Assessment...")
        print(f"   Overall Score: {overall_score:.1%}")
        print(f"   Target (95%+): {'ACHIEVED' if overall_score >= 0.95 else 'NOT ACHIEVED'}")

        if overall_score >= 0.95:
            print(f"   [EXCELLENT] Memory-enhanced agent meets 95%+ target!")
        elif overall_score >= 0.85:
            print(f"   [GOOD] Memory-enhanced agent performs well but needs improvement")
        else:
            print(f"   [NEEDS_WORK] Memory-enhanced agent requires significant improvements")

        # Cleanup
        await agent.cleanup()

        return results

    except Exception as e:
        print(f"   [ERROR] Test failed: {e}")
        logger.exception("Test failed")
        return {
            'success': False,
            'error': str(e),
            'overall_score': 0.0
        }

def generate_improvement_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate improvement recommendations based on test results."""
    recommendations = []

    if not results.get('overall_metrics'):
        return ["Test failed - cannot generate recommendations"]

    metrics = results['overall_metrics']

    if metrics['success_rate'] < 0.9:
        recommendations.append("Improve overall query success rate - check error handling")

    if metrics['confidence_rate'] < 0.85:
        recommendations.append("Boost confidence scores - improve context relevance and routing")

    if metrics['memory_usage_rate'] < 0.8:
        recommendations.append("Increase memory utilization - improve memory retrieval and relevance")

    if metrics['learning_rate'] < 0.7:
        recommendations.append("Enhance learning mechanisms - improve pattern recognition and feedback integration")

    if metrics['performance_rate'] < 0.9:
        recommendations.append("Optimize execution performance - reduce response times")

    if not results.get('initialization', {}).get('memory_enabled', False):
        recommendations.append("Configure Supabase memory for full long-term learning capabilities")

    return recommendations

async def main():
    """Run the memory-enhanced agent test."""
    print("Memory-Enhanced Prince Flowers Agent - 95% Performance Target Test")
    print("=" * 80)

    # Run the test
    results = await test_memory_enhanced_agent()

    # Generate recommendations
    recommendations = generate_improvement_recommendations(results)

    # Save results
    test_results = {
        'test_date': datetime.now().isoformat(),
        'test_type': 'memory_enhanced_agent_95_percent_target',
        'results': results,
        'recommendations': recommendations,
        'target_achieved': results.get('overall_metrics', {}).get('target_achieved', False)
    }

    try:
        with open("E:/TORQ-CONSOLE/maxim_integration/memory_enhanced_agent_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n[OK] Results saved to: memory_enhanced_agent_test_results.json")
    except Exception as e:
        print(f"\n[FAILED] Could not save results: {e}")

    # Print recommendations
    if recommendations:
        print(f"\nRecommendations for Improvement:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print(f"\n[EXCELLENT] No improvements needed - target achieved!")

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())