#!/usr/bin/env python3
"""
TORQ CONSOLE Demo Script.

Demonstrates the enhanced AI pair programming capabilities with
Claude Code integration and MCP connectivity.
"""

import asyncio
import sys
from pathlib import Path

# Add TORQ CONSOLE to path
sys.path.insert(0, str(Path(__file__).parent))

from torq_console.core.console import TorqConsole
from torq_console.core.config import TorqConfig


async def demo_torq_console():
    """Demonstrate TORQ CONSOLE capabilities."""
    print("TORQ CONSOLE Demo - Enhanced AI Pair Programming")
    print("=" * 60)

    # Initialize configuration
    print("\n1. Initializing TORQ CONSOLE...")
    config = TorqConfig.create_default()
    print(f"   OK Configuration loaded")
    print(f"   INFO MCP Servers configured: {len(config.mcp_servers)}")
    print(f"   INFO AI Models available: {len(config.ai_models)}")

    # Initialize console
    console = TorqConsole(
        config=config,
        repo_path=Path.cwd(),
        model="claude-3-5-sonnet-20241022",
        ideation_mode=True,
        planning_mode=True
    )

    print(f"   OK Console initialized at {console.repo_path}")

    # Start session
    print("\n2. Starting AI session...")
    session = await console.start_session()
    print(f"   OK Session started: {session['id']}")

    # Demonstrate file detection
    print("\n3. Testing intelligent file detection...")
    test_message = "update the pyproject.toml to add new dependencies"
    files = await console.detect_relevant_files(test_message)
    print(f"   FILES Detected relevant files: {files}")

    # Demonstrate visual diff
    print("\n4. Testing visual diff engine...")
    diff_content = await console.get_visual_diff("rich")
    if diff_content and "No changes detected" not in diff_content:
        print(f"   DIFF Generated visual diff ({len(diff_content)} chars)")
    else:
        print("   DIFF No changes to display (clean repository)")

    # Demonstrate MCP connectivity (simulated)
    print("\n5. Testing MCP integration...")
    print("   MCP Servers configured:")
    for server in config.mcp_servers:
        print(f"      - {server.name}: {server.endpoint}")

    # Demonstrate planning
    print("\n6. Testing AI planning capabilities...")
    plan = await console.generate_plan("Add voice command support to TORQ CONSOLE")
    print(f"   PLAN Generated plan with {len(plan.get('steps', []))} steps")
    if 'steps' in plan:
        for i, step in enumerate(plan['steps'][:3], 1):
            print(f"      {i}. {step}")

    # Show session info
    print("\n7. Session summary...")
    session_info = console.get_session_info()
    print(f"   ID Session ID: {session_info.get('id', 'Unknown')}")
    print(f"   REPO Repository: {Path(session_info.get('repo_path', '')).name}")
    print(f"   MODEL Model: {session_info.get('model', 'Unknown')}")

    # Cleanup
    await console.shutdown()

    print("\nDemo complete! TORQ CONSOLE is ready for enhanced AI pair programming.")
    print("\nNext steps:")
    print("   - Run 'torq --interactive' for interactive mode")
    print("   - Run 'torq --web' for web UI")
    print("   - Connect your existing MCP servers")
    print("   - Start coding with AI assistance!")


def show_architecture_overview():
    """Show TORQ CONSOLE architecture overview."""
    print("\nTORQ CONSOLE Architecture")
    print("=" * 40)
    print("""
+------------------+    +-------------------+    +------------------+
|   Claude Code    |<-->|   TORQ CONSOLE    |<-->|  Your MCP        |
|   Integration    |    |    Core Engine    |    |  Infrastructure  |
+------------------+    +-------------------+    +------------------+
        |                        |                        |
        v                        v                        v
+------------------+    +-------------------+    +------------------+
| - File Editing   |    | - AI Planning     |    | - N8N Workflows  |
| - Git Ops        |    | - MCP Bridge      |    | - Memory System  |
| - Diff Viewing   |    | - Session Mgmt    |    | - Browser Auto   |
| - Syntax Highlight|   | - Voice Commands  |    | - Database Ops   |
+------------------+    +-------------------+    +------------------+

Key Features:
- Native MCP integration with your existing infrastructure
- Enhanced visual diffs (delta, bat, rich syntax highlighting)
- Voice command support (Whisper + TTS)
- Modern web UI with real-time collaboration
- AI-powered ideation and planning modes
- Claude Code tool compatibility layer
""")


async def main():
    """Run the demo."""
    try:
        show_architecture_overview()
        await demo_torq_console()
        return 0
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Thanks for trying TORQ CONSOLE!")
        return 0
    except Exception as e:
        print(f"\nError: Demo error: {e}")
        print("\nThis is expected in a development environment.")
        print("Install dependencies and connect MCP servers for full functionality.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)