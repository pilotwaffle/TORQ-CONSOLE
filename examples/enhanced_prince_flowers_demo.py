"""
Enhanced Prince Flowers with Action-Oriented Learning - Demo

This demo shows how the enhanced Prince Flowers agent learns from feedback
and makes better action decisions.
"""

import asyncio
from torq_console.agents import (
    create_enhanced_prince_flowers,
    apply_tiktok_lesson,
    ActionDecision,
    get_action_learning
)


async def demo_1_apply_tiktok_lesson():
    """
    Demo 1: Apply the TikTok Search Lesson

    This permanently teaches Prince Flowers to immediately search
    when users say "under ideation: search for X".
    """
    print("\n" + "=" * 80)
    print("DEMO 1: Applying TikTok Search Lesson")
    print("=" * 80 + "\n")

    print("Teaching Prince Flowers the lesson from the TikTok search feedback...")
    print("Lesson: When user says 'under ideation: search X', immediately search!")
    print()

    # Apply the lesson
    apply_tiktok_lesson()

    print("✅ Lesson applied successfully!")
    print()
    print("What was learned:")
    print("  - Pattern: 'under ideation' + 'search for' → IMMEDIATE_ACTION")
    print("  - Keywords: under ideation, search for, find, top")
    print("  - Confidence: 95%")
    print()
    print("Now when users request research/ideation, Prince will act immediately!")


async def demo_2_action_analysis():
    """
    Demo 2: Analyze Different Request Types

    Shows how the action learning system analyzes different types of requests.
    """
    print("\n" + "=" * 80)
    print("DEMO 2: Request Action Analysis")
    print("=" * 80 + "\n")

    action_learning = get_action_learning()

    test_requests = [
        "search for top viral TikTok videos",
        "under ideation: find best React libraries",
        "build a tool to search TikTok",
        "explain how async/await works",
        "help me choose a database",
        "find the latest AI news"
    ]

    print("Analyzing various request types:\n")

    for request in test_requests:
        analysis = action_learning.analyze_request(request)

        print(f"Request: \"{request}\"")
        print(f"  → Action: {analysis['recommended_action'].value.upper()}")
        print(f"  → Confidence: {analysis['confidence']:.2f}")
        print(f"  → Reasoning: {analysis['reasoning']}")
        print()


async def demo_3_enhanced_prince_chat():
    """
    Demo 3: Using Enhanced Prince Flowers

    Shows how to use the enhanced agent with action-oriented behavior.
    """
    print("\n" + "=" * 80)
    print("DEMO 3: Enhanced Prince Flowers in Action")
    print("=" * 80 + "\n")

    # Create enhanced agent
    prince = create_enhanced_prince_flowers()

    print("Created Enhanced Prince Flowers agent")
    print()

    # Example 1: Research request (should act immediately)
    print("Example 1: Research Request")
    print("-" * 40)
    research_request = "search for top 5 programming languages in 2025"
    print(f"User: {research_request}")
    print()

    # In a real scenario, Prince would immediately use WebSearch
    # For demo, we'll just show the action analysis
    action_learning = get_action_learning()
    analysis = action_learning.analyze_request(research_request)

    print(f"Prince's Action Decision: {analysis['recommended_action'].value}")
    print(f"Confidence: {analysis['confidence']:.2f}")
    print(f"What Prince does: Immediately uses WebSearch tool (no questions asked)")
    print()

    # Example 2: Build request (should ask clarification)
    print("Example 2: Build Request")
    print("-" * 40)
    build_request = "build a tool to monitor API performance"
    print(f"User: {build_request}")
    print()

    analysis2 = action_learning.analyze_request(build_request)
    print(f"Prince's Action Decision: {analysis2['recommended_action'].value}")
    print(f"Confidence: {analysis2['confidence']:.2f}")
    print(f"What Prince does: Asks 2-3 targeted clarifying questions")
    print()


