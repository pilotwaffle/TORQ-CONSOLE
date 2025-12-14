#!/usr/bin/env python3
"""Simple TORQ Console validation without Unicode"""

import subprocess
import sys
import os
import json

def run_test(name, cmd):
    """Run a test command"""
    print(f"\nTesting: {name}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"[PASS] {name}")
            return True, result.stdout
        else:
            print(f"[FAIL] {name}")
            print(f"Error: {result.stderr[:200]}")
            return False, result.stderr
    except Exception as e:
        print(f"[FAIL] {name} - Exception: {e}")
        return False, str(e)

def main():
    print("TORQ CONSOLE VALIDATION REPORT")
    print("=" * 50)

    results = {}

    # Test 1: Check Python files exist
    print("\n1. CHECKING CRITICAL FILES")
    critical_files = [
        "torq_console/__init__.py",
        "torq_console/cli.py",
        "eval_sets/v1.0/tasks.json",
        "policies/routing/v1.yaml",
        "slo.yml",
        "torq_console/core/telemetry/event.py"
    ]

    file_results = {}
    for file_path in critical_files:
        exists = os.path.exists(file_path)
        file_results[file_path] = exists
        print(f"[{'OK' if exists else 'MISS'}] {file_path}")

    results["files"] = file_results

    # Test 2: Import test
    print("\n2. TESTING PACKAGE IMPORT")
    try:
        import torq_console
        print("[OK] Package imports successfully")
        results["import"] = True
    except ImportError as e:
        print(f"[FAIL] Import failed: {e}")
        results["import"] = False

    # Test 3: CLI commands
    print("\n3. TESTING CLI COMMANDS")
    cli_results = {}

    # Try torq-console help
    success, output = run_test("torq-console --help", "torq-console --help")
    cli_results["help"] = success

    # Try torq telemetry
    success, output = run_test("torq telemetry --compliance", "python -m torq_console.core.telemetry.cli --compliance")
    cli_results["telemetry"] = success

    # Try evaluation
    success, output = run_test("evaluation runner", "python -m torq_console.core.evaluation.runner --help")
    cli_results["evaluation"] = success

    results["cli"] = cli_results

    # Test 4: Web interface (basic check)
    print("\n4. TESTING WEB INTERFACE CAPABILITY")
    web_files = [
        "torq_console/web",
        "torq_landing.html"
    ]

    web_results = {}
    for item in web_files:
        exists = os.path.exists(item)
        web_results[item] = exists
        print(f"[{'OK' if exists else 'MISS'}] {item}")

    results["web"] = web_results

    # Test 5: Load evaluation set
    print("\n5. TESTING EVALUATION SET")
    eval_path = "eval_sets/v1.0/tasks.json"
    if os.path.exists(eval_path):
        try:
            with open(eval_path) as f:
                eval_data = json.load(f)
            task_count = len(eval_data.get("tasks", []))
            print(f"[OK] Loaded {task_count} evaluation tasks")
            results["evaluation_set"] = {"loaded": True, "tasks": task_count}
        except Exception as e:
            print(f"[FAIL] Could not load eval set: {e}")
            results["evaluation_set"] = {"loaded": False, "error": str(e)}
    else:
        print("[FAIL] Evaluation set not found")
        results["evaluation_set"] = {"loaded": False, "error": "File not found"}

    # Generate summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    total_checks = 0
    passed_checks = 0

    # Count file checks
    for file_path, exists in file_results.items():
        total_checks += 1
        if exists:
            passed_checks += 1

    # Count other checks
    if results.get("import"):
        passed_checks += 1
    total_checks += 1

    for cmd, success in cli_results.items():
        total_checks += 1
        if success:
            passed_checks += 1

    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Success Rate: {passed_checks/total_checks*100:.1f}%")

    # Save results
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: validation_results.json")

    # Key findings
    print("\nKEY FINDINGS:")
    print("-" * 20)

    if not results.get("import"):
        print("WARNING: Package import failed - installation issue")

    if not cli_results.get("help"):
        print("WARNING: CLI command not working - check PATH/installation")

    if not results.get("evaluation_set", {}).get("loaded"):
        print("WARNING: Evaluation system not functional")

    print("\nWhat users CAN do:")
    print("- Install the package (if files exist)")

    if results.get("import"):
        print("- Import torq_console in Python")

    if cli_results.get("help"):
        print("- Use torq-console CLI command")

    if results.get("evaluation_set", {}).get("loaded"):
        print(f"- Run evaluation sets ({results['evaluation_set']['tasks']} tasks available)")

    return results

if __name__ == "__main__":
    main()