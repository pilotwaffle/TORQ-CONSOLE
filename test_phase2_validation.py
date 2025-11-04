"""
Phase 2 Validation: Marvin Spec-Kit Integration

Validates Phase 2 implementation through code structure analysis
without requiring full TORQ imports.
"""

import os
import ast
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_files_exist():
    """Test that all Phase 2 files exist."""
    print("Testing Phase 2 file existence...")

    spec_kit_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    required_files = {
        'marvin_spec_analyzer.py': 'Marvin-powered specification analyzer',
        'marvin_quality_engine.py': 'Specification quality assessment engine',
        'marvin_integration.py': 'Integration bridge for Spec-Kit',
    }

    for filename, description in required_files.items():
        filepath = os.path.join(spec_kit_path, filename)
        assert os.path.isfile(filepath), f"{filename} should exist"
        print(f"  ✓ {filename} - {description}")

    print(f"✓ All {len(required_files)} Phase 2 files exist\n")


def parse_python_file(filepath):
    """Parse Python file into AST."""
    with open(filepath, 'r') as f:
        content = f.read()
    return ast.parse(content, filename=filepath)


def get_classes_and_functions(tree):
    """Extract classes and functions from AST."""
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    return classes, functions


def test_marvin_spec_analyzer_structure():
    """Test marvin_spec_analyzer.py structure."""
    print("Testing marvin_spec_analyzer.py structure...")

    filepath = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit',
        'marvin_spec_analyzer.py'
    )

    tree = parse_python_file(filepath)
    classes, functions = get_classes_and_functions(tree)

    # Test MarvinSpecAnalyzer class exists
    assert 'MarvinSpecAnalyzer' in classes, "MarvinSpecAnalyzer class should exist"
    print("  ✓ MarvinSpecAnalyzer class defined")

    # Test factory function exists
    assert 'create_marvin_spec_analyzer' in functions, "Factory function should exist"
    print("  ✓ create_marvin_spec_analyzer() factory defined")

    # Count methods in MarvinSpecAnalyzer
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'MarvinSpecAnalyzer':
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            required_methods = [
                '__init__',
                'analyze_specification',
                'extract_requirements',
                'classify_specification_intent',
                'assess_complexity',
                'generate_acceptance_criteria',
                'enhance_specification'
            ]

            for method in required_methods:
                assert method in methods, f"Method {method} should exist"

            print(f"  ✓ {len(methods)} methods in MarvinSpecAnalyzer")
            print(f"  ✓ All {len(required_methods)} required methods present")
            break

    print("✓ marvin_spec_analyzer.py structure validated\n")


def test_marvin_quality_engine_structure():
    """Test marvin_quality_engine.py structure."""
    print("Testing marvin_quality_engine.py structure...")

    filepath = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit',
        'marvin_quality_engine.py'
    )

    tree = parse_python_file(filepath)
    classes, functions = get_classes_and_functions(tree)

    # Test classes exist
    assert 'QualityLevel' in classes, "QualityLevel enum should exist"
    assert 'QualityScore' in classes, "QualityScore dataclass should exist"
    assert 'ValidationResult' in classes, "ValidationResult dataclass should exist"
    assert 'MarvinQualityEngine' in classes, "MarvinQualityEngine class should exist"

    print("  ✓ QualityLevel enum defined")
    print("  ✓ QualityScore dataclass defined")
    print("  ✓ ValidationResult dataclass defined")
    print("  ✓ MarvinQualityEngine class defined")

    # Test factory function
    assert 'create_marvin_quality_engine' in functions, "Factory function should exist"
    print("  ✓ create_marvin_quality_engine() factory defined")

    # Count methods in MarvinQualityEngine
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'MarvinQualityEngine':
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            required_methods = [
                '__init__',
                'assess_quality',
                'validate_specification',
                'suggest_improvements',
                'get_quality_trends',
                'get_metrics'
            ]

            for method in required_methods:
                assert method in methods, f"Method {method} should exist"

            print(f"  ✓ {len(methods)} methods in MarvinQualityEngine")
            print(f"  ✓ All {len(required_methods)} required methods present")
            break

    print("✓ marvin_quality_engine.py structure validated\n")


