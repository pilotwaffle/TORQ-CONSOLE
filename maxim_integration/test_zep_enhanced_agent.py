"""
Test Zep-Enhanced Prince Flowers Agent

Comprehensive test to validate Zep memory integration and
measure performance improvements toward 95%+ target.
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

async def test_zep_enhanced_agent():
    """Test the Zep-enhanced Prince Flowers agent."""
    print("Zep-Enhanced Prince Flowers Agent Performance Test")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: Validate 95%+ performance with Zep temporal memory")
    print("=" * 60)

    results = {}

    try:
        # Initialize the Zep-enhanced agent
        print("\n1. Initializing Zep-Enhanced Agent...")

        from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers

        agent = create_zep_enhanced_prince_flowers()
        zep_ready = await agent.initialize()

        print(f"   [OK] Agent initialized")
        print(f"   [OK] Zep Memory: {'Connected' if zep_ready else 'Local fallback'}")

        results['initialization'] = {
            'success': True,
            'zep_memory_enabled': zep_ready
        }

        if not zep_ready:
            print(f"   [ERROR] Zep memory not available - using fallback")
            # Continue with fallback testing

        # Test queries with expected memory improvements
        test_queries = [
            {
                'name': 'First Query - AI Basics',
                'query': 'What is artificial intelligence and how does it work?',
                'expected_memory_usage': False,  # First query - no prior context
                'category': 'research',
                'confidence_threshold': 0.7
            },
            {
                'name': 'Code Generation with Memory',
                'query': 'Generate a Python function for sentiment analysis using NLTK',
                'expected_memory_usage': False,  # Different topic
                'category': 'code',
                'confidence_threshold': 0.75
            },
            {
                'name': 'Memory-Enhanced Research',
                'query': 'What is artificial intelligence and how does it work?',  # Same as first
                'expected_memory_usage': True,   # Should use memory from first query
                'category': 'research',
                'confidence_threshold': 0.85,  # Should be higher due to memory
                'expect_improvement': True
            },
            {
                'name': 'Complex Analysis with Memory',
                'query': 'Compare the AI concepts mentioned in our previous discussions',
                'expected_memory_usage': True,
                'category': 'analysis',
                'confidence_threshold': 0.85,
                'expect_improvement': True
            },
            {
                'name': 'Follow-up Technical Question',
                'query': 'Can you explain machine learning models mentioned earlier?',
                'expected_memory_usage': True,
                'category': 'research',
                'confidence_threshold': 0.8,
                'expect_improvement': True
            },
            {
                'name': 'Code Enhancement with Memory',
                'query': 'Improve the Python function we created earlier for sentiment analysis',
                'expected_memory_usage': True,
                'category': 'code',
                'confidence_threshold': 0.8,
                'expect_improvement': True
            }
        ]

        print(f"\n2. Testing {len(test_queries)} queries with Zep memory integration...")

        interaction_ids = []
        query_results = []
        session_ids = []

        for i, test_case in enumerate(test_queries, 1):
            print(f"\n   Test {i}: {test_case['name']}")
            print(f"   Query: {test_case['query']}")

            # Create unique session for each test category or reuse for continuity
            if i == 1 or test_case['category'] not in ['research', 'analysis']:
                session_id = await agent.create_new_session(
                    metadata={
                        'test_case': test_case['name'],
                        'category': test_case['category'],
                        'test_number': i
                    }
                )
                session_ids.append(session_id)
            else:
                session_id = session_ids[-1]  # Reuse session for continuity

            start_time = time.time()
            result = await agent.process_query_with_zep_memory(
                query=test_case['query'],
                session_id=session_id
            )
            execution_time = time.time() - start_time

            print(f"   Success: {result['success']}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Tools Used: {result.get('tools_used', [])}")
            print(f"   Execution Time: {execution_time:.3f}s")

            # Zep memory integration metrics
            zep_memory = result.get('zep_memory', {})
            print(f"   Zep Memory Context:")
            print(f"     - Memories Used: {zep_memory.get('memories_used', 0)}")
            print(f"     - Confidence Boost: {zep_memory.get('confidence_boost', 0):.3f}")
            print(f"     - Context Available: {zep_memory.get('context_available', False)}")
            print(f"     - Context Length: {zep_memory.get('formatted_context_length', 0)} chars")

            # Learning metrics
            learning_applied = result.get('learning_applied', {})
            print(f"   Learning Applied:")
            print(f"     - Memory Enhanced: {learning_applied.get('memory_enhanced', False)}")
            print(f"     - Context Retrieved: {learning_applied.get('context_retrieved', False)}")
            print(f"     - Confidence Improved: {learning_applied.get('confidence_improved', False)}")

            # Validate expectations
            validation_results = {
                'success': result['success'],
                'confidence_above_threshold': result['confidence'] >= test_case['confidence_threshold'],
                'memory_used_as_expected': zep_memory.get('memories_used', 0) > 0 if test_case['expected_memory_usage'] else zep_memory.get('memories_used', 0) == 0,
                'execution_reasonable': execution_time < 15.0,
                'session_id_provided': 'session_id' in result,
                'response_quality': len(result.get('content', '')) > 100,
                'learning_applied': any(learning_applied.values()),
                'expectation_met': True  # Will be updated below
            }

            # Check if expectations were met
            if test_case.get('expect_improvement'):
                # For queries expecting improvement, check if performance is better
                previous_results = [qr for qr in query_results if qr['category'] == test_case['category']]
                if previous_results:
                    avg_prev_confidence = sum(qr['validation']['confidence_above_threshold'] for qr in previous_results) / len(previous_results)
                    validation_results['expectation_met'] = result['confidence'] > avg_prev_confidence
                else:
                    validation_results['expectation_met'] = result['confidence'] >= test_case['confidence_threshold']
            else:
                validation_results['expectation_met'] = validation_results['success'] and validation_results['confidence_above_threshold']

            print(f"   Validation:")
            for key, value in validation_results.items():
                status = "[OK]" if value else "[FAIL]"
                print(f"     - {key}: {status}")

            query_results.append({
                'test_case': test_case['name'],
                'category': test_case['category'],
                'result': result,
                'validation': validation_results,
                'execution_time': execution_time,
                'session_id': session_id
            })

            if 'interaction_id' in result:
                interaction_ids.append(result['interaction_id'])

        # Test feedback learning with Zep
        print(f"\n3. Testing Zep feedback learning...")

        if interaction_ids:
            # Provide feedback for several interactions
            feedback_results = []
            for i, interaction_id in enumerate(interaction_ids[:3]):  # Test first 3
                feedback_score = 0.85 + (i * 0.05)  # 0.85, 0.9, 0.95
                await agent.learn_from_feedback(
                    interaction_id=interaction_id,
                    feedback_score=feedback_score,
                    feedback_text=f"Test feedback #{i+1} - Very helpful response!",
                    session_id=query_results[i]['session_id']
                )
                feedback_results.append(feedback_score)
                print(f"   ✓ Feedback provided for interaction {i+1}: {feedback_score:.2f}")

            results['feedback_learning'] = True
            print(f"   ✓ Average feedback score: {sum(feedback_results)/len(feedback_results):.2f}")

        else:
            print(f"   [SKIP] No interactions to provide feedback for")
            results['feedback_learning'] = False

        # Test memory search functionality
        print(f"\n4. Testing Zep memory search...")

        search_results = []
        search_queries = ["artificial intelligence", "Python function", "memory system"]

        for search_query in search_queries:
            results_found = await agent.search_memory(
                query=search_query,
                limit=5
            )
            search_results.append({
                'query': search_query,
                'results_found': len(results_found),
                'success': len(results_found) > 0
            })
            print(f"   Query: '{search_query}' - Found {len(results_found)} results")

        avg_search_results = sum(r['results_found'] for r in search_results) / len(search_results)
        results['memory_search'] = {
            'total_queries': len(search_queries),
            'avg_results': avg_search_results,
            'success_rate': sum(r['success'] for r in search_results) / len(search_results)
        }

        print(f"   Average search results: {avg_search_results:.1f}")

        # Get session history
        print(f"\n5. Testing session history...")

        if session_ids:
            first_session = session_ids[0]
            history = await agent.get_session_history(first_session, limit=10)
            print(f"   Retrieved {len(history.get('context', []))} messages from session {first_session}")
            results['session_history'] = {
                'session_id': first_session,
                'messages_retrieved': len(history.get('context', [])),
                'success': len(history.get('context', [])) > 0
            }

        # Get performance metrics
        print(f"\n6. Getting performance metrics...")

        performance_metrics = await agent.get_performance_metrics()
        print(f"   [OK] Performance metrics retrieved")

        print(f"   Session Metrics:")
        session_metrics = performance_metrics.get('session_metrics', {})
        print(f"     - Total Interactions: {session_metrics.get('total_interactions', 0)}")
        print(f"     - Successful Interactions: {session_metrics.get('successful_interactions', 0)}")
        print(f"     - Success Rate: {session_metrics.get('session_success_rate', 0):.1%}")

        print(f"   Zep Memory Stats:")
        zep_stats = performance_metrics.get('zep_memory_stats', {})
        if zep_stats:
            print(f"     - Total Sessions: {zep_stats.get('total_sessions', 0)}")
            print(f"     - Active Sessions: {zep_stats.get('active_sessions', 0)}")
            print(f"     - Total Messages: {zep_stats.get('total_messages', 0)}")
            print(f"     - Memory Hits: {zep_stats.get('memory_hits', 0)}")
            print(f"     - Hit Rate: {zep_stats.get('hit_rate', 0):.1%}")

        print(f"   Agent Status:")
        print(f"     - Memory Enhancement Rate: {performance_metrics.get('memory_enhancement_rate', 0):.1%}")
        print(f"     - Tools Available: {performance_metrics.get('tools_available', 0)}")
        print(f"     - Learning Active: {performance_metrics.get('learning_active', False)}")

        results['performance_metrics'] = performance_metrics

        # Calculate overall success metrics
        print(f"\n7. Calculating overall performance...")

        total_tests = len(query_results)
        successful_tests = sum(1 for qr in query_results if qr['validation']['success'])
        confident_tests = sum(1 for qr in query_results if qr['validation']['confidence_above_threshold'])
        memory_used_tests = sum(1 for qr in query_results if qr['validation']['memory_used_as_expected'])
        learning_tests = sum(1 for qr in query_results if qr['validation']['learning_applied'])
        expectation_met_tests = sum(1 for qr in query_results if qr['validation']['expectation_met'])
        fast_tests = sum(1 for qr in query_results if qr['validation']['execution_reasonable'])
        quality_tests = sum(1 for qr in query_results if qr['validation']['response_quality'])

        success_rate = successful_tests / total_tests
        confidence_rate = confident_tests / total_tests
        memory_usage_rate = memory_used_tests / total_tests
        learning_rate = learning_tests / total_tests
        expectation_rate = expectation_met_tests / total_tests
        performance_rate = fast_tests / total_tests
        quality_rate = quality_tests / total_tests

        print(f"   Test Results:")
        print(f"     - Success Rate: {success_rate:.1%} ({successful_tests}/{total_tests})")
        print(f"     - Confidence Rate: {confidence_rate:.1%} ({confident_tests}/{total_tests})")
        print(f"     - Memory Usage Rate: {memory_usage_rate:.1%} ({memory_used_tests}/{total_tests})")
        print(f"     - Learning Applied Rate: {learning_rate:.1%} ({learning_tests}/{total_tests})")
        print(f"     - Expectation Met Rate: {expectation_rate:.1%} ({expectation_met_tests}/{total_tests})")
        print(f"     - Performance Rate: {performance_rate:.1%} ({fast_tests}/{total_tests})")
        print(f"     - Response Quality Rate: {quality_rate:.1%} ({quality_tests}/{total_tests})")

        # Calculate overall score (targeting 95%+)
        weights = {
            'success': 0.20,
            'confidence': 0.20,
            'memory_usage': 0.25,
            'learning': 0.15,
            'expectation_met': 0.10,
            'performance': 0.10
        }

        overall_score = (
            success_rate * weights['success'] +
            confidence_rate * weights['confidence'] +
            memory_usage_rate * weights['memory_usage'] +
            learning_rate * weights['learning'] +
            expectation_rate * weights['expectation_met'] +
            performance_rate * weights['performance'] +
            quality_rate * weights['quality']
        )

        results['overall_metrics'] = {
            'total_tests': total_tests,
            'success_rate': success_rate,
            'confidence_rate': confidence_rate,
            'memory_usage_rate': memory_usage_rate,
            'learning_rate': learning_rate,
            'expectation_met_rate': expectation_rate,
            'performance_rate': performance_rate,
            'quality_rate': quality_rate,
            'overall_score': overall_score,
            'target_achieved': overall_score >= 0.95,
            'target_95_plus': overall_score >= 0.95,
            'target_90_plus': overall_score >= 0.90
        }

        print(f"\n8. Final Assessment...")
        print(f"   Overall Score: {overall_score:.1%}")
        print(f"   Target (95%+): {'ACHIEVED' if overall_score >= 0.95 else 'NOT ACHIEVED'}")
        print(f"   Target (90%+): {'ACHIEVED' if overall_score >= 0.90 else 'NOT ACHIEVED'}")

        if overall_score >= 0.95:
            print(f"   [EXCELLENT] Zep-enhanced agent achieves 95%+ performance target!")
        elif overall_score >= 0.90:
            print(f"   [EXCELLENT] Zep-enhanced agent achieves 90%+ performance!")
        elif overall_score >= 0.80:
            print(f"   [GOOD] Zep-enhanced agent performs well but needs optimization")
        elif overall_score >= 0.70:
            print(f"   [FAIR] Zep-enhanced agent shows promise but needs improvement")
        else:
            print(f"   [NEEDS_WORK] Zep-enhanced agent requires significant improvements")

        # Performance improvement analysis
        print(f"\n9. Performance Improvement Analysis...")

        # Analyze by category
        categories = {}
        for qr in query_results:
            cat = qr['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(qr['validation']['success'])

        print(f"   Performance by Category:")
        for cat, successes in categories.items():
            cat_rate = sum(successes) / len(successes)
            print(f"     - {cat}: {cat_rate:.1%} ({sum(successes)}/{len(successes)})")

        # Memory impact analysis
        memory_tests = [qr for qr in query_results if qr['validation']['memory_used_as_expected']]
        if memory_tests:
            memory_success_rate = sum(1 for qr in memory_tests if qr['validation']['success']) / len(memory_tests)
            print(f"     - Memory-Enhanced Queries: {memory_success_rate:.1%} success rate")

        # Learning impact analysis
        learning_tests = [qr for qr in query_results if qr['validation']['learning_applied']]
        if learning_tests:
            learning_success_rate = sum(1 for qr in learning_tests if qr['validation']['success']) / len(learning_tests)
            print(f"     - Learning-Enhanced Queries: {learning_success_rate:.1%} success rate")

        # First vs subsequent query comparison
        first_queries = [qr for qr in query_results if not qr.get('expect_improvement', False)]
        subsequent_queries = [qr for qr in query_results if qr.get('expect_improvement', False)]

        if first_queries and subsequent_queries:
            first_avg_confidence = sum(qr['validation']['confidence_above_threshold'] for qr in first_queries) / len(first_queries)
            subsequent_avg_confidence = sum(qr['validation']['confidence_above_threshold'] for qr in subsequent_queries) / len(subsequent_queries)
            improvement = subsequent_avg_confidence - first_avg_confidence

            print(f"     - First Query Confidence: {first_avg_confidence:.1%}")
            print(f"     - Subsequent Query Confidence: {subsequent_avg_confidence:.1%}")
            print(f"     - Memory-Driven Improvement: {improvement:.1%}")

        # Cleanup
        await agent.cleanup()

        return results

    except Exception as e:
        print(f"   [ERROR] Test failed: {e}")
        logger.exception("Zep agent test failed")
        return {
            'success': False,
            'error': str(e),
            'overall_score': 0.0
        }

def generate_performance_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate improvement recommendations based on test results."""
    recommendations = []

    if not results.get('overall_metrics'):
        return ["Test failed - cannot generate recommendations"]

    metrics = results['overall_metrics']

    if metrics['success_rate'] < 0.95:
        recommendations.append("Improve overall query success rate - focus on error handling and robustness")

    if metrics['confidence_rate'] < 0.90:
        recommendations.append("Boost confidence scores - enhance context relevance and memory retrieval quality")

    if metrics['memory_usage_rate'] < 0.80:
        recommendations.append("Increase memory utilization - improve memory retrieval and contextual relevance matching")

    if metrics['learning_rate'] < 0.80:
        recommendations.append("Enhance learning mechanisms - improve feedback integration and pattern recognition")

    if metrics['expectation_met_rate'] < 0.85:
        recommendations.append("Improve expectation accuracy - better align memory retrieval with query intent")

    if metrics['performance_rate'] < 0.90:
        recommendations.append("Optimize execution performance - reduce response times and improve efficiency")

    if metrics['quality_rate'] < 0.90:
        recommendations.append("Improve response quality - enhance content generation and context integration")

    # High-priority recommendations
    if metrics['overall_score'] < 0.85:
        recommendations.insert(0, "CRITICAL: Overall score below 85% - requires immediate attention")

    if metrics['memory_usage_rate'] < 0.50:
        recommendations.insert(0, "HIGH: Memory usage below 50% - Zep integration not functioning properly")

    if not results.get('initialization', {}).get('zep_memory_enabled', False):
        recommendations.insert(0, "HIGH: Zep memory not connected - check Docker setup")

    return recommendations

