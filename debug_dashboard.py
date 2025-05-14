#!/usr/bin/env python3
"""
Debug script for the dashboard content issue in BlueAbel AIOS

This script will help diagnose issues with content display in the dashboard
by directly calling the get_content_items function and printing the results.
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
    from flask_ui.app import get_content_items, format_date
except ImportError:
    print("Error: Could not import functions from flask_ui.app")
    sys.exit(1)

def main():
    """Main function to debug dashboard content issues"""
    print("BlueAbel AIOS Dashboard Content Debugger")
    print("-" * 50)
    
    # Get content items using the same function as the dashboard
    print("Fetching content items using get_content_items(limit=5)...")
    content_data = get_content_items(limit=5)
    
    print("\nContent data structure:")
    print(f"Type: {type(content_data)}")
    print(f"Keys: {content_data.keys() if isinstance(content_data, dict) else 'Not a dictionary'}")
    
    # Analyze the items
    if "items" in content_data:
        items = content_data["items"]
        print(f"\nItems count: {len(items)}")
        
        # Print item types
        print(f"Item type: {type(items)}")
        if items and isinstance(items, list):
            print(f"First item type: {type(items[0])}")
        
        # Display each item
        print("\nContent Items:")
        for i, item in enumerate(items):
            print(f"\nItem {i+1}:")
            try:
                print(f"  Title: {item.get('title', 'N/A')} (type: {type(item.get('title', 'N/A'))})")
                print(f"  Type: {item.get('type', 'N/A')}")
                print(f"  Date: {format_date(item.get('created_at', 'N/A'))}")
                print(f"  Summary: {item.get('summary', 'N/A')[:50]}...")
                
                # Check if title is correctly formatted
                title = item.get('title', 'N/A')
                if not isinstance(title, str) or "<built-in method" in str(title):
                    print(f"  WARNING: Title appears to be a method reference instead of a string: {title}")
                    print(f"  Representation: {repr(title)}")
            except Exception as e:
                print(f"  Error processing item: {str(e)}")
    else:
        print("No 'items' key found in content_data")
    
    print("\nComplete content data (for debugging):")
    try:
        print(json.dumps(content_data, indent=2, default=str))
    except:
        print("Could not serialize content_data to JSON")
        import pprint
        pprint.pprint(content_data)

if __name__ == "__main__":
    main()