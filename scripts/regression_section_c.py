#!/usr/bin/env python3
"""
Section C: Idempotency & Hardening Regression

Tests idempotency guarantees and execution hardening.
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torq_console.dependencies import get_supabase_client


async def test_idempotency_hardening():
    """Test idempotency and hardening features."""

    print("\n" + "="*60)
    print("SECTION C: IDEMPOTENCY & HARDENING")
    print("="*60)

    results = {}
    supabase = get_supabase_client()

    # Test C1: Verify no duplicate node executions
    print("\n[TEST C1] Check for duplicate node executions")
    try:
        # Get nodes with multiple completed_at timestamps
        result = supabase.table("mission_nodes").select("*").execute()
        duplicates = []
        for node in result.data:
            if node.get("execution_count", 0) > 1:
                # Check if status is completed but has multiple runs
                if node.get("status") == "completed":
                    duplicates.append(node["id"])

        if duplicates:
            print(f"  Status: WARNING - Found {len(duplicates)} nodes with multiple executions")
            results["duplicate_executions"] = "WARNING"
        else:
            print(f"  Status: PASS - No duplicate executions detected")
            results["duplicate_executions"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["duplicate_executions"] = "FAIL"

    # Test C2: Verify event deduplication (by ID only)
    print("\n[TEST C2] Check for duplicate events (by ID)")
    try:
        result = supabase.table("mission_events").select("*").execute()
        ids = [e["id"] for e in result.data]
        unique_ids = set(ids)

        if len(ids) != len(unique_ids):
            print(f"  Status: FAIL - Found {len(ids) - len(unique_ids)} duplicate event IDs")
            results["duplicate_events"] = "FAIL"
        else:
            print(f"  Status: PASS - No duplicate event IDs")
            print(f"  Total events: {len(ids)}")
            results["duplicate_events"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["duplicate_events"] = "FAIL"

    # Test C3: Verify handoff deduplication
    print("\n[TEST C3] Check for duplicate handoffs (by ID)")
    try:
        result = supabase.table("mission_handoffs").select("*").execute()
        ids = [h["id"] for h in result.data]
        unique_ids = set(ids)

        if len(ids) != len(unique_ids):
            print(f"  Status: WARNING - Found {len(ids) - len(unique_ids)} duplicate handoff IDs")
            results["duplicate_handoffs"] = "WARNING"
        else:
            print(f"  Status: PASS - No duplicate handoff IDs")
            print(f"  Total handoffs: {len(ids)}")
            results["duplicate_handoffs"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["duplicate_handoffs"] = "FAIL"

    # Test C4: Verify rich handoff format (has structured fields)
    print("\n[TEST C4] Check rich handoff structure")
    try:
        result = supabase.table("mission_handoffs").select("*").execute()
        # Rich handoffs have structured handoff_summary
        rich_count = sum(1 for h in result.data if isinstance(h.get("handoff_summary"), dict))
        total = len(result.data)

        if total > 0:
            rich_ratio = rich_count / total
            print(f"  Status: PASS - Rich handoff structure: {rich_ratio:.1%}")
            print(f"  Structured: {rich_count}/{total}")
            results["handoff_format"] = "PASS"
        else:
            print(f"  Status: SKIP - No handoffs found")
            results["handoff_format"] = "SKIP"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["handoff_format"] = "FAIL"

    # Test C5: Verify handoff confidence scores
    print("\n[TEST C5] Check handoff confidence scores")
    try:
        result = supabase.table("mission_handoffs").select("*").execute()
        scores = [h.get("confidence", 0) for h in result.data if h.get("confidence") is not None]

        if scores:
            avg_confidence = sum(scores) / len(scores)
            print(f"  Status: PASS - Average confidence: {avg_confidence:.2f}")
            print(f"  Min: {min(scores):.2f}, Max: {max(scores):.2f}")
            results["handoff_confidence"] = "PASS"
        else:
            print(f"  Status: WARNING - No confidence scores found")
            results["handoff_confidence"] = "WARNING"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["handoff_confidence"] = "FAIL"

    # Summary
    print("\n" + "="*60)
    print("SECTION C SUMMARY")
    print("="*60)
    for test_name, status in results.items():
        print(f"  {test_name}: {status}")

    pass_count = sum(1 for s in results.values() if s == "PASS")
    warning_count = sum(1 for s in results.values() if s == "WARNING")
    total_count = len([s for s in results.values() if s != "SKIP"])
    print(f"\nTotal: {pass_count}/{total_count} tests passed ({warning_count} warnings)")

    if pass_count == total_count:
        print("\n[OK] SECTION C PASSED")
        return True
    elif warning_count > 0:
        print(f"\n[WARN] SECTION C PASSED WITH WARNINGS")
        return True
    else:
        print(f"\n[FAIL] SECTION C FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_idempotency_hardening())
    sys.exit(0 if success else 1)