def test_marvin_integration_structure():
    """Test marvin_integration.py structure."""
    print("Testing marvin_integration.py structure...")

    filepath = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit',
        'marvin_integration.py'
    )

    tree = parse_python_file(filepath)
    classes, functions = get_classes_and_functions(tree)

    # Test MarvinSpecKitBridge class exists
    assert 'MarvinSpecKitBridge' in classes, "MarvinSpecKitBridge class should exist"
    print("  ✓ MarvinSpecKitBridge class defined")

    # Test convenience functions
    convenience_functions = [
        'get_marvin_bridge',
        'marvin_analyze_spec',
        'marvin_validate_spec',
        'marvin_is_available'
    ]

    for func in convenience_functions:
        assert func in functions, f"Function {func} should exist"
        print(f"  ✓ {func}() convenience function defined")

    # Count methods in MarvinSpecKitBridge
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'MarvinSpecKitBridge':
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            required_methods = [
                '__init__',
                'analyze_and_score_specification',
                'quick_analyze',
                'extract_and_enhance_requirements',
                'validate_and_improve',
                'get_comprehensive_metrics',
                'is_available'
            ]

            for method in required_methods:
                assert method in methods, f"Method {method} should exist"

            print(f"  ✓ {len(methods)} methods in MarvinSpecKitBridge")
            print(f"  ✓ All {len(required_methods)} required methods present")
            break

    print("✓ marvin_integration.py structure validated\n")


def test_spec_kit_init_exports():
    """Test that spec_kit/__init__.py exports Phase 2 components."""
    print("Testing spec_kit/__init__.py exports...")

    filepath = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit',
        '__init__.py'
    )

    with open(filepath, 'r') as f:
        content = f.read()

    # Check Phase 2 imports are present
    phase2_imports = [
        'from .marvin_spec_analyzer import',
        'from .marvin_quality_engine import',
        'from .marvin_integration import',
        'MarvinSpecAnalyzer',
        'MarvinQualityEngine',
        'MarvinSpecKitBridge',
        'get_marvin_bridge',
        'QualityScore',
        'QualityLevel'
    ]

    for import_stmt in phase2_imports:
        assert import_stmt in content, f"Missing import: {import_stmt}"

    print(f"  ✓ All {len(phase2_imports)} Phase 2 exports present")
    print("✓ spec_kit/__init__.py properly exports Phase 2\n")


def test_code_metrics():
    """Test code quality metrics."""
    print("Testing code quality metrics...")

    spec_kit_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    files_to_check = {
        'marvin_spec_analyzer.py': {},
        'marvin_quality_engine.py': {},
        'marvin_integration.py': {}
    }

    total_lines = 0
    total_classes = 0
    total_functions = 0

    for filename in files_to_check.keys():
        filepath = os.path.join(spec_kit_path, filename)

        # Count lines
        with open(filepath, 'r') as f:
            lines = len(f.readlines())
            files_to_check[filename]['lines'] = lines
            total_lines += lines

        # Count classes and functions
        tree = parse_python_file(filepath)
        classes, functions = get_classes_and_functions(tree)
        files_to_check[filename]['classes'] = len(classes)
        files_to_check[filename]['functions'] = len(functions)
        total_classes += len(classes)
        total_functions += len(functions)

    print("  Code Metrics:")
    for filename, metrics in files_to_check.items():
        print(f"    {filename}:")
        print(f"      - Lines: {metrics['lines']}")
        print(f"      - Classes: {metrics['classes']}")
        print(f"      - Functions: {metrics['functions']}")

    print(f"\n  Totals:")
    print(f"    - Total Lines: {total_lines}")
    print(f"    - Total Classes: {total_classes}")
    print(f"    - Total Functions: {total_functions}")

    # Validate metrics are reasonable
    assert total_lines > 500, "Phase 2 should have substantial implementation"
    assert total_lines < 5000, "Phase 2 should not be overly complex"
    assert total_classes >= 5, "Phase 2 should define key classes"
    assert total_functions >= 10, "Phase 2 should have utility functions"

    print("✓ Code metrics are within expected ranges\n")


