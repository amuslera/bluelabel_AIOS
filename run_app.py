#!/usr/bin/env python3
"""
BlueAbel AIOS Application Runner

This script starts both the API server and Flask UI simultaneously.
It reads configuration from server_config.json and handles proper shutdown.
"""

import os
import sys
import json
import time
import signal
import subprocess
import atexit
from pathlib import Path

# Load configuration
try:
    with open(Path(__file__).parent / "server_config.json", "r") as f:
        config = json.load(f)
    
    API_HOST = config["api"]["host"]
    API_PORT = config["api"]["port"]
    UI_TYPE = config["ui"].get("type", "flask")
    
    if UI_TYPE == "flask":
        UI_PORT = config["ui"]["flask"]["port"]
        UI_SCRIPT = "run_flask_ui.py"
    else:
        UI_PORT = config["ui"]["streamlit"]["port"]
        UI_SCRIPT = "run_streamlit.py"
        
except Exception as e:
    print(f"Error loading configuration: {e}")
    API_HOST = "127.0.0.1"
    API_PORT = 8081
    UI_PORT = 8080
    UI_SCRIPT = "run_flask_ui.py"
    UI_TYPE = "flask"

# Store process information
processes = []

def cleanup():
    """Kill all spawned processes on exit"""
    for process in processes:
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:  # Process didn't terminate
                    process.kill()
        except Exception as e:
            print(f"Error killing process: {e}")

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    print("\nShutting down all services...")
    cleanup()
    sys.exit(0)

# Register cleanup and signal handlers
atexit.register(cleanup)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_api_server():
    """Start the API server"""
    print(f"Starting API server on port {API_PORT}...")
    api_process = subprocess.Popen([sys.executable, "-m", "app.main"])
    processes.append(api_process)
    print(f"API server started with PID {api_process.pid}")
    return api_process

def start_ui_server():
    """Start the UI server"""
    print(f"Starting {UI_TYPE.capitalize()} UI on port {UI_PORT}...")
    ui_process = subprocess.Popen([sys.executable, UI_SCRIPT])
    processes.append(ui_process)
    print(f"{UI_TYPE.capitalize()} UI started with PID {ui_process.pid}")
    return ui_process

def wait_for_api():
    """Wait for API server to become available"""
    import requests
    print("Waiting for API server to start...")
    max_attempts = 30
    attempts = 0
    while attempts < max_attempts:
        try:
            response = requests.get(f"http://{API_HOST}:{API_PORT}/status", timeout=1)
            if response.status_code == 200:
                print("API server is running!")
                return True
        except requests.RequestException:
            pass
        
        attempts += 1
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(1)
    
    print("\nWarning: API server did not respond within expected time")
    print("UI may not function correctly without API connectivity")
    return False

if __name__ == "__main__":
    # Start API server
    api_process = start_api_server()
    
    # Wait for API to become available
    wait_for_api()
    
    # Start UI server
    ui_process = start_ui_server()
    
    # Print access information
    print("\nBlueAbel AIOS is now running!")
    print(f"API: http://{API_HOST}:{API_PORT}")
    print(f"UI:  http://{API_HOST}:{UI_PORT}")
    print("\nPress Ctrl+C to stop all servers")
    
    # Keep the script running until Ctrl+C
    try:
        while True:
            # Check if processes are still alive
            if api_process.poll() is not None:
                print("API server has stopped. Shutting down...")
                break
            
            if ui_process.poll() is not None:
                print("UI server has stopped. Shutting down...")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all services...")
    finally:
        cleanup()