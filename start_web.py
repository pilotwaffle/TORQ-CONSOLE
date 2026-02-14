#!/usr/bin/env python3
import subprocess
import sys
import os

# Start TORQ Console web server directly
subprocess.Popen([sys.executable, "-u", "torq_console", "--web"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print("TORQ Console Web Server starting on http://127.0.0.1:8000")
print("Press Ctrl+C to stop")