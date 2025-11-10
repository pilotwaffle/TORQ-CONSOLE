#!/usr/bin/env python3
"""
Configure LLM Provider and Test Complete 95%+ Performance System

This script configures the Claude LLM provider and runs the complete
Zep-enhanced Prince Flowers agent to validate 95%+ performance target.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Add TORQ Console to path
sys.path.append('E:/TORQ-CONSOLE')

from torq_console.llm.providers.claude import ClaudeProvider
from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

async def configure_and_test_complete_system():
    """Configure LLM provider and test complete system."""
    print("CONFIGURING LLM PROVIDER & TESTING COMPLETE SYSTEM")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Configure LLM Provider
    print("\n1. Configuring Claude LLM Provider...")
    print("-" * 40)

    try:
        # Get Anthropic configuration
        api_key = os.getenv('ANTHROPIC_AUTH_TOKEN')
        base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
        model = os.getenv('ANTHROPIC_DEFAULT_SONNET_MODEL', 'claude-sonnet-4-5-20250929')

        if not api_key:
            print("[ERROR] No ANTHROPIC_AUTH_TOKEN found in environment")
            return False

        # Create Claude provider configuration
        claude_config = {
            'api_key': api_key,
            'model': model,
            'base_url': base_url,
            'timeout': 60
        }

        # Initialize Claude provider
        llm_provider = ClaudeProvider(claude_config)

        if not llm_provider.is_configured():
            print("[ERROR] Claude provider not properly configured")
            return False

        print("[OK] Claude provider configured successfully")
        print(f"[OK] Model: {model}")
        print(f"[OK] Base URL: {base_url}")

    except Exception as e:
        print(f"[ERROR] Failed to configure LLM provider: {e}")
        return False

    # Step 2: Initialize Zep-Enhanced Agent with LLM
    print("\n2. Initializing Zep-Enhanced Agent with LLM...")
    print("-" * 40)

    try:
        agent = create_zep_enhanced_prince_flowers(llm_provider=llm_provider)
        initialized = await agent.initialize()

        if not initialized:
            print("[ERROR] Agent initialization failed")
            return False

        print("[OK] Agent initialized successfully")
        print(f"[OK] Zep Memory: {agent.zep_memory is not None}")
        print(f"[OK] LLM Provider: {agent.llm_provider is not None}")
        print(f"[OK] Maxim Tools: {agent.maxim_tools is not None}")

    except Exception as e:
        print(f"[ERROR] Agent initialization failed: {e}")
        return False

    # Step 3: Test Complete System Performance
    print("\n3. Testing Complete System Performance...")
    print("-" * 40)

    test_queries = [
        "What is artificial intelligence and how does it work?",
        "Generate a Python function for sentiment analysis",
        "Explain the key differences between SQL and NoSQL databases",
        "What is artificial intelligence and how does it work?",  # Repeat for memory test
        "Create a sorting algorithm in Python",
        "How do neural networks learn from data?"
    ]

    test_results = []

    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: {query[:50]}...")

        try:
            start_time = time.time()

            # Process query with complete system
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
                "response_length": len(result.get("content", "")),
                "tools_used": result.get("tools_used", []),
                "response_preview": result.get("content", "")[:100] + "..." if len(result.get("content", "")) > 100 else result.get("content", "")
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
            print(f"   Tools Used: {test_result['tools_used']}")
            print(f"   Response: {test_result['response_preview']}")

            # Simulate feedback for learning
            if test_result["success"] and test_result.get("interaction_id"):
                feedback_score = 0.8 + (test_result["confidence"] * 0.2)
                try:
                    await agent.learn_from_feedback(
                        interaction_id=test_result["interaction_id"],
                        feedback_score=feedback_score,
                        feedback_text="Complete system test feedback",
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

    # Step 4: Calculate Performance Metrics
    print(f"\n4. Performance Analysis")
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

    # Step 5: Get Final Agent Metrics
    print(f"\n5. Final System Metrics")
    print("-" * 30)

    try:
        final_metrics = await agent.get_performance_metrics()
        print(f"Total Interactions: {final_metrics.get('session_metrics', {}).get('total_interactions', 0)}")
        print(f"Session Success Rate: {final_metrics.get('session_metrics', {}).get('session_success_rate', 0):.1%}")
        print(f"Memory Enhancement Rate: {final_metrics.get('memory_enhancement_rate', 0):.1%}")
        print(f"Zep Memory Stats: {final_metrics.get('zep_memory_stats', {}).get('total_sessions', 0)} sessions")
    except Exception as e:
        print(f"[ERROR] Could not get final metrics: {e}")

    # Step 6: Save Results
    results_data = {
        "test_date": datetime.now().isoformat(),
        "test_type": "complete_system_with_llm_95_percent_target",
        "llm_provider": {
            "type": "Claude",
            "model": model,
            "configured": True
        },
        "metrics": metrics,
        "target_95_percent_achieved": target_95,
        "target_90_percent_achieved": target_90,
        "target_85_percent_achieved": target_85,
        "test_results": test_results,
        "total_tests": len(test_results)
    }

    with open("E:/TORQ-CONSOLE/maxim_integration/complete_system_test_results.json", "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[OK] Results saved to: complete_system_test_results.json")

    # Cleanup
    try:
        await agent.cleanup()
        print("[OK] Agent cleanup completed")
    except Exception as e:
        print(f"[WARNING] Cleanup failed: {e}")

    return target_95

async def main():
    """Main function to configure and test complete system."""
    print("Starting Complete System Configuration and Test...")

    try:
        success = await configure_and_test_complete_system()

        if success:
            print("\n[SUCCESS] 95% performance target ACHIEVED!")
            print("Complete system with LLM + Zep memory is working perfectly!")
            return True
        else:
            print("\n[INFO] System configured but 95% target not yet achieved")
            print("Check the results for areas of improvement.")
            return False

    except Exception as e:
        print(f"\n[ERROR] Complete system test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())