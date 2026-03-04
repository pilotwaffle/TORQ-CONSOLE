"""
TORQ Chrome Bridge - Test Script

Run this to verify the Chrome Bridge is working correctly.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_connection():
    """Test basic connection to the bridge."""
    print("=" * 50)
    print("TORQ Chrome Bridge - Connection Test")
    print("=" * 50)
    print()

    # Import after path setup
    from torq_console.tools.chrome_operator import ChromeOperator, CHROME_BRIDGE_URL

    print(f"Bridge URL: {CHROME_BRIDGE_URL}")
    print()

    chrome = ChromeOperator()

    try:
        print("[1/3] Testing health check...")
        health = await chrome.health_check()
        print(f"  Status: {health['status']}")
        print(f"  Service: {health['service']}")
        print(f"  Version: {health['version']}")
        print(f"  Active sessions: {health['active_sessions']}")
        print("  [OK] Health check passed")
        print()

    except Exception as e:
        print(f"  [FAIL] Health check failed: {e}")
        print()
        print("Make sure the bridge is running:")
        print("  cd chrome_bridge && python host.py")
        return False

    try:
        print("[2/3] Creating session...")
        session = await chrome.create_session(metadata={"test": True})
        print(f"  Session ID: {session.session_id}")
        print(f"  Message: {session.message}")
        print("  [OK] Session created")
        print()

    except Exception as e:
        print(f"  [FAIL] Session creation failed: {e}")
        return False

    try:
        print("[3/3] Testing screenshot action...")
        print()
        print("  NOTE: For this test to work:")
        print(f"  1. Open Chrome extension popup")
        print(f"  2. Paste session_id: {session.session_id}")
        print(f"  3. Click 'Approve'")
        print(f"  4. Press Enter to continue...")
        input()

        result = await chrome.act(
            session.session_id,
            actions=[
                {"op": "get_title"},
                {"op": "screenshot"}
            ],
            require_approval=False
        )

        print(f"  OK: {result.ok}")
        print(f"  Results: {len(result.results)} actions executed")

        for r in result.results:
            print(f"    - {r.op}: {r.status}")
            if r.data:
                print(f"      Data: {r.data}")

        if result.artifacts.get("screenshot_png_data_url"):
            print(f"  Screenshot: Captured ({len(result.artifacts['screenshot_png_data_url'])} bytes)")

        if result.errors:
            print(f"  Errors: {result.errors}")

        if result.ok:
            print("  [OK] Screenshot test passed")
        else:
            print("  [FAIL] Screenshot test failed")

    except Exception as e:
        print(f"  [FAIL] Screenshot test failed: {e}")
        return False

    finally:
        await chrome.close()

    print()
    print("=" * 50)
    print("All tests passed! Chrome Bridge is working.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    asyncio.run(test_connection())