async def demo_4_feedback_learning():
    """
    Demo 4: Learning from Feedback

    Shows how to provide feedback and how Prince learns from it.
    """
    print("\n" + "=" * 80)
    print("DEMO 4: Learning from User Feedback")
    print("=" * 80 + "\n")

    prince = create_enhanced_prince_flowers()

    print("Scenario: User wants immediate research, but Prince asked questions")
    print()

    # Simulate the interaction
    user_request = "find trending AI tools"
    print(f"User: {user_request}")
    print()

    # Simulate Prince asking instead of searching (wrong action)
    print("Prince (BAD): Would you like me to:")
    print("  1) Use WebSearch to find trending AI tools")
    print("  2) Build a TypeScript application to search...")
    print()

    # User provides feedback
    print("User feedback: 'No, just search! Don't ask me how'")
    print("Feedback score: 0.2 (low = bad response)")
    print()

    # Record the feedback
    prince.record_user_feedback(
        expected_action=ActionDecision.IMMEDIATE_ACTION,
        feedback_score=0.2,
        feedback_comment="Just search, don't ask how"
    )

    print("✅ Feedback recorded and learned!")
    print()
    print("What Prince learned:")
    print("  - 'find trending X' → IMMEDIATE_ACTION")
    print("  - Don't offer options for simple research requests")
    print("  - User expects action, not discussion")
    print()
    print("Next time Prince sees 'find trending X', he'll immediately search!")


async def demo_5_learning_stats():
    """
    Demo 5: View Learning Statistics

    Shows the learning progress and statistics.
    """
    print("\n" + "=" * 80)
    print("DEMO 5: Learning Statistics")
    print("=" * 80 + "\n")

    action_learning = get_action_learning()
    stats = action_learning.get_learning_summary()

    print("Action-Oriented Learning Statistics:")
    print("-" * 40)
    print(f"Total Patterns: {stats['total_patterns']}")
    print(f"Built-in Patterns: {stats['built_in_patterns']}")
    print(f"Learned Patterns: {stats['learned_patterns']}")
    print(f"Average Confidence: {stats['average_confidence']:.2f}")
    print()

    print("Patterns by Action Type:")
    print(f"  • Immediate Action: {stats['patterns_by_action']['immediate_action']}")
    print(f"  • Ask Clarification: {stats['patterns_by_action']['ask_clarification']}")
    print(f"  • Provide Options: {stats['patterns_by_action']['provide_options']}")
    print()

    # If enhanced Prince was used, show agent stats
    print("These patterns help Prince make better decisions about:")
    print("  ✓ When to immediately search/research")
    print("  ✓ When to ask clarifying questions")
    print("  ✓ When to offer multiple approaches")


async def demo_6_real_world_usage():
    """
    Demo 6: Real-World Usage Pattern

    Shows how to integrate enhanced Prince into real applications.
    """
    print("\n" + "=" * 80)
    print("DEMO 6: Real-World Usage Pattern")
    print("=" * 80 + "\n")

    print("Example: Integrating Enhanced Prince into a chatbot")
    print()

    code_example = '''
from torq_console.agents import create_enhanced_prince_flowers, ActionDecision

# 1. Create enhanced Prince (one time, at app startup)
prince = create_enhanced_prince_flowers()

# 2. Handle user messages
async def handle_user_message(user_message: str):
    """Handle incoming user message with action-oriented behavior."""

    # Prince automatically analyzes and decides action vs clarification
    response = await prince.chat(user_message)

    return response

# 3. Optional: Provide feedback for learning
async def handle_user_feedback(expected_action: str, score: float):
    """Record user feedback to improve future responses."""

    prince.record_user_feedback(
        expected_action=ActionDecision(expected_action),
        feedback_score=score
    )

# 4. View learning progress
def get_learning_progress():
    """Get statistics about learning and improvement."""

    stats = prince.get_learning_stats()
    return stats

# Usage examples:
# await handle_user_message("search for top AI tools")  # Immediate search
# await handle_user_message("build a monitoring dashboard")  # Ask questions
# await handle_user_feedback("immediate_action", 0.9)  # Good response
    '''

    print(code_example)
    print()
    print("Key Benefits:")
    print("  ✓ Learns from every interaction")
    print("  ✓ Improves action decisions over time")
    print("  ✓ Reduces unnecessary clarification questions")
    print("  ✓ More efficient user experience")


async def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("Enhanced Prince Flowers - Action-Oriented Learning Demo")
    print("=" * 80)

    # Run all demos
    await demo_1_apply_tiktok_lesson()
    await demo_2_action_analysis()
    await demo_3_enhanced_prince_chat()
    await demo_4_feedback_learning()
    await demo_5_learning_stats()
    await demo_6_real_world_usage()

    print("\n" + "=" * 80)
    print("All demos completed!")
    print("=" * 80 + "\n")

    print("Next Steps:")
    print("  1. Use create_enhanced_prince_flowers() instead of create_prince_flowers_agent()")
    print("  2. Apply the TikTok lesson: apply_tiktok_lesson()")
    print("  3. Provide feedback using prince.record_user_feedback()")
    print("  4. Monitor learning with prince.get_learning_stats()")
    print()


if __name__ == "__main__":
    # Run the demos
    asyncio.run(main())
