"""
Clean restart script for TORQ Console
Clears Python cache and restarts server
"""
import os
import sys
import shutil
import subprocess
import time

print("=" * 60)
print("TORQ CONSOLE - CLEAN RESTART")
print("=" * 60)

# Kill existing Python processes
print("\n1. Stopping existing TORQ processes...")
try:
    subprocess.run("taskkill /F /IM python.exe", shell=True, capture_output=True)
    time.sleep(2)
    print("   ✓ Processes stopped")
except:
    print("   ✓ No processes to stop")

# Clear Python cache
print("\n2. Clearing Python cache...")
cache_cleared = 0
for root, dirs, files in os.walk(r"E:\Torq-Console"):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(cache_path)
            cache_cleared += 1
        except:
            pass
    for file in files:
        if file.endswith('.pyc'):
            try:
                os.remove(os.path.join(root, file))
            except:
                pass

print(f"   ✓ Cleared {cache_cleared} cache directories")

# Start server
print("\n3. Starting TORQ Console...")
print("=" * 60)
os.chdir(r"E:\Torq-Console")
subprocess.run([sys.executable, "start_torq_with_fixes.py"])
