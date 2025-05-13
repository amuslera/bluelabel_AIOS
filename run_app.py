#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def run_streamlit():
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    
    # Set PYTHONPATH to include project root
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{project_root}:{env.get('PYTHONPATH', '')}"
    
    # Kill any existing Streamlit processes
    try:
        subprocess.run(["pkill", "-f", "streamlit"], check=False)
        time.sleep(1)  # Give processes time to clean up
    except Exception as e:
        print(f"Warning: Could not kill existing processes: {e}")
    
    # Run Streamlit
    streamlit_cmd = [
        "streamlit", "run",
        str(project_root / "app" / "ui" / "streamlit_app.py"),
        "--server.port=8502",
        "--server.address=127.0.0.1"
    ]
    
    try:
        subprocess.run(streamlit_cmd, env=env)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_streamlit() 