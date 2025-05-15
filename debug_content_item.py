#!/usr/bin/env python3
"""
Debug script for testing content item retrieval in BlueAbel AIOS

This script will help diagnose issues with content item detail display
by directly calling the get_content_item function and printing the results.
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Try to import from the flask_ui app
try:
    from flask_ui.app import get_content_item, API_BASE_URL
except ImportError:
    print("Error: Could not import functions from flask_ui.app")
    sys.exit(1)

def main():
    """Main function to debug content item retrieval issues"""
    print("BlueAbel AIOS Content Item Debugger")
    print("-" * 50)

    # Test content IDs to check
    test_ids = [
        "df347171-39a0-4617-b4df-74fd93b20d56",  # Real UUID-style ID from logs
        "ab9530f7-bcb0-4ddf-8210-fdfe8d5baf8d",  # Another real ID from logs
        "1",  # Demo data ID
        "non-existent-id"  # Non-existent ID to test fallback
    ]
    
    # Display API base URL
    print(f"API Base URL: {API_BASE_URL}\n")
    
    # Test each content ID
    for content_id in test_ids:
        print(f"Testing content ID: {content_id}")
        content = get_content_item(content_id)
        
        print(f"  Result type: {type(content)}")
        print(f"  Has content: {'Yes' if content else 'No'}")
        
        if content:
            print(f"  Title: {content.get('title', 'N/A')}")
            print(f"  Type: {content.get('type', 'N/A')}")
            print(f"  Content available: {'Yes' if 'content' in content else 'No'}")
            if 'content' in content:
                content_length = len(content['content']) if isinstance(content['content'], str) else 'Non-string content'
                print(f"  Content length: {content_length}")
            
            # Check if critical fields for display are present
            missing_fields = []
            for field in ['title', 'summary', 'type', 'source', 'created_at', 'content', 'tags']:
                if field not in content or content[field] is None or content[field] == '':
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"  WARNING: Missing fields: {', '.join(missing_fields)}")
        
        print("-" * 50)

if __name__ == "__main__":
    main()