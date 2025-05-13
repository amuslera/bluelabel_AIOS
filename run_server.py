#!/usr/bin/env python3
"""
Server management script for BlueAbel AIOS.
This script starts both the FastAPI server and Flask UI with proper configuration.
"""

import json
import os
import signal
import subprocess
import sys
import time
import logging
import argparse
import atexit
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("server")

# Store process IDs for cleanup
PROCESS_LIST = []

def load_config():
    """Load configuration from server_config.json"""
    config_path = Path(__file__).parent / "server_config.json"
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
        
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing configuration file: {str(e)}")
        print(f"Error: Could not parse configuration file: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

def start_api_server(api_config):
    """Start the FastAPI server"""
    logger.info("Starting API server...")
    
    cmd = [
        "python3", "-m", "uvicorn",
        "app.main:app",
        "--host", api_config.get("host", "127.0.0.1"),
        "--port", str(api_config.get("port", 8081)),
        "--workers", "1"  # Always use single worker
    ]
    
    # Only add reload flag if explicitly enabled
    if api_config.get("reload", False):
        cmd.append("--reload")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        PROCESS_LIST.append(process.pid)
        logger.info(f"API server started with PID {process.pid}")
        
        # Log the first few lines to confirm startup
        for _ in range(10):
            line = process.stdout.readline()
            if line:
                logger.info(f"API: {line.strip()}")
            if "Application startup complete" in line:
                break
            time.sleep(0.1)
        
        return process
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        print(f"Error: Failed to start API server: {str(e)}")
        cleanup()
        sys.exit(1)

def start_ui_server(ui_config):
    """Start the Flask UI server"""
    logger.info("Starting Flask UI server...")
    
    # Get Flask configuration
    flask_config = ui_config.get("flask", {})
    flask_port = flask_config.get("port", 8080)
    flask_host = flask_config.get("host", "127.0.0.1")
    flask_debug = flask_config.get("debug", True)
    
    # Use the Flask UI implementation
    ui_path = Path(__file__).parent / "run_flask_ui.py"
    
    if not ui_path.exists():
        logger.error(f"UI file not found: {ui_path}")
        print(f"Error: UI file not found: {ui_path}")
        cleanup()
        sys.exit(1)
    
    cmd = [
        "python3", str(ui_path),
        "--port", str(flask_port)
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        PROCESS_LIST.append(process.pid)
        logger.info(f"UI server started with PID {process.pid}")
        
        # Log the first few lines to confirm startup
        for _ in range(10):
            line = process.stdout.readline()
            if line:
                logger.info(f"UI: {line.strip()}")
            if "Running on" in line:
                break
            time.sleep(0.1)
        
        return process
    except Exception as e:
        logger.error(f"Failed to start UI server: {str(e)}")
        print(f"Error: Failed to start UI server: {str(e)}")
        cleanup()
        sys.exit(1)

def cleanup():
    """Cleanup processes on exit"""
    logger.info("Cleaning up processes...")
    for pid in PROCESS_LIST:
        try:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Terminated process with PID {pid}")
        except ProcessLookupError:
            # Process already gone
            pass
        except Exception as e:
            logger.warning(f"Error terminating process {pid}: {str(e)}")

def main():
    """Main function to start servers"""
    parser = argparse.ArgumentParser(description="Start BlueAbel AIOS servers")
    parser.add_argument("--api-only", action="store_true", help="Start only the API server")
    parser.add_argument("--ui-only", action="store_true", help="Start only the UI server")
    args = parser.parse_args()
    
    # Register cleanup handler
    atexit.register(cleanup)
    
    # Load configuration
    config = load_config()
    
    try:
        # Start servers based on arguments
        api_process = None
        ui_process = None
        
        if not args.ui_only:
            api_process = start_api_server(config["api"])
            print(f"API server running at http://{config['api']['host']}:{config['api']['port']}")
        
        if not args.api_only:
            # Small delay to ensure API is up before UI
            if api_process:
                time.sleep(2)
            
            ui_process = start_ui_server(config["ui"])
            print(f"UI server running at http://{config['ui']['flask']['host']}:{config['ui']['flask']['port']}")
        
        print("\nPress Ctrl+C to stop servers\n")
        
        # Keep script running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if api_process and api_process.poll() is not None:
                logger.error("API server stopped unexpectedly")
                print("Error: API server stopped unexpectedly")
                if not args.ui_only:
                    break
            
            if ui_process and ui_process.poll() is not None:
                logger.error("UI server stopped unexpectedly")
                print("Error: UI server stopped unexpectedly")
                if not args.api_only:
                    break
                
    except KeyboardInterrupt:
        print("\nStopping servers...")
        logger.info("Received keyboard interrupt, shutting down")
    finally:
        cleanup()

if __name__ == "__main__":
    main()