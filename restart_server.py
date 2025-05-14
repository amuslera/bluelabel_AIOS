#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
from pathlib import Path

# Kill existing Flask processes
try:
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'flask' in ' '.join(proc.info['cmdline'] or []).lower():
                print(f"Killing Flask process: {proc.info['pid']}")
                os.kill(proc.info['pid'], signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
except ImportError:
    print("psutil not available, using ps | grep")
    try:
        ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
        for line in ps_output.splitlines():
            if 'flask' in line.lower():
                try:
                    pid = int(line.split()[1])
                    print(f"Killing Flask process: {pid}")
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass
    except:
        print("Could not kill Flask processes")

# Start a new Flask server
app_path = Path(__file__).parent / "flask_ui" / "app.py"
print(f"Starting Flask with app: {app_path}")

os.environ["FLASK_APP"] = str(app_path)
os.environ["FLASK_ENV"] = "development"

# Run Flask on port 8005
port = 8005
print(f"Starting server at http://127.0.0.1:{port}")
os.system(f"python3 -m flask run --host=127.0.0.1 --port={port}")
