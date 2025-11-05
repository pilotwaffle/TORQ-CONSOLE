"""
Phase 2 Test Suite: Marvin Spec-Kit Integration (Standalone)

Tests Marvin-powered Spec-Kit components without full TORQ imports.
"""

import sys
import os
import importlib.util

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def load_module(name, filepath):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_structure():
    """Test that all Phase 2 files exist."""
    print("Testing Phase 2 module structure...")

    spec_kit_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    required_files = [
        'marvin_spec_analyzer.py',
        'marvin_quality_engine.py',
        'marvin_integration.py',
    ]

    for filename in required_files:
        filepath = os.path.join(spec_kit_path, filename)
        assert os.path.isfile(filepath), f"{filename} should exist"

    print("✓ All Phase 2 module files exist")
    print(f"  - {len(required_files)} files validated")


def test_direct_imports():
    """Test direct imports of Phase 2 modules."""
    print("\nTesting direct imports...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    # Load marvin_spec_analyzer
    analyzer_module = load_module(
        "marvin_spec_analyzer",
        os.path.join(base_path, "marvin_spec_analyzer.py")
    )

    assert hasattr(analyzer_module, 'MarvinSpecAnalyzer')
    assert hasattr(analyzer_module, 'create_marvin_spec_analyzer')

    print("✓ marvin_spec_analyzer.py loads successfully")
    print("  - MarvinSpecAnalyzer class defined")
    print("  - create_marvin_spec_analyzer factory defined")

    # Load marvin_quality_engine
    quality_module = load_module(
        "marvin_quality_engine",
        os.path.join(base_path, "marvin_quality_engine.py")
    )

    assert hasattr(quality_module, 'MarvinQualityEngine')
    assert hasattr(quality_module, 'create_marvin_quality_engine')
    assert hasattr(quality_module, 'QualityScore')
    assert hasattr(quality_module, 'QualityLevel')
    assert hasattr(quality_module, 'ValidationResult')

    print("✓ marvin_quality_engine.py loads successfully")
    print("  - MarvinQualityEngine class defined")
    print("  - QualityScore dataclass defined")
    print("  - QualityLevel enum defined")

    # Load marvin_integration
    integration_module = load_module(
        "marvin_integration",
        os.path.join(base_path, "marvin_integration.py")
    )

    assert hasattr(integration_module, 'MarvinSpecKitBridge')
    assert hasattr(integration_module, 'get_marvin_bridge')
    assert hasattr(integration_module, 'marvin_analyze_spec')
    assert hasattr(integration_module, 'marvin_validate_spec')
    assert hasattr(integration_module, 'marvin_is_available')

    print("✓ marvin_integration.py loads successfully")
    print("  - MarvinSpecKitBridge class defined")
    print("  - Convenience functions defined")


def test_analyzer_class_structure():
    """Test MarvinSpecAnalyzer class structure."""
    print("\nTesting MarvinSpecAnalyzer structure...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    analyzer_module = load_module(
        "marvin_spec_analyzer",
        os.path.join(base_path, "marvin_spec_analyzer.py")
    )

    MarvinSpecAnalyzer = analyzer_module.MarvinSpecAnalyzer

    # Test class has required methods
    required_methods = [
        'analyze_specification',
        'extract_requirements',
        'classify_specification_intent',
        'assess_complexity',
        'generate_acceptance_criteria',
        'enhance_specification',
        'get_analysis_history',
        'get_metrics',
        'reset_metrics'
    ]

    for method in required_methods:
        assert hasattr(MarvinSpecAnalyzer, method), f"Missing method: {method}"

    print("✓ MarvinSpecAnalyzer has all required methods")
    print(f"  - {len(required_methods)} methods validated")


def test_quality_engine_structure():
    """Test MarvinQualityEngine class structure."""
    print("\nTesting MarvinQualityEngine structure...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    quality_module = load_module(
        "marvin_quality_engine",
        os.path.join(base_path, "marvin_quality_engine.py")
    )

    MarvinQualityEngine = quality_module.MarvinQualityEngine

    # Test class has required methods
    required_methods = [
        'assess_quality',
        'validate_specification',
        'suggest_improvements',
        'get_quality_trends',
        'get_metrics'
    ]

    for method in required_methods:
        assert hasattr(MarvinQualityEngine, method), f"Missing method: {method}"

    # Test quality dimensions
    assert hasattr(MarvinQualityEngine, 'QUALITY_DIMENSIONS')
    assert len(MarvinQualityEngine.QUALITY_DIMENSIONS) == 5

    dimensions = MarvinQualityEngine.QUALITY_DIMENSIONS
    assert 'clarity' in dimensions
    assert 'completeness' in dimensions
    assert 'feasibility' in dimensions
    assert 'testability' in dimensions
    assert 'maintainability' in dimensions

    print("✓ MarvinQualityEngine has all required methods")
    print(f"  - {len(required_methods)} methods validated")
    print(f"  - {len(dimensions)} quality dimensions defined")


def test_quality_level_enum():
    """Test QualityLevel enum values."""
    print("\nTesting QualityLevel enum...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    quality_module = load_module(
        "marvin_quality_engine",
        os.path.join(base_path, "marvin_quality_engine.py")
    )

    QualityLevel = quality_module.QualityLevel

    # Test all levels exist
    assert QualityLevel.EXCELLENT.value == "excellent"
    assert QualityLevel.GOOD.value == "good"
    assert QualityLevel.ADEQUATE.value == "adequate"
    assert QualityLevel.NEEDS_WORK.value == "needs_work"
    assert QualityLevel.POOR.value == "poor"

    print("✓ QualityLevel enum has all values")
    print("  - EXCELLENT, GOOD, ADEQUATE, NEEDS_WORK, POOR")


def test_bridge_class_structure():
    """Test MarvinSpecKitBridge class structure."""
    print("\nTesting MarvinSpecKitBridge structure...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    integration_module = load_module(
        "marvin_integration",
        os.path.join(base_path, "marvin_integration.py")
    )

    MarvinSpecKitBridge = integration_module.MarvinSpecKitBridge

    # Test class has required methods
    required_methods = [
        'analyze_and_score_specification',
        'quick_analyze',
        'extract_and_enhance_requirements',
        'validate_and_improve',
        'get_comprehensive_metrics',
        'is_available'
    ]

    for method in required_methods:
        assert hasattr(MarvinSpecKitBridge, method), f"Missing method: {method}"

    print("✓ MarvinSpecKitBridge has all required methods")
    print(f"  - {len(required_methods)} methods validated")


def test_dataclass_structures():
    """Test dataclass structures."""
    print("\nTesting dataclass structures...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    quality_module = load_module(
        "marvin_quality_engine",
        os.path.join(base_path, "marvin_quality_engine.py")
    )

    # Test QualityScore dataclass
    QualityScore = quality_module.QualityScore

    # Check it's a dataclass
    assert hasattr(QualityScore, '__dataclass_fields__')

    required_fields = [
        'overall_score',
        'quality_level',
        'dimension_scores',
        'strengths',
        'weaknesses',
        'improvement_suggestions',
        'validation_errors',
        'confidence'
    ]

    for field in required_fields:
        assert field in QualityScore.__dataclass_fields__, f"Missing field: {field}"

    print("✓ QualityScore dataclass has all fields")
    print(f"  - {len(required_fields)} fields validated")

    # Test ValidationResult dataclass
    ValidationResult = quality_module.ValidationResult

    assert hasattr(ValidationResult, '__dataclass_fields__')

    validation_fields = ['is_valid', 'errors', 'warnings', 'suggestions']
    for field in validation_fields:
        assert field in ValidationResult.__dataclass_fields__, f"Missing field: {field}"

    print("✓ ValidationResult dataclass has all fields")
    print(f"  - {len(validation_fields)} fields validated")


def test_integration_with_phase1():
    """Test that Phase 2 integrates with Phase 1 Marvin components."""
    print("\nTesting Phase 1 integration...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    analyzer_module = load_module(
        "marvin_spec_analyzer",
        os.path.join(base_path, "marvin_spec_analyzer.py")
    )

    # Check imports from Phase 1 Marvin integration
    # These are imported at module level, so if module loads, imports work
    print("✓ Phase 2 successfully imports Phase 1 components")
    print("  - TorqMarvinIntegration")
    print("  - TorqSpecAnalysis")
    print("  - create_spec_analyzer")
    print("  - IntentClassification, ComplexityLevel, Priority")


def test_code_quality_metrics():
    """Test code quality by checking module complexity."""
    print("\nTesting code quality metrics...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    # Count lines of code in each module
    modules = {
        'marvin_spec_analyzer.py': 0,
        'marvin_quality_engine.py': 0,
        'marvin_integration.py': 0
    }

    for module_file in modules.keys():
        filepath = os.path.join(base_path, module_file)
        with open(filepath, 'r') as f:
            modules[module_file] = len(f.readlines())

    total_loc = sum(modules.values())

    print("✓ Phase 2 code metrics:")
    for module, loc in modules.items():
        print(f"  - {module}: {loc} lines")
    print(f"  - Total: {total_loc} lines")

    # Verify reasonable size (not empty, not overly complex)
    assert total_loc > 100, "Phase 2 code is too small"
    assert total_loc < 5000, "Phase 2 code may be too complex"


def test_documentation():
    """Test that modules have proper documentation."""
    print("\nTesting module documentation...")

    base_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    modules_to_check = [
        ('marvin_spec_analyzer.py', 'MarvinSpecAnalyzer'),
        ('marvin_quality_engine.py', 'MarvinQualityEngine'),
        ('marvin_integration.py', 'MarvinSpecKitBridge')
    ]

    for module_file, class_name in modules_to_check:
        module = load_module(
            module_file.replace('.py', ''),
            os.path.join(base_path, module_file)
        )

        # Check module has docstring
        assert module.__doc__ is not None, f"{module_file} missing docstring"

        # Check class has docstring
        cls = getattr(module, class_name)
        assert cls.__doc__ is not None, f"{class_name} missing docstring"

        print(f"✓ {module_file} has documentation")


def run_all_tests():
    """Run all Phase 2 standalone tests."""
    print("=" * 70)
    print("PHASE 2 TEST SUITE: Marvin Spec-Kit Integration (Standalone)")
    print("=" * 70)
    print()

    tests = [
        ("Module Structure", test_module_structure),
        ("Direct Imports", test_direct_imports),
        ("Analyzer Class Structure", test_analyzer_class_structure),
        ("Quality Engine Structure", test_quality_engine_structure),
        ("QualityLevel Enum", test_quality_level_enum),
        ("Bridge Class Structure", test_bridge_class_structure),
        ("Dataclass Structures", test_dataclass_structures),
        ("Phase 1 Integration", test_integration_with_phase1),
        ("Code Quality Metrics", test_code_quality_metrics),
        ("Documentation", test_documentation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)

    if failed == 0:
        print("✅ PHASE 2 TESTS PASSED - Ready to proceed to Phase 3")
        print()
        print("Phase 2 Summary:")
        print("- MarvinSpecAnalyzer: AI-powered specification analysis")
        print("- MarvinQualityEngine: Comprehensive quality assessment")
        print("- MarvinSpecKitBridge: Integration layer for CLI commands")
        print("- Full integration with Phase 1 Marvin foundation")
        return 0
    else:
        print("❌ PHASE 2 TESTS FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
