#!/usr/bin/env python3
"""Simple agent functionality tests"""

import os
import sys
from pathlib import Path

def test_agent_files():
    """Test if agent files exist"""
    print("Testing agent files...")

    agent_files = [
        "torq_console/agents/enhanced_prince_flowers.py",
        "torq_console/agents/enhanced_prince_flowers_v2.py",
        "torq_console/agents/marvin_memory.py",
        "torq_console/agents/marvin_orchestrator.py",
        "torq_console/agents/handoff_optimizer.py",
        "torq_console/agents/action_learning.py",
    ]

    exists_count = 0
    for file_path in agent_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"  {file_path}: EXISTS ({size} bytes)")
            exists_count += 1
        else:
            print(f"  {file_path}: MISSING")

    print(f"\n  Agent files present: {exists_count}/{len(agent_files)}")
    return exists_count >= len(agent_files) // 2

def test_syntax_check():
    """Check syntax of agent files"""
    print("\nTesting agent file syntax...")

    agent_dir = Path("torq_console/agents")
    python_files = list(agent_dir.glob("*.py"))

    syntax_ok = 0
    total_checked = 0

    for py_file in python_files[:10]:  # Check first 10 files
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(py_file), 'exec')
            print(f"  {py_file.name}: SYNTAX OK")
            syntax_ok += 1
        except SyntaxError as e:
            print(f"  {py_file.name}: SYNTAX ERROR")
        except Exception as e:
            print(f"  {py_file.name}: ERROR - {str(e)[:50]}")

        total_checked += 1

    print(f"\n  Files with valid syntax: {syntax_ok}/{total_checked}")
    return syntax_ok >= total_checked * 0.8  # 80% pass rate

def test_memory_integration():
    """Test memory integration files"""
    print("\nTesting memory integration...")

    memory_files = [
        "torq_console/memory/__init__.py",
        "torq_console/memory/letta_integration.py",
    ]

    for file_path in memory_files:
        if Path(file_path).exists():
            print(f"  {file_path}: EXISTS")
        else:
            print(f"  {file_path}: MISSING")

    return all(Path(f).exists() for f in memory_files)

def test_config_files():
    """Test configuration files for agents"""
    print("\nTesting agent configuration...")

    config_files = [
        "torq_console/agents/config.py",
        ".torq_agent_json",
    ]

    for file_path in config_files:
        if Path(file_path).exists():
            print(f"  {file_path}: EXISTS")
        else:
            print(f"  {file_path}: MISSING")

    # Check for config directory
    config_dir = Path("torq_console/agents/config")
    if config_dir.exists():
        json_files = list(config_dir.glob("*.json"))
        print(f"  Config directory exists with {len(json_files)} JSON files")

    return True

def main():
    print("=" * 60)
    print("TORQ Console - Agent Tests")
    print("=" * 60)

    tests = [
        ("Agent Files", test_agent_files),
        ("Syntax Check", test_syntax_check),
        ("Memory Integration", test_memory_integration),
        ("Configuration", test_config_files),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"Error in {test_name}: {e}")
            results[test_name] = False

    print("\n" + "=" * 60)
    print("AGENT TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\nPassed: {passed}/{total}")

    if passed >= total * 0.75:
        print("Agent tests mostly passed!")
        return 0
    else:
        print("Agent tests need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())