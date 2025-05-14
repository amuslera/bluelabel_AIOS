#!/usr/bin/env python3
"""
Run Flask UI for BlueAbel AIOS on an alternative port
"""

import os
import sys
import json
from pathlib import Path

# Directly specify a different port
HOST = "127.0.0.1"
PORT = 9005  # Using port 9005 instead of 9002

# Path to Flask app
flask_app_path = Path(__file__).parent / "flask_ui" / "app.py"

if not flask_app_path.exists():
    print(f"Error: Flask app not found at {flask_app_path}")
    sys.exit(1)

# Environment variables
os.environ["FLASK_APP"] = str(flask_app_path)
os.environ["FLASK_ENV"] = "development"

print(f"Starting Flask UI on http://{HOST}:{PORT}")
# Run Flask directly
os.system(f"python3 -m flask run --host={HOST} --port={PORT}")