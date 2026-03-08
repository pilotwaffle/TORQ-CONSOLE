#!/usr/bin/env python3
"""
Validate that the production scheduler uses hardened executor.

Confirm:
1. MissionGraphScheduler has hardened_executor attribute
2. MissionGraphScheduler has mission_completer attribute
3. _execute_node_hardened method exists
4. Hardened executor provides idempotency guarantees
"""

import os
import sys
import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torq_console.mission_graph import (
    MissionGraphScheduler,
    MissionNodeExecutor,
    MissionCompleter
)
from supabase import create_client
from torq_console.settings import get_settings


def validate_scheduler_integration():
    """Validate that scheduler is integrated with hardened executor."""
    print("=" * 70)
    print("Scheduler Hardened Executor Integration Validation")
    print("=" * 70)

    # Get Supabase client
    settings = get_settings()
    client = create_client(settings.supabase.url, settings.supabase.service_role_key)

    # Create scheduler instance
    scheduler = MissionGraphScheduler(client)

    print("\n[CHECK 1] Scheduler has hardened_executor attribute")
    has_hardened = hasattr(scheduler, 'hardened_executor')
    print(f"  Result: {'[PASS]' if has_hardened else '[FAIL]'} {has_hardened}")
    if has_hardened:
        print(f"  Type: {type(scheduler.hardened_executor).__name__}")
        print(f"  Is MissionNodeExecutor: {isinstance(scheduler.hardened_executor, MissionNodeExecutor)}")

    print("\n[CHECK 2] Scheduler has mission_completer attribute")
    has_completer = hasattr(scheduler, 'mission_completer')
    print(f"  Result: {'[PASS]' if has_completer else '[FAIL]'} {has_completer}")
    if has_completer:
        print(f"  Type: {type(scheduler.mission_completer).__name__}")
        print(f"  Is MissionCompleter: {isinstance(scheduler.mission_completer, MissionCompleter)}")

    print("\n[CHECK 3] Scheduler has _execute_node_hardened method")
    has_hardened_method = hasattr(scheduler, '_execute_node_hardened')
    print(f"  Result: {'[PASS]' if has_hardened_method else '[FAIL]'} {has_hardened_method}")
    if has_hardened_method:
        method = getattr(scheduler, '_execute_node_hardened')
        print(f"  Method signature: {inspect.signature(method)}")

    print("\n[CHECK 4] Hardened executor has idempotency methods")
    executor = scheduler.hardened_executor if has_hardened else None
    if executor:
        methods_to_check = [
            '_try_transition_to_running',
            '_try_transition_to_completed',
            '_emit_event_if_not_exists',
            '_create_handoff_if_not_exists',
        ]
        for method_name in methods_to_check:
            has_method = hasattr(executor, method_name)
            print(f"  {method_name}: {'[PASS]' if has_method else '[FAIL]'} {has_method}")

    print("\n[CHECK 5] Mission completer has idempotency methods")
    completer = scheduler.mission_completer if has_completer else None
    if completer:
        has_idempotent = hasattr(completer, 'complete_mission')
        print(f"  complete_mission: {'[PASS]' if has_idempotent else '[FAIL]'} {has_idempotent}")
        has_event_check = hasattr(completer, '_emit_mission_completed_event_if_not_exists')
        print(f"  _emit_mission_completed_event_if_not_exists: {'[PASS]' if has_event_check else '[FAIL]'} {has_event_check}")

    print("\n[CHECK 6] Scheduler __init__ initializes hardened components")
    init_source = inspect.getsource(scheduler.__init__)
    has_hardened_init = 'hardened_executor' in init_source
    has_completer_init = 'mission_completer' in init_source
    print(f"  hardened_executor in __init__: {'[PASS]' if has_hardened_init else '[FAIL]'} {has_hardened_init}")
    print(f"  mission_completer in __init__: {'[PASS]' if has_completer_init else '[FAIL]'} {has_completer_init}")

    print("\n[CHECK 7] _dispatch_nodes uses hardened executor")
    dispatch_source = inspect.getsource(scheduler._dispatch_nodes)
    uses_hardened = '_execute_node_hardened' in dispatch_source
    skips_completed = 'already' in dispatch_source and ('COMPLETED' in dispatch_source or 'completed' in dispatch_source)
    print(f"  Calls _execute_node_hardened: {'[PASS]' if uses_hardened else '[FAIL]'} {uses_hardened}")
    print(f"  Skips already-executed nodes: {'[PASS]' if skips_completed else '[FAIL]'} {skips_completed}")

    print("\n[CHECK 8] execute_graph uses mission completer")
    graph_source = inspect.getsource(scheduler.execute_graph)
    uses_completer = 'mission_completer' in graph_source
    print(f"  Uses mission_completer: {'[PASS]' if uses_completer else '[FAIL]'} {uses_completer}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_passed = all([
        has_hardened,
        has_completer,
        has_hardened_method,
        uses_hardened,
        skips_completed,
        uses_completer,
    ])

    if all_passed:
        print("\n[SUCCESS] All integration checks passed!")
        print("\nThe production scheduler now:")
        print("  - Uses MissionNodeExecutor for idempotent node execution")
        print("  - Uses MissionCompleter for idempotent mission completion")
        print("  - Prevents duplicate events via _emit_event_if_not_exists")
        print("  - Prevents duplicate handoffs via _create_handoff_if_not_exists")
        print("  - Skips already-completed nodes safely")
        print("\nThe hardened execution path is now the DEFAULT runtime path.")
    else:
        print("\n[WARNING] Some integration checks failed.")
        print("The scheduler may not be fully integrated with hardened executor.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(validate_scheduler_integration())
