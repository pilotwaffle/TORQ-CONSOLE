#!/usr/bin/env python3
"""
Apply Action-Oriented Learning Lesson to Prince Flowers

This script applies the lesson learned from the TikTok search feedback,
permanently teaching Prince Flowers to immediately search when users
request research/ideation instead of asking how to build a tool.

Usage:
    python scripts/apply_action_learning_lesson.py

    or

    chmod +x scripts/apply_action_learning_lesson.py
    ./scripts/apply_action_learning_lesson.py
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from torq_console.agents import apply_tiktok_lesson, get_action_learning

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Apply the TikTok search lesson and show learning stats."""
    print("\n" + "=" * 80)
    print("Applying Action-Oriented Learning Lesson to Prince Flowers")
    print("=" * 80 + "\n")

    print("📚 Teaching Prince Flowers from the TikTok search feedback...")
    print()

    # Apply the lesson
    try:
        apply_tiktok_lesson()
        print("✅ Lesson applied successfully!")
    except Exception as e:
        logger.error(f"Failed to apply lesson: {e}")
        print(f"\n❌ Error: {e}")
        return 1

    print()
    print("What was learned:")
    print("-" * 80)
    print()
    print("🎯 The Problem:")
    print("  User: 'Under ideation: search for top 2 viral TikTok videos'")
    print("  Prince: 'Would you like me to: 1) Search 2) Build a tool...'")
    print("  User: 'No! Just search!'")
    print()
    print("✨ The Solution:")
    print("  User: 'Under ideation: search for top 2 viral TikTok videos'")
    print("  Prince: *Immediately uses WebSearch and returns results*")
    print()
    print("📝 Pattern Created:")
    print("  • Name: ideation_research_immediate")
    print("  • Keywords: under ideation, search for, find, top")
    print("  • Action: IMMEDIATE_ACTION")
    print("  • Confidence: 95%")
    print()
    print("💡 Lesson:")
    print("  When user says 'under ideation' or brainstorming context with")
    print("  'search/find/look up', immediately perform the action - don't")
    print("  ask about building tools or offer multiple options.")
    print()

    # Show learning statistics
    print("=" * 80)
    print("Current Learning Statistics")
    print("=" * 80 + "\n")

    try:
        learning = get_action_learning()
        stats = learning.get_learning_summary()

        print(f"Total Action Patterns: {stats['total_patterns']}")
        print(f"  • Built-in Patterns: {stats['built_in_patterns']}")
        print(f"  • Learned Patterns: {stats['learned_patterns']}")
        print(f"  • Average Confidence: {stats['average_confidence']:.2%}")
        print()

        print("Patterns by Action Type:")
        print(f"  • Immediate Action: {stats['patterns_by_action']['immediate_action']}")
        print(f"  • Ask Clarification: {stats['patterns_by_action']['ask_clarification']}")
        print(f"  • Provide Options: {stats['patterns_by_action']['provide_options']}")
        print()

    except Exception as e:
        logger.warning(f"Could not retrieve stats: {e}")

    print("=" * 80)
    print("Next Steps")
    print("=" * 80 + "\n")

    print("1. Use Enhanced Prince Flowers in your code:")
    print("   from torq_console.agents import create_enhanced_prince_flowers")
    print("   prince = create_enhanced_prince_flowers()")
    print()

    print("2. Test the improvement:")
    print("   response = await prince.chat('search for trending topics')")
    print("   # Prince will immediately search, not ask questions")
    print()

    print("3. Provide feedback to keep learning:")
    print("   prince.record_user_feedback(")
    print("       expected_action=ActionDecision.IMMEDIATE_ACTION,")
    print("       feedback_score=0.9")
    print("   )")
    print()

    print("4. Monitor learning progress:")
    print("   stats = prince.get_learning_stats()")
    print()

    print("=" * 80)
    print("Lesson Applied Successfully! Prince Flowers will now be more action-oriented.")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
