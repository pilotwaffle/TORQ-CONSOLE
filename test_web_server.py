#!/usr/bin/env python3
"""Test script to diagnose web server startup issues"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_web_ui():
    """Test WebUI initialization"""
    print("Testing WebUI initialization...")

    from torq_console.ui.web import WebUI
    from torq_console.core.config import TorqConfig
    from torq_console.core.console import TorqConsole
    from torq_console.core.context_manager import ContextManager

    print("Creating config...")
    config = TorqConfig()

    print("Creating console...")
    console = TorqConsole(config)

    print("Creating context manager...")
    console.context_manager = ContextManager(config=config)

    print("Calling console.initialize_async()...")
    try:
        await console.initialize_async()
        print("console.initialize_async() completed")
    except Exception as e:
        print(f"ERROR in console.initialize_async(): {e}")
        import traceback
        traceback.print_exc()
        return

    print("Creating WebUI...")
    try:
        web_ui = WebUI(console=console)
        print("WebUI created successfully")
    except Exception as e:
        print(f"ERROR creating WebUI: {e}")
        import traceback
        traceback.print_exc()
        return

    print("Testing _get_console_info()...")
    try:
        info = await web_ui._get_console_info()
        print(f"Console info retrieved: {info}")
    except Exception as e:
        print(f"ERROR in _get_console_info(): {e}")
        import traceback
        traceback.print_exc()

    print("\nAll tests passed!")

if __name__ == "__main__":
    asyncio.run(test_web_ui())
