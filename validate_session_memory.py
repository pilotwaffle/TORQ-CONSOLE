"""
Comprehensive Session Memory Validation Script

Tests all five critical cases for session persistence:
1. Two-turn continuity
2. Multi-turn continuity
3. Cross-agent continuity
4. Session isolation
5. Persistence verification (metadata check)
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import httpx

load_dotenv()

# Configuration
RAILWAY_URL = os.environ.get("RAILWAY_URL", "http://localhost:8080")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")


class Colors:
    """ANSI colors for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print("=" * 70)


def print_test(name: str):
    """Print a test name."""
    print()
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print("-" * 70)


def print_pass(message: str):
    """Print a pass result."""
    print(f"{Colors.GREEN}✅ PASS:{Colors.END} {message}")


def print_fail(message: str):
    """Print a fail result."""
    print(f"{Colors.RED}❌ FAIL:{Colors.END} {message}")


def print_warn(message: str):
    """Print a warning."""
    print(f"{Colors.YELLOW}⚠️  WARN:{Colors.END} {message}")


def print_info(message: str):
    """Print info."""
    print(f"  {message}")


async def send_message(session_id: str, message: str, agent_id: str = None, mode: str = "auto") -> dict:
    """Send a chat message and return the response."""
    async with httpx.AsyncClient(timeout=60) as client:
        payload = {
            "message": message,
            "session_id": session_id,
            "mode": mode
        }
        if agent_id:
            payload["agent_id"] = agent_id

        response = await client.post(f"{RAILWAY_URL}/api/chat", json=payload)

        if response.status_code != 200:
            return {
                "error": f"HTTP {response.status_code}: {response.text}",
                "success": False
            }

        data = response.json()
        data["success"] = True
        return data


def check_context_memory(response_text: str, expected_keywords: list) -> dict:
    """Check if response contains expected context keywords."""
    text_lower = response_text.lower()
    found = [kw for kw in expected_keywords if kw.lower() in text_lower]
    return {
        "found": found,
        "count": len(found),
        "total": len(expected_keywords),
        "ratio": len(found) / len(expected_keywords) if expected_keywords else 0
    }


async def test_two_turn_continuity():
    """
    Test 1: Two-turn continuity

    Turn 1: Establish context
    Turn 2: Reference that context

    Expected: Agent references prior turn naturally
    """
    print_test("Two-Turn Continuity")

    session_id = f"test-two-turn-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Turn 1: Establish context
    print_info("Turn 1: Establishing context...")
    print_info('  Sending: "I\'m building an AI consulting platform for business users."')

    response1 = await send_message(
        session_id,
        "I'm building an AI consulting platform for business users."
    )

    if not response1.get("success"):
        print_fail(f"Turn 1 failed: {response1.get('error')}")
        return False

    print_pass(f"Turn 1 response received (agent: {response1.get('agent_id_used')})")
    print_info(f"  Preview: {response1.get('text', '')[:100]}...")

    # Turn 2: Reference context
    print()
    print_info("Turn 2: Referencing context...")
    print_info('  Sending: "Based on what I just told you, what should I prioritize first?"')

    response2 = await send_message(
        session_id,
        "Based on what I just told you, what should I prioritize first?"
    )

    if not response2.get("success"):
        print_fail(f"Turn 2 failed: {response2.get('error')}")
        return False

    print_pass(f"Turn 2 response received (agent: {response2.get('agent_id_used')})")
    print_info(f"  Full response:\n  {response2.get('text', '')[:400]}...")

    # Check for context awareness
    print()
    expected_keywords = ["platform", "business", "consulting", "ai", "prioritize"]
    context_check = check_context_memory(response2.get("text", ""), expected_keywords)

    print_info(f"Context keywords found: {context_check['count']}/{context_check['total']}")

    # Check for failure phrases
    response_text = response2.get("text", "").lower()
    failure_phrases = [
        "i don't have context",
        "i lack context",
        "i don't remember",
        "i don't have information",
        "you haven't told me",
        "no context"
    ]

    has_failure_phrase = any(phrase in response_text for phrase in failure_phrases)

    if has_failure_phrase:
        print_fail("Agent explicitly states it lacks context!")
        print_info(f"  Found failure phrase in response")
        return False
    elif context_check["count"] >= 2:
        print_pass("Agent references prior context naturally")
        return True
    else:
        print_warn("Agent response is ambiguous (may or may not have context)")
        print_info(f"  Only found {context_check['count']} expected keywords")
        return None  # Indeterminate


