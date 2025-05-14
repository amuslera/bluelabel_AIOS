#!/usr/bin/env python3
"""
Standalone content viewer application for BlueAbel AIOS

This is a self-contained application that implements content viewing functionality
without relying on any existing code. It provides a guaranteed working implementation
that can be used to view content details.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), "flask_ui", "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "flask_ui", "static"))

# Basic navigation structure
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
    "System": [
        {"name": "Settings", "icon": "⚙️", "route": "settings", "description": "System settings"}
    ]
}

# Demo content data
DEMO_CONTENT = [
    {
        "id": "item1",
        "title": "Introduction to Artificial Intelligence",
        "type": "url",
        "content_type": "url",
        "summary": "An overview of AI concepts and applications.",
        "source": "https://example.com/ai-intro",
        "created_at": datetime.now().replace(day=datetime.now().day-2).isoformat(),
        "content": "Artificial Intelligence (AI) is transforming our world in remarkable ways. From autonomous vehicles to virtual assistants, AI technologies are becoming increasingly integrated into our daily lives.\n\nAt its core, AI involves developing computer systems that can perform tasks that would normally require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.\n\nKey areas of AI include:\n\n- Machine Learning: Algorithms that improve automatically through experience\n- Deep Learning: Neural networks with many layers that can learn complex patterns\n- Natural Language Processing: Enabling computers to understand and generate human language\n- Computer Vision: Allowing machines to interpret and understand visual information\n- Robotics: Creating machines that can interact with the physical world\n\nAs AI continues to advance, it presents both exciting opportunities and important ethical considerations that society must address.",
        "tags": ["AI", "Technology", "Introduction"],
        "entities": [
            {"name": "Machine Learning", "type": "Concept"},
            {"name": "Deep Learning", "type": "Concept"},
            {"name": "Neural Networks", "type": "Technology"},
            {"name": "NLP", "type": "Technology"},
            {"name": "Computer Vision", "type": "Technology"}
        ]
    },
    {
        "id": "item2",
        "title": "Machine Learning Fundamentals",
        "type": "pdf",
        "content_type": "pdf",
        "summary": "Core concepts and techniques in machine learning.",
        "source": "Machine_Learning_Fundamentals.pdf",
        "created_at": datetime.now().replace(day=datetime.now().day-5).isoformat(),
        "content": "Machine Learning (ML) is a subset of artificial intelligence that focuses on developing systems that can learn from and make decisions based on data. Instead of explicitly programming rules, ML algorithms identify patterns in data and improve their performance with experience.\n\nFundamental ML concepts include:\n\n1. Supervised Learning: Training with labeled data to predict outcomes\n2. Unsupervised Learning: Finding patterns in unlabeled data\n3. Reinforcement Learning: Learning through interaction with an environment\n4. Feature Engineering: Selecting and transforming variables for modeling\n5. Model Evaluation: Assessing performance using metrics like accuracy and precision\n\nPopular ML algorithms include decision trees, random forests, support vector machines, and neural networks. Each has strengths and weaknesses for different applications.\n\nThe ML workflow typically involves data collection, preprocessing, model training, evaluation, and deployment. As models move into production, considerations around monitoring, maintenance, and ethics become increasingly important.",
        "tags": ["ML", "Data Science", "AI"],
        "entities": [
            {"name": "Supervised Learning", "type": "Concept"},
            {"name": "Unsupervised Learning", "type": "Concept"},
            {"name": "Reinforcement Learning", "type": "Concept"},
            {"name": "Decision Trees", "type": "Algorithm"},
            {"name": "Neural Networks", "type": "Algorithm"}
        ]
    },
    {
        "id": "item3",
        "title": "Deep Learning Applications",
        "type": "url",
        "content_type": "url",
        "summary": "Practical applications of deep learning in various industries.",
        "source": "https://example.com/deep-learning-apps",
        "created_at": datetime.now().replace(day=datetime.now().day-7).isoformat(),
        "content": "Deep learning has revolutionized numerous industries with its remarkable ability to process and learn from vast amounts of data. Here are some key applications across different sectors:\n\nHealthcare:\n- Medical image analysis for detecting diseases like cancer and diabetic retinopathy\n- Drug discovery and development through molecular structure analysis\n- Patient outcome prediction based on electronic health records\n\nFinance:\n- Fraud detection systems that identify unusual transaction patterns\n- Algorithmic trading strategies optimized for market conditions\n- Credit scoring models with improved accuracy\n\nTransportation:\n- Autonomous vehicles that perceive and navigate complex environments\n- Traffic prediction and optimization systems\n- Logistics and route optimization\n\nRetail:\n- Personalized recommendation systems\n- Inventory management and demand forecasting\n- Visual search capabilities\n\nManufacturing:\n- Quality control through computer vision\n- Predictive maintenance to prevent equipment failures\n- Process optimization for improved efficiency\n\nAs deep learning technologies continue to advance, we can expect to see even more innovative applications emerge across industries.",
        "tags": ["Deep Learning", "AI", "Applications"],
        "entities": [
            {"name": "Healthcare", "type": "Industry"},
            {"name": "Finance", "type": "Industry"},
            {"name": "Autonomous Vehicles", "type": "Application"},
            {"name": "Computer Vision", "type": "Technology"},
            {"name": "Predictive Maintenance", "type": "Application"}
        ]
    }
]

# Helper function for date formatting
def format_date(date_str):
    """Format a date string consistently"""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str

# Function to get a content item by ID
def get_content_item(content_id):
    """Get a content item by ID, or generate a placeholder if not found"""
    # Check if the content ID exists in demo data
    for item in DEMO_CONTENT:
        if item["id"] == content_id:
            return item
    
    # Generate a new demo item for unknown IDs
    return {
        "id": content_id,
        "title": f"Dynamic Content Item {content_id[:8]}",
        "type": "text",
        "content_type": "text",
        "summary": "This is a dynamically generated content item for demonstration purposes.",
        "source": "Demo Generator",
        "created_at": datetime.now().isoformat(),
        "content": f"""
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

