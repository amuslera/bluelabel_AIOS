"""
BlueAbel AIOS - Flask UI Implementation

This is a Flask-based implementation of the BlueAbel AIOS UI.
It provides a full-featured web interface without the Streamlit sidebar duplication issues.
"""

import os
import sys
import json
import requests
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime, timedelta

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load configuration
try:
    with open(Path(project_root) / "server_config.json", "r") as f:
        config = json.load(f)
        
    # Get API configuration
    API_HOST = config["api"]["host"]
    API_PORT = config["api"]["port"]
    API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
except Exception as e:
    print(f"Warning: Could not load server configuration - {str(e)}")
    API_HOST = "127.0.0.1"
    API_PORT = 9001
    API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "static"))

# Configure Flask app
app.secret_key = os.urandom(24)  # For session management
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates during development

# Navigation configuration
NAV_ITEMS = {
    "Main": [
        {"name": "Dashboard", "icon": "🏠", "route": "dashboard", "description": "Overview and status"},
        {"name": "Process Content", "icon": "📝", "route": "process_content", "description": "Process new content"},
    ],
    "Content": [
        {"name": "View Content", "icon": "📚", "route": "view_content", "description": "Browse content repository"},
        {"name": "Search", "icon": "🔍", "route": "search", "description": "Search content"},
        {"name": "Digests", "icon": "📊", "route": "digests", "description": "Content digests"},
    ],
    "Components": [
        {"name": "Component Editor", "icon": "✏️", "route": "component_editor", "description": "Edit prompt components"},
        {"name": "Component Library", "icon": "📋", "route": "component_library", "description": "Browse components"},
    ],
    "System": [
        {"name": "Settings", "icon": "⚙️", "route": "settings", "description": "System settings"},
        {"name": "OAuth Setup", "icon": "🔐", "route": "oauth_setup", "description": "Configure OAuth"},
    ]
}

