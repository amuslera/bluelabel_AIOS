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

def check_endpoint_status(endpoint, method="GET", data=None, timeout=5):
    """Check if a specific API endpoint is working"""
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=timeout)
        elif method == "POST":
            response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data, timeout=timeout)
        
        print(f"[DEBUG] Endpoint {endpoint} status: {response.status_code}")
        if response.status_code == 200:
            return {"status": "ok", "details": response.json()}
        else:
            return {"status": "error", "code": response.status_code, "details": response.text[:500]}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "details": f"Request timed out after {timeout} seconds"}
    except requests.exceptions.ConnectionError:
        return {"status": "connection_error", "details": "Could not connect to the API"}
    except Exception as e:
        return {"status": "exception", "details": str(e)}

def get_content_items(limit=10, content_type=None, sort_by="date_desc", page=1, query=None):
    """Get content items from the API"""
    try:
        # Prepare parameters for API call
        params = {
            "limit": limit,
            "page": page
        }
        
        if content_type:
            params["type"] = content_type
            
        if sort_by:
            params["sort"] = sort_by
            
        if query:
            params["query"] = query
        
        # Log the API call for debugging
        print(f"[DEBUG] Fetching content items: {API_BASE_URL}/knowledge/list with params {params}")
        
        # Call the API to get content items
        response = requests.get(
            f"{API_BASE_URL}/knowledge/list", 
            params=params,
            timeout=5  # 5 second timeout to prevent UI hanging
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                items = result.get("results", [])
                
                # Additional metadata for pagination if available
                total_count = result.get("total", len(items))
                total_pages = result.get("pages", 1)
                
                print(f"[DEBUG] Fetched {len(items)} items (total: {total_count} in {total_pages} pages)")
                
                return {
                    "items": items, 
                    "total": total_count,
                    "pages": total_pages,
                    "current_page": page
                }
            else:
                print(f"[DEBUG] API returned non-success status: {result}")
                # Return empty result if API call fails
                return {
                    "items": [],
                    "total": 0,
                    "pages": 1,
                    "current_page": page,
                    "error": f"API returned error: {result.get('message', 'Unknown error')}"
                }
        else:
            print(f"[DEBUG] API returned status code: {response.status_code}")
            # Return empty result if API returns error status
            return {
                "items": [],
                "total": 0,
                "pages": 1,
                "current_page": page,
                "error": f"API returned status code: {response.status_code}"
            }
    
    except Exception as e:
        print(f"[ERROR] Error fetching content items: {str(e)}")
        # Return empty list if API call fails
        return {
            "items": [],
            "total": 0,
            "pages": 1,
            "current_page": page,
            "error": str(e)
        }

def get_content_item(content_id):
    """Get a specific content item from the API"""
    print(f"[DEBUG] get_content_item called with ID: {content_id}")
    
    try:
        # Call the API to get content item details
        response = requests.get(
            f"{API_BASE_URL}/knowledge/{content_id}",
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                item = result.get("data", {})
                print(f"[DEBUG] Successfully fetched content item: {item.get('title', 'Unknown')}")
                
                # Ensure required fields exist
                required_fields = {
                    "id": content_id,
                    "title": "Untitled Content",
                    "summary": "No summary available",
                    "type": "unknown",
                    "content_type": "unknown",
                    "source": "Unknown source",
                    "created_at": datetime.now().isoformat(),
                    "content": "No content available",
                    "tags": [],
                    "entities": []
                }
                
                # Update with actual values from response
                for key, default_value in required_fields.items():
                    if key not in item or item[key] is None:
                        item[key] = default_value
                
                # Ensure type/content_type consistency
                if "type" in item and "content_type" not in item:
                    item["content_type"] = item["type"]
                elif "content_type" in item and "type" not in item:
                    item["type"] = item["content_type"]
                
                return item
            else:
                print(f"[DEBUG] API returned non-success status: {result}")
                return None
        else:
            print(f"[DEBUG] API returned status code: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"[ERROR] Error fetching content item: {str(e)}")
        return None

def get_components(component_type=None):
    """Get MCP components from the API"""
    try:
            "type": "url",
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
        "2": {
            "id": "2",
            "title": "Machine Learning Fundamentals",
            "summary": "Core concepts and techniques in machine learning.",
            "type": "pdf",
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
        "3": {
            "id": "3",
            "title": "Deep Learning Applications",
            "summary": "Practical applications of deep learning in various industries.",
            "type": "url",
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
        },
        "4": {
            "id": "4",
            "title": "Natural Language Processing",
            "summary": "Introduction to NLP techniques and models.",
            "type": "text",
            "source": "Manual Entry",
            "created_at": datetime.now().replace(day=datetime.now().day-10).isoformat(),
            "content": "Natural Language Processing (NLP) combines linguistics, computer science, and artificial intelligence to enable computers to understand, interpret, and generate human language. This field has seen remarkable advances in recent years, particularly with the development of large language models.\n\nCore NLP Tasks:\n\n- Text Classification: Categorizing text into predefined groups (e.g., spam detection, sentiment analysis)\n- Named Entity Recognition: Identifying entities like people, organizations, and locations in text\n- Part-of-Speech Tagging: Marking words with their grammatical categories\n- Dependency Parsing: Analyzing the grammatical structure of sentences\n- Machine Translation: Converting text from one language to another\n- Question Answering: Providing answers to natural language questions\n- Summarization: Creating concise versions of longer texts\n- Text Generation: Producing human-like text based on prompts or conditions\n\nRecent advances in transformer-based models like BERT, GPT, and T5 have significantly improved performance across these tasks. These models use attention mechanisms to understand context and relationships between words, allowing for more nuanced language understanding.\n\nApplications of NLP include virtual assistants, chatbots, content analysis, automated reporting, and language translation services. As models continue to grow in size and capability, they increasingly approach human-level performance on many language tasks.",
            "tags": ["NLP", "AI", "Language"],
            "entities": [
                {"name": "BERT", "type": "Model"},
                {"name": "GPT", "type": "Model"},
                {"name": "Text Classification", "type": "Task"},
                {"name": "Machine Translation", "type": "Task"},
                {"name": "Transformers", "type": "Architecture"}
            ]
        },
        "5": {
            "id": "5",
            "title": "Computer Vision Basics",
            "summary": "Fundamentals of computer vision and image processing.",
            "type": "pdf",
            "source": "Computer_Vision_Basics.pdf",
            "created_at": datetime.now().replace(day=datetime.now().day-12).isoformat(),
            "content": "Computer Vision (CV) is the field of computer science that enables machines to derive meaningful information from digital images and videos. It aims to automate tasks that the human visual system can do.\n\nFundamental concepts in Computer Vision include:\n\n1. Image Formation and Representation: How images are captured and stored digitally\n2. Image Preprocessing: Techniques like noise reduction, contrast enhancement, and normalization\n3. Feature Detection and Extraction: Identifying key points and patterns in images\n4. Image Segmentation: Dividing images into meaningful regions\n5. Object Detection and Recognition: Identifying and classifying objects within images\n6. Motion Analysis: Tracking movement across video frames\n7. 3D Vision: Reconstructing three-dimensional information from 2D images\n\nModern computer vision relies heavily on deep learning, particularly Convolutional Neural Networks (CNNs) that are specifically designed to process pixel data. Architectures like ResNet, YOLO, and U-Net have achieved remarkable results in various CV tasks.\n\nApplications of computer vision are vast and include facial recognition, autonomous vehicles, medical image analysis, augmented reality, industrial inspection, and surveillance systems. As algorithms improve and computing power increases, the capabilities and applications of computer vision continue to expand rapidly.",
            "tags": ["Computer Vision", "AI", "Image Processing"],
            "entities": [
                {"name": "CNN", "type": "Architecture"},
                {"name": "ResNet", "type": "Model"},
                {"name": "YOLO", "type": "Model"},
                {"name": "Object Detection", "type": "Task"},
                {"name": "Image Segmentation", "type": "Task"}
            ]
        }
    }
    
    try:
        # Log the API call for debugging
        print(f"[DEBUG] Fetching content item with ID: {content_id}")
        
        # Call the API to get content item details
        response = requests.get(
            f"{API_BASE_URL}/knowledge/item/{content_id}",
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                item = result.get("item", {})
                print(f"[DEBUG] Successfully fetched content item: {item.get('title', 'Unknown')}")
                return item
            else:
                print(f"[DEBUG] API returned non-success status: {result}")
        else:
            print(f"[DEBUG] API returned status code: {response.status_code}")
    
    except Exception as e:
        print(f"[ERROR] Error fetching content item: {str(e)}")
    
    # Return demo data if API call fails or item not found
    if content_id in demo_data:
        print(f"[DEBUG] Returning demo data for content ID: {content_id}")
        demo_item = demo_data[content_id]
    else:
        # If the content_id doesn't match our demo data, create enriched demo content
        print(f"[DEBUG] Content ID {content_id} not found, creating dynamic demo item")
        
        # Extract a readable ID segment from UUID if possible
        short_id = content_id
        if '-' in content_id:
            short_id = content_id.split('-')[0][:8]
        
        # Select a demo item as a template (rotating based on ID)
        demo_keys = list(demo_data.keys())
        template_index = hash(content_id) % len(demo_keys)
        template_id = demo_keys[template_index]
        demo_item = demo_data[template_id].copy()
        
        # Customize the demo item
        demo_item["id"] = content_id
        demo_item["title"] = f"Dynamic Content {short_id.upper()}"
        demo_item["summary"] = f"Auto-generated content for ID: {content_id}"
        
        # Ensure content field is well-formed
        if "content" not in demo_item or not demo_item["content"]:
            demo_item["content"] = f"This is dynamically generated content for ID: {content_id}\n\nThe actual content could not be retrieved from the API, so this placeholder is shown instead.\n\nIn a production environment, you would see the actual content here."
    
    # Ensure all necessary fields exist
    required_fields = {
        "type": "unknown",
        "source": "Generated Content",
        "created_at": datetime.now().isoformat(),
        "tags": ["demo", "placeholder"],
        "content": "No content available."
    }
    
    for field, default_value in required_fields.items():
        if field not in demo_item or demo_item[field] is None:
            demo_item[field] = default_value
    

    # Perform a final sanitation of data to ensure it's properly formatted
    sanitized_item = {}
    for key, value in demo_item.items():
        # Convert any method references to strings
        if callable(value):
            sanitized_item[key] = str(value)
        # Convert any complex objects to strings
        elif not isinstance(value, (str, int, float, bool, list, dict, type(None))):
            sanitized_item[key] = str(value)
        # Ensure lists contain only simple types
        elif isinstance(value, list):
            sanitized_list = []
            for item in value:
                if isinstance(item, (str, int, float, bool)):
                    sanitized_list.append(item)
                elif isinstance(item, dict):
                    # For dictionaries in lists, sanitize them recursively
                    sanitized_dict = {}
                    for k, v in item.items():
                        if callable(v):
                            sanitized_dict[k] = str(v)
                        elif not isinstance(v, (str, int, float, bool, list, dict, type(None))):
                            sanitized_dict[k] = str(v)
                        else:
                            sanitized_dict[k] = v
                    sanitized_list.append(sanitized_dict)
                else:
                    sanitized_list.append(str(item))
            sanitized_item[key] = sanitized_list
        # For direct dictionaries, keep as is (they'll be sanitized at the end if needed)
        elif isinstance(value, dict):
            sanitized_item[key] = value
        # Keep other simple types as is
        else:
            sanitized_item[key] = value
    
    # Ensure required fields exist and have the right types
    required_fields = {
        "id": str(demo_item.get("id", "unknown")),
        "title": str(demo_item.get("title", "Untitled Content")),
        "summary": str(demo_item.get("summary", "No summary available")),
        "type": str(demo_item.get("type", demo_item.get("content_type", "unknown"))),
        "content_type": str(demo_item.get("content_type", demo_item.get("type", "unknown"))),
        "source": str(demo_item.get("source", "Unknown source")),
        "created_at": str(demo_item.get("created_at", datetime.now().isoformat())),
        "content": str(demo_item.get("content", "No content available")),
        "tags": demo_item.get("tags", []) if isinstance(demo_item.get("tags"), list) else ["untagged"],
        "entities": demo_item.get("entities", []) if isinstance(demo_item.get("entities"), list) else []
    }
    
    # Update sanitized item with required fields
    for key, value in required_fields.items():
        sanitized_item[key] = value
    
    print(f"[DEBUG] Returning sanitized content item with title: {sanitized_item['title']}")
    return sanitized_item

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
    content_data = get_content_items(limit=5)
    recent_content = content_data.get("items", [])
    
    # Get content counts from actual data
    content_count = content_data.get("total", len(recent_content))
    
    # Generate content types from the actual content items
    content_types = {}
    if content_count > 0:
        # Get all content to build accurate type counts
        try:
            all_content_response = requests.get(
                f"{API_BASE_URL}/knowledge/list", 
                params={"limit": 1000},
                timeout=5
            )
            if all_content_response.status_code == 200:
                all_result = all_content_response.json()
                if all_result.get("status") == "success":
                    all_items = all_result.get("results", [])
                    for item in all_items:
                        item_type = item.get("type", item.get("content_type", "Unknown"))
                        content_types[item_type] = content_types.get(item_type, 0) + 1
                else:
                    # Fallback to recent content for type counts
                    for item in recent_content:
                        item_type = item.get("type", item.get("content_type", "Unknown"))
                        content_types[item_type] = content_types.get(item_type, 0) + 1
            else:
                # Fallback to recent content
                for item in recent_content:
                    item_type = item.get("type", item.get("content_type", "Unknown"))
                    content_types[item_type] = content_types.get(item_type, 0) + 1
        except Exception as e:
            print(f"Error fetching all content for stats: {str(e)}")
            # Fallback to recent content
            for item in recent_content:
                item_type = item.get("type", item.get("content_type", "Unknown"))
                content_types[item_type] = content_types.get(item_type, 0) + 1
    
    # If content_types is empty, provide some defaults
    if not content_types:
        content_types = {"URL": 2, "PDF": 1, "Text": 1, "Email": 1}
    
    # Get recent activity - build from actual recent content
    recent_activity = []
    
    # Convert recent content to activity entries
    for idx, item in enumerate(recent_content[:5]):  # Show last 5 items as activities
        created_at = item.get("created_at", "")
        item_type = item.get("type", item.get("content_type", "Unknown"))
        title = item.get("title", "Untitled")
        
        # Parse the datetime and format it
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            # Check if it's today
            if dt.date() == datetime.now().date():
                time_str = dt.strftime("%-I:%M %p")  # e.g., "10:15 AM"
            elif dt.date() == (datetime.now() - timedelta(days=1)).date():
                time_str = "Yesterday"
            else:
                time_str = dt.strftime("%Y-%m-%d")
        except:
            time_str = "Unknown"
        
        activity = {
            "time": time_str,
            "action": f"Content Processing - {item_type}",
            "status": "Completed",
            "details": title[:50] + "..." if len(title) > 50 else title
        }
        recent_activity.append(activity)
    
    # If no recent activity, show a message
    if not recent_activity:
        recent_activity = [{
            "time": "Now",
            "action": "System Status",
            "status": "Active",
            "details": "No recent activity to display"
        }]
    
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
        # Log request details
        print(f"[DEBUG] Process content POST request received with content type: {request.content_type}")
        print(f"[DEBUG] Request form data: {request.form}")
        
        content_type = request.form.get('content_type')
        print(f"[DEBUG] Form content_type: {content_type}")
        
        # AJAX response flag - used for the progress indicator feature
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                 'text/html' not in request.headers.get('Accept', '')
        
        result = {
            "status": "error",
            "message": "Unknown error occurred"
        }
        
        if content_type == 'url':
            url = request.form.get('url')
            create_digest = 'create_digest' in request.form
            model = request.form.get('model', 'Auto')
            
            print(f"[DEBUG] Processing URL: {url}, create_digest: {create_digest}, model: {model}")
            
            try:
                # Call the API to process the URL with a timeout
                response = requests.post(
                    f"{API_BASE_URL}/agents/contentmind/process", 
                    json={
                        "content_type": "url", 
                        "content": url, 
                        "metadata": {
                            "create_digest": create_digest, 
                            "model": model
                        }
                    },
                    timeout=30  # 30 second timeout
                )
                
                print(f"[DEBUG] API response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        flash(f"Successfully processed URL: {url}", "success")
                        result["message"] = f"Successfully processed URL: {url}"
                    else:
                        flash(f"Error processing URL: {result.get('message', 'Unknown error')}", "error")
                else:
                    error_msg = f"Error processing URL: HTTP {response.status_code}"
                    flash(error_msg, "error")
                    print(f"[ERROR] API response: {response.text}")
                    result["message"] = error_msg
            except requests.exceptions.Timeout:
                error_msg = "Request timed out. The server took too long to process your request."
                flash(error_msg, "error")
                print("[ERROR] API request timed out after 30 seconds")
                result["message"] = error_msg
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error. Please check if the API server is running."
                flash(error_msg, "error")
                print("[ERROR] API connection error - server may be down")
                result["message"] = error_msg
            except Exception as e:
                error_msg = f"Error processing URL: {str(e)}"
                flash(error_msg, "error")
                print(f"[ERROR] Exception while processing URL: {str(e)}")
                result["message"] = error_msg
            
        elif content_type == 'text':
            text = request.form.get('text')
            create_digest = 'create_digest' in request.form
            model = request.form.get('model', 'Auto')
            
            print(f"[DEBUG] Processing text of length {len(text) if text else 0}, create_digest: {create_digest}, model: {model}")
            
            try:
                # Call the API to process the text with a timeout
                response = requests.post(
                    f"{API_BASE_URL}/agents/contentmind/process", 
                    json={
                        "content_type": "text", 
                        "content": text, 
                        "metadata": {
                            "create_digest": create_digest, 
                            "model": model
                        }
                    },
                    timeout=30  # 30 second timeout
                )
                
                print(f"[DEBUG] API response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        success_msg = f"Successfully processed text content ({len(text)} characters)"
                        flash(success_msg, "success")
                        result["message"] = success_msg
                    else:
                        error_msg = f"Error processing text: {result.get('message', 'Unknown error')}"
                        flash(error_msg, "error")
                        result["message"] = error_msg
                else:
                    error_msg = f"Error processing text: HTTP {response.status_code}"
                    flash(error_msg, "error")
                    print(f"[ERROR] API response: {response.text}")
                    result["message"] = error_msg
            except requests.exceptions.Timeout:
                error_msg = "Request timed out. The server took too long to process your request."
                flash(error_msg, "error")
                print("[ERROR] API request timed out after 30 seconds")
                result["message"] = error_msg
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error. Please check if the API server is running."
                flash(error_msg, "error")
                print("[ERROR] API connection error - server may be down")
                result["message"] = error_msg
            except Exception as e:
                error_msg = f"Error processing text: {str(e)}"
                flash(error_msg, "error")
                print(f"[ERROR] Exception while processing text: {str(e)}")
                result["message"] = error_msg
            
        elif content_type == 'file':
            # Handle file upload
            file = request.files.get('file')
            file_type = request.form.get('file_type', 'pdf')
            summarize = 'summarize' in request.form
            
            if file:
                print(f"[DEBUG] File received: {file.filename}, {file.content_type}, file_type: {file_type}")
                
                try:
                    # Create a temporary file to store the uploaded content
                    import tempfile
                    import os
                    
                    # Create a temporary file with the correct extension
                    fd, temp_path = tempfile.mkstemp(suffix=f".{file_type}")
                    print(f"[DEBUG] Created temporary file: {temp_path}")
                    
                    try:
                        # Save the file
                        file.save(temp_path)
                        
                        # Read the file content (for API submission)
                        with open(temp_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Convert to base64 for API transmission
                        import base64
                        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
                        
                        # Call the API to process the file
                        response = requests.post(
                            f"{API_BASE_URL}/agents/contentmind/process", 
                            json={
                                "content_type": "file", 
                                "content": {
                                    "filename": file.filename,
                                    "file_type": file_type,
                                    "data": file_content_b64
                                },
                                "metadata": {
                                    "summarize": summarize
                                }
                            },
                            timeout=45  # 45 second timeout for file processing
                        )
                        
                        print(f"[DEBUG] API response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("status") == "success":
                                success_msg = f"Successfully processed file: {file.filename}"
                                flash(success_msg, "success")
                                result["message"] = success_msg
                            else:
                                error_msg = f"Error processing file: {result.get('message', 'Unknown error')}"
                                flash(error_msg, "error")
                                result["message"] = error_msg
                        else:
                            error_msg = f"Error processing file: HTTP {response.status_code}"
                            flash(error_msg, "error")
                            print(f"[ERROR] API response: {response.text}")
                            result["message"] = error_msg
                    
                    finally:
                        # Clean up the temporary file
                        os.close(fd)
                        os.unlink(temp_path)
                        print(f"[DEBUG] Removed temporary file: {temp_path}")
                
                except requests.exceptions.Timeout:
                    error_msg = "Request timed out. The server took too long to process your request."
                    flash(error_msg, "error")
                    print("[ERROR] API request timed out")
                    result["message"] = error_msg
                except requests.exceptions.ConnectionError:
                    error_msg = "Connection error. Please check if the API server is running."
                    flash(error_msg, "error")
                    print("[ERROR] API connection error - server may be down")
                    result["message"] = error_msg
                except Exception as e:
                    error_msg = f"Error processing file: {str(e)}"
                    flash(error_msg, "error")
                    print(f"[ERROR] Exception while processing file: {str(e)}")
                    result["message"] = error_msg
            else:
                error_msg = "No file received."
                print("[ERROR] No file received in the request")
                flash(error_msg, "error")
                result["message"] = error_msg
                
        elif content_type == 'email':
            # Handle email processing
            subject = request.form.get('subject')
            body = request.form.get('body')
            include_attachments = 'include_attachments' in request.form
            
            print(f"[DEBUG] Email processing - Subject: {subject}, Body length: {len(body) if body else 0}")
            
            try:
                # Call the API to process the email
                response = requests.post(
                    f"{API_BASE_URL}/agents/contentmind/process", 
                    json={
                        "content_type": "email", 
                        "content": {
                            "subject": subject,
                            "body": body
                        },
                        "metadata": {
                            "include_attachments": include_attachments
                        }
                    },
                    timeout=30  # 30 second timeout
                )
                
                print(f"[DEBUG] API response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        success_msg = f"Successfully processed email with subject: {subject}"
                        flash(success_msg, "success")
                        result["message"] = success_msg
                    else:
                        error_msg = f"Error processing email: {result.get('message', 'Unknown error')}"
                        flash(error_msg, "error")
                        result["message"] = error_msg
                else:
                    error_msg = f"Error processing email: HTTP {response.status_code}"
                    flash(error_msg, "error")
                    print(f"[ERROR] API response: {response.text}")
                    result["message"] = error_msg
            except requests.exceptions.Timeout:
                error_msg = "Request timed out. The server took too long to process your request."
                flash(error_msg, "error")
                print("[ERROR] API request timed out after 30 seconds")
                result["message"] = error_msg
            except requests.exceptions.ConnectionError:
                error_msg = "Connection error. Please check if the API server is running."
                flash(error_msg, "error")
                print("[ERROR] API connection error - server may be down")
                result["message"] = error_msg
            except Exception as e:
                error_msg = f"Error processing email: {str(e)}"
                flash(error_msg, "error")
                print(f"[ERROR] Exception while processing email: {str(e)}")
                result["message"] = error_msg
        
        else:
            error_msg = f"Unknown content type: {content_type}"
            print(f"[ERROR] {error_msg}")
            flash(error_msg, "error")
            result["message"] = error_msg
        
        # Return JSON response for AJAX requests
        if is_ajax:
            return jsonify(result)
        
        # Redirect to the same page for regular form submissions
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
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))  # Number of items per page
    
    # Get content items with pagination
    content_data = get_content_items(
        content_type=content_type, 
        sort_by=sort_by,
        page=page,
        limit=limit
    )
    
    # Extract items and pagination metadata
    content_items = content_data["items"]
    total_items = content_data["total"]
    total_pages = content_data["pages"]
    current_page = content_data["current_page"]
    
    # Generate pagination links
    pagination = {
        "current_page": current_page,
        "total_pages": total_pages,
        "total_items": total_items,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
        "prev_page": max(1, current_page - 1),
        "next_page": min(total_pages, current_page + 1),
        "pages": [p for p in range(max(1, current_page - 2), min(total_pages + 1, current_page + 3))]
    }
    
    return render_template('view_content.html', 
                          active_page='view_content', 
                          nav_items=NAV_ITEMS,
                          content_items=content_items,
                          format_date=format_date,
                          selected_type=content_type,
                          selected_sort=sort_by,
                          pagination=pagination)

@app.route('/content/<content_id>')
def content_detail(content_id):
    """Content detail page"""
    # Get content item
    content = get_content_item(content_id)
    
    # Force dictionary values to strings
    sanitized_content = {}
    for key, value in content.items():
        if isinstance(value, dict):
            sanitized_content[key] = str(value)
        elif isinstance(value, list):
            sanitized_content[key] = [str(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized_content[key] = value
    
    return render_template('content_detail.html', 
                          active_page='view_content', 
                          nav_items=NAV_ITEMS,
                          content=sanitized_content,
                          format_date=format_date)

@app.route('/debug/content/<content_id>')
def debug_content_item(content_id):
    """Debug content item"""
    # Get content item directly
    content = get_content_item(content_id)
    
    # Add helper filters for the debug template
    def type_filter(value):
        return str(type(value))
    
    def pprint_filter(value):
        import pprint
        return pprint.pformat(value)
    
    # Add these filters to the Jinja environment
    app.jinja_env.filters['type'] = type_filter
    app.jinja_env.filters['pprint'] = pprint_filter
    
    return render_template('debug_content.html',
                          content=content,
                          content_id=content_id)

@app.route('/search')
def search():
    """Search page"""
    query = request.args.get('q', '')
    content_type = request.args.get('type', '')
    in_title = 'in_title' in request.args
    in_content = 'in_content' in request.args
    in_tags = 'in_tags' in request.args
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    # If no specific search areas are selected, search in all areas
    if not any([in_title, in_content, in_tags]):
        in_title = in_content = in_tags = True
    
    if query:
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "page": page,
                "limit": limit,
                "in_title": in_title,
                "in_content": in_content,
                "in_tags": in_tags
            }
            
            if content_type:
                search_params["type"] = content_type
                
            print(f"[DEBUG] Searching with params: {search_params}")
            
            # Call the API to search content
            response = requests.get(
                f"{API_BASE_URL}/knowledge/search", 
                params=search_params,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    search_data = result
                    results = result.get("results", [])
                    total_items = result.get("total", len(results))
                    total_pages = result.get("pages", 1)
                else:
                    print(f"[DEBUG] Search API returned non-success status: {result}")
                    results = []
                    total_items = 0
                    total_pages = 1
            else:
                print(f"[DEBUG] Search API returned error status: {response.status_code}")
                results = []
                total_items = 0
                total_pages = 1
        except Exception as e:
            print(f"[ERROR] Error searching content: {str(e)}")
            
            # For demo purposes, use the content items function with query parameter
            search_data = get_content_items(query=query, content_type=content_type, page=page, limit=limit)
            results = search_data["items"]
            total_items = search_data["total"]
            total_pages = search_data["pages"]
            
            # Add relevance scores to demo results
            for item in results:
                # Calculate a fake relevance score based on how many times the query appears
                title_count = item["title"].lower().count(query.lower())
                summary_count = item["summary"].lower().count(query.lower())
                tag_count = sum(1 for tag in item["tags"] if query.lower() in tag.lower())
                
                # Weighted score
                relevance = min(0.95, (title_count * 0.5 + summary_count * 0.3 + tag_count * 0.2) / 5)
                item["relevance"] = relevance if relevance > 0 else 0.7
    else:
        results = []
        total_items = 0
        total_pages = 1
    
    # Generate pagination object
    pagination = {
        "current_page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": max(1, page - 1),
        "next_page": min(total_pages, page + 1),
        "pages": [p for p in range(max(1, page - 2), min(total_pages + 1, page + 3))]
    }
    
    return render_template('search.html', 
                          active_page='search', 
                          nav_items=NAV_ITEMS,
                          query=query,
                          results=results,
                          format_date=format_date,
                          pagination=pagination,
                          selected_type=content_type,
                          in_title=in_title,
                          in_content=in_content,
                          in_tags=in_tags)

@app.route('/digests', methods=['GET', 'POST'])
def digests():
    """Digests page"""
    # Handle POST request to create a new digest
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        model = request.form.get('model', 'Auto')
        
        # Selection mode and related parameters
        content_ids = request.form.getlist('content[]')
        selection_criteria = request.form.get('criteria')
        tags = request.form.get('tags', '')
        keywords = request.form.get('keywords', '')
        
        # Validate required fields
        if not title:
            flash("Digest title is required", "error")
            return redirect(url_for('digests'))
        
        # Prepare API request based on selection method
        digest_request = {
            "title": title,
            "description": description,
            "model": model,
        }
        
        if content_ids:  # Manual selection
            digest_request["content_ids"] = content_ids
        elif selection_criteria == 'recent':
            digest_request["selection_method"] = "recent"
            digest_request["days"] = 7
        elif selection_criteria == 'tag' and tags:
            digest_request["selection_method"] = "tag"
            digest_request["tags"] = [tag.strip() for tag in tags.split(',')]
        elif selection_criteria == 'keyword' and keywords:
            digest_request["selection_method"] = "keyword"
            digest_request["keywords"] = [kw.strip() for kw in keywords.split(',')]
        else:
            flash("Please select content for the digest", "error")
            return redirect(url_for('digests'))
        
        # Call API to create digest
        try:
            print(f"[DEBUG] Creating digest with: {digest_request}")
            
            response = requests.post(
                f"{API_BASE_URL}/agents/digest/create", 
                json=digest_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    flash(f"Successfully created digest: {title}", "success")
                else:
                    flash(f"Error creating digest: {result.get('message', 'Unknown error')}", "error")
            else:
                flash(f"Error creating digest: HTTP {response.status_code}", "error")
                print(f"[ERROR] API response: {response.text}")
        except Exception as e:
            flash(f"Error creating digest: {str(e)}", "error")
            print(f"[ERROR] Exception creating digest: {str(e)}")
        
        return redirect(url_for('digests'))
    
    # GET request - display digests page
    # Try to get digests from the API
    try:
        response = requests.get(f"{API_BASE_URL}/agents/digest/list", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                digest_list = result.get("digests", [])
                print(f"[DEBUG] Fetched {len(digest_list)} digests from API")
            else:
                print(f"[DEBUG] API returned non-success status: {result}")
                digest_list = []
        else:
            print(f"[DEBUG] API returned error status: {response.status_code}")
            digest_list = []
    except Exception as e:
        print(f"[ERROR] Error fetching digests: {str(e)}")
        # Provide demo data
        digest_list = [
            {
                "id": "1",
                "title": "Weekly AI Research Digest",
                "description": "Summary of key AI research papers and developments from the past week.",
                "created_at": datetime.now().replace(day=datetime.now().day-2).isoformat(),
                "document_count": 8,
                "created_by": "Digest Agent",
                "model": "GPT-4",
                "tags": ["AI", "Research", "Weekly"]
            },
            {
                "id": "2",
                "title": "ML Framework Comparison",
                "description": "A detailed comparison of popular machine learning frameworks and their performance.",
                "created_at": datetime.now().replace(day=datetime.now().day-5).isoformat(),
                "document_count": 5,
                "created_by": "Digest Agent",
                "model": "Claude 3",
                "tags": ["ML", "Frameworks", "Technical"]
            },
            {
                "id": "3",
                "title": "AI Ethics and Governance",
                "description": "Analysis of recent developments in AI ethics, regulation, and governance frameworks.",
                "created_at": datetime.now().replace(day=datetime.now().day-10).isoformat(),
                "document_count": 12,
                "created_by": "Digest Agent",
                "model": "GPT-4",
                "tags": ["Ethics", "Governance", "Regulation"]
            }
        ]
    
    # Get available content for the creation modal
    content_data = get_content_items(limit=20)
    content_for_digest = content_data.get("items", [])
    
    # Get available models
    try:
        response = requests.get(f"{API_BASE_URL}/model-router/available-models", timeout=3)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                available_models = result.get("models", ["Auto", "GPT-4", "Claude 3", "Llama 3"])
            else:
                available_models = ["Auto", "GPT-4", "Claude 3", "Llama 3"]
        else:
            available_models = ["Auto", "GPT-4", "Claude 3", "Llama 3"]
    except Exception as e:
        print(f"[ERROR] Error fetching models: {str(e)}")
        available_models = ["Auto", "GPT-4", "Claude 3", "Llama 3"]
    
    return render_template('digests.html', 
                          active_page='digests', 
                          nav_items=NAV_ITEMS,
                          digests=digest_list,
                          content_for_digest=content_for_digest,
                          available_models=available_models,
                          format_date=format_date)

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

@app.route('/api-diagnostics')
def api_diagnostics():
    """Detailed API diagnostics page"""
    # Check base API status
    base_status = check_api_status()
    
    # Check critical endpoints
    endpoints = {
        "status": check_endpoint_status("status"),
        "knowledge_list": check_endpoint_status("knowledge/list"),
        "model_router": check_endpoint_status("model-router/available-models"),
        "components": check_endpoint_status("components/"),
        "contentmind_test": check_endpoint_status(
            "agents/contentmind/process", 
            method="POST", 
            data={
                "content_type": "text",
                "content": "This is a test message for API diagnostics.",
                "metadata": {"create_digest": False}
            },
            timeout=10
        )
    }
    
    # Check server configuration
    try:
        with open(Path(project_root) / "server_config.json", "r") as f:
            server_config = json.load(f)
    except Exception as e:
        server_config = {"error": str(e)}
    
    # Return diagnostics page
    return render_template(
        'diagnostics.html',
        active_page='settings',
        nav_items=NAV_ITEMS,
        base_status=base_status,
        endpoints=endpoints,
        server_config=server_config,
        api_base_url=API_BASE_URL
    )

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