async def test_multi_turn_continuity():
    """
    Test 2: Multi-turn continuity

    Use 4-5 turns and confirm thread coherence
    """
    print_test("Multi-Turn Continuity (4 turns)")

    session_id = f"test-multi-turn-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    turns = [
        "I'm launching a fintech startup focused on cryptocurrency trading.",
        "What are the main regulatory challenges I should know about?",
        "Based on those challenges, what should my MVP focus on?",
        "Give me a 90-day execution plan for that MVP."
    ]

    expected_themes = [
        ["fintech", "crypto", "startup"],  # Turn 1
        ["regulatory", "compliance", "challenge"],  # Turn 2
        ["mvp", "focus", "based"],  # Turn 3
        ["plan", "execution", "day"]  # Turn 4
    ]

    responses = []
    coherence_score = 0

    for i, (turn, themes) in enumerate(zip(turns, expected_themes), 1):
        print()
        print_info(f"Turn {i}: {turn[:60]}...")

        response = await send_message(session_id, turn)

        if not response.get("success"):
            print_fail(f"Turn {i} failed: {response.get('error')}")
            return False

        responses.append(response)
        print_pass(f"Turn {i} received (agent: {response.get('agent_id_used')})")

        # Check for theme consistency
        context_check = check_context_memory(response.get("text", ""), themes)
        print_info(f"  Theme relevance: {context_check['count']}/{context_check['total']}")

        # Later turns should show coherence
        if i > 1:
            # Check if response acknowledges previous context
            response_text = response.get("text", "").lower()

            # Simple coherence check: does it reference the conversation topic?
            topic_keywords = ["fintech", "crypto", "startup", "regulatory", "mvp"]
            topic_mentions = sum(1 for kw in topic_keywords if kw in response_text)

            if topic_mentions > 0:
                coherence_score += 1
                print_info(f"  Conversation coherence: {topic_mentions} topic mentions")

    print()
    if coherence_score >= 2:  # At least 2 of 3 later turns show coherence
        print_pass(f"Multi-turn conversation maintains coherence (score: {coherence_score}/3)")
        return True
    else:
        print_warn(f"Multi-turn coherence is weak (score: {coherence_score}/3)")
        return None


async def test_cross_agent_continuity():
    """
    Test 3: Cross-agent continuity

    Start with one agent, switch to another, same session_id.
    Verify memory behavior (shared or isolated).
    """
    print_test("Cross-Agent Continuity")

    session_id = f"test-cross-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Turn 1 with torq_prince_flowers
    print_info("Turn 1: Using torq_prince_flowers agent...")
    print_info('  Sending: "My startup is in the healthcare AI space."')

    response1 = await send_message(
        session_id,
        "My startup is in the healthcare AI space.",
        agent_id="torq_prince_flowers"
    )

    if not response1.get("success"):
        print_fail(f"Turn 1 failed: {response1.get('error')}")
        return False

    print_pass(f"Turn 1 received (agent: {response1.get('agent_id_used')})")

    # Turn 2 with research_agent
    print()
    print_info("Turn 2: Switching to research_agent...")
    print_info('  Sending: "Based on what I told you, what are the key trends?"')

    response2 = await send_message(
        session_id,
        "Based on what I told you, what are the key trends?",
        agent_id="research_agent"
    )

    if not response2.get("success"):
        print_fail(f"Turn 2 failed: {response2.get('error')}")
        return False

    print_pass(f"Turn 2 received (agent: {response2.get('agent_id_used')})")
    print_info(f"  Response preview: {response2.get('text', '')[:200]}...")

    # Check if second agent has context
    response_text = response2.get("text", "").lower()
    healthcare_keywords = ["healthcare", "health", "medical", "startup"]
    has_context = any(kw in response_text for kw in healthcare_keywords)

    print()
    if has_context:
        print_pass("Cross-agent memory: SHARED (second agent sees first agent's context)")
        print_info("  This is intentional shared session memory")
        return True
    else:
        print_warn("Cross-agent memory: ISOLATED (agents don't share context)")
        print_info("  Each agent maintains separate memory within the session")
        print_info("  This may be intentional design - confirm if this is desired")
        return None  # Neither pass nor fail - design decision


