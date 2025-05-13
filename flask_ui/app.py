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
import base64
import secrets

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
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(16))  # For session management
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
        # Call the API to get content items
        response = requests.get(f"{API_BASE_URL}/knowledge/list", 
                               params={"limit": limit, "type": content_type, "sort": sort_by})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result.get("results", [])
            
        # If API call fails, return demo data
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
    except Exception as e:
        print(f"Error fetching content items: {str(e)}")
        # Return empty list if API call fails
        return []

def get_content_item(content_id):
    """Get a specific content item from the API (with fallback to demo data)"""
    try:
        # Call the API to get content item details
        response = requests.get(f"{API_BASE_URL}/knowledge/item/{content_id}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result.get("item", {})
    except Exception as e:
        print(f"Error fetching content item: {str(e)}")
        
    # Return demo data if API call fails
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
    try:
        # Call the API to get components
        params = {}
        if component_type:
            params["tag"] = component_type
            
        response = requests.get(f"{API_BASE_URL}/components/", params=params)
        
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching components: {str(e)}")
    
    # Return demo data if API call fails
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

def get_oauth_status(service):
    """Get OAuth status for a specific service"""
    try:
        if service == "google":
            response = requests.get(f"{API_BASE_URL}/gateway/google/status")
            if response.status_code == 200:
                return response.json()
        elif service == "gmail":
            response = requests.get(f"{API_BASE_URL}/gateway/email/status")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Error fetching OAuth status: {str(e)}")
    
    return {"status": "unknown"}

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
    
    # Get recent content (from API if available)
    recent_content = get_content_items(limit=5)
    
    # Get content counts (would come from API in a full implementation)
    try:
        response = requests.get(f"{API_BASE_URL}/knowledge/stats")
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                content_count = result.get("total_count", 0)
                content_types = result.get("type_counts", {})
            else:
                content_count = len(recent_content)
                content_types = {"Demo": content_count}
        else:
            content_count = len(recent_content)
            content_types = {"Demo": content_count}
    except Exception as e:
        print(f"Error fetching content stats: {str(e)}")
        content_count = len(recent_content)
        content_types = {"URL": 2, "PDF": 1, "Text": 1}
    
    # Get recent activity (would come from API in full implementation)
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
            
            try:
                # Call the API to process the URL
                response = requests.post(f"{API_BASE_URL}/agents/contentmind/process", 
                                       json={"content_type": "url", 
                                             "content": url, 
                                             "metadata": {
                                                 "create_digest": create_digest, 
                                                 "model": model
                                             }
                                            })
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        flash(f"Successfully processed URL: {url}", "success")
                    else:
                        flash(f"Error processing URL: {result.get('message', 'Unknown error')}", "error")
                else:
                    flash(f"Error processing URL: {response.status_code}", "error")
            except Exception as e:
                flash(f"Error processing URL: {str(e)}", "error")
            
        elif content_type == 'text':
            text = request.form.get('text')
            create_digest = 'create_digest' in request.form
            model = request.form.get('model')
            
            try:
                # Call the API to process the text
                response = requests.post(f"{API_BASE_URL}/agents/contentmind/process", 
                                       json={"content_type": "text", 
                                             "content": text, 
                                             "metadata": {
                                                 "create_digest": create_digest, 
                                                 "model": model
                                             }
                                            })
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        flash(f"Successfully processed text content ({len(text)} characters)", "success")
                    else:
                        flash(f"Error processing text: {result.get('message', 'Unknown error')}", "error")
                else:
                    flash(f"Error processing text: {response.status_code}", "error")
            except Exception as e:
                flash(f"Error processing text: {str(e)}", "error")
            
        # Redirect to the same page to prevent form resubmission
        return redirect(url_for('process_content'))
    
    # GET request - render the page
    # Get available models from API or use defaults
    try:
        response = requests.get(f"{API_BASE_URL}/model-router/available-models")
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                models = {model: model for model in result.get("models", [])}
            else:
                models = {"Auto": "Auto-select", "GPT-4": "GPT-4", "Claude 3": "Claude 3", "Llama 3": "Llama 3"}
        else:
            models = {"Auto": "Auto-select", "GPT-4": "GPT-4", "Claude 3": "Claude 3", "Llama 3": "Llama 3"}
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        models = {"Auto": "Auto-select", "GPT-4": "GPT-4", "Claude 3": "Claude 3", "Llama 3": "Llama 3"}
    
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
        try:
            # Call the API to search content
            response = requests.get(f"{API_BASE_URL}/knowledge/search", params={"query": query})
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    results = result.get("results", [])
                else:
                    results = []
            else:
                results = []
        except Exception as e:
            print(f"Error searching content: {str(e)}")
            # For demo purposes, return sample results
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
        try:
            # Get specific component details from API
            response = requests.get(f"{API_BASE_URL}/components/{component_id}")
            
            if response.status_code == 200:
                component = response.json()
            else:
                component = {"id": component_id, "name": "Component Not Found", "content": "# Error loading component"}
        except Exception as e:
            print(f"Error fetching component: {str(e)}")
            component = {"id": component_id, "name": "Component Not Found", "content": "# Error loading component"}
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
    # Get current OAuth status
    google_status = get_oauth_status("google")
    gmail_status = get_oauth_status("gmail")
    
    # Determine connection status
    gmail_connected = gmail_status.get("status") == "running"
    gdrive_connected = google_status.get("status") == "authenticated"
    
    # Get email details if connected
    if gmail_connected:
        email_details = {
            "email": gmail_status.get("details", {}).get("username", "user@gmail.com"),
            "connected_date": "May 10, 2023",
            "scopes": "gmail.readonly, gmail.labels"
        }
    else:
        email_details = None
        
    return render_template('oauth_setup.html', 
                          active_page='oauth_setup', 
                          nav_items=NAV_ITEMS,
                          gmail_connected=gmail_connected,
                          gdrive_connected=gdrive_connected,
                          email_details=email_details)

@app.route('/api-status')
def api_status():
    """API status check endpoint (can be called from AJAX)"""
    status = check_api_status()
    return jsonify({"status": "online" if status else "offline"})

# OAuth routes
@app.route('/connect-service/<service>')
def connect_service(service):
    """Start OAuth flow for a service"""
    try:
        if service == "gmail" or service == "gdrive":
            # Call the API to start Google OAuth
            response = requests.get(f"{API_BASE_URL}/gateway/google/auth")
            
            if response.status_code == 200:
                result = response.json()
                auth_url = result.get("auth_url")
                
                if auth_url:
                    # Store service in session for callback
                    session["oauth_service"] = service
                    return redirect(auth_url)
                else:
                    flash(f"Error starting OAuth flow: No authorization URL returned", "error")
            else:
                flash(f"Error starting OAuth flow: {response.status_code}", "error")
        else:
            flash(f"OAuth not implemented for {service}", "error")
    except Exception as e:
        flash(f"Error starting OAuth flow: {str(e)}", "error")
    
    return redirect(url_for('oauth_setup'))

@app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback"""
    service = session.get("oauth_service")
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        flash(f"OAuth error: {error}", "error")
        return redirect(url_for('oauth_setup'))
    
    if not code:
        flash("No authorization code received", "error")
        return redirect(url_for('oauth_setup'))
    
    try:
        if service in ["gmail", "gdrive"]:
            # Call the API to complete Google OAuth
            response = requests.get(f"{API_BASE_URL}/gateway/google/callback?code={code}")
            
            if response.status_code == 200:
                flash(f"Successfully connected to {service.capitalize()}", "success")
                
                # If this is Gmail OAuth, also configure the email gateway
                if service == "gmail":
                    # Start the email gateway with OAuth
                    email_response = requests.post(f"{API_BASE_URL}/gateway/email/google")
                    
                    if email_response.status_code == 200:
                        flash("Email gateway configured with OAuth", "success")
                    else:
                        flash(f"Error configuring email gateway: {email_response.status_code}", "error")
            else:
                flash(f"Error completing OAuth flow: {response.status_code}", "error")
        else:
            flash(f"OAuth not implemented for {service}", "error")
    except Exception as e:
        flash(f"Error completing OAuth flow: {str(e)}", "error")
    
    return redirect(url_for('oauth_setup'))

@app.route('/disconnect-service/<service>')
def disconnect_service(service):
    """Disconnect a service"""
    try:
        if service == "gmail":
            # Call the API to stop the email gateway
            response = requests.post(f"{API_BASE_URL}/gateway/email/stop")
            
            if response.status_code == 200:
                flash("Successfully disconnected from Gmail", "success")
            else:
                flash(f"Error disconnecting from Gmail: {response.status_code}", "error")
        else:
            flash(f"Disconnect not implemented for {service}", "error")
    except Exception as e:
        flash(f"Error disconnecting service: {str(e)}", "error")
    
    return redirect(url_for('oauth_setup'))

@app.route('/save-credentials/<service>', methods=['POST'])
def save_credentials(service):
    """Save OAuth credentials"""
    try:
        if service == "google":
            # Get credentials from form
            client_id = request.form.get("client_id")
            client_secret = request.form.get("client_secret")
            
            if not client_id or not client_secret:
                flash("Client ID and Client Secret are required", "error")
                return redirect(url_for('oauth_setup'))
            
            # Call the API to update Google OAuth config
            response = requests.post(
                f"{API_BASE_URL}/gateway/google/config",
                json={
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            )
            
            if response.status_code == 200:
                flash("Google OAuth credentials saved", "success")
            else:
                flash(f"Error saving Google OAuth credentials: {response.status_code}", "error")
        elif service == "whatsapp":
            # Get credentials from form
            phone_id = request.form.get("phone_id")
            access_token = request.form.get("access_token")
            
            if not phone_id or not access_token:
                flash("Phone ID and Access Token are required", "error")
                return redirect(url_for('oauth_setup'))
            
            # Call the API to update WhatsApp config
            response = requests.post(
                f"{API_BASE_URL}/gateway/whatsapp/config",
                json={
                    "phone_id": phone_id,
                    "access_token": access_token,
                    "enabled": True
                }
            )
            
            if response.status_code == 200:
                flash("WhatsApp credentials saved", "success")
            else:
                flash(f"Error saving WhatsApp credentials: {response.status_code}", "error")
        else:
            flash(f"Saving credentials not implemented for {service}", "error")
    except Exception as e:
        flash(f"Error saving credentials: {str(e)}", "error")
    
    return redirect(url_for('oauth_setup'))

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
            if request.content_type == 'application/json':
                response = requests.post(url, json=request.get_json())
            else:
                response = requests.post(url, data=request.form)
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