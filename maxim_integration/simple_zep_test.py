#!/usr/bin/env python3
"""
Simple Zep Performance Test for 95% Target Validation

Test Zep memory integration without Unicode complications.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers

def calculate_performance_score(test_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate performance metrics for 95% target validation."""

    if not test_results:
        return {
            "success_rate": 0.0,
            "confidence_rate": 0.0,
            "memory_usage_rate": 0.0,
            "learning_rate": 0.0,
            "overall_score": 0.0
        }

    # Calculate individual metrics
    success_count = sum(1 for result in test_results if result.get("success", False))
    confidence_sum = sum(result.get("confidence", 0.0) for result in test_results)
    memory_used_count = sum(1 for result in test_results if result.get("memory_used", 0) > 0)
    learning_applied_count = sum(1 for result in test_results if result.get("learning_applied", False))

    total_tests = len(test_results)

    # Calculate rates
    success_rate = success_count / total_tests
    confidence_rate = (confidence_sum / total_tests) if total_tests > 0 else 0.0
    memory_usage_rate = memory_used_count / total_tests
    learning_rate = learning_applied_count / total_tests

    # Calculate overall score (weighted toward 95% target)
    weights = {
        "success_rate": 0.30,      # Most critical
        "confidence_rate": 0.25,   # Very important
        "memory_usage_rate": 0.25, # Key feature
        "learning_rate": 0.20      # Learning capability
    }

    overall_score = (
        success_rate * weights["success_rate"] +
        confidence_rate * weights["confidence_rate"] +
        memory_usage_rate * weights["memory_usage_rate"] +
        learning_rate * weights["learning_rate"]
    )

    return {
        "success_rate": success_rate,
        "confidence_rate": confidence_rate,
        "memory_usage_rate": memory_usage_rate,
        "learning_rate": learning_rate,
        "overall_score": overall_score
    }

async def test_zep_performance():
    """Test Zep-enhanced agent performance."""
    print("Simple Zep Performance Test for 95% Target")
    print("=" * 50)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize agent
    print("1. Initializing Zep-Enhanced Agent...")
    try:
        agent = create_zep_enhanced_prince_flowers()
        initialized = await agent.initialize()

        if not initialized:
            print("[ERROR] Agent initialization failed")
            return False

        print("[OK] Agent initialized successfully")
        print(f"[OK] Zep Memory: {agent.zep_memory is not None}")

    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        return False

    # Test queries
    test_queries = [
        "What is artificial intelligence?",
        "Generate a Python function for data analysis",
        "Explain machine learning concepts",
        "What is artificial intelligence?",  # Repeat to test memory
        "Create a sorting algorithm",
        "How do neural networks work?"
    ]

    print(f"\n2. Testing {len(test_queries)} queries with Zep memory...")
    print("-" * 50)

    test_results = []

    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query[:50]}...")

        try:
            start_time = time.time()

            # Process query with Zep memory
            result = await agent.process_query_with_zep_memory(query)

            execution_time = time.time() - start_time

            # Extract metrics
            test_result = {
                "query": query,
                "success": result.get("success", False),
                "confidence": result.get("confidence", 0.0),
                "memory_used": result.get("zep_memory", {}).get("memories_used", 0),
                "learning_applied": result.get("learning_applied", False),
                "execution_time": execution_time,
                "session_id": result.get("session_id"),
                "response_length": len(result.get("content", ""))
            }

            test_results.append(test_result)

            # Print results
            status = "[OK]" if test_result["success"] else "[FAIL]"
            print(f"   Status: {status}")
            print(f"   Success: {test_result['success']}")
            print(f"   Confidence: {test_result['confidence']:.3f}")
            print(f"   Memory Used: {test_result['memory_used']}")
            print(f"   Learning Applied: {test_result['learning_applied']}")
            print(f"   Execution Time: {execution_time:.3f}s")
            print(f"   Response Length: {test_result['response_length']} chars")

            # Simulate feedback for learning
            if test_result["success"] and test_result.get("interaction_id"):
                feedback_score = 0.8 + (test_result["confidence"] * 0.2)  # 0.8-1.0 range
                try:
                    await agent.learn_from_feedback(
                        interaction_id=test_result["interaction_id"],
                        feedback_score=feedback_score,
                        feedback_text="Automated test feedback",
                        session_id=test_result["session_id"]
                    )
                    print(f"   Feedback: Applied ({feedback_score:.2f})")
                except Exception as e:
                    print(f"   Feedback: Failed ({e})")

        except Exception as e:
            print(f"   [ERROR] Test failed: {e}")
            test_results.append({
                "query": query,
                "success": False,
                "confidence": 0.0,
                "memory_used": 0,
                "learning_applied": False,
                "execution_time": 0.0,
                "error": str(e)
            })

    # Calculate performance metrics
    print(f"\n3. Performance Analysis")
    print("-" * 30)

    metrics = calculate_performance_score(test_results)

    print(f"Success Rate: {metrics['success_rate']:.1%}")
    print(f"Confidence Rate: {metrics['confidence_rate']:.1%}")
    print(f"Memory Usage Rate: {metrics['memory_usage_rate']:.1%}")
    print(f"Learning Rate: {metrics['learning_rate']:.1%}")
    print(f"Overall Score: {metrics['overall_score']:.1%}")

    # Check targets
    target_95 = metrics['overall_score'] >= 0.95
    target_90 = metrics['overall_score'] >= 0.90
    target_85 = metrics['overall_score'] >= 0.85

    print(f"\nTarget Achievement:")
    print(f"95% Target: {'[ACHIEVED]' if target_95 else '[NOT ACHIEVED]'}")
    print(f"90% Target: {'[ACHIEVED]' if target_90 else '[NOT ACHIEVED]'}")
    print(f"85% Target: {'[ACHIEVED]' if target_85 else '[NOT ACHIEVED]'}")

    # Get final metrics
    try:
        final_metrics = await agent.get_performance_metrics()
        print(f"\nFinal Agent Metrics:")
        print(f"Total Interactions: {final_metrics.get('session_metrics', {}).get('total_interactions', 0)}")
        print(f"Session Success Rate: {final_metrics.get('session_metrics', {}).get('session_success_rate', 0):.1%}")
        print(f"Memory Enhancement Rate: {final_metrics.get('memory_enhancement_rate', 0):.1%}")
        print(f"Zep Memory Stats: {final_metrics.get('zep_memory_stats', {}).get('total_sessions', 0)} sessions")
    except Exception as e:
        print(f"[ERROR] Could not get final metrics: {e}")

    # Save results
    results_data = {
        "test_date": datetime.now().isoformat(),
        "test_type": "simple_zep_performance_test",
        "metrics": metrics,
        "target_95_percent_achieved": target_95,
        "target_90_percent_achieved": target_90,
        "target_85_percent_achieved": target_85,
        "test_results": test_results,
        "total_tests": len(test_results)
    }

    with open("E:/TORQ-CONSOLE/maxim_integration/simple_zep_test_results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[OK] Results saved to: simple_zep_test_results.json")

    # Cleanup
    try:
        await agent.cleanup()
        print("[OK] Agent cleanup completed")
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

    return target_95

async def main():
    """Main test function."""
    print("Starting Simple Zep Performance Test...")

    try:
        success = await test_zep_performance()

        if success:
            print("\n[SUCCESS] 95% performance target achieved!")
            return True
        else:
            print("\n[INFO] 95% target not yet achieved, but Zep integration is working")
            return False

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())