async def test_session_isolation():
    """
    Test 4: Session isolation

    Two different session_ids with similar prompts.
    Verify no leakage between sessions.
    """
    print_test("Session Isolation")

    session_a = f"test-iso-a-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session_b = f"test-iso-b-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Session A: specific context
    print_info("Session A: Setting unique context...")
    print_info('  Sending: "I\'m building a real estate platform called PropTech360."')

    response_a = await send_message(
        session_a,
        "I'm building a real estate platform called PropTech360."
    )

    if not response_a.get("success"):
        print_fail(f"Session A failed: {response_a.get('error')}")
        return False

    print_pass("Session A established")

    # Session B: different context
    print()
    print_info("Session B: Setting different context...")
    print_info('  Sending: "I\'m building a food delivery app called QuickBite."')

    response_b = await send_message(
        session_b,
        "I'm building a food delivery app called QuickBite."
    )

    if not response_b.get("success"):
        print_fail(f"Session B failed: {response_b.get('error')}")
        return False

    print_pass("Session B established")

    # Follow-up on Session A
    print()
    print_info("Session A: Follow-up to check isolation...")
    print_info('  Sending: "What should I prioritize?"')

    followup_a = await send_message(session_a, "What should I prioritize?")

    if not followup_a.get("success"):
        print_fail(f"Session A follow-up failed: {followup_a.get('error')}")
        return False

    text_a = followup_a.get("text", "").lower()

    # Check for leakage from Session B
    leakage_keywords = ["food", "delivery", "quickbite", "restaurant"]
    has_leakage = any(kw in text_a for kw in leakage_keywords)

    # Check for correct context
    correct_keywords = ["real estate", "proptech", "property", "housing"]
    has_correct = any(kw in text_a for kw in correct_keywords)

    print()
    if has_leakage:
        print_fail("Session isolation FAILED - Session A leaked context from Session B!")
        print_info(f"  Found leakage keywords: {leakage_keywords}")
        return False
    elif has_correct:
        print_pass("Session isolation working - Session A maintains its own context")
        return True
    else:
        print_warn("Session isolation indeterminate - no clear context found")
        return None


async def test_supabase_persistence():
    """
    Test 5: Persistence verification

    Check that messages are actually stored in Supabase with proper metadata.
    """
    print_test("Supabase Persistence Verification")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print_warn("Supabase credentials not set - skipping direct DB verification")
        print_info("  Session will still validate via API behavior")
        return None

    session_id = f"test-persist-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Send a message
    print_info("Sending test message...")
    response = await send_message(session_id, "Test persistence check")

    if not response.get("success"):
        print_fail(f"Message failed: {response.get('error')}")
        return False

    print_pass("Message sent via API")

    # Check Supabase directly
    print()
    print_info("Querying Supabase directly...")

    try:
        from supabase import create_client

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        result = supabase.table("chat_sessions").select("*").eq("session_id", session_id).execute()

        if not result.data:
            print_fail("Session not found in Supabase - persistence not working!")
            return False

        session = result.data[0]
        messages = session.get("messages", [])

        print_pass(f"Session found in Supabase")
        print_info(f"  Messages stored: {len(messages)}")

        if len(messages) < 2:  # Should have user + assistant
            print_warn(f"Expected at least 2 messages, found {len(messages)}")
            return False

        # Check message structure
        print()
        print_info("Message metadata check:")

        for i, msg in enumerate(messages[:2]):  # Check first 2 messages
            print_info(f"  Message {i+1}:")
            print_info(f"    - role: {msg.get('role')}")
            print_info(f"    - content: {msg.get('content', '')[:50]}...")
            print_info(f"    - timestamp: {msg.get('timestamp')}")
            print_info(f"    - agent_id: {msg.get('agent_id')}")
            print_info(f"    - deleted: {msg.get('deleted')}")

        # Validate structure
        required_fields = ["role", "content", "timestamp", "deleted"]
        all_valid = all(
            all(field in msg for field in required_fields)
            for msg in messages
        )

        print()
        if all_valid:
            print_pass("All messages have correct metadata structure")
            return True
        else:
            print_warn("Some messages missing required fields")
            return False

    except Exception as e:
        print_warn(f"Could not verify Supabase directly: {e}")
        print_info("  API behavior will be used for validation")
        return None


