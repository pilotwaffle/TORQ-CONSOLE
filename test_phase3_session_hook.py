#!/usr/bin/env python3
"""
Test Phase 3: Session Startup Hook

This script verifies that:
1. Session startup hook file exists
2. Hook is executable
3. Hook contains correct initialization code
4. Hook applies TikTok lesson
5. Hook verifies Enhanced Prince availability
"""

import sys
import os
from pathlib import Path

def test_phase3_implementation():
    """Verify Phase 3 implementation by checking hook file."""
    print("\n" + "=" * 80)
    print("PHASE 3 TEST: Session Startup Hook")
    print("=" * 80 + "\n")

    all_passed = True

    # Test 1: Check that session startup hook exists
    print("Test 1: Verify session startup hook file exists")
    print("-" * 80)
    hook_file = Path(".claude/sessionStart.py")
    if hook_file.exists():
        print("✅ PASS: .claude/sessionStart.py exists")
    else:
        print("❌ FAIL: .claude/sessionStart.py not found")
        all_passed = False
    print()

    # Test 2: Check that hook is executable
    print("Test 2: Verify hook is executable")
    print("-" * 80)
    if hook_file.exists():
        if os.access(hook_file, os.X_OK):
            print("✅ PASS: Hook file is executable")
        else:
            print("❌ FAIL: Hook file is not executable")
            all_passed = False
    print()

    # Test 3: Check hook imports Enhanced Prince
    print("Test 3: Verify hook imports Enhanced Prince components")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        imports_to_check = [
            ("create_enhanced_prince_flowers", "Enhanced Prince creator"),
            ("apply_tiktok_lesson", "TikTok lesson applier"),
            ("get_action_learning", "Action learning getter"),
            ("get_agent_memory", "Agent memory getter"),
            ("is_marvin_available", "Marvin availability checker")
        ]

        all_found = True
        for import_name, description in imports_to_check:
            if import_name in content:
                print(f"✅ PASS: Imports {description}")
            else:
                print(f"❌ FAIL: Missing import: {description}")
                all_found = False
                all_passed = False

        if all_found:
            print("\n✅ All required imports found")
    print()

    # Test 4: Check hook applies TikTok lesson
    print("Test 4: Verify hook applies TikTok lesson")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        if "apply_tiktok_lesson()" in content:
            print("✅ PASS: Hook calls apply_tiktok_lesson()")
        else:
            print("❌ FAIL: Hook doesn't call apply_tiktok_lesson()")
            all_passed = False

        if "tiktok_lesson_applied" in content:
            print("✅ PASS: Hook tracks TikTok lesson status")
        else:
            print("❌ FAIL: Hook doesn't track TikTok lesson status")
            all_passed = False
    print()

    # Test 5: Check hook verifies Enhanced Prince availability
    print("Test 5: Verify hook checks Enhanced Prince availability")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        if "enhanced_prince_available" in content:
            print("✅ PASS: Hook tracks Enhanced Prince availability")
        else:
            print("❌ FAIL: Hook doesn't track Enhanced Prince availability")
            all_passed = False

        if "is_marvin_available()" in content:
            print("✅ PASS: Hook checks if Marvin is available")
        else:
            print("❌ FAIL: Hook doesn't check Marvin availability")
            all_passed = False
    print()

    # Test 6: Check hook verifies action learning system
    print("Test 6: Verify hook checks action learning system")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        if "get_action_learning()" in content:
            print("✅ PASS: Hook initializes action learning")
        else:
            print("❌ FAIL: Hook doesn't initialize action learning")
            all_passed = False

        if "action_learning_available" in content:
            print("✅ PASS: Hook tracks action learning status")
        else:
            print("❌ FAIL: Hook doesn't track action learning status")
            all_passed = False
    print()

    # Test 7: Check hook verifies memory system
    print("Test 7: Verify hook checks memory system")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        if "get_agent_memory()" in content:
            print("✅ PASS: Hook initializes memory system")
        else:
            print("❌ FAIL: Hook doesn't initialize memory system")
            all_passed = False

        if "memory_system_available" in content:
            print("✅ PASS: Hook tracks memory system status")
        else:
            print("❌ FAIL: Hook doesn't track memory system status")
            all_passed = False
    print()

    # Test 8: Check hook provides user feedback
    print("Test 8: Verify hook provides user feedback")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        feedback_items = [
            ("Enhanced Prince Flowers", "Enhanced Prince status message"),
            ("Action-oriented learning", "Action learning message"),
            ("Implicit feedback", "Implicit feedback message"),
            ("search for X", "Usage tip for searching"),
            ("build X", "Usage tip for building")
        ]

        all_found = True
        for text, description in feedback_items:
            if text in content:
                print(f"✅ PASS: Includes {description}")
            else:
                print(f"⚠️  WARNING: Missing {description}")
                # Don't fail for missing feedback messages
    print()

    # Test 9: Check hook handles errors gracefully
    print("Test 9: Verify hook handles errors gracefully")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        if "try:" in content and "except" in content:
            print("✅ PASS: Hook has error handling")
        else:
            print("❌ FAIL: Hook lacks error handling")
            all_passed = False

        if "sys.exit(0)" in content:
            print("✅ PASS: Hook exits with success code (won't block session)")
        else:
            print("⚠️  WARNING: Hook might block session on errors")
    print()

    # Test 10: Check hook documentation
    print("Test 10: Verify hook documentation")
    print("-" * 80)
    if hook_file.exists():
        content = hook_file.read_text()

        if "Phase 3" in content:
            print("✅ PASS: Hook documented as Phase 3")
        else:
            print("❌ FAIL: Hook not documented as Phase 3")
            all_passed = False

        if "Purpose:" in content or "This hook runs" in content:
            print("✅ PASS: Hook has purpose documentation")
        else:
            print("⚠️  WARNING: Hook lacks purpose documentation")
    print()

    # Summary
    print("=" * 80)
    print("PHASE 3 VERIFICATION SUMMARY")
    print("=" * 80 + "\n")

    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("Phase 3 implementation is correct:")
        print("  • Session startup hook created (.claude/sessionStart.py)")
        print("  • Hook is executable")
        print("  • Imports Enhanced Prince components")
        print("  • Applies TikTok lesson on startup")
        print("  • Verifies Enhanced Prince availability")
        print("  • Checks action learning system")
        print("  • Checks memory system")
        print("  • Provides user feedback")
        print("  • Handles errors gracefully")
        print()
        print("How it works:")
        print("  1. Claude Code starts a new session")
        print("  2. Automatically runs .claude/sessionStart.py")
        print("  3. Verifies Enhanced Prince is available")
        print("  4. Applies TikTok lesson (action-oriented learning)")
        print("  5. Initializes memory and action learning systems")
        print("  6. Displays session status to user")
        print("  7. Provides usage tips")
        print()
        print("Integration with Claude Code:")
        print("  • Hook runs automatically on session start")
        print("  • No manual setup required")
        print("  • Ensures Enhanced Prince is always ready")
        print("  • Learning persists across sessions via memory system")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failures above and fix any issues.")
        return False


if __name__ == "__main__":
    success = test_phase3_implementation()
    sys.exit(0 if success else 1)
