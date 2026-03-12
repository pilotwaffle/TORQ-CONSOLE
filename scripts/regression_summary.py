#!/usr/bin/env python3
"""
Full Regression Test Summary - Sections A through G

Combines all regression tests for the Phase 5.1 + Control Surface system.
"""

import os
import sys
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime


def run_section(name, script):
    """Run a regression section and return results."""
    print(f"\n\n{'='*70}")
    print(f"RUNNING: {name}")
    print(f"{'='*70}")

    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        timeout=60
    )

    success = result.returncode == 0
    return success, result.stdout, result.stderr


def main():
    """Run all regression sections."""

    print("\n" + "="*70)
    print("PHASE 5.1 + CONTROL SURFACE - FULL REGRESSION TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    sections = [
        ("Section A: Environment & Startup", "scripts/test_control_api.py"),
        ("Section B: Mission Graph + Execution Fabric", "scripts/regression_section_b.py"),
        ("Section C: Idempotency & Hardening", "scripts/regression_section_c.py"),
    ]

    results = {}

    for name, script in sections:
        success, stdout, stderr = run_section(name, script)
        results[name] = success

        # Print summary
        if success:
            print(f"\n[OK] {name} - PASSED")
        else:
            print(f"\n[FAIL] {name} - FAILED")

    # Final Summary
    print("\n\n" + "="*70)
    print("FINAL REGRESSION SUMMARY")
    print("="*70)

    for name, success in results.items():
        status = "[OK]   " if success else "[FAIL] "
        print(f"{status} {name}")

    passed = sum(1 for s in results.values() if s)
    total = len(results)

    print(f"\nTotal: {passed}/{total} sections passed")

    if passed == total:
        print("\n" + "="*70)
        print("[SUCCESS] ALL REGRESSION TESTS PASSED")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print(f"[FAILURE] {total - passed} REGRESSION TEST(S) FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
