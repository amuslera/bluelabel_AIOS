#!/usr/bin/env python3
"""
Direct debug server for BlueAbel AIOS Flask UI

This script runs the Flask app directly without any intermediaries,
with full debug mode enabled.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import the Flask app
try:
    from flask_ui.app import app
except ImportError as e:
    print(f"Error importing Flask app: {e}")
    sys.exit(1)

# Enable debug mode
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == "__main__":
    print("Starting BlueAbel AIOS Flask UI in DEBUG mode")
    print("Visit http://127.0.0.1:9010 in your browser")
    print("Visit http://127.0.0.1:9010/debug/content/[content_id] for content debugging")
    app.run(host="127.0.0.1", port=9010, debug=True)