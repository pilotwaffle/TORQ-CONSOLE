"""
Test script to verify session persistence is working.

Run this after deploying the updated Railway backend and applying the migration.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_session_continuity():
    """Test that agents remember prior messages."""
    import httpx

    # Use Railway URL or localhost for testing
    base_url = os.environ.get("RAILWAY_URL", "http://localhost:8080")
    session_id = "test-session-continuity"

    print("=" * 60)
    print("TESTING SESSION CONTINUITY")
    print("=" * 60)
    print(f"Backend: {base_url}")
    print(f"Session ID: {session_id}")
    print()

    async with httpx.AsyncClient(timeout=30) as client:
        # Message 1: Establish context
        print("Message 1: Establishing context...")
        response1 = await client.post(
            f"{base_url}/api/chat",
            json={
                "message": "I'm building an AI consulting platform for business users.",
                "session_id": session_id,
                "mode": "auto"
            }
        )
        print(f"Status: {response1.status_code}")

        if response1.status_code == 200:
            data1 = response1.json()
            print(f"Agent: {data1.get('agent_id_used')}")
            print(f"Response preview: {data1.get('text', '')[:100]}...")
        else:
            print(f"Error: {response1.text}")
            return

        print()
        print("-" * 60)
        print()

        # Message 2: Follow-up (tests memory)
        print("Message 2: Follow-up question (tests memory)...")
        response2 = await client.post(
            f"{base_url}/api/chat",
            json={
                "message": "Based on what I just told you, what should I prioritize first?",
                "session_id": session_id,
                "mode": "auto"
            }
        )
        print(f"Status: {response2.status_code}")

        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Agent: {data2.get('agent_id_used')}")
            print(f"Response preview: {data2.get('text', '')[:200]}...")
            print()

            # Check if agent remembered context
            response_text = data2.get('text', '').lower()
            keywords = ['platform', 'business', 'consulting', 'ai', 'users']
            remembered = sum(1 for kw in keywords if kw in response_text)

            print("=" * 60)
            if remembered >= 2:
                print("✅ SESSION CONTINUITY: WORKING!")
                print(f"   Agent remembered context (found {remembered}/5 keywords)")
            else:
                print("❌ SESSION CONTINUITY: MAY BE BROKEN")
                print(f"   Agent may not have context (found {remembered}/5 keywords)")
                print()
                print("   Check that:")
                print("   1. Migration 003_chat_sessions_table.sql was applied")
                print("   2. Railway has been redeployed")
                print("   3. SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
        else:
            print(f"Error: {response2.text}")

    print("=" * 60)


async def test_sessions_api():
    """Test sessions API endpoints."""
    import httpx

    base_url = os.environ.get("RAILWAY_URL", "http://localhost:8080")

    print()
    print("=" * 60)
    print("TESTING SESSIONS API")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=30) as client:
        # List agents
        print("Testing /api/chat/agents...")
        response = await client.get(f"{base_url}/api/chat/agents")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Found {len(agents)} agents")
            for agent in agents[:3]:
                print(f"   - {agent.get('agent_id')}: {agent.get('agent_name')}")
        else:
            print(f"❌ Error: {response.text}")

        # Health check
        print()
        print("Testing /api/chat/health...")
        response = await client.get(f"{base_url}/api/chat/health")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            health = response.json()
            print(f"✅ Status: {health.get('status')}")
            print(f"   Active agents: {health.get('active_agents')}")
        else:
            print(f"❌ Error: {response.text}")

    print("=" * 60)


if __name__ == "__main__":
    print()
    print("TORQ Console - Session Persistence Test")
    print()
    print("This test will:")
    print("  1. Send a message establishing context")
    print("  2. Send a follow-up message")
    print("  3. Check if the agent remembers the context")
    print()

    asyncio.run(test_session_continuity())
    asyncio.run(test_sessions_api())

    print()
    print("To test after Railway deployment:")
    print("  1. Apply migration 003_chat_sessions_table.sql to Supabase")
    print("  2. Deploy Railway (git push or manual deploy)")
    print("  3. Set RAILWAY_URL to your Railway URL")
    print("  4. Run: python test_session_persistence.py")
    print()
