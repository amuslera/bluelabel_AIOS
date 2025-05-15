#!/usr/bin/env python3
"""
Restart Flask UI with fixed content display

This script restarts the Flask UI server on a new port to apply the fixes.
"""

import os
import sys
import signal
import subprocess
from pathlib import Path

# Kill any existing Flask processes
try:
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            if 'flask' in cmdline and 'run' in cmdline:
                print(f"Killing Flask process: {proc.info['pid']}")
                os.kill(proc.info['pid'], signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
except ImportError:
    print("psutil not available, using ps | grep")
    try:
        ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
        for line in ps_output.splitlines():
            if 'flask' in line.lower() and 'run' in line.lower():
                try:
                    pid = int(line.split()[1])
                    print(f"Killing Flask process: {pid}")
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass
    except:
        print("Could not kill Flask processes")

# Get the project root
project_root = Path(__file__).parent
flask_app_path = project_root / "flask_ui" / "app.py"

# Set environment variables
os.environ["FLASK_APP"] = str(flask_app_path)
os.environ["FLASK_ENV"] = "development"

# Start Flask on a new port
port = 7070
print(f"Starting Flask UI on http://127.0.0.1:{port}")
subprocess.run([sys.executable, "-m", "flask", "run", "--host=127.0.0.1", "--port", str(port)])