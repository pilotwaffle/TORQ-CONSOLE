#!/usr/bin/env python3
"""Simple test runner for TORQ Console"""

import os
import sys
from pathlib import Path

def test_basic_structure():
    """Test if basic structure exists"""
    print("Testing basic file structure...")

    checks = [
        ("torq_console directory", Path("torq_console").exists()),
        ("torq_console/__init__.py", Path("torq_console/__init__.py").exists()),
        ("CLI file", Path("torq_console/cli.py").exists()),
        ("Requirements", Path("requirements.txt").exists()),
        ("README", Path("README.md").exists()),
        ("License", Path("LICENSE").exists()),
    ]

    for name, exists in checks:
        status = "OK" if exists else "MISSING"
        print(f"  {name}: {status}")

    return all(c[1] for c in checks)

def test_dependencies():
    """Test if key dependencies are installed"""
    print("\nTesting dependencies...")

    deps = [
        "click",
        "rich",
        "pydantic",
        "anthropic",
        "openai",
        "pytest"
    ]

    results = []
    for dep in deps:
        try:
            __import__(dep)
            print(f"  {dep}: OK")
            results.append(True)
        except ImportError:
            print(f"  {dep}: MISSING")
            results.append(False)

    return all(results)

def test_syntax():
    """Test Python syntax of key files"""
    print("\nTesting Python syntax...")

    key_files = [
        "torq_console/cli.py"
    ]

    for file_path in key_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"  {file_path}: OK")
            except SyntaxError as e:
                print(f"  {file_path}: SYNTAX ERROR - {e}")
                return False
        else:
            print(f"  {file_path}: MISSING")

    return True

def main():
    print("TORQ Console - Simple Test Runner")
    print("=" * 40)

    tests = [
        test_basic_structure,
        test_dependencies,
        test_syntax
    ]

    results = []
    for test in tests:
        result = test()
        results.append(result)

    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())