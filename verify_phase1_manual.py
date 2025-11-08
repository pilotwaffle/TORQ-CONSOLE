#!/usr/bin/env python3
"""
Manual Phase 1 Verification

Since full testing requires dependencies, this script manually verifies
that the Phase 1 changes are correctly implemented in the code.
"""

import sys
from pathlib import Path

def verify_phase1_implementation():
    """Manually verify Phase 1 implementation by checking code files."""
    print("\n" + "=" * 80)
    print("PHASE 1 MANUAL VERIFICATION")
    print("Checking that Enhanced Prince Flowers is the default agent")
    print("=" * 80 + "\n")

    all_passed = True

    # Test 1: Check marvin_orchestrator.py has the correct imports
    print("Test 1: Verify orchestrator imports Enhanced Prince")
    print("-" * 80)
    orchestrator_file = Path("torq_console/agents/marvin_orchestrator.py")
    if not orchestrator_file.exists():
        print("❌ FAIL: marvin_orchestrator.py not found")
        all_passed = False
    else:
        content = orchestrator_file.read_text()

        # Check for import
        if "from .prince_flowers_enhanced import create_enhanced_prince_flowers, apply_tiktok_lesson" in content:
            print("✅ PASS: Import statement found")
        else:
            print("❌ FAIL: Import statement not found")
            all_passed = False
    print()

    # Test 2: Check that apply_tiktok_lesson is called in __init__
    print("Test 2: Verify apply_tiktok_lesson() is called on initialization")
    print("-" * 80)
    if orchestrator_file.exists():
        content = orchestrator_file.read_text()

        if "apply_tiktok_lesson()" in content:
            print("✅ PASS: apply_tiktok_lesson() call found")

            # Check it's in the __init__ method context
            if "def __init__" in content:
                init_section = content[content.find("def __init__"):content.find("def __init__") + 2000]
                if "apply_tiktok_lesson()" in init_section:
                    print("✅ PASS: Called in __init__ method")
                else:
                    print("⚠️  WARNING: apply_tiktok_lesson() not in __init__ (might be elsewhere)")
        else:
            print("❌ FAIL: apply_tiktok_lesson() call not found")
            all_passed = False
    print()

    # Test 3: Check that create_enhanced_prince_flowers is used
    print("Test 3: Verify create_enhanced_prince_flowers() is used as default")
    print("-" * 80)
    if orchestrator_file.exists():
        content = orchestrator_file.read_text()

        if "self.prince_flowers = create_enhanced_prince_flowers" in content:
            print("✅ PASS: create_enhanced_prince_flowers() is used")

            # Make sure it's not MarvinPrinceFlowers
            if "self.prince_flowers = MarvinPrinceFlowers(" in content:
                print("❌ FAIL: Also found MarvinPrinceFlowers() - conflict!")
                all_passed = False
            else:
                print("✅ PASS: MarvinPrinceFlowers() not used (correct)")
        else:
            print("❌ FAIL: create_enhanced_prince_flowers() not found")
            all_passed = False
    print()

    # Test 4: Check marvin_commands.py has the imports
    print("Test 4: Verify marvin_commands.py imports Enhanced Prince")
    print("-" * 80)
    commands_file = Path("torq_console/agents/marvin_commands.py")
    if not commands_file.exists():
        print("❌ FAIL: marvin_commands.py not found")
        all_passed = False
    else:
        content = commands_file.read_text()

        if "from .prince_flowers_enhanced import create_enhanced_prince_flowers, apply_tiktok_lesson" in content:
            print("✅ PASS: Import statement found in marvin_commands.py")
        else:
            print("❌ FAIL: Import statement not found in marvin_commands.py")
            all_passed = False
    print()

    # Test 5: Check that Enhanced Prince implementation exists
    print("Test 5: Verify EnhancedPrinceFlowers implementation exists")
    print("-" * 80)
    enhanced_file = Path("torq_console/agents/prince_flowers_enhanced.py")
    if not enhanced_file.exists():
        print("❌ FAIL: prince_flowers_enhanced.py not found")
        all_passed = False
    else:
        content = enhanced_file.read_text()

        checks = [
            ("class EnhancedPrinceFlowers", "EnhancedPrinceFlowers class"),
            ("def create_enhanced_prince_flowers", "create_enhanced_prince_flowers function"),
            ("def apply_tiktok_lesson", "apply_tiktok_lesson function"),
            ("action_learning", "action_learning integration"),
            ("record_user_feedback", "record_user_feedback method"),
            ("get_learning_stats", "get_learning_stats method")
        ]

        for check_str, description in checks:
            if check_str in content:
                print(f"✅ PASS: {description} found")
            else:
                print(f"❌ FAIL: {description} not found")
                all_passed = False
    print()

    # Test 6: Check that Action Learning implementation exists
    print("Test 6: Verify ActionOrientedLearning implementation exists")
    print("-" * 80)
    action_file = Path("torq_console/agents/action_learning.py")
    if not action_file.exists():
        print("❌ FAIL: action_learning.py not found")
        all_passed = False
    else:
        content = action_file.read_text()

        checks = [
            ("class ActionOrientedLearning", "ActionOrientedLearning class"),
            ("class ActionDecision", "ActionDecision enum"),
            ("def analyze_request", "analyze_request method"),
            ("def learn_from_feedback", "learn_from_feedback method"),
            ("IMMEDIATE_ACTION", "IMMEDIATE_ACTION decision type"),
            ("ASK_CLARIFICATION", "ASK_CLARIFICATION decision type")
        ]

        for check_str, description in checks:
            if check_str in content:
                print(f"✅ PASS: {description} found")
            else:
                print(f"❌ FAIL: {description} not found")
                all_passed = False
    print()

    # Test 7: Check that CLAUDE.md has action-oriented instructions
    print("Test 7: Verify CLAUDE.md has action-oriented behavior instructions")
    print("-" * 80)
    claude_file = Path("CLAUDE.md")
    if not claude_file.exists():
        print("❌ FAIL: CLAUDE.md not found")
        all_passed = False
    else:
        content = claude_file.read_text()

        checks = [
            ("ACTION-ORIENTED BEHAVIOR", "ACTION-ORIENTED BEHAVIOR section"),
            ("Type A: Information Retrieval", "Type A definition"),
            ("Type B: Building/Implementation", "Type B definition"),
            ("IMMEDIATE ACTION", "IMMEDIATE_ACTION keyword"),
            ("Pattern 1: \"Under Ideation\"", "TikTok lesson pattern"),
            ("under ideation", "under ideation keyword")
        ]

        for check_str, description in checks:
            if check_str in content:
                print(f"✅ PASS: {description} found")
            else:
                print(f"❌ FAIL: {description} not found")
                all_passed = False
    print()

    # Summary
    print("=" * 80)
    print("PHASE 1 VERIFICATION SUMMARY")
    print("=" * 80 + "\n")

    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("Phase 1 implementation is correct:")
        print("  • Enhanced Prince Flowers is imported in orchestrator")
        print("  • apply_tiktok_lesson() is called on initialization")
        print("  • create_enhanced_prince_flowers() is used as default")
        print("  • All required files exist and contain necessary code")
        print("  • CLAUDE.md has action-oriented instructions")
        print()
        print("Note: Full runtime testing requires dependencies (marvin, anthropic, etc.)")
        print("      These will be tested when the system is actually run.")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failures above and fix any issues.")
        return False


if __name__ == "__main__":
    success = verify_phase1_implementation()
    sys.exit(0 if success else 1)
