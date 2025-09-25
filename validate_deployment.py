#!/usr/bin/env python3
"""
Prince Flowers Enhanced Deployment Validation

This script validates that the Prince Flowers Enhanced Agent has been
properly deployed and integrated into TORQ Console.
"""

import ast
import sys
from pathlib import Path


def validate_file_syntax(file_path: Path) -> bool:
    """Validate Python file syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Parse the AST to check syntax
        ast.parse(source)
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False


def validate_imports_and_classes(file_path: Path, expected_classes: list) -> bool:
    """Validate that expected classes exist in the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)

        # Find all class definitions
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        # Check if all expected classes are present
        missing_classes = [cls for cls in expected_classes if cls not in classes]

        if missing_classes:
            print(f"❌ Missing classes in {file_path}: {missing_classes}")
            return False

        print(f"✅ All expected classes found in {file_path}: {expected_classes}")
        return True

    except Exception as e:
        print(f"❌ Error validating classes in {file_path}: {e}")
        return False


def validate_integration_points(console_file: Path) -> bool:
    """Validate that console.py has the Prince Flowers integration points."""
    try:
        with open(console_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key integration points
        integration_checks = [
            ('Prince Flowers import', 'from ..agents.torq_prince_flowers import TORQPrinceFlowersInterface'),
            ('Prince Flowers initialization', 'self.prince_flowers = TORQPrinceFlowersInterface(self)'),
            ('Prince command handler', 'async def handle_prince_command'),
            ('Command routing', 'if command.lower().startswith(\'prince \')'),
            ('Alternative @prince format', '@prince'),
        ]

        all_good = True
        for check_name, check_pattern in integration_checks:
            if check_pattern in content:
                print(f"✅ {check_name} found")
            else:
                print(f"❌ {check_name} missing: '{check_pattern}'")
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ Error validating integration points: {e}")
        return False


def validate_shell_integration(shell_file: Path) -> bool:
    """Validate that shell.py has the Prince Flowers commands."""
    try:
        with open(shell_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for shell integration points
        shell_checks = [
            ('Prince Flowers help text', 'Prince Flowers Enhanced Agent'),
            ('Command routing', 'await self.console.process_command(command)'),
            ('Prince command examples', 'prince search'),
        ]

        all_good = True
        for check_name, check_pattern in shell_checks:
            if check_pattern in content:
                print(f"✅ Shell {check_name} found")
            else:
                print(f"❌ Shell {check_name} missing: '{check_pattern}'")
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ Error validating shell integration: {e}")
        return False


def main():
    """Main validation function."""
    print("🔍 Prince Flowers Enhanced Deployment Validation")
    print("=" * 60)

    # Define file paths
    base_path = Path(__file__).parent
    torq_console_path = base_path / "torq_console"

    # Files to validate
    files_to_check = [
        (torq_console_path / "agents" / "torq_prince_flowers.py",
         ["TORQPrinceFlowers", "TORQPrinceFlowersInterface", "ReasoningMode", "AgenticAction", "ReasoningTrajectory"]),
        (torq_console_path / "core" / "console.py",
         ["TorqConsole"]),
        (torq_console_path / "ui" / "shell.py",
         ["InteractiveShell"]),
    ]

    print("\n🔧 Validating File Syntax:")
    print("-" * 40)

    syntax_results = []
    for file_path, expected_classes in files_to_check:
        print(f"\nChecking: {file_path.relative_to(base_path)}")

        # Check if file exists
        if not file_path.exists():
            print(f"❌ File does not exist: {file_path}")
            syntax_results.append(False)
            continue

        # Check syntax
        syntax_ok = validate_file_syntax(file_path)

        # Check classes if syntax is ok
        classes_ok = True
        if syntax_ok and expected_classes:
            classes_ok = validate_imports_and_classes(file_path, expected_classes)

        result = syntax_ok and classes_ok
        syntax_results.append(result)

        if result:
            print(f"✅ {file_path.name} validation passed")
        else:
            print(f"❌ {file_path.name} validation failed")

    print("\n🔗 Validating Integration Points:")
    print("-" * 40)

    # Validate console integration
    console_file = torq_console_path / "core" / "console.py"
    console_integration_ok = validate_integration_points(console_file)

    # Validate shell integration
    shell_file = torq_console_path / "ui" / "shell.py"
    shell_integration_ok = validate_shell_integration(shell_file)

    print("\n📊 Validation Summary:")
    print("-" * 30)

    # Count results
    syntax_passed = sum(syntax_results)
    total_syntax = len(syntax_results)

    integration_passed = sum([console_integration_ok, shell_integration_ok])
    total_integration = 2

    print(f"Syntax validation: {syntax_passed}/{total_syntax} files passed")
    print(f"Integration validation: {integration_passed}/{total_integration} components passed")

    overall_success = (syntax_passed == total_syntax) and (integration_passed == total_integration)

    print(f"\n🎯 Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")

    if overall_success:
        print("""
🎉 Deployment Validation Successful!

The Prince Flowers Enhanced Agent has been successfully deployed with:
✅ All Python files have valid syntax
✅ All required classes are present
✅ Console integration is complete
✅ Shell integration is complete

The enhanced agentic RL agent is ready for use with these commands:
- prince <query>
- prince search <topic>
- prince status
- prince health
- prince capabilities
- prince help
- @prince <query>

You can now run TORQ Console and use the Prince Flowers Enhanced Agent!
""")
    else:
        print("""
⚠️  Deployment Validation Issues Detected

Please review the errors above and fix any issues before using the agent.
Common issues might include:
- Missing imports
- Syntax errors
- Missing integration points
- File path issues

Fix the issues and run this validation again.
""")

    return overall_success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Validation script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)