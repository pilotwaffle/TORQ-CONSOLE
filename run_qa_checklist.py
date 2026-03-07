"""
TORQ Console QA Checklist - Focused Re-run

Priority tests after session memory implementation:
- Test 1: Capability explanation
- Test 2: Session continuity
- Test 9: Follow-up reasoning
- Test 10: Execution planning
"""

import asyncio
import os
from datetime import datetime
import httpx

RAILWAY_URL = os.environ.get("RAILWAY_URL", "https://web-production-74ed0.up.railway.app")


async def send_message(session_id: str, message: str, agent_id: str = None):
    """Send a message and return response."""
    payload = {"message": message, "session_id": session_id, "mode": "auto"}
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
    print("=" * 70)
    print(text)
    print("=" * 70)


def print_test(name):
    print()
    print(f"TEST: {name}")
    print("-" * 70)


def print_ok(msg):
    print(f"[OK] {msg}")


def print_fail(msg):
    print(f"[FAIL] {msg}")


def print_info(msg):
    print(f"  {msg}")


def score_response(response_text: str, test_name: str) -> dict:
    """Score a response on Correctness, Clarity, Speed, Agent Choice, Usefulness."""
    text_lower = response_text.lower()

    # Heuristic scoring based on content analysis
    scores = {
        "correctness": 3,  # 1-5
        "clarity": 3,      # 1-5
        "speed": 3,        # 1-5 (simulated)
        "agent_choice": 3, # 1-5
        "usefulness": 3,   # 1-5
    }

    # Positive indicators
    if "torq" in text_lower or "console" in text_lower:
        scores["correctness"] += 1
    if "agent" in text_lower:
        scores["agent_choice"] += 1
    if len(response_text) > 200:
        scores["clarity"] += 1
    if any(word in text_lower for word in ["can", "help", "able", "support", "provide"]):
        scores["usefulness"] += 1

    # Cap at 5
    for key in scores:
        scores[key] = min(5, scores[key])

    return scores


async def test_1_capability_explanation():
    """Test 1: What can you help me with inside TORQ Console?"""
    print_test("Test 1: Capability Explanation")

    session_id = f"qa-test-1-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    response = await send_message(
        session_id,
        "What can you help me with inside TORQ Console?"
    )

    if not response.get("success"):
        print_fail(f"Request failed: {response.get('error')}")
        return {"passed": False}

    text = response.get("text", "")
    print_info(f"Agent: {response.get('agent_id_used')}")
    print_info(f"Response preview: {text[:150]}...")

    # Check for expected keywords
    expected = ["agent", "workflow", "task", "graph", "orchestrat", "research"]
    text_lower = text.lower()
    found = [kw for kw in expected if kw in text_lower]

    print_info(f"Keywords found: {found}")

    scores = score_response(text, "Capability Explanation")

    # Check if it's TORQ-native (not generic)
    is_torq_native = any(kw in text_lower for kw in ["torq", "console", "multi-agent", "orchestrat"])

    print()
    print(f"Scores: Correctness={scores['correctness']}/5, Clarity={scores['clarity']}/5, "
          f"Usefulness={scores['usefulness']}/5")
    print_info(f"TORQ-native: {'Yes' if is_torq_native else 'No'}")

    if len(found) >= 3 and is_torq_native:
        print_ok("PASS - Good capability explanation with TORQ context")
        return {"passed": True, "scores": scores}
    else:
        print_fail("FAIL - Generic or insufficient capability explanation")
        return {"passed": False, "scores": scores}


async def test_2_session_continuity():
    """Test 2: Session continuity"""
    print_test("Test 2: Session Continuity")

    session_id = f"qa-test-2-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Turn 1
    print_info("Turn 1: Establishing context...")
    r1 = await send_message(session_id, "I'm building an AI consulting platform for business users.")
    if not r1.get("success"):
        print_fail("Turn 1 failed")
        return {"passed": False}
    print_ok("Turn 1 received")

    # Turn 2
    print_info("Turn 2: Follow-up question...")
    r2 = await send_message(session_id, "Based on what I just told you, what should I prioritize first?")
    if not r2.get("success"):
        print_fail("Turn 2 failed")
        return {"passed": False}

    text = r2.get("text", "").lower()

    # Check for context awareness
    has_context = any(kw in text for kw in ["platform", "business", "consulting", "ai"])
    no_failure = not any(phrase in text for phrase in ["don't have context", "lack context", "don't remember"])

    print_info(f"Context keywords: {['platform', 'business', 'consulting', 'ai' if has_context else 'None found']}")
    print_info(f"No 'lack context' phrases: {no_failure}")

    if has_context and no_failure:
        print_ok("PASS - Session continuity working")
        return {"passed": True}
    else:
        print_fail("FAIL - Session continuity not working")
        return {"passed": False}


