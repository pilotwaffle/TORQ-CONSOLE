#!/usr/bin/env python3
"""Start web server on port 8082"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from start_simple_web_server import app
import uvicorn

if __name__ == "__main__":
    print("Starting server on http://127.0.0.1:8082")
    uvicorn.run(app, host="127.0.0.1", port=8082, log_level="info")