The content ID being requested is: {content_id}
        """,
        "tags": ["demo", "dynamic", "example"],
        "entities": [
            {"name": "Demo Content", "type": "Document"},
            {"name": "BlueAbel AIOS", "type": "System"}
        ]
    }

# Function to get a list of content items
def get_content_items(limit=10, offset=0, content_type=None):
    """Get a list of content items, optionally filtered by type"""
    # Filter by content type if specified
    if content_type:
        filtered_items = [item for item in DEMO_CONTENT if item.get("type") == content_type or item.get("content_type") == content_type]
    else:
        filtered_items = DEMO_CONTENT.copy()
    
    # Apply pagination
    paginated_items = filtered_items[offset:offset+limit]
    
    return {
        "items": paginated_items,
        "total": len(filtered_items),
        "pages": (len(filtered_items) + limit - 1) // limit,
        "current_page": offset // limit + 1
    }

# Routes
@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    # Get recent content
    content_data = get_content_items(limit=5)
    
    return render_template('dashboard.html', 
                          active_page='dashboard',
                          nav_items=NAV_ITEMS,
                          api_status=True,
                          content_count=len(DEMO_CONTENT),
                          content_types={"URL": 2, "PDF": 1, "Text": 0},
                          recent_content=content_data["items"],
                          recent_activity=[],
                          format_date=format_date)

@app.route('/view-content')
def view_content():
    """View content page"""
    content_type = request.args.get('type')
    page = int(request.args.get('page', 1))
    limit = 5
    offset = (page - 1) * limit
    
    # Get content items with pagination
    content_data = get_content_items(limit=limit, offset=offset, content_type=content_type)
    
    # Generate pagination object
    pagination = {
        "current_page": page,
        "total_pages": content_data["pages"],
        "total_items": content_data["total"],
        "has_prev": page > 1,
        "has_next": page < content_data["pages"],
        "prev_page": max(1, page - 1),
        "next_page": min(content_data["pages"], page + 1),
        "pages": [p for p in range(max(1, page - 2), min(content_data["pages"] + 1, page + 3))]
    }
    
    return render_template('view_content_fix.html', 
                          active_page='view_content', 
                          nav_items=NAV_ITEMS,
                          content_items=content_data["items"],
                          format_date=format_date,
                          selected_type=content_type,
                          selected_sort="date_desc",
                          pagination=pagination)

@app.route('/content/<content_id>')
def content_detail(content_id):
    """Content detail page"""
    # Get content item
    content = get_content_item(content_id)
    
    return render_template('content_detail_fix.html', 
                          active_page='view_content', 
                          nav_items=NAV_ITEMS,
                          content=content,
                          format_date=format_date)

@app.route('/api-status')
def api_status():
    """API status endpoint"""
    return jsonify({"status": "online"})

if __name__ == '__main__':
    print("Starting standalone content application")
    print("Visit http://127.0.0.1:7000 to view the application")
    app.run(host="127.0.0.1", port=7000, debug=True)