async def test_9_followup_reasoning():
    """Test 9: Follow-up reasoning"""
    print_test("Test 9: Follow-up Reasoning")

    session_id = f"qa-test-9-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Turn 1
    print_info("Turn 1: I want TORQ to feel more enterprise-grade.")
    r1 = await send_message(session_id, "I want TORQ to feel more enterprise-grade.")
    if not r1.get("success"):
        print_fail("Turn 1 failed")
        return {"passed": False}

    # Turn 2
    print_info("Turn 2: What are the top 5 product upgrades?")
    r2 = await send_message(session_id, "What are the top 5 product upgrades that would move it in that direction?")
    if not r2.get("success"):
        print_fail("Turn 2 failed")
        return {"passed": False}

    text = r2.get("text", "")

    # Check for numbered list or structured response
    has_structure = (
        any(pattern in text for pattern in ["1.", "1)", "- ", "•", "*"])
        or "upgrade" in text.lower()
    )

    # Check for enterprise-relevant suggestions
    enterprise_keywords = ["security", "audit", "sso", "rbac", "compliance", "monitoring", "telemetry", "sla"]
    has_enterprise = any(kw in text.lower() for kw in enterprise_keywords)

    print_info(f"Structured response: {has_structure}")
    print_info(f"Enterprise keywords: {has_enterprise}")

    scores = score_response(text, "Follow-up Reasoning")

    print()
    print(f"Scores: Correctness={scores['correctness']}/5, Clarity={scores['clarity']}/5, "
          f"Usefulness={scores['usefulness']}/5")

    if has_structure and has_enterprise:
        print_ok("PASS - Good follow-up with enterprise-relevant suggestions")
        return {"passed": True, "scores": scores}
    else:
        print_fail("FAIL - Weak follow-up reasoning")
        return {"passed": False, "scores": scores}


async def test_10_execution_planning():
    """Test 10: Execution planning"""
    print_test("Test 10: Execution Planning")

    session_id = f"qa-test-10-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    response = await send_message(
        session_id,
        "Give me a 30-day execution plan to improve TORQ Console from backend-complete to user-ready."
    )

    if not response.get("success"):
        print_fail("Request failed")
        return {"passed": False}

    text = response.get("text", "")

    # Check for plan structure
    has_phases = any(kw in text.lower() for kw in ["phase", "week", "step", "stage", "1.", "first"])
    has_timeline = any(kw in text.lower() for kw in ["day", "week", "month", "30-day", "timeline"])
    has_actions = any(kw in text.lower() for kw in ["implement", "build", "add", "create", "deploy"])

    print_info(f"Has phases/steps: {has_phases}")
    print_info(f"Has timeline: {has_timeline}")
    print_info(f"Has action items: {has_actions}")

    scores = score_response(text, "Execution Planning")

    print()
    print(f"Scores: Correctness={scores['correctness']}/5, Clarity={scores['clarity']}/5, "
          f"Usefulness={scores['usefulness']}/5")

    if has_phases and has_timeline and has_actions:
        print_ok("PASS - Structured execution plan provided")
        return {"passed": True, "scores": scores}
    else:
        print_fail("FAIL - Weak execution planning")
        return {"passed": False, "scores": scores}


async def main():
    print_header("TORQ Console QA Checklist - Priority Tests")
    print(f"Testing: {RAILWAY_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Run tests
    results["test1"] = await test_1_capability_explanation()
    results["test2"] = await test_2_session_continuity()
    results["test9"] = await test_9_followup_reasoning()
    results["test10"] = await test_10_execution_planning()

    # Summary
    print_header("QA RESULTS SUMMARY")

    test_names = {
        "test1": "Test 1: Capability Explanation",
        "test2": "Test 2: Session Continuity",
        "test9": "Test 9: Follow-up Reasoning",
        "test10": "Test 10: Execution Planning"
    }

    passed = sum(1 for v in results.values() if v.get("passed"))
    failed = sum(1 for v in results.values() if not v.get("passed"))

    for key, name in test_names.items():
        result = results[key]
        status = "[PASS]" if result.get("passed") else "[FAIL]"
        print(f"{status} {name}")
        if "scores" in result:
            s = result["scores"]
            print(f"      C={s['correctness']}/5 Cl={s['clarity']}/5 U={s['usefulness']}/5")

    print()
    print(f"Passed: {passed}/4")
    print(f"Failed: {failed}/4")

    # Calculate average scores
    all_scores = [r.get("scores") for r in results.values() if r.get("scores")]
    if all_scores:
        avg_correctness = sum(s["correctness"] for s in all_scores) / len(all_scores)
        avg_clarity = sum(s["clarity"] for s in all_scores) / len(all_scores)
        avg_usefulness = sum(s["usefulness"] for s in all_scores) / len(all_scores)

        print()
        print("Average Scores:")
        print(f"  Correctness: {avg_correctness:.1f}/5")
        print(f"  Clarity:     {avg_clarity:.1f}/5")
        print(f"  Usefulness:  {avg_usefulness:.1f}/5")

    print()
    if failed == 0:
        print("[SUCCESS] All priority tests passed!")
        print()
        print("Next steps:")
        print("  1. Verify TORQ-native onboarding (separate test)")
        print("  2. Proceed with Workflow Builder UI v1")
        return True
    else:
        print("[ISSUES] Some tests failed - review above")
        print()
        print("If scores are 3+/5 but tests failed, may need to adjust thresholds.")
        print("If responses are generic, tighten TORQ-native system context.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
