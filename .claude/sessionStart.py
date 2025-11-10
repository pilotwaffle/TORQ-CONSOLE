#!/usr/bin/env python3
"""
TORQ Console - Claude Code Session Startup Hook
Phase 3: Ensures Enhanced Prince Flowers is active and ready

This hook runs automatically when a Claude Code session starts.

Purpose:
- Verify Enhanced Prince Flowers agent is available
- Apply TikTok lesson (action-oriented learning)
- Initialize memory and learning systems
- Provide session status to user

Phases Applied:
- Phase 1: Enhanced Prince as default agent ✅
- Phase 2: Implicit feedback detection ✅
- Phase 3: Session startup hook ✅ (this file)
"""

import sys
import os
from pathlib import Path

# Add TORQ Console to path
torq_path = Path(__file__).parent.parent
sys.path.insert(0, str(torq_path))


def startup_hook():
    """
    Run session startup tasks.

    Returns:
        dict: Status information about the session
    """
    status = {
        'enhanced_prince_available': False,
        'tiktok_lesson_applied': False,
        'action_learning_available': False,
        'memory_system_available': False,
        'errors': []
    }

    try:
        # Import and check Enhanced Prince
        from torq_console.agents import (
            is_marvin_available,
            create_enhanced_prince_flowers,
            apply_tiktok_lesson,
            get_action_learning,
            get_agent_memory
        )

        # Check if Marvin is available
        if not is_marvin_available():
            status['errors'].append("Marvin integration not available (missing dependencies)")
            print("⚠️  TORQ Console Session: Marvin integration not available")
            print("   Install dependencies: pip install marvin anthropic")
            return status

        # Enhanced Prince is available
        status['enhanced_prince_available'] = True

        # Apply TikTok lesson (idempotent - safe to call multiple times)
        try:
            apply_tiktok_lesson()
            status['tiktok_lesson_applied'] = True
        except Exception as e:
            status['errors'].append(f"Could not apply TikTok lesson: {e}")

        # Verify action learning system
        try:
            action_learning = get_action_learning()
            summary = action_learning.get_learning_summary()
            status['action_learning_available'] = True
            status['action_patterns'] = summary.get('total_patterns', 0)
        except Exception as e:
            status['errors'].append(f"Action learning system error: {e}")

        # Verify memory system
        try:
            memory = get_agent_memory()
            snapshot = memory.get_memory_snapshot()
            status['memory_system_available'] = True
            status['total_interactions'] = snapshot.total_interactions
            status['success_rate'] = snapshot.success_rate
        except Exception as e:
            status['errors'].append(f"Memory system error: {e}")

        # Print session status
        print("\n" + "=" * 70)
        print("🌟 TORQ Console Session Ready - Enhanced Prince Flowers Active")
        print("=" * 70)
        print()

        if status['enhanced_prince_available']:
            print("✅ Enhanced Prince Flowers: Available")
            print("   • Action-oriented learning enabled")
            print("   • Immediate action on research requests")
            print("   • Implicit feedback detection active")

        if status['tiktok_lesson_applied']:
            print("✅ TikTok Lesson: Applied")
            print("   • Pattern: 'under ideation' + 'search' → immediate action")

        if status['action_learning_available']:
            print(f"✅ Action Learning: Active ({status.get('action_patterns', 0)} patterns)")

        if status['memory_system_available']:
            print(f"✅ Memory System: Active ({status.get('total_interactions', 0)} interactions)")
            if status.get('success_rate', 0) > 0:
                print(f"   • Success rate: {status['success_rate']:.1%}")

        if status['errors']:
            print("\n⚠️  Warnings:")
            for error in status['errors']:
                print(f"   • {error}")

        print()
        print("💡 Tips:")
        print("   • Say 'search for X' → I'll search immediately")
        print("   • Say 'build X' → I'll ask clarifying questions first")
        print("   • Correct me with 'No, just search' → I'll learn from it")
        print()
        print("=" * 70 + "\n")

        return status

    except ImportError as e:
        status['errors'].append(f"Import error: {e}")
        print("⚠️  TORQ Console: Could not load Enhanced Prince Flowers")
        print(f"   Error: {e}")
        print()
        return status
    except Exception as e:
        status['errors'].append(f"Unexpected error: {e}")
        print(f"⚠️  TORQ Console Session Startup Error: {e}")
        print()
        return status


if __name__ == "__main__":
    # Run startup hook
    status = startup_hook()

    # Exit with success code (0) even if there are warnings
    # We don't want to block the session from starting
    sys.exit(0)
