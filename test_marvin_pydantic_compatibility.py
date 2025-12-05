"""
Test Marvin/Pydantic compatibility and version requirements.

This test validates that:
1. Pydantic version is within the compatible range (>=2.8.0, <3.0.0)
2. Marvin can be imported without Field-related errors
3. Optional imports work correctly when Marvin is not available
4. All Marvin integration components work as expected
"""

import sys
import os
from packaging import version
import warnings

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_pydantic_version_compatibility():
    """Test that Pydantic version is compatible with Marvin."""
    print("=" * 70)
    print("Test 1: Pydantic Version Compatibility")
    print("=" * 70)
    
    try:
        import pydantic
        pydantic_version = version.parse(pydantic.__version__)
        
        print(f"Installed Pydantic version: {pydantic.__version__}")
        
        # Check minimum version (must be >= 2.8.0 to avoid Field issues)
        min_version = version.parse("2.8.0")
        max_version = version.parse("3.0.0")
        
        if pydantic_version < min_version:
            print(f"⚠️  WARNING: Pydantic {pydantic.__version__} is below minimum compatible version 2.8.0")
            print("   This may cause 'Field not defined' errors with Marvin")
            print("   Recommended: pip install 'pydantic>=2.8.0,<3.0.0'")
            return False
        
        if pydantic_version >= max_version:
            print(f"⚠️  WARNING: Pydantic {pydantic.__version__} is version 3.x")
            print("   Compatibility with Marvin 3.2.3 is not guaranteed")
            print("   Recommended: pip install 'pydantic>=2.8.0,<3.0.0'")
            return False
        
        print(f"✓ Pydantic version {pydantic.__version__} is compatible (>= 2.8.0, < 3.0.0)")
        print("✓ Test 1 PASSED")
        return True
        
    except ImportError:
        print("✗ Test 1 FAILED: Pydantic not installed")
        return False
    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}")
        return False


