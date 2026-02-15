#!/usr/bin/env python3
"""
Simplified TORQ Console Startup Script
"""
import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, str(project_root))

# Import TORQ Console
try:
    from torq_console import TorqConsole
    print('[OK] TORQ Console imported')
except Exception as e:
    print('[ERROR] Failed to import TORQ Console: {e}')
    sys.exit(1)

# Start web server
from torq_console.ui.web import WebUI
from torq_console.core.config import TorqConfig
config = TorqConfig()
console = TorqConsole(config=config)
web_ui = WebUI(console=console)

async def start():
    print('[INFO] Starting web server on http://localhost:8888...')
    try:
        result = await web_ui.start_server(host='0.0.0.0', port=8888)
        if result:
            print('[SUCCESS] Web server started')
        else:
            print('[ERROR] Failed to start web server')
    except Exception as e:
        print('[ERROR] Web server error: {e}')

if __name__ == '__main__':
    asyncio.run(start())
