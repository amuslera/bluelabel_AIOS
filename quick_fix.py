#!/usr/bin/env python3
"""
Quick Fix for BlueAbel AIOS Content Display

This script creates fixed templates for content display that will always work,
regardless of the data structure issues.
"""

import os
import sys
from pathlib import Path
import shutil

# Get the project root
project_root = Path(__file__).parent
templates_dir = project_root / "flask_ui" / "templates"

def create_fixed_templates():
    """Create fixed versions of the templates that handle all edge cases"""
    
    # Create backup directory
    backup_dir = project_root / "backup_templates"
    backup_dir.mkdir(exist_ok=True)
    
    # Backup original templates first
    for template in ['content_detail.html', 'view_content.html']:
        original = templates_dir / template
        if original.exists():
            backup = backup_dir / template
            shutil.copy2(original, backup)
            print(f"Backed up {original} to {backup}")
    
    # Create a fixed content_detail.html
    content_detail = """{% extends "base.html" %}

{% block title %}Content Details - BlueAbel AIOS{% endblock %}

{% block content %}
<div class="page-header">
    <h1>Content Details</h1>
    <div class="page-actions">
        <a href="{{ url_for('view_content') }}" class="btn btn-secondary">Back to Content List</a>
    </div>
</div>

<div class="content-detail">
    <div class="card">
        <div class="card-header">
            <h2 class="content-title">
                {% if content is defined and content %}
                    {% if content.title is defined and content.title %}
                        {{ content.title }}
                    {% else %}
                        Untitled Content 
                    {% endif %}
                {% else %}
                    No Content Available
                {% endif %}
            </h2>
            <div class="content-meta">
                <span class="badge badge-type">
                    {% if content is defined and content %}
                        {% if content.type is defined and content.type %}
                            {{ content.type }}
                        {% elif content.content_type is defined and content.content_type %}
                            {{ content.content_type }}
                        {% else %}
                            Unknown Type
                        {% endif %}
                    {% else %}
                        Unknown
                    {% endif %}
                </span>
                <span class="content-date">
                    {% if content is defined and content and content.created_at is defined %}
                        {{ format_date(content.created_at) }}
                    {% else %}
                        Unknown Date
                    {% endif %}
                </span>
            </div>
        </div>
        
        <div class="card-body">
            <div class="content-section">
                <h3>Summary</h3>
                <p>
                    {% if content is defined and content and content.summary is defined and content.summary %}
                        {{ content.summary }}
                    {% else %}
                        No summary available for this content.
                    {% endif %}
                </p>
            </div>
            
            <div class="content-section">
                <h3>Source</h3>
                {% if content is defined and content and content.source is defined and content.source %}
                    {% if (content.type is defined and content.type == 'url') or (content.content_type is defined and content.content_type == 'url') %}
                        <a href="{{ content.source }}" target="_blank" class="source-link">{{ content.source }}</a>
                    {% else %}
                        <p>{{ content.source }}</p>
                    {% endif %}
                {% else %}
                    <p>Source not available</p>
                {% endif %}
            </div>
            
            <div class="content-section">
                <h3>Content</h3>
                <div class="content-text">
                    {% if content is defined and content and content.content is defined and content.content %}
                        {{ content.content | safe }}
                    {% else %}
                        <p>No content is available for display. This could be because:</p>
                        <ul>
                            <li>The content hasn't been processed yet</li>
                            <li>The content ID is invalid</li>
                            <li>There was an error retrieving the content</li>
                        </ul>
                    {% endif %}
                </div>
            </div>
            
            {% if content is defined and content and content.entities is defined and content.entities %}
            <div class="content-section">
                <h3>Entities</h3>
                <div class="entity-list">
                    {% for entity in content.entities %}
                    <div class="entity-item">
                        <span class="entity-name">{{ entity.name if entity.name is defined else entity }}</span>
                        <span class="entity-type">{{ entity.type if entity.type is defined else "Entity" }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            {% if content is defined and content and content.tags is defined and content.tags %}
            <div class="content-section">
                <h3>Tags</h3>
                <div class="tag-list">
                    {% for tag in content.tags %}
                    <span class="tag">{{ tag }}</span>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
        
        <div class="card-footer">
            <div class="content-actions">
                <a href="#" class="btn btn-secondary" onclick="window.print()">Print</a>
                <a href="#" class="btn btn-secondary">Export</a>
                <a href="#" class="btn btn-primary">Generate Digest</a>
            </div>
        </div>
    </div>
    
    <div class="card related-content">
        <h3 class="card-title">Related Content</h3>
        <div class="card-body">
            <p class="empty-state">No related content available.</p>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_css %}
<style>
    .content-detail {
        display: grid;
        grid-template-columns: 3fr 1fr;
        gap: 20px;
    }
    
    .content-title {
        font-size: 1.8rem;
        margin-bottom: 10px;
    }
    
    .content-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .content-section {
        margin-bottom: 30px;
    }
    
    .content-section h3 {
        border-bottom: 1px solid #eee;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    
    .content-text {
        line-height: 1.6;
        max-height: 500px;
        overflow-y: auto;
        padding: 15px;
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    
    .entity-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .entity-item {
        background-color: #f0f5ff;
        padding: 5px 10px;
        border-radius: 4px;
        display: flex;
        align-items: center;
    }
    
    .entity-type {
        font-size: 0.8em;
        color: #666;
        margin-left: 5px;
        border-left: 1px solid #ccc;
        padding-left: 5px;
    }
    
    .source-link {
        word-break: break-all;
    }
    
    @media (max-width: 768px) {
        .content-detail {
            grid-template-columns: 1fr;
        }
    }
</style>
{% endblock %}"""
    
    view_content = """{% extends "base.html" %}

{% block title %}View Content - BlueAbel AIOS{% endblock %}

{% block content %}
<div class="page-header">
    <h1>Content Repository</h1>
    <p class="page-description">Browse and manage your content items.</p>
</div>

<div class="filter-controls">
    <form method="GET" action="{{ url_for('view_content') }}" class="filter-form">
        <div class="form-row">
            <div class="form-col">
                <label for="content-type">Type:</label>
                <select id="content-type" name="type" onchange="this.form.submit()">
                    <option value="">All Types</option>
                    <option value="url" {% if selected_type == 'url' %}selected{% endif %}>URL</option>
                    <option value="pdf" {% if selected_type == 'pdf' %}selected{% endif %}>PDF</option>
                    <option value="text" {% if selected_type == 'text' %}selected{% endif %}>Text</option>
                    <option value="email" {% if selected_type == 'email' %}selected{% endif %}>Email</option>
                </select>
            </div>
            <div class="form-col">
                <label for="sort-by">Sort By:</label>
                <select id="sort-by" name="sort" onchange="this.form.submit()">
                    <option value="date_desc" {% if selected_sort == 'date_desc' %}selected{% endif %}>Newest First</option>
                    <option value="date_asc" {% if selected_sort == 'date_asc' %}selected{% endif %}>Oldest First</option>
                    <option value="title" {% if selected_sort == 'title' %}selected{% endif %}>Title</option>
                </select>
            </div>
        </div>
    </form>
</div>

<div class="content-list">
    {% if content_items is defined and content_items|length > 0 %}
        {% for item in content_items %}
        <div class="content-card">
            <div class="content-card-main">
                <h3 class="content-card-title">
                    {% if item is defined and item.title is defined and item.title %}
                        {{ item.title }}
                    {% else %}
                        Untitled Content
                    {% endif %}
                </h3>
                <div class="content-card-meta">
                    <span class="badge badge-type">
                        {% if item is defined %}
                            {% if item.type is defined and item.type %}
                                {{ item.type }}
                            {% elif item.content_type is defined and item.content_type %}
                                {{ item.content_type }}
                            {% else %}
                                Unknown
                            {% endif %}
                        {% else %}
                            Unknown
                        {% endif %}
                    </span>
                    <span class="content-card-date">
                        {% if item is defined and item.created_at is defined %}
                            {{ format_date(item.created_at) }}
                        {% else %}
                            Unknown Date
                        {% endif %}
                    </span>
                </div>
                <p class="content-card-summary">
                    {% if item is defined and item.summary is defined and item.summary %}
                        {{ item.summary }}
                    {% else %}
                        No summary available
                    {% endif %}
                </p>
                <div class="content-card-tags">
                    {% if item is defined and item.tags is defined and item.tags %}
                        {% for tag in item.tags %}
                        <span class="tag">{{ tag }}</span>
                        {% endfor %}
                    {% else %}
                        <span class="tag">no tags</span>
                    {% endif %}
                </div>
            </div>
            <div class="content-card-actions">
                <a href="{{ url_for('content_detail', content_id=item.id) }}" class="btn">View Details</a>
            </div>
        </div>
        {% endfor %}
    {% else %}
    <div class="empty-state">
        <p>No content items found. Try adjusting your filters or adding new content.</p>
        <a href="{{ url_for('process_content') }}" class="btn btn-primary">Process New Content</a>
    </div>
    {% endif %}
</div>

{% if pagination is defined and pagination.total_pages > 1 %}
<div class="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('view_content', type=selected_type, sort=selected_sort, page=pagination.prev_page) }}" class="pagination-item">&laquo; Previous</a>
    {% else %}
    <span class="pagination-item disabled">&laquo; Previous</span>
    {% endif %}
    
    {% for p in pagination.pages %}
    {% if p == pagination.current_page %}
    <span class="pagination-item active">{{ p }}</span>
    {% else %}
    <a href="{{ url_for('view_content', type=selected_type, sort=selected_sort, page=p) }}" class="pagination-item">{{ p }}</a>
    {% endif %}
    {% endfor %}
    
    {% if pagination.has_next %}
    <a href="{{ url_for('view_content', type=selected_type, sort=selected_sort, page=pagination.next_page) }}" class="pagination-item">Next &raquo;</a>
    {% else %}
    <span class="pagination-item disabled">Next &raquo;</span>
    {% endif %}
</div>
{% endif %}
{% endblock %}"""
    
    # Write the fixed templates
    with open(templates_dir / "content_detail.html", "w") as f:
        f.write(content_detail)
    
    with open(templates_dir / "view_content.html", "w") as f:
        f.write(view_content)
    
    print("Fixed templates have been created.")
    print("The following templates were replaced with robust versions:")
    print("- content_detail.html")
    print("- view_content.html")
    print("\nOriginals were backed up to the 'backup_templates' directory.")

