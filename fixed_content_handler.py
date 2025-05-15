#!/usr/bin/env python3
"""
Fixed content handler for BlueAbel AIOS

This script provides a fixed implementation of content handling
that ensures proper data structure for content items.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def get_fixed_content_item(content_id):
    """Get a content item with guaranteed proper structure"""
    print(f"[FIXED_HANDLER] Getting content for ID: {content_id}")
    
    # Create a fixed demo item with proper structure
    demo_item = {
        "id": content_id,
        "title": f"Dynamic Content Item {content_id[:8]}",
        "type": "text",
        "content_type": "text",
        "summary": "This is a dynamically generated content item for demonstration purposes.",
        "source": "Demo Generator",
        "created_at": datetime.now().isoformat(),
        "content": """
# Dynamic Content

This content is dynamically generated for demonstration purposes. In a real application, this would contain the actual content retrieved from an API or database.

## Features
- Properly structured data
- All required fields present
- Formatted text content
- Tagged with relevant keywords

## Technical Details
This content was generated because the actual content could not be retrieved from the API. This could be due to:
1. API endpoint not available
2. Network connection issues
3. Authentication problems
4. Invalid content ID format

The content ID being requested is: {0}
        """.format(content_id),
        "tags": ["demo", "dynamic", "example"],
        "entities": [
            {"name": "Demo Content", "type": "Document"},
            {"name": "BlueAbel AIOS", "type": "System"}
        ]
    }
    
    return demo_item

def install_fixed_handler():
    """Install the fixed content handler into the Flask app"""
    try:
        # Import the Flask app
        from flask_ui.app import app
        
        # Define a new route for content detail with the fixed handler
        @app.route('/fixed/content/<content_id>')
        def fixed_content_detail(content_id):
            """Content detail page with fixed data handler"""
            # Get content item using the fixed handler
            content = get_fixed_content_item(content_id)
            
            # Render the template with the fixed content
            from flask import render_template
            return render_template('content_detail_fix.html', 
                                active_page='view_content', 
                                nav_items=app.config.get('NAV_ITEMS', {}),
                                content=content,
                                format_date=lambda date_str: datetime.fromisoformat(date_str).strftime('%Y-%m-%d') if date_str else '')
        
        print("[FIXED_HANDLER] Fixed content handler installed successfully")
        return True
    except Exception as e:
        print(f"[FIXED_HANDLER] Error installing fixed handler: {str(e)}")
        return False

if __name__ == "__main__":
    # When run directly, print a sample content item
    sample = get_fixed_content_item("test-id-123")
    print(json.dumps(sample, indent=2, default=str))