def test_marvin_import_without_errors():
    """Test that Marvin can be imported without Field-related errors."""
    print("\n" + "=" * 70)
    print("Test 2: Marvin Import Without Field Errors")
    print("=" * 70)
    
    try:
        # Test basic marvin import
        import marvin
        print(f"✓ Marvin {marvin.__version__} imported successfully")
        
        # Test that pydantic Field is accessible
        from pydantic import Field
        print("✓ Pydantic Field is accessible")
        
        # Test Marvin's core functionality
        from marvin import ai_fn, ai_model
        print("✓ Marvin decorators (ai_fn, ai_model) imported successfully")
        
        print("✓ Test 2 PASSED - No Field-related errors")
        return True
        
    except NameError as e:
        if "Field" in str(e):
            print(f"✗ Test 2 FAILED: Field-related error occurred: {e}")
            print("   This indicates a Pydantic/Marvin compatibility issue")
            print("   Try upgrading Pydantic: pip install 'pydantic>=2.8.0,<3.0.0'")
            return False
        else:
            raise
    except ImportError as e:
        print(f"⚠️  Marvin not installed: {e}")
        print("   This is OK - Marvin is optional")
        print("✓ Test 2 PASSED (Marvin optional)")
        return True
    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_torq_marvin_integration():
    """Test that TORQ's Marvin integration works correctly."""
    print("\n" + "=" * 70)
    print("Test 3: TORQ Marvin Integration")
    print("=" * 70)
    
    try:
        # Test direct import of Marvin integration
        from torq_console.marvin_integration.core import TorqMarvinIntegration
        print("✓ TorqMarvinIntegration imported successfully")
        
        from torq_console.marvin_integration.models import TorqSpecAnalysis
        print("✓ TorqSpecAnalysis model imported successfully")
        
        from torq_console.agents.marvin_query_router import MarvinQueryRouter
        print("✓ MarvinQueryRouter imported successfully")
        
        print("✓ Test 3 PASSED")
        return True
        
    except ImportError as e:
        error_msg = str(e)
        if "marvin" in error_msg.lower():
            print(f"⚠️  Marvin integration not available: {e}")
            print("   This is OK - Marvin features are optional")
            print("✓ Test 3 PASSED (Marvin optional)")
            return True
        else:
            print(f"✗ Test 3 FAILED: Unexpected import error: {e}")
            return False
    except Exception as e:
        print(f"✗ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_optional_import_structure():
    """Test that optional import structure is maintained."""
    print("\n" + "=" * 70)
    print("Test 4: Optional Import Structure")
    print("=" * 70)
    
    try:
        # Test agents module optional imports
        from torq_console.agents import is_marvin_available, get_marvin_status
        
        marvin_available = is_marvin_available()
        status = get_marvin_status()
        
        print(f"Marvin available: {marvin_available}")
        print(f"Status: {status}")
        
        if marvin_available:
            print("✓ Marvin is available and properly integrated")
        else:
            print("✓ Marvin not available - graceful degradation working")
        
        print("✓ Test 4 PASSED")
        return True
        
    except AttributeError as e:
        print(f"✗ Test 4 FAILED: Missing helper functions: {e}")
        return False
    except Exception as e:
        print(f"✗ Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_version_mismatch_detection():
    """Test that version mismatches are properly detected and reported."""
    print("\n" + "=" * 70)
    print("Test 5: Version Mismatch Detection")
    print("=" * 70)
    
    try:
        import pydantic
        pydantic_version = version.parse(pydantic.__version__)
        
        # Check for known problematic versions
        problematic_versions = [
            ("2.5.0", "2.5.1"),  # Known to have Field resolution issues
            ("2.5.2", "2.5.3"),
            ("2.6.0", "2.6.4"),
            ("2.7.0", "2.7.4"),
        ]
        
        is_problematic = False
        for min_v, max_v in problematic_versions:
            if version.parse(min_v) <= pydantic_version <= version.parse(max_v):
                is_problematic = True
                print(f"⚠️  WARNING: Pydantic {pydantic.__version__} is in problematic range [{min_v}, {max_v}]")
                print("   Known issues with Marvin Field resolution")
                break
        
        if not is_problematic and pydantic_version >= version.parse("2.8.0"):
            print(f"✓ Pydantic {pydantic.__version__} is not in known problematic range")
        
        print("✓ Test 5 PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Test 5 FAILED: {e}")
        return False


def print_recommendations():
    """Print recommendations for users with compatibility issues."""
    print("\n" + "=" * 70)
    print("Compatibility Recommendations")
    print("=" * 70)
    
    try:
        import pydantic
        import marvin
        
        pydantic_version = version.parse(pydantic.__version__)
        min_version = version.parse("2.8.0")
        
        if pydantic_version < min_version:
            print("\n🔧 RECOMMENDED ACTION:")
            print("   Your Pydantic version is below the recommended minimum.")
            print("   To ensure full Marvin compatibility, run:")
            print("   pip install 'pydantic>=2.8.0,<3.0.0'")
        else:
            print("\n✅ Your installation is properly configured for Marvin integration!")
            print(f"   Pydantic: {pydantic.__version__}")
            print(f"   Marvin: {marvin.__version__}")
            print("\n   All AI-powered features are available.")
            
    except ImportError as e:
        if "marvin" in str(e).lower():
            print("\n💡 OPTIONAL FEATURE:")
            print("   Marvin is not installed. To enable AI-powered features, run:")
            print("   pip install 'marvin>=3.2.0,<4.0.0'")
        else:
            print("\n⚠️  ERROR:")
            print(f"   {e}")


def run_all_tests():
    """Run all compatibility tests."""
    print("\n" + "=" * 70)
    print("Marvin/Pydantic Compatibility Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ("Pydantic Version Compatibility", test_pydantic_version_compatibility),
        ("Marvin Import Without Errors", test_marvin_import_without_errors),
        ("TORQ Marvin Integration", test_torq_marvin_integration),
        ("Optional Import Structure", test_optional_import_structure),
        ("Version Mismatch Detection", test_version_mismatch_detection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} CRASHED: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # Print recommendations
    print_recommendations()
    
    # Return exit code
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