async def main():
    """Run the Zep-enhanced agent test."""
    print("Zep-Enhanced Prince Flowers Agent - 95% Performance Target Test")
    print("=" * 80)

    # Run the test
    results = await test_zep_enhanced_agent()

    # Generate recommendations
    recommendations = generate_performance_recommendations(results)

    # Save results
    test_results = {
        'test_date': datetime.now().isoformat(),
        'test_type': 'zep_enhanced_agent_95_percent_target',
        'results': results,
        'recommendations': recommendations,
        'target_95_percent_achieved': results.get('overall_metrics', {}).get('target_95_plus', False),
        'target_90_percent_achieved': results.get('overall_metrics', {}).get('target_90_plus', False)
    }

    try:
        with open("E:/TORQ-CONSOLE/maxim_integration/zep_enhanced_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n[OK] Results saved to: zep_enhanced_test_results.json")
    except Exception as e:
        print(f"\n[FAILED] Could not save results: {e}")

    # Print recommendations
    if recommendations:
        print(f"\nRecommendations for Further Improvement:")
        for i, rec in enumerate(recommendations, 1):
            priority = "HIGH" if i <= 2 else "MEDIUM" if i <= 4 else "LOW"
            print(f"   {i}. [{priority}] {rec}")
    else:
        print(f"\n[EXCELLENT] No improvements needed - 95%+ target achieved!")

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())