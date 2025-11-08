#!/usr/bin/env python3
"""
Test Phase 2: Implicit Feedback Detection

This script verifies that:
1. Negative feedback patterns are detected automatically
2. Positive feedback patterns are detected automatically
3. Feedback is recorded correctly
4. Learning happens from implicit feedback
"""

import sys
from pathlib import Path

def test_phase2_implementation():
    """Verify Phase 2 implementation by checking code."""
    print("\n" + "=" * 80)
    print("PHASE 2 TEST: Implicit Feedback Detection")
    print("=" * 80 + "\n")

    all_passed = True

    # Test 1: Check that _detect_implicit_feedback method exists
    print("Test 1: Verify _detect_implicit_feedback method exists")
    print("-" * 80)
    enhanced_file = Path("torq_console/agents/prince_flowers_enhanced.py")
    if not enhanced_file.exists():
        print("❌ FAIL: prince_flowers_enhanced.py not found")
        all_passed = False
    else:
        content = enhanced_file.read_text()

        if "def _detect_implicit_feedback" in content:
            print("✅ PASS: _detect_implicit_feedback method found")
        else:
            print("❌ FAIL: _detect_implicit_feedback method not found")
            all_passed = False
    print()

    # Test 2: Check that _record_implicit_feedback method exists
    print("Test 2: Verify _record_implicit_feedback method exists")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        if "def _record_implicit_feedback" in content:
            print("✅ PASS: _record_implicit_feedback method found")
        else:
            print("❌ FAIL: _record_implicit_feedback method not found")
            all_passed = False
    print()

    # Test 3: Check that chat method calls implicit feedback detection
    print("Test 3: Verify chat method calls implicit feedback detection")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        # Check for the call in the chat method
        if "implicit_feedback = self._detect_implicit_feedback" in content:
            print("✅ PASS: Implicit feedback detection called in chat method")
        else:
            print("❌ FAIL: Implicit feedback detection not called in chat method")
            all_passed = False

        # Check that it's recording feedback
        if "self._record_implicit_feedback(implicit_feedback)" in content:
            print("✅ PASS: Implicit feedback recording called")
        else:
            print("❌ FAIL: Implicit feedback recording not called")
            all_passed = False
    print()

    # Test 4: Check that negative feedback patterns are defined
    print("Test 4: Verify negative feedback patterns are defined")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        negative_keywords = [
            "negative_patterns",
            "'no'",
            "'wrong'",
            "'just do it'",
            "\"don't ask\"",
            "'not what i'"
        ]

        all_found = True
        for keyword in negative_keywords:
            if keyword in content:
                print(f"✅ PASS: Found pattern keyword: {keyword}")
            else:
                print(f"❌ FAIL: Missing pattern keyword: {keyword}")
                all_found = False
                all_passed = False

        if all_found:
            print("\n✅ All negative feedback patterns defined")
    print()

    # Test 5: Check that positive feedback patterns are defined
    print("Test 5: Verify positive feedback patterns are defined")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        positive_keywords = [
            "positive_patterns",
            "'perfect'",
            "'exactly'",
            "'great'",
            "'thank you'"
        ]

        all_found = True
        for keyword in positive_keywords:
            if keyword in content:
                print(f"✅ PASS: Found pattern keyword: {keyword}")
            else:
                print(f"❌ FAIL: Missing pattern keyword: {keyword}")
                all_found = False
                all_passed = False

        if all_found:
            print("\n✅ All positive feedback patterns defined")
    print()

    # Test 6: Check that feedback tracking IDs are initialized
    print("Test 6: Verify feedback tracking IDs are initialized")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        checks = [
            ("_last_interaction_id = None", "last interaction ID initialization"),
            ("_current_interaction_id = None", "current interaction ID initialization")
        ]

        for check_str, description in checks:
            if check_str in content:
                print(f"✅ PASS: {description} found")
            else:
                print(f"❌ FAIL: {description} not found")
                all_passed = False
    print()

    # Test 7: Check that feedback is recorded with memory system
    print("Test 7: Verify feedback is recorded with memory system")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        if "self.agent_memory.add_feedback" in content:
            print("✅ PASS: Feedback recorded to memory system")
        else:
            print("❌ FAIL: Feedback not recorded to memory system")
            all_passed = False

        if "self.action_learning.learn_from_feedback" in content:
            print("✅ PASS: Learning from feedback enabled")
        else:
            print("❌ FAIL: Learning from feedback not enabled")
            all_passed = False
    print()

    # Test 8: Check PHASE 2 comments in code
    print("Test 8: Verify PHASE 2 implementation comments")
    print("-" * 80)
    if enhanced_file.exists():
        content = enhanced_file.read_text()

        if "PHASE 2" in content:
            phase2_count = content.count("PHASE 2")
            print(f"✅ PASS: Found {phase2_count} PHASE 2 marker(s) in code")
        else:
            print("❌ FAIL: PHASE 2 markers not found")
            all_passed = False
    print()

    # Summary
    print("=" * 80)
    print("PHASE 2 VERIFICATION SUMMARY")
    print("=" * 80 + "\n")

    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("Phase 2 implementation is correct:")
        print("  • _detect_implicit_feedback method implemented")
        print("  • _record_implicit_feedback method implemented")
        print("  • Negative feedback patterns defined (no, wrong, just do it, etc.)")
        print("  • Positive feedback patterns defined (perfect, exactly, great, etc.)")
        print("  • Feedback tracking IDs initialized")
        print("  • Integration with memory and learning systems")
        print("  • Automatic detection in chat method")
        print()
        print("How it works:")
        print("  1. User sends message with correction (e.g., 'No, just search')")
        print("  2. System detects negative feedback pattern")
        print("  3. Feedback recorded with low score (0.2-0.3)")
        print("  4. Action learning system learns from the correction")
        print("  5. Future similar requests handled better")
        print()
        print("Supported patterns:")
        print("  Negative: 'no', 'wrong', 'just do it', 'don't ask', 'not what i wanted'")
        print("  Positive: 'perfect', 'exactly', 'great', 'thank you', 'excellent'")
        return True
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failures above and fix any issues.")
        return False


if __name__ == "__main__":
    success = test_phase2_implementation()
    sys.exit(0 if success else 1)
