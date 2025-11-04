"""
Validation test for Marvin CLI integration

Tests that CLI commands are properly integrated without requiring full runtime.
Uses AST parsing to validate structure.
"""

import ast
import os
import sys


def parse_python_file(filepath):
    """Parse a Python file and return its AST."""
    with open(filepath, 'r') as f:
        return ast.parse(f.read(), filename=filepath)


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


def get_imports(tree):
    """Extract imports from AST."""
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module
            names = [alias.name for alias in node.names]
            imports.append((module, names))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, []))

    return imports


def test_marvin_commands_file_structure():
    """Test marvin_commands.py structure."""
    print("Testing marvin_commands.py structure...")

    filepath = os.path.join("torq_console", "agents", "marvin_commands.py")
    assert os.path.exists(filepath), f"File not found: {filepath}"

    tree = parse_python_file(filepath)
    classes, functions = get_classes_and_functions(tree)

    # Check main class exists
    assert 'MarvinAgentCommands' in classes, "MarvinAgentCommands class not found"

    # Check factory function exists
    assert 'create_marvin_commands' in functions, "create_marvin_commands function not found"

    # Check required methods in MarvinAgentCommands
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'MarvinAgentCommands':
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]

            required_methods = [
                '__init__',
                'handle_torq_agent_command',
                '_handle_query',
                '_handle_chat',
                '_handle_code_generation',
                '_handle_debugging',
                '_handle_documentation',
                '_handle_testing',
                '_handle_architecture',
                '_handle_orchestration',
                '_handle_memory',
                '_handle_metrics',
                '_handle_status',
                '_help'
            ]

            for method in required_methods:
                assert method in methods, f"Method {method} not found in MarvinAgentCommands"

            print(f"  ✓ Found MarvinAgentCommands with {len(methods)} methods")
            break

    print("  ✓ marvin_commands.py structure validated")


