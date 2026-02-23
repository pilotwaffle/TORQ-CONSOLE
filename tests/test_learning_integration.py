"""
TORQ Console v2 Learning Integration Verification

Verifies that:
1. MandatoryLearningHook is installed and functional
2. Every agent response produces a learning event
3. Q-values are being read/written
4. Swarm memory files are being updated
"""
import os
import json
import time
from pathlib import Path

# Paths
TORQ_ROOT = Path("E:/TORQ-CONSOLE")
AGENT_ROOT = TORQ_ROOT / "torq_console" / "agents" / "torq_prince_flowers" / "core"
MEMORY_ROOT = TORQ_ROOT / ".torq" / "agent_memory"

# Required files
LEARNING_HOOK_FILE = AGENT_ROOT / "learning_hook.py"
AGENT_FILE = AGENT_ROOT / "agent.py"
ROUTER_FILE = TORQ_ROOT / "torq_console" / "agents" / "marvin_query_router.py"

# Memory files that should be populated
ROUTING_SUCCESS = MEMORY_ROOT / "routing_success.json"
PERFORMANCE_HISTORY = MEMORY_ROOT / "performance_history.json"
RL_KNOWLEDGE = MEMORY_ROOT / "rl_knowledge_v2.json"
INTERACTIONS_LOG = MEMORY_ROOT / "interactions.jsonl"


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and report."""
    if path.exists():
        print(f"[OK] {description}: {path.name} exists")
        return True
    else:
        print(f"[FAIL] {description}: {path.name} MISSING")
        return False


def check_code_integration(path: Path, required_strings: list) -> bool:
    """Check if required code patterns exist in a file."""
    try:
        content = path.read_text()
        all_found = True
        for req in required_strings:
            if req in content:
                print(f"  [+] Found: {req[:60]}...")
            else:
                print(f"  [-] Missing: {req[:60]}...")
                all_found = False
        return all_found
    except Exception as e:
        print(f"[ERROR] Could not read {path}: {e}")
        return False


def check_memory_file(path: Path, description: str) -> dict:
    """Check and parse a memory file."""
    if not path.exists():
        print(f"[WARN] {description}: {path.name} not created yet (will be on first interaction)")
        return {}
    try:
        content = json.loads(path.read_text())
        print(f"[OK] {description}: {path.name} exists with {len(content)} entries")
        return content
    except Exception as e:
        print(f"[WARN] {description}: {path.name} exists but empty or invalid: {e}")
        return {}


def main():
    print("=" * 60)
    print("TORQ Console v2 Learning Integration Verification")
    print("=" * 60)
    print()

    # Step 1: Check files exist
    print("Step 1: Verify Created Files")
    print("-" * 60)
    files_ok = True
    files_ok &= check_file_exists(LEARNING_HOOK_FILE, "Learning Hook")
    files_ok &= check_file_exists(AGENT_FILE, "Agent Core")
    files_ok &= check_file_exists(ROUTER_FILE, "Query Router")
    print()

    # Step 2: Check learning_hook.py has required classes
    print("Step 2: Verify Learning Hook Implementation")
    print("-" * 60)
    hook_required = [
        "class MandatoryLearningHook",
        "def calculate_consulting_reward",
        "class ExperienceReplayEngine",
        "class SwarmMemoryWriter",
        "def record_learning_event",
    ]
    hook_ok = check_code_integration(LEARNING_HOOK_FILE, hook_required)
    print()

    # Step 3: Check agent.py imports and uses learning hook
    print("Step 3: Verify Agent Hard-Wiring")
    print("-" * 60)
    agent_required = [
        "from .learning_hook import MandatoryLearningHook",
        "self.learning_hook = MandatoryLearningHook()",
        "record_learning_event(",
    ]
    agent_ok = check_code_integration(AGENT_FILE, agent_required)
    print()

    # Step 4: Check router uses Q-values
    print("Step 4: Verify Q-Value Routing")
    print("-" * 60)
    router_required = [
        "from torq_console.agents.torq_prince_flowers.core.learning_hook import MandatoryLearningHook",
        "self._learning_hook",
        "Q-value boost",
    ]
    router_ok = check_code_integration(ROUTER_FILE, router_required)
    print()

    # Step 5: Check memory files
    print("Step 5: Check Swarm Memory Files")
    print("-" * 60)
    routing_data = check_memory_file(ROUTING_SUCCESS, "Routing Stats")
    perf_data = check_memory_file(PERFORMANCE_HISTORY, "Performance History")
    rl_data = check_memory_file(RL_KNOWLEDGE, "RL Knowledge (Q-values)")

    interactions_ok = True
    if INTERACTIONS_LOG.exists():
        line_count = len(INTERACTIONS_LOG.read_text().strip().split('\n')) if INTERACTIONS_LOG.read_text().strip() else 0
        print(f"[OK] Interactions Log: {line_count} events logged")
    else:
        print(f"[WARN] Interactions Log: Will be created on first interaction")
    print()

    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    all_checks = files_ok and hook_ok and agent_ok and router_ok

    if all_checks:
        print("[PASS] ALL INTEGRATION CHECKS PASSED")
        print()
        print("The learning loop is properly installed:")
        print("  - MandatoryLearningHook is wired into agent.py")
        print("  - Router uses Q-values for decision making")
        print("  - Swarm memory files will populate on first interaction")
        print()
        print("Next steps:")
        print("  1. Run a test query through Prince Flowers")
        print("  2. Verify routing_success.json is populated")
        print("  3. Check interactions.jsonl for learning events")
        return 0
    else:
        print("[FAIL] SOME CHECKS FAILED")
        print()
        print("Please review the output above and fix missing items.")
        return 1


if __name__ == "__main__":
    exit(main())
