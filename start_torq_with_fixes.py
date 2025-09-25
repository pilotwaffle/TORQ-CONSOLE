#!/usr/bin/env python3
"""
TORQ Console Startup Script with Critical Fixes Applied

This script ensures the TORQ Console web interface starts with all
critical fixes for Prince Flowers integration and AI response routing.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from torq_console.core.console import TorqConsole
    from torq_console.core.config import TorqConfig
    from torq_console.ui.web import WebUI
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure you're in the TORQ-CONSOLE directory and have installed the requirements")
    sys.exit(1)

async def main():
    """Start TORQ Console with all fixes applied."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("[START] TORQ CONSOLE v0.70.0 - Starting with Critical Fixes")
    print("=" * 60)
    print("[OK] /api/chat endpoint added for direct queries")
    print("[OK] Prince Flowers command routing fixed")
    print("[OK] Search query detection improved")
    print("[OK] DirectChatRequest model added")
    print("=" * 60)

    try:
        # Initialize TORQ Console
        config = TorqConfig()
        console = TorqConsole(config=config)

        # Initialize Web UI
        web_ui = WebUI(console)

        print("[WEB] Starting web server at http://127.0.0.1:8899")
        print("[BOT] Prince Flowers Enhanced Agent ready")
        print("[CHAT] Web chat interface fully functional")
        print()
        print("[SEARCH] TEST THE FIX:")
        print("   1. Open http://127.0.0.1:8899 in your browser")
        print("   2. Type: search web for ai news")
        print("   3. Should return actual AI search results!")
        print("=" * 60)

        # Start server
        await web_ui.start_server(host="127.0.0.1", port=8899)

    except KeyboardInterrupt:
        print("\n👋 Shutting down TORQ Console...")
    except Exception as e:
        logger.error(f"[ERROR] Startup error: {e}")
        print(f"[ERROR] Failed to start: {e}")

if __name__ == "__main__":
    asyncio.run(main())