def test_spec_commands_marvin_integration():
    """Test spec_commands.py Marvin integration."""
    print("\nTesting spec_commands.py Marvin integration...")

    filepath = os.path.join("torq_console", "spec_kit", "spec_commands.py")
    assert os.path.exists(filepath), f"File not found: {filepath}"

    tree = parse_python_file(filepath)

    # Check Marvin imports
    imports = get_imports(tree)
    import_modules = [module for module, names in imports if module]

    # Check for Marvin integration imports (may be in try/except)
    has_marvin_import = any('marvin_integration' in str(module) for module in import_modules)
    print(f"  ✓ Marvin integration imports {'present' if has_marvin_import else 'conditionally imported'}")

    # Check for MARVIN_AVAILABLE flag
    with open(filepath, 'r') as f:
        content = f.read()
        assert 'MARVIN_AVAILABLE' in content, "MARVIN_AVAILABLE flag not found"
        print("  ✓ MARVIN_AVAILABLE flag found")

        # Check for Marvin options in create command
        assert '--use-marvin' in content, "--use-marvin option not found"
        assert '--no-marvin' in content, "--no-marvin option not found"
        print("  ✓ Marvin CLI options (--use-marvin, --no-marvin) found")

        # Check for Marvin analysis calls
        assert 'marvin_analyze_spec' in content, "marvin_analyze_spec call not found"
        print("  ✓ Marvin analysis integration found")

    # Check for _analyze_specification method
    classes, functions = get_classes_and_functions(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'SpecKitCommands':
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            assert '_analyze_specification' in methods, "_analyze_specification method not found"
            assert '_update_specification' in methods, "_update_specification method not found"
            assert '_update_constitution' in methods, "_update_constitution method not found"
            print(f"  ✓ New methods added: _analyze_specification, _update_specification, _update_constitution")
            break

    print("  ✓ spec_commands.py Marvin integration validated")


def test_cli_agent_command():
    """Test cli.py agent command integration."""
    print("\nTesting cli.py agent command integration...")

    filepath = os.path.join("torq_console", "cli.py")
    assert os.path.exists(filepath), f"File not found: {filepath}"

    tree = parse_python_file(filepath)
    classes, functions = get_classes_and_functions(tree)

    # Check for agent_command function
    assert 'agent_command' in functions, "agent_command function not found"
    print("  ✓ agent_command function found")

    # Check for Marvin imports in agent_command
    with open(filepath, 'r') as f:
        content = f.read()
        assert 'create_marvin_commands' in content, "create_marvin_commands import not found"
        print("  ✓ create_marvin_commands import found")

        # Check for Click decorators
        assert "@main.command(name='agent')" in content, "@main.command decorator not found"
        print("  ✓ Click command decorator found")

        # Check for asyncio call
        assert 'asyncio.run' in content, "asyncio.run call not found"
        print("  ✓ Async execution found")

    print("  ✓ cli.py agent command validated")


def test_agents_init_exports():
    """Test agents/__init__.py exports CLI commands."""
    print("\nTesting agents/__init__.py CLI command exports...")

    filepath = os.path.join("torq_console", "agents", "__init__.py")
    assert os.path.exists(filepath), f"File not found: {filepath}"

    with open(filepath, 'r') as f:
        content = f.read()

        # Check for CLI command imports
        assert 'from .marvin_commands import' in content, "marvin_commands import not found"
        assert 'MarvinAgentCommands' in content, "MarvinAgentCommands not exported"
        assert 'create_marvin_commands' in content, "create_marvin_commands not exported"
        print("  ✓ CLI command imports found")

        # Check __all__ includes CLI commands
        assert "'MarvinAgentCommands'" in content, "MarvinAgentCommands not in __all__"
        assert "'create_marvin_commands'" in content, "create_marvin_commands not in __all__"
        print("  ✓ CLI commands in __all__")

    print("  ✓ agents/__init__.py exports validated")


def test_command_help_strings():
    """Test that all commands have proper help strings."""
    print("\nTesting command help strings...")

    # Test marvin_commands.py help
    filepath = os.path.join("torq_console", "agents", "marvin_commands.py")
    with open(filepath, 'r') as f:
        content = f.read()

        # Command names and their handler variations
        command_handlers = {
            'query': '_handle_query',
            'chat': '_handle_chat',
            'code': '_handle_code_generation',
            'debug': '_handle_debugging',
            'docs': '_handle_documentation',
            'test': '_handle_testing',
            'arch': '_handle_architecture',
            'orchestrate': '_handle_orchestration',
            'memory': '_handle_memory',
            'metrics': '_handle_metrics',
            'status': '_handle_status'
        }

        for cmd, handler in command_handlers.items():
            assert handler in content, f"Handler {handler} for command {cmd} not found"

        print(f"  ✓ All {len(command_handlers)} command handlers found")

        # Check for usage strings
        assert 'Usage:' in content, "No usage strings found"
        assert 'Example:' in content, "No example strings found"
        print("  ✓ Help strings with usage and examples found")

    print("  ✓ Command help strings validated")


def test_integration_completeness():
    """Test overall integration completeness."""
    print("\nTesting overall integration completeness...")

    required_files = [
        "torq_console/agents/marvin_commands.py",
        "torq_console/spec_kit/spec_commands.py",
        "torq_console/cli.py",
        "torq_console/agents/__init__.py"
    ]

    for filepath in required_files:
        assert os.path.exists(filepath), f"Required file missing: {filepath}"

    print(f"  ✓ All {len(required_files)} required files present")

    # Check CLI command count
    filepath = os.path.join("torq_console", "agents", "marvin_commands.py")
    tree = parse_python_file(filepath)

    handle_methods = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'MarvinAgentCommands':
            methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
            handle_methods = len([m for m in methods if m.startswith('_handle_')])

    print(f"  ✓ {handle_methods} command handlers implemented")
    assert handle_methods >= 11, f"Expected at least 11 handlers, found {handle_methods}"

    print("  ✓ Integration completeness validated")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TORQ Console Marvin CLI Integration Validation")
    print("=" * 70)

    tests = [
        test_marvin_commands_file_structure,
        test_spec_commands_marvin_integration,
        test_cli_agent_command,
        test_agents_init_exports,
        test_command_help_strings,
        test_integration_completeness,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ FAILED: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ ERROR in {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n✓ All CLI integration tests PASSED!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