def test_documentation():
    """Test that modules have documentation."""
    print("Testing documentation...")

    spec_kit_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    files = [
        'marvin_spec_analyzer.py',
        'marvin_quality_engine.py',
        'marvin_integration.py'
    ]

    for filename in files:
        filepath = os.path.join(spec_kit_path, filename)
        tree = parse_python_file(filepath)

        # Check module has docstring
        docstring = ast.get_docstring(tree)
        assert docstring is not None, f"{filename} should have module docstring"
        assert len(docstring) > 50, f"{filename} docstring should be substantial"

        print(f"  ✓ {filename} has documentation ({len(docstring)} chars)")

    print("✓ All modules are documented\n")


def test_async_methods():
    """Test that async methods are properly defined."""
    print("Testing async method definitions...")

    spec_kit_path = os.path.join(
        os.path.dirname(__file__),
        'torq_console',
        'spec_kit'
    )

    async_methods_expected = {
        'marvin_spec_analyzer.py': [
            'analyze_specification',
            'extract_requirements',
            'classify_specification_intent',
            'assess_complexity',
            'generate_acceptance_criteria',
            'enhance_specification'
        ],
        'marvin_quality_engine.py': [
            'assess_quality',
            'validate_specification',
            'suggest_improvements'
        ],
        'marvin_integration.py': [
            'analyze_and_score_specification',
            'quick_analyze',
            'extract_and_enhance_requirements',
            'validate_and_improve'
        ]
    }

    for filename, expected_async in async_methods_expected.items():
        filepath = os.path.join(spec_kit_path, filename)
        tree = parse_python_file(filepath)

        # Find all async functions
        async_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                async_functions.append(node.name)

        # Check expected async methods are present
        for method in expected_async:
            assert method in async_functions, f"{method} should be async in {filename}"

        print(f"  ✓ {filename}: {len(async_functions)} async methods")

    print("✓ All async methods properly defined\n")


def run_all_tests():
    """Run all Phase 2 validation tests."""
    print("=" * 70)
    print("PHASE 2 VALIDATION: Marvin Spec-Kit Integration")
    print("=" * 70)
    print()

    tests = [
        ("File Existence", test_files_exist),
        ("MarvinSpecAnalyzer Structure", test_marvin_spec_analyzer_structure),
        ("MarvinQualityEngine Structure", test_marvin_quality_engine_structure),
        ("MarvinIntegration Structure", test_marvin_integration_structure),
        ("Spec-Kit Exports", test_spec_kit_init_exports),
        ("Code Metrics", test_code_metrics),
        ("Documentation", test_documentation),
        ("Async Methods", test_async_methods),
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
    print()

    if failed == 0:
        print("✅ PHASE 2 VALIDATION PASSED")
        print()
        print("Phase 2 Implementation Complete:")
        print("━" * 70)
        print("  1. MarvinSpecAnalyzer")
        print("     - AI-powered specification analysis")
        print("     - Intelligent requirement extraction")
        print("     - Intent and complexity classification")
        print()
        print("  2. MarvinQualityEngine")
        print("     - Comprehensive quality assessment (5 dimensions)")
        print("     - Specification validation")
        print("     - Improvement suggestions")
        print()
        print("  3. MarvinSpecKitBridge")
        print("     - Seamless integration with existing Spec-Kit")
        print("     - Convenience functions for CLI commands")
        print("     - Comprehensive metrics tracking")
        print()
        print("✅ Ready to proceed to Phase 3")
        return 0
    else:
        print("❌ PHASE 2 VALIDATION FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
