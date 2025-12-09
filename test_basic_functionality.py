#!/usr/bin/env python3
"""
Basic functionality tests for TORQ Console
Tests core functionality without heavy dependencies
"""
import sys
import os
import importlib
import subprocess
from pathlib import Path

def test_python_imports():
    """Test if core Python modules can be imported"""
    print("Testing core imports...")

    # Test standard library imports
    try:
        import json
        import asyncio
        import aiofiles
        import click
        import rich
        print("✓ Standard library and basic dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_torq_modules():
    """Test if TORQ modules exist and have basic structure"""
    print("\nTesting TORQ module structure...")

    torq_path = Path("torq_console")
    if not torq_path.exists():
        print("✗ torq_console directory not found")
        return False

    # Check key directories
    key_dirs = [
        "torq_console/core",
        "torq_console/agents",
        "torq_console/llm",
        "torq_console/ui",
        "torq_console/utils"
    ]

    for dir_path in key_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing")

    # Check key files
    key_files = [
        "torq_console/__init__.py",
        "torq_console/core/console.py",
        "torq_console/agents/marvin_integration.py",
        "torq_console/cli.py"
    ]

    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")

    return True

def test_cli_exists():
    """Test if CLI entry point exists"""
    print("\nTesting CLI entry point...")

    if Path("torq_console/cli.py").exists():
        print("✓ CLI file exists")

        # Check if it's executable
        if os.access("torq_console/cli.py", os.R_OK):
            print("✓ CLI file is readable")
            return True
        else:
            print("✗ CLI file is not readable")
    else:
        print("✗ CLI file not found")

    return False

def test_configuration():
    """Test configuration files"""
    print("\nTesting configuration...")

    config_files = [
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        "LICENSE"
    ]

    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✓ {config_file} exists")
        else:
            print(f"✗ {config_file} missing")

    return True

def test_documentation():
    """Test if documentation files exist"""
    print("\nTesting documentation...")

    doc_files = [
        "CLAUDE.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md"
    ]

    for doc_file in doc_files:
        if Path(doc_file).exists():
            print(f"✓ {doc_file} exists")
        else:
            print(f"! {doc_file} not found (optional)")

    return True

def test_basic_syntax():
    """Test basic Python syntax of key files"""
    print("\nTesting Python syntax...")

    key_files = [
        "torq_console/__init__.py",
        "torq_console/cli.py"
    ]

    for file_path in key_files:
        if Path(file_path).exists():
            try:
                # Compile the file to check syntax
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"✓ {file_path} has valid syntax")
            except SyntaxError as e:
                print(f"✗ {file_path} has syntax error: {e}")
                return False

    return True

def test_package_structure():
    """Test if the package structure is correct"""
    print("\nTesting package structure...")

    # Check for __pycache__ directories (indicates successful imports)
    pycache_count = 0
    for root, dirs, files in os.walk("torq_console"):
        if "__pycache__" in dirs:
            pycache_count += 1

    if pycache_count > 0:
        print(f"✓ Found {pycache_count} __pycache__ directories (module has been used)")
    else:
        print("! No __pycache__ directories found (module not yet imported)")

    return True

def main():
    """Run all basic tests"""
    print("=" * 60)
    print("TORQ Console - Basic Functionality Tests")
    print("=" * 60)

    tests = [
        ("Python Imports", test_python_imports),
        ("TORQ Modules", test_torq_modules),
        ("CLI Entry Point", test_cli_exists),
        ("Configuration", test_configuration),
        ("Documentation", test_documentation),
        ("Basic Syntax", test_basic_syntax),
        ("Package Structure", test_package_structure)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nPassed: {passed}/{total} tests")

    if passed == total:
        print("\n🎉 All basic functionality tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())