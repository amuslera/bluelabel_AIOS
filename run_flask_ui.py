#!/usr/bin/env python3
"""
Run Flask UI for BlueAbel AIOS

This script starts the Flask UI for the BlueAbel AIOS system.
"""

import os
import sys
import argparse
import json
from pathlib import Path

def load_config():
    """Load configuration from server_config.json"""
    config_path = Path(__file__).parent / "server_config.json"
    if not config_path.exists():
        print(f"Warning: Configuration file not found: {config_path}")
        return {
            "ui": {
                "host": "127.0.0.1",
                "port": 8080
            }
        }
        
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)

def run_flask_ui(host, port):
    """Run the Flask UI"""
    print(f"Starting BlueAbel AIOS Flask UI on http://{host}:{port}")
    
    # Path to Flask app
    flask_app_path = Path(__file__).parent / "flask_ui" / "app.py"
    
    if not flask_app_path.exists():
        print(f"Error: Flask app not found at {flask_app_path}")
        sys.exit(1)
    
    # Ensure Flask is installed
    try:
        import flask
    except ImportError:
        print("Flask is not installed. Installing Flask...")
        os.system("pip3 install flask requests")
    
    # Environment variables
    os.environ["FLASK_APP"] = str(flask_app_path)
    os.environ["FLASK_ENV"] = "development"
    
    # Run Flask
    os.system(f"python3 -m flask run --host={host} --port={port}")

def main():
    """Main function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run BlueAbel AIOS Flask UI")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Get host and port (command line arguments override config)
    host = args.host or config.get("ui", {}).get("host", "127.0.0.1")
    port = args.port or config.get("ui", {}).get("port", 8080)
    
    # Run Flask UI
    run_flask_ui(host, port)

if __name__ == "__main__":
    main()