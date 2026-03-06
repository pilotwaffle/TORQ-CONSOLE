"""
Simple Session Memory Validation - Windows Compatible

Tests session continuity with Railway backend.
"""

import asyncio
import os
import sys
from datetime import datetime
import httpx

# Configuration - use your Railway URL
RAILWAY_URL = os.environ.get("RAILWAY_URL", "https://web-production-74ed0.up.railway.app")


async def send_message(session_id: str, message: str, agent_id: str = None):
    """Send a message and return response."""
    payload = {
        "message": message,
        "session_id": session_id,
        "mode": "auto"
    }
    if agent_id:
        payload["agent_id"] = agent_id

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{RAILWAY_URL}/api/chat", json=payload)
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        data = response.json()
        data["success"] = True
        return data


def print_header(text):
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)


def print_ok(msg):
    print(f"[OK] {msg}")


def print_fail(msg):
    print(f"[FAIL] {msg}")


def print_info(msg):
    print(f"  {msg}")


async def test_two_turn_continuity():
    """Test that agent remembers first message in second response."""
    print_header("TEST 1: Two-Turn Continuity")

    session_id = f"test-two-turn-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Turn 1
    print_info("Turn 1: Establishing context...")
    print_info('  Message: "I\'m building an AI consulting platform for business users."')

    response1 = await send_message(
        session_id,
        "I'm building an AI consulting platform for business users."
    )

    if not response1.get("success"):
        print_fail(f"Turn 1 failed: {response1.get('error')}")
        return False

    print_ok(f"Turn 1 received (agent: {response1.get('agent_id_used')})")
    print_info(f"  Preview: {response1.get('text', '')[:100]}...")

    # Turn 2
    print()
    print_info("Turn 2: Asking follow-up...")
    print_info('  Message: "Based on what I just told you, what should I prioritize first?"')

    response2 = await send_message(
        session_id,
        "Based on what I just told you, what should I prioritize first?"
    )

    if not response2.get("success"):
        print_fail(f"Turn 2 failed: {response2.get('error')}")
        return False

    print_ok(f"Turn 2 received (agent: {response2.get('agent_id_used')})")

    # Check for context awareness
    response_text = response2.get("text", "").lower()

    # Failure phrases
    failure_phrases = [
        "i don't have context",
        "i lack context",
        "i don't remember",
        "you haven't told me"
    ]

    has_failure = any(phrase in response_text for phrase in failure_phrases)

    # Expected keywords
    expected_keywords = ["platform", "business", "consulting", "ai", "prioritize"]
    found_keywords = [kw for kw in expected_keywords if kw in response_text]

    print()
    print_info(f"Response preview: {response_text[:200]}...")
    print_info(f"Keywords found: {found_keywords}")

    if has_failure:
        print_fail("Agent explicitly states it lacks context!")
        return False
    elif len(found_keywords) >= 2:
        print_ok("Agent references prior context - PASS")
        return True
    else:
        print_fail("Agent doesn't show clear context awareness")
        return False


async def test_multi_turn():
    """Test 4-turn conversation coherence."""
    print_header("TEST 2: Multi-Turn Continuity (4 turns)")

    session_id = f"test-multi-turn-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    turns = [
        "I'm launching a fintech startup focused on cryptocurrency trading.",
        "What are the main regulatory challenges?",
        "Based on those challenges, what should my MVP focus on?",
        "Give me a 90-day execution plan."
    ]

    responses = []
    coherence_count = 0

    for i, turn in enumerate(turns, 1):
        print()
        print_info(f"Turn {i}: {turn[:50]}...")

        response = await send_message(session_id, turn)

        if not response.get("success"):
            print_fail(f"Turn {i} failed: {response.get('error')}")
            return False

        responses.append(response)
        print_ok(f"Turn {i} received")

        # Check for topic keywords in later turns
        if i > 1:
            text = response.get("text", "").lower()
            topics = ["fintech", "crypto", "startup", "regulatory", "mvp", "plan"]
            if any(t in text for t in topics):
                coherence_count += 1
                print_info(f"  Shows topic coherence")

    print()
    if coherence_count >= 2:
        print_ok(f"Multi-turn coherence maintained ({coherence_count}/3)")
        return True
    else:
        print_fail(f"Multi-turn coherence weak ({coherence_count}/3)")
        return False


async def test_session_isolation():
    """Test that different sessions don't leak context."""
    print_header("TEST 3: Session Isolation")

    session_a = f"test-iso-a-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session_b = f"test-iso-b-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Session A
    print_info("Session A: real estate platform context")
    await send_message(session_a, "I'm building a real estate platform called PropTech360.")

    # Session B
    print_info("Session B: food delivery app context")
    await send_message(session_b, "I'm building a food delivery app called QuickBite.")

    # Follow-up on Session A
    print()
    print_info("Session A: follow-up question")
    response = await send_message(session_a, "What should I prioritize?")

    if not response.get("success"):
        print_fail("Follow-up failed")
        return False

    text = response.get("text", "").lower()

    # Check for leakage from Session B
    leakage = ["food", "delivery", "quickbite", "restaurant"]
    has_leakage = any(kw in text for kw in leakage)

    # Check for correct context
    correct = ["real estate", "proptech", "property", "housing"]
    has_correct = any(kw in text for kw in correct)

    print_info(f"Response preview: {text[:150]}...")

    if has_leakage:
        print_fail("Session leaked context from other session!")
        return False
    elif has_correct:
        print_ok("Session isolation working - no leakage")
        return True
    else:
        print_fail("Session isolation unclear - no clear context")
        return False


async def main():
    print_header("TORQ Console - Session Memory Validation")
    print(f"Testing: {RAILWAY_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Run tests
    results["two_turn"] = await test_two_turn_continuity()
    results["multi_turn"] = await test_multi_turn()
    results["isolation"] = await test_session_isolation()

    # Summary
    print_header("RESULTS")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)

    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test}")

    print()
    print(f"Passed: {passed}/3")
    print(f"Failed: {failed}/3")

    if failed == 0:
        print()
        print("[SUCCESS] Session memory is working!")
        print()
        print("Next steps:")
        print("  1. Run full QA checklist")
        print("  2. Verify TORQ-native onboarding")
        print("  3. Proceed with frontend / Workflow Builder UI")
    else:
        print()
        print("[ISSUES] Some tests failed - check logs above")

    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
        sys.exit(1)
