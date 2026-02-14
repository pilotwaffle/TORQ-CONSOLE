#!/usr/bin/env python3
import subprocess
import sys

# Start TORQ Console web server directly
subprocess.Popen([sys.executable, "-m", "torq_console", "--web"])
print("TORQ Console Web Server starting on http://127.0.0.1:8081")
print("Press Ctrl+C to stop")