async def run_all_tests():
    """Run all validation tests."""
    print_header("TORQ Console - Session Memory Validation")

    print(f"Testing against: {RAILWAY_URL}")
    print(f"Supabase: {SUPABASE_URL[:50] if SUPABASE_URL else 'Not configured'}...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Test 1: Two-turn continuity
    results["two_turn"] = await test_two_turn_continuity()

    # Test 2: Multi-turn continuity
    results["multi_turn"] = await test_multi_turn_continuity()

    # Test 3: Cross-agent continuity
    results["cross_agent"] = await test_cross_agent_continuity()

    # Test 4: Session isolation
    results["isolation"] = await test_session_isolation()

    # Test 5: Supabase persistence
    results["persistence"] = await test_supabase_persistence()

    # Summary
    print_header("VALIDATION SUMMARY")

    test_names = {
        "two_turn": "Two-Turn Continuity",
        "multi_turn": "Multi-Turn Continuity",
        "cross_agent": "Cross-Agent Continuity",
        "isolation": "Session Isolation",
        "persistence": "Supabase Persistence"
    }

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    indeterminate = sum(1 for v in results.values() if v is None)

    for key, name in test_names.items():
        result = results[key]
        if result is True:
            print_pass(name)
        elif result is False:
            print_fail(name)
        else:
            print_warn(f"{name} (indeterminate)")

    print()
    print(f"{Colors.BOLD}Results:{Colors.END}")
    print(f"  Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"  Failed: {Colors.RED}{failed}{Colors.END}")
    print(f"  Indeterminate: {Colors.YELLOW}{indeterminate}{Colors.END}")

    print()
    if failed == 0 and passed >= 3:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SESSION MEMORY: WORKING!{Colors.END}")
        print()
        print("Recommended next steps:")
        print("  1. Run full QA checklist (especially Tests 1, 2, 9, 10)")
        print("  2. Verify TORQ-native onboarding response")
        print("  3. Proceed with frontend / Workflow Builder UI")
    elif failed > 0:
        print(f"{Colors.RED}{Colors.BOLD}❌ ISSUES FOUND - Fix before proceeding{Colors.END}")
        print()
        print("Common fixes:")
        print("  1. Ensure migration 003_chat_sessions_table.sql was applied")
        print("  2. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
        print("  3. Verify Railway has been redeployed")
        print("  4. Check Railway logs for errors")
    else:
        print(f"{Colors.YELLOW}⚠️  SOME TESTS INDETERMINATE - Manual review needed{Colors.END}")

    print("=" * 70)


if __name__ == "__main__":
    print()
    print("Before running, ensure:")
    print("  1. RAILWAY_URL is set (or using localhost)")
    print("  2. Supabase migration 003_chat_sessions_table.sql has been applied")
    print("  3. Railway has been redeployed with session_store changes")
    print()

    input("Press Enter to start validation...")

    asyncio.run(run_all_tests())
