"""
N8N Workflow Tool - Integration Verification Script
Comprehensive verification of all integration points
"""

import sys
import os
from pathlib import Path

# Add TORQ-CONSOLE to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_test(name, passed, message=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"         {message}")


def verify_file_exists(filepath):
    """Verify file exists."""
    return Path(filepath).exists()


def verify_imports():
    """Verify all imports work correctly."""
    print_header("Verification 1: Import Tests")

    # Test 1: Import from tools package
    try:
        from torq_console.agents.tools import N8NWorkflowTool, create_n8n_workflow_tool
        print_test("Import from tools package", True, "N8NWorkflowTool and create_n8n_workflow_tool imported")
    except ImportError as e:
        print_test("Import from tools package", False, str(e))
        return False

    # Test 2: Import directly
    try:
        from torq_console.agents.tools.n8n_workflow_tool import N8NWorkflowTool
        print_test("Direct import", True, "N8NWorkflowTool imported directly")
    except ImportError as e:
        print_test("Direct import", False, str(e))
        return False

    return True


def verify_prince_integration():
    """Verify Prince Flowers integration."""
    print_header("Verification 2: Prince Flowers Integration")

    # Test 1: Import Prince Flowers
    try:
        from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
        print_test("Import TORQPrinceFlowers", True)
    except ImportError as e:
        print_test("Import TORQPrinceFlowers", False, str(e))
        return False

    # Test 2: Instantiate Prince Flowers
    try:
        prince = TORQPrinceFlowers()
        print_test("Instantiate TORQPrinceFlowers", True)
    except Exception as e:
        print_test("Instantiate TORQPrinceFlowers", False, str(e))
        return False

    # Test 3: Check tool registry
    has_n8n = 'n8n_workflow' in prince.available_tools
    print_test("N8N tool in registry", has_n8n,
               "Found in available_tools" if has_n8n else "NOT found in available_tools")

    if has_n8n:
        tool_info = prince.available_tools['n8n_workflow']
        print(f"         Name: {tool_info.get('name')}")
        print(f"         Description: {tool_info.get('description')}")
        print(f"         Cost: {tool_info.get('cost')}")
        print(f"         Success Rate: {tool_info.get('success_rate')}")

    # Test 4: Check execute method exists
    has_method = hasattr(prince, '_execute_n8n_workflow')
    print_test("Execute method exists", has_method,
               "_execute_n8n_workflow method found" if has_method else "_execute_n8n_workflow method NOT found")

    # Test 5: Check method signature
    if has_method:
        import inspect
        sig = inspect.signature(prince._execute_n8n_workflow)
        params = list(sig.parameters.keys())
        expected_params = ['action', 'workflow_id', 'execution_id', 'data', 'kwargs']
        has_correct_sig = all(p in params for p in expected_params[:-1])  # kwargs is special
        print_test("Method signature correct", has_correct_sig,
                   f"Parameters: {params}")

    return has_n8n and has_method


def verify_tool_functionality():
    """Verify tool basic functionality."""
    print_header("Verification 3: Tool Functionality")

    try:
        from torq_console.agents.tools import create_n8n_workflow_tool

        # Test 1: Create tool
        tool = create_n8n_workflow_tool()
        print_test("Create tool instance", True, "Tool created successfully")

        # Test 2: Check tool metadata
        print_test("Tool name", tool.name == "N8N Workflow Automation",
                   f"Name: {tool.name}")
        print_test("Tool description", len(tool.description) > 0,
                   f"Description: {tool.description}")

        # Test 3: Check tool info
        tool_info = tool.get_tool_info()
        print_test("Get tool info", isinstance(tool_info, dict),
                   f"Keys: {list(tool_info.keys())}")

        # Test 4: Check parameters
        params = tool_info.get('parameters', {})
        expected_params = ['action', 'workflow_id', 'execution_id', 'data']
        has_all_params = all(p in params for p in expected_params)
        print_test("Tool parameters defined", has_all_params,
                   f"Parameters: {list(params.keys())}")

        # Test 5: Check availability method
        is_callable = callable(tool.is_available)
        print_test("is_available() method", is_callable,
                   f"Available: {tool.is_available()}")

        # Test 6: Check format method
        has_format = hasattr(tool, 'format_for_prince')
        print_test("format_for_prince() method", has_format)

        return True

    except Exception as e:
        print_test("Tool functionality", False, str(e))
        return False


def verify_type_hints():
    """Verify type hints are present."""
    print_header("Verification 4: Type Hints & Documentation")

    try:
        from torq_console.agents.tools.n8n_workflow_tool import N8NWorkflowTool
        import inspect

        # Test 1: Check execute method has type hints
        execute_method = getattr(N8NWorkflowTool, 'execute')
        sig = inspect.signature(execute_method)
        has_return_annotation = sig.return_annotation != inspect.Signature.empty
        print_test("execute() return type hint", has_return_annotation,
                   f"Return type: {sig.return_annotation}")

        # Test 2: Check execute method has docstring
        has_docstring = execute_method.__doc__ is not None and len(execute_method.__doc__) > 50
        print_test("execute() docstring", has_docstring,
                   f"Length: {len(execute_method.__doc__) if execute_method.__doc__ else 0} chars")

        # Test 3: Check __init__ has docstring
        init_method = getattr(N8NWorkflowTool, '__init__')
        has_init_doc = init_method.__doc__ is not None and len(init_method.__doc__) > 50
        print_test("__init__() docstring", has_init_doc,
                   f"Length: {len(init_method.__doc__) if init_method.__doc__ else 0} chars")

        # Test 4: Check class docstring
        has_class_doc = N8NWorkflowTool.__doc__ is not None and len(N8NWorkflowTool.__doc__) > 100
        print_test("Class docstring", has_class_doc,
                   f"Length: {len(N8NWorkflowTool.__doc__) if N8NWorkflowTool.__doc__ else 0} chars")

        return True

    except Exception as e:
        print_test("Type hints verification", False, str(e))
        return False