# Helper Functions
def check_api_status():
    """Check if the API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/status", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_content_items(limit=10, content_type=None, sort_by="date_desc"):
    """Get content items from the API (with fallback to demo data)"""
    try:
        # In a real implementation, this would call the API
        # response = requests.get(f"{API_BASE_URL}/content", params={"limit": limit, "type": content_type, "sort": sort_by})
        # return response.json()
        
        # For now, return demo data
        return [
            {
                "id": "1",
                "title": "Introduction to Artificial Intelligence",
                "summary": "An overview of AI concepts and applications.",
                "type": "url",
                "source": "https://example.com/ai-intro",
                "created_at": "2023-05-15T10:30:00Z",
                "tags": ["AI", "Technology", "Introduction"]
            },
            {
                "id": "2",
                "title": "Machine Learning Fundamentals",
                "summary": "Core concepts and techniques in machine learning.",
                "type": "pdf",
                "source": "Machine_Learning_Fundamentals.pdf",
                "created_at": "2023-05-10T14:45:00Z",
                "tags": ["ML", "Data Science", "AI"]
            }
        ]
    except:
        # Return empty list if API call fails
        return []

def get_content_item(content_id):
    """Get a specific content item from the API (with fallback to demo data)"""
    # In a real implementation, this would call the API
    # response = requests.get(f"{API_BASE_URL}/content/{content_id}")
    # return response.json()
    
    # For now, return demo data
    return {
        "id": content_id,
        "title": "Introduction to Artificial Intelligence",
        "summary": "An overview of AI concepts and applications.",
        "type": "url",
        "source": "https://example.com/ai-intro",
        "created_at": "2023-05-15T10:30:00Z",
        "content": "Artificial Intelligence (AI) is transforming our world in remarkable ways...",
        "tags": ["AI", "Technology", "Introduction"],
        "entities": [
            {"name": "Machine Learning", "type": "Concept"},
            {"name": "Deep Learning", "type": "Concept"},
            {"name": "Neural Networks", "type": "Technology"}
        ]
    }

def get_components(component_type=None):
    """Get MCP components from the API (with fallback to demo data)"""
    # In a real implementation, this would call the API
    # response = requests.get(f"{API_BASE_URL}/components", params={"type": component_type})
    # return response.json()
    
    # For now, return demo data
    return [
        {
            "id": "extract_summary",
            "name": "Extract Summary",
            "type": "Content Analysis",
            "version": "1.2"
        },
        {
            "id": "identify_themes",
            "name": "Identify Themes",
            "type": "Content Analysis",
            "version": "1.0"
        },
        {
            "id": "generate_digest",
            "name": "Generate Digest",
            "type": "Digest Generation",
            "version": "2.1"
        }
    ]

def format_date(date_str):
    """Format a date string consistently"""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str

# Routes
@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    # Check API status
    api_status = check_api_status()
    
    # Get recent content (would come from API in real implementation)
    recent_content = get_content_items(limit=5)
    
    # In a real implementation, these would come from the API
    content_count = 254
    content_types = {
        "URL": 124,
        "PDF": 76,
        "Text": 54
    }
    
    recent_activity = [
        {"time": "10:15 AM", "action": "Content Processing", "status": "Completed", "details": "URL: example.com/article"},
        {"time": "09:30 AM", "action": "Digest Generation", "status": "Completed", "details": "3 Documents"},
        {"time": "Yesterday", "action": "OAuth Setup", "status": "Completed", "details": "Gmail access"},
        {"time": "Yesterday", "action": "Content Search", "status": "Completed", "details": "Query: 'AI trends'"}
    ]
    
    return render_template('dashboard.html', 
                          active_page='dashboard',
                          nav_items=NAV_ITEMS,
                          api_status=api_status,
                          content_count=content_count,
                          content_types=content_types,
                          recent_content=recent_content,
                          recent_activity=recent_activity,
                          format_date=format_date)

@app.route('/process-content', methods=['GET', 'POST'])
def process_content():
    """Process content page"""
    if request.method == 'POST':
        content_type = request.form.get('content_type')
        
        if content_type == 'url':
            url = request.form.get('url')
            create_digest = 'create_digest' in request.form
            model = request.form.get('model')
            
            # In a real implementation, this would call the API
            # response = requests.post(f"{API_BASE_URL}/content/process", 
            #                          json={"content_type": "url", "content": url, "create_digest": create_digest, "model": model})
            
            # For demo, just flash a message
            flash(f"Processing URL: {url}", "success")
            
        elif content_type == 'text':
            text = request.form.get('text')
            create_digest = 'create_digest' in request.form
            model = request.form.get('model')
            
            # In a real implementation, this would call the API
            # response = requests.post(f"{API_BASE_URL}/content/process", 
            #                          json={"content_type": "text", "content": text, "create_digest": create_digest, "model": model})
            
            # For demo, just flash a message
            flash(f"Processing text content ({len(text)} characters)", "success")
            
        # Redirect to the same page to prevent form resubmission
        return redirect(url_for('process_content'))
    
    # GET request - render the page
    models = {
        "Auto": "Auto-select",
        "GPT-4": "GPT-4",
        "Claude 3": "Claude 3",
        "Llama 3": "Llama 3"
    }
    
    return render_template('process_content.html', 
                          active_page='process_content', 
                          nav_items=NAV_ITEMS,
                          models=models)

@app.route('/view-content')
def view_content():
    """View content page"""
    content_type = request.args.get('type')
    sort_by = request.args.get('sort', 'date_desc')
    
    # Get content items
    content_items = get_content_items(content_type=content_type, sort_by=sort_by)
    
    return render_template('view_content.html', 
                          active_page='view_content', 
                          nav_items=NAV_ITEMS,
                          content_items=content_items,
                          format_date=format_date,
                          selected_type=content_type,
                          selected_sort=sort_by)

@app.route('/content/<content_id>')
def content_detail(content_id):
    """Content detail page"""
    # Get content item
    content = get_content_item(content_id)
    
    return render_template('content_detail.html', 
                          active_page='view_content', 
                          nav_items=NAV_ITEMS,
                          content=content,
                          format_date=format_date)

@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    
    if query:
        # In a real implementation, this would call the API
        # response = requests.get(f"{API_BASE_URL}/search", params={"q": query})
        # results = response.json()
        
        # For now, return demo data
        results = [
            {
                "id": "1",
                "title": "Introduction to Artificial Intelligence",
                "summary": "An overview of AI concepts and applications.",
                "type": "url",
                "source": "https://example.com/ai-intro",
                "created_at": "2023-05-15T10:30:00Z",
                "tags": ["AI", "Technology", "Introduction"],
                "relevance": 0.95
            }
        ] if "ai" in query.lower() else []
    else:
        results = []
    
    return render_template('search.html', 
                          active_page='search', 
                          nav_items=NAV_ITEMS,
                          query=query,
                          results=results,
                          format_date=format_date)

@app.route('/digests')
def digests():
    """Digests page"""
    return render_template('digests.html', 
                          active_page='digests', 
                          nav_items=NAV_ITEMS)

@app.route('/component-editor')
def component_editor():
    """Component editor page"""
    component_id = request.args.get('id')
    
    if component_id:
        # In a real implementation, this would get the component from the API
        component = {"id": component_id, "name": "Sample Component", "content": "# This is a sample component\n\n{{input}} -> {{output}}"}
    else:
        component = None
    
    return render_template('component_editor.html', 
                          active_page='component_editor', 
                          nav_items=NAV_ITEMS,
                          component=component)

@app.route('/component-library')
def component_library():
    """Component library page"""
    component_type = request.args.get('type')
    
    # Get components
    components = get_components(component_type)
    
    return render_template('component_library.html', 
                          active_page='component_library', 
                          nav_items=NAV_ITEMS,
                          components=components)

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html', 
                          active_page='settings', 
                          nav_items=NAV_ITEMS)

@app.route('/oauth-setup')
def oauth_setup():
    """OAuth setup page"""
    return render_template('oauth_setup.html', 
                          active_page='oauth_setup', 
                          nav_items=NAV_ITEMS)

@app.route('/api-status')
def api_status():
    """API status check endpoint (can be called from AJAX)"""
    status = check_api_status()
    return jsonify({"status": "online" if status else "offline"})

# API proxy routes
@app.route('/api/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(endpoint):
    """Proxy requests to the API backend"""
    url = f"{API_BASE_URL}/{endpoint}"
    
    # Forward the request to the API
    try:
        if request.method == 'GET':
            response = requests.get(url, params=request.args)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json())
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json())
        elif request.method == 'DELETE':
            response = requests.delete(url)
        
        # Return the API response
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app if executed directly
if __name__ == '__main__':
    # Get port from command line or use default
    import argparse
    parser = argparse.ArgumentParser(description='Run the Flask UI')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    args = parser.parse_args()
    
    print(f"Starting Flask UI on http://localhost:{args.port}")
    app.run(debug=True, host='0.0.0.0', port=args.port)