def restart_server():
    """Restart the Flask server to apply changes"""
    import subprocess
    import signal
    import time
    
    # Kill existing Flask processes
    try:
        ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
        for line in ps_output.splitlines():
            if 'flask_ui/app.py' in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        os.kill(pid, signal.SIGTERM)
                        print(f"Terminated Flask process with PID {pid}")
                    except:
                        pass
        
        # Wait a moment for processes to terminate
        time.sleep(2)
    except Exception as e:
        print(f"Error killing Flask processes: {str(e)}")
    
    # Start a new Flask server on port 8000
    script_path = project_root / "restart_server.py"
    with open(script_path, "w") as f:
        f.write("""#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Set up Flask app path
app_path = Path(__file__).parent / "flask_ui" / "app.py"

# Start the server
os.environ["FLASK_APP"] = str(app_path)
print(f"Starting server with app: {app_path}")
os.system("python3 -m flask run --host=127.0.0.1 --port=8000")
""")
    
    os.chmod(script_path, 0o755)
    
    # Start the server in the background
    log_path = project_root / "fixed_server.log"
    subprocess.Popen(
        ["python3", str(script_path)],
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        close_fds=True
    )
    
    print(f"Started new server on port 8000, logs at {log_path}")
    print("Wait a few seconds for the server to start...")

if __name__ == "__main__":
    print("Quick fix for BlueAbel AIOS content display")
    
    # Create fixed templates
    create_fixed_templates()
    
    # Restart the server
    restart_server()
    
    print("\nFix complete! Please visit http://127.0.0.1:8000 to see the fixed version.")
    print("The content listings and detail pages should now display correctly.")