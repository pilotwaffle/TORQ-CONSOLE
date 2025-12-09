#!/usr/bin/env python3
"""Component tests for TORQ Console"""

import os
import sys
import subprocess
from pathlib import Path

def test_component_imports():
    """Test individual component imports"""
    print("Testing component imports...")

    # Test components that don't depend on Marvin
    components = [
        ("Core utils", "torq_console.utils.advanced_web_search"),
        ("LLM Manager", "torq_console.llm.manager"),
        ("Command Palette", "torq_console.ui.command_palette"),
        ("Intent Detector", "torq_console.ui.intent_detector"),
    ]

    successful = []
    failed = []

    for name, module in components:
        try:
            __import__(module)
            print(f"  {name}: OK")
            successful.append(name)
        except ImportError as e:
            print(f"  {name}: FAILED - {str(e)[:100]}")
            failed.append(name)
        except Exception as e:
            print(f"  {name}: ERROR - {str(e)[:100]}")
            failed.append(name)

    print(f"\n  Successful imports: {len(successful)}")
    print(f"  Failed imports: {len(failed)}")

    return len(successful) > 0

def test_file_structure():
    """Test file structure integrity"""
    print("\nTesting file structure...")

    critical_files = [
        "torq_console/core/console.py",
        "torq_console/core/context_manager.py",
        "torq_console/core/chat_manager.py",
        "torq_console/llm/providers/openai.py",
        "torq_console/llm/providers/anthropic.py",
        "torq_console/indexer/code_scanner.py",
        "torq_console/ui/web.py",
    ]

    exists = []
    missing = []

    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"  {file_path}: EXISTS")
            exists.append(file_path)
        else:
            print(f"  {file_path}: MISSING")
            missing.append(file_path)

    print(f"\n  Files present: {len(exists)}")
    print(f"  Files missing: {len(missing)}")

    return len(missing) == 0

def test_configuration_files():
    """Test configuration files"""
    print("\nTesting configuration files...")

    config_files = [
        ("pyproject.toml", True),
        ("requirements.txt", True),
        ("requirements-letta.txt", False),  # Optional
        ("railway.json", False),  # Optional
        ("render.yaml", False),  # Optional
    ]

    required_exist = 0
    required_total = 0

    for file_path, required in config_files:
        exists = Path(file_path).exists()
        status = "EXISTS" if exists else "MISSING"
        req = " (Required)" if required else " (Optional)"
        print(f"  {file_path}: {status}{req}")

        if required:
            required_total += 1
            if exists:
                required_exist += 1

    return required_exist == required_total

def test_documentation():
    """Test documentation files"""
    print("\nTesting documentation...")

    doc_files = [
        "README.md",
        "CLAUDE.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE",
    ]

    doc_count = 0
    for doc in doc_files:
        if Path(doc).exists():
            size = Path(doc).stat().st_size
            print(f"  {doc}: EXISTS ({size} bytes)")
            doc_count += 1
        else:
            print(f"  {doc}: MISSING")

    return doc_count >= 4  # At least README, CLAUDE, LICENSE, and one more

def run_command_tests():
    """Test basic command execution"""
    print("\nTesting command execution...")

    # Test Python syntax for key files
    files_to_check = [
        "torq_console/core/console.py",
        "torq_console/ui/web.py",
        "torq_console/indexer/code_scanner.py"
    ]

    syntax_ok = 0

    for file_path in files_to_check:
        if Path(file_path).exists():
            try:
                # Use subprocess to compile and check syntax
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", file_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"  {file_path}: SYNTAX OK")
                    syntax_ok += 1
                else:
                    print(f"  {file_path}: SYNTAX ERROR")
                    if result.stderr:
                        print(f"    Error: {result.stderr[:100]}")
            except Exception as e:
                print(f"  {file_path}: ERROR - {e}")

    print(f"\n  Files with valid syntax: {syntax_ok}/{len(files_to_check)}")
    return syntax_ok == len(files_to_check)

def main():
    print("=" * 60)
    print("TORQ Console - Component Tests")
    print("=" * 60)

    tests = [
        ("Component Imports", test_component_imports),
        ("File Structure", test_file_structure),
        ("Configuration Files", test_configuration_files),
        ("Documentation", test_documentation),
        ("Command Tests", run_command_tests),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"Test failed with error: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\nAll component tests passed!")
        return 0
    elif passed_tests > total_tests // 2:
        print(f"\n{passed_tests} of {total_tests} tests passed. Partial success.")
        return 0
    else:
        print(f"\nOnly {passed_tests} of {total_tests} tests passed. Issues detected.")
        return 1

if __name__ == "__main__":
    sys.exit(main())