"""
A super simple Flask web app for BlueAbel AIOS
"""

from flask import Flask, render_template_string, redirect, url_for
from pathlib import Path
import os

app = Flask(__name__)

# Simple HTML template with no external dependencies
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BlueAbel AIOS - Simple UI</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
        }
        
        .sidebar {
            width: 250px;
            background-color: #f0f2f5;
            height: 100vh;
            padding: 20px;
            box-sizing: border-box;
        }
        
        .content {
            flex-grow: 1;
            padding: 20px;
        }
        
        h1 {
            color: #333;
        }
        
        .nav-item {
            margin-bottom: 10px;
        }
        
        .nav-item a {
            display: block;
            padding: 10px;
            text-decoration: none;
            color: #333;
            border-radius: 5px;
        }
        
        .nav-item a:hover {
            background-color: #e0e3e6;
        }
        
        .nav-item a.active {
            background-color: #4a6bf2;
            color: white;
        }
        
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background-color: #4a6bf2;
            color: white;
            border-radius: 4px;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>BlueAbel AIOS</h2>
        <hr>
        <div class="nav-item">
            <a href="/" {% if page == 'home' %}class="active"{% endif %}>Home</a>
        </div>
        <div class="nav-item">
            <a href="/process-content" {% if page == 'process' %}class="active"{% endif %}>Process Content</a>
        </div>
        <div class="nav-item">
            <a href="/view-content" {% if page == 'view' %}class="active"{% endif %}>View Content</a>
        </div>
        <div class="nav-item">
            <a href="/settings" {% if page == 'settings' %}class="active"{% endif %}>Settings</a>
        </div>
    </div>
    
    <div class="content">
        <h1>{{ title }}</h1>
        <div>
            {{ content | safe }}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    content = """
    <p>Welcome to the BlueAbel AIOS system. This is a simple web interface with no dependencies.</p>
    <div style="padding: 15px; background-color: #e7f3ff; border-radius: 5px; margin-top: 20px;">
        <p>This is a replacement UI that avoids the Streamlit sidebar duplication issues.</p>
    </div>
    """
    return render_template_string(HTML_TEMPLATE, page='home', title='Home', content=content)

@app.route('/process-content')
def process_content():
    content = """
    <p>Use this page to process new content.</p>
    <form method="GET" action="/process-content">
        <div style="margin-bottom: 15px;">
            <label for="content_type">Content Type:</label>
            <select id="content_type" name="content_type">
                <option value="url">URL</option>
                <option value="text">Text</option>
                <option value="file">File</option>
            </select>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label for="url">URL:</label>
            <input type="text" id="url" name="url" style="width: 300px;">
        </div>
        
        <div style="margin-bottom: 15px;">
            <label><input type="checkbox" name="create_digest"> Create Digest</label>
        </div>
        
        <button type="submit" class="btn">Process Content</button>
    </form>
    """
    return render_template_string(HTML_TEMPLATE, page='process', title='Process Content', content=content)

@app.route('/view-content')
def view_content():
    content = """
    <p>View and manage your processed content.</p>
    <div style="padding: 15px; background-color: #f9f9f9; border-radius: 5px; margin-top: 20px;">
        <p>No content available yet.</p>
    </div>
    """
    return render_template_string(HTML_TEMPLATE, page='view', title='View Content', content=content)

@app.route('/settings')
def settings():
    content = """
    <p>Configure system settings.</p>
    <form method="GET" action="/settings">
        <div style="margin-bottom: 15px;">
            <label for="api_endpoint">API Endpoint:</label>
            <input type="text" id="api_endpoint" name="api_endpoint" value="http://localhost:8081" style="width: 300px;">
        </div>
        
        <div style="margin-bottom: 15px;">
            <label><input type="checkbox" name="dark_mode"> Dark Mode</label>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label for="model">Default Model:</label>
            <select id="model" name="model">
                <option value="gpt4">GPT-4</option>
                <option value="claude">Claude</option>
                <option value="llama3">Llama 3</option>
            </select>
        </div>
        
        <button type="submit" class="btn">Save Settings</button>
    </form>
    """
    return render_template_string(HTML_TEMPLATE, page='settings', title='Settings', content=content)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)