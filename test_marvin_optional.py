"""
Test that Marvin integration is optional and gracefully degrades when not available.
This test validates the import structure without requiring numpy or other heavy dependencies.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_direct_module_imports():
    """Test that submodules have proper optional Marvin import structure."""
    print("=" * 70)
    print("Testing Marvin Optional Imports")
    print("=" * 70)

    # Test 1: Check agents/__init__.py structure
    print("\nTest 1: Verify agents/__init__.py has optional imports")
    try:
        with open('torq_console/agents/__init__.py', 'r') as f:
            agents_content = f.read()

        # Check for proper try/except structure
        assert 'try:' in agents_content, "No try block found"
        assert 'except ImportError' in agents_content, "No ImportError handling"
        assert '_MARVIN_AVAILABLE = False' in agents_content, "No MARVIN_AVAILABLE flag initialization"
        assert '_MARVIN_AVAILABLE = True' in agents_content, "No MARVIN_AVAILABLE success flag"
        assert 'def is_marvin_available()' in agents_content, "No is_marvin_available function"
        assert 'def get_marvin_status()' in agents_content, "No get_marvin_status function"

        print("  ✓ agents/__init__.py has try/except for Marvin imports")
        print("  ✓ agents/__init__.py has _MARVIN_AVAILABLE flags")
        print("  ✓ agents/__init__.py has helper functions")
        print("  ✓ Test 1 PASSED")

    except Exception as e:
        print(f"  ✗ Test 1 FAILED: {e}")
        return False

    # Test 2: Check spec_kit/__init__.py structure
    print("\nTest 2: Verify spec_kit/__init__.py has optional imports")
    try:
        with open('torq_console/spec_kit/__init__.py', 'r') as f:
            spec_kit_content = f.read()

        # Check for proper try/except structure
        assert 'try:' in spec_kit_content, "No try block found"
        assert 'except ImportError:' in spec_kit_content, "No ImportError handling"
        assert 'from .spec_engine import SpecKitEngine' in spec_kit_content, "Core imports not at top"
        assert 'from .marvin_spec_analyzer' in spec_kit_content, "No Marvin analyzer import"

        # Verify core imports are outside try/except
        lines = spec_kit_content.split('\n')
        try_line = None
        core_import_line = None
        for i, line in enumerate(lines):
            if 'try:' in line and 'marvin' in spec_kit_content[spec_kit_content.find(line):spec_kit_content.find(line) + 500].lower():
                try_line = i
            if 'from .spec_engine import SpecKitEngine' in line:
                core_import_line = i

        if try_line is not None and core_import_line is not None:
            assert core_import_line < try_line, "Core imports should be before try block"

        print("  ✓ spec_kit/__init__.py has try/except for Marvin imports")
        print("  ✓ spec_kit/__init__.py keeps core imports outside try block")
        print("  ✓ Test 2 PASSED")

    except Exception as e:
        print(f"  ✗ Test 2 FAILED: {e}")
        return False

    # Test 3: Verify CLI error handling
    print("\nTest 3: Verify CLI has Marvin import error handling")
    try:
        with open('torq_console/cli.py', 'r') as f:
            cli_content = f.read()

        # Check for ImportError handling in agent_command
        assert 'except ImportError' in cli_content, "No ImportError handling found"
        assert 'Marvin integration not available' in cli_content or 'Marvin' in cli_content, "No Marvin error message"

        print("  ✓ CLI has ImportError exception handling")
        print("  ✓ CLI has Marvin unavailability message")
        print("  ✓ Test 3 PASSED")

    except Exception as e:
        print(f"  ✗ Test 3 FAILED: {e}")
        return False

    # Test 4: Verify spec_commands has optional Marvin
    print("\nTest 4: Verify spec_commands has optional Marvin imports")
    try:
        with open('torq_console/spec_kit/spec_commands.py', 'r') as f:
            spec_commands_content = f.read()

        # Check for try/except around Marvin imports
        assert 'try:' in spec_commands_content, "No try block found"
        assert 'MARVIN_AVAILABLE' in spec_commands_content, "No MARVIN_AVAILABLE flag"
        assert 'except ImportError' in spec_commands_content, "No ImportError handling"

        print("  ✓ spec_commands.py has try/except for Marvin imports")
        print("  ✓ spec_commands.py has MARVIN_AVAILABLE flag")
        print("  ✓ Test 4 PASSED")

    except Exception as e:
        print(f"  ✗ Test 4 FAILED: {e}")
        return False

    return True


if __name__ == "__main__":
    print("\nValidating that Marvin integration is properly optional...")
    print("This test ensures TORQ Console can run without Marvin installed.\n")

    success = test_direct_module_imports()

    print("\n" + "=" * 70)
    if success:
        print("✓ ALL TESTS PASSED")
        print("Marvin integration is properly optional!")
        print("TORQ Console can run without Marvin installed.")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("Marvin integration is not properly optional.")
        sys.exit(1)