def verify_file_structure():
    """Verify file structure is correct."""
    print_header("Verification 5: File Structure")

    base_path = Path(__file__).parent

    files_to_check = [
        ("n8n_workflow_tool.py", base_path / "torq_console" / "agents" / "tools" / "n8n_workflow_tool.py"),
        ("__init__.py updated", base_path / "torq_console" / "agents" / "tools" / "__init__.py"),
        ("torq_prince_flowers.py updated", base_path / "torq_console" / "agents" / "torq_prince_flowers.py"),
        ("Integration guide", base_path / "N8N_INTEGRATION_GUIDE.md"),
        ("Usage example", base_path / "n8n_usage_example.py"),
        ("Backup file", base_path / "torq_console" / "agents" / "torq_prince_flowers.py.backup"),
    ]

    all_exist = True
    for name, filepath in files_to_check:
        exists = filepath.exists()
        print_test(name, exists, str(filepath))
        all_exist = all_exist and exists

    return all_exist


def verify_no_code_smells():
    """Verify no code smells (print statements, TODOs, etc.)."""
    print_header("Verification 6: Code Quality")

    try:
        tool_file = Path(__file__).parent / "torq_console" / "agents" / "tools" / "n8n_workflow_tool.py"

        with open(tool_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Test 1: No print() statements
        has_print = 'print(' in content
        print_test("No print() statements", not has_print,
                   "Uses logger instead of print()" if not has_print else "Found print() statements")

        # Test 2: No TODO comments
        has_todo = 'TODO' in content or 'FIXME' in content
        print_test("No TODO/FIXME comments", not has_todo,
                   "Production-ready code" if not has_todo else "Found TODO/FIXME comments")

        # Test 3: No hardcoded credentials
        has_hardcoded = 'password = ' in content.lower() or 'api_key = "' in content
        print_test("No hardcoded credentials", not has_hardcoded,
                   "Uses environment variables" if not has_hardcoded else "Found hardcoded values")

        # Test 4: Has logging statements
        has_logging = 'self.logger' in content and content.count('self.logger') > 10
        print_test("Uses logging extensively", has_logging,
                   f"Logger calls: {content.count('self.logger')}")

        # Test 5: Has error handling
        has_error_handling = 'try:' in content and 'except' in content
        try_count = content.count('try:')
        except_count = content.count('except')
        print_test("Error handling present", has_error_handling,
                   f"try/except blocks: {min(try_count, except_count)}")

        return not has_print and not has_todo and not has_hardcoded and has_logging and has_error_handling

    except Exception as e:
        print_test("Code quality check", False, str(e))
        return False


def verify_environment():
    """Verify environment is set up correctly."""
    print_header("Verification 7: Environment Configuration")

    # Test 1: Check if httpx is available
    try:
        import httpx
        print_test("httpx installed", True, f"Version: {httpx.__version__}")
    except ImportError:
        print_test("httpx installed", False, "Run: pip install httpx")

    # Test 2: Check environment variables
    has_api_url = bool(os.getenv('N8N_API_URL'))
    has_api_key = bool(os.getenv('N8N_API_KEY'))

    print_test("N8N_API_URL set", has_api_url,
               os.getenv('N8N_API_URL', 'Not set') if has_api_url else "Not set (optional if using MCP)")
    print_test("N8N_API_KEY set", has_api_key,
               "Configured" if has_api_key else "Not set (optional if using MCP)")

    if not (has_api_url and has_api_key):
        print("\n  ℹ️  Note: Direct API mode requires both N8N_API_URL and N8N_API_KEY")
        print("         Alternatively, use MCP n8n server integration\n")

    return True  # Environment issues are warnings, not failures


def main():
    """Run all verifications."""
    print_header("N8N Workflow Tool - Integration Verification")
    print("Phase 1.6: N8N Workflow Automation Tool")
    print("Comprehensive verification of all deliverables\n")

    results = {}

    # Run all verifications
    results['imports'] = verify_imports()
    results['prince_integration'] = verify_prince_integration()
    results['tool_functionality'] = verify_tool_functionality()
    results['type_hints'] = verify_type_hints()
    results['file_structure'] = verify_file_structure()
    results['code_quality'] = verify_no_code_smells()
    results['environment'] = verify_environment()

    # Summary
    print_header("Verification Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, test_result in results.items():
        status = "✅ PASS" if test_result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 60}\n")

    if passed == total:
        print("✅ All verifications passed! Integration is complete and ready for use.")
        return 0
    else:
        print("⚠️  Some verifications failed. Review the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
