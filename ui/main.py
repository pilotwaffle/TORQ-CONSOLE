#!/usr/bin/env python3
"""
TORQ Console UI Main Entry Point
Main entry point for the TORQ Console web interface.
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from torq_console.ui.web import WebUI
from torq_console.core.console import TorqConsole
from torq_console.core.config import TorqConfig

async def main():
    """Main entry point for TORQ Console UI."""
    parser = argparse.ArgumentParser(description='TORQ Console Web Interface')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8899, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print(f"Starting TORQ Console Web UI at http://{args.host}:{args.port}")

    try:
        # Create TORQ Console instance first with config
        config = TorqConfig()
        console = TorqConsole(config=config)

        # Create and start the web application
        web_ui = WebUI(console)
        await web_ui.start_server(host=args.host, port=args.port)

    except KeyboardInterrupt:
        print("\nTORQ Console shutting down...")
    except Exception as e:
        print(f"Error starting TORQ Console: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())