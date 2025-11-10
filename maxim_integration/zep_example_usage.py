"""
# Example: Using Zep-Enhanced Prince Flowers Agent

import asyncio
from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers

async def main():
    # Create Zep-enhanced agent
    agent = create_zep_enhanced_prince_flowers()

    # Initialize the agent
    initialized = await agent.initialize()
    if not initialized:
        print("Failed to initialize agent")
        return

    print("Zep-enhanced Prince Flowers agent ready!")

    # Process queries with memory
    queries = [
        "What is artificial intelligence?",
        "Generate a Python function for data analysis",
        "Explain machine learning concepts",
        "What is artificial intelligence?"  # Repeat to test memory
    ]

    for query in queries:
        print(f"\nQuery: {query}")

        result = await agent.process_query_with_zep_memory(query)

        print(f"Success: {result['success']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Memory Used: {result['zep_memory']['memories_used']}")
        print(f"Context Available: {result['zep_memory']['context_available']}")
        print(f"Response: {result['content'][:200]}...")

        # Learn from feedback (simulate user feedback)
        if result['success']:
            await agent.learn_from_feedback(
                interaction_id=result['interaction_id'],
                feedback_score=0.9,
                feedback_text="Great response!",
                session_id=result['session_id']
            )

    # Get performance metrics
    metrics = await agent.get_performance_metrics()
    print(f"\nPerformance Metrics:")
    print(f"  Total Interactions: {metrics['session_metrics']['total_interactions']}")
    print(f"  Success Rate: {metrics['session_metrics']['session_success_rate']:.1%}")
    print(f"  Memory Enhancement Rate: {metrics['memory_enhancement_rate']:.1%}")
    print(f"  Zep Memory Stats: {metrics['zep_memory_stats']['total_sessions']} sessions")

    # Cleanup
    await agent.cleanup()
    print("\nAgent cleaned up successfully")

if __name__ == "__main__":
    asyncio.run(main())