#!/usr/bin/env python3
"""
Comprehensive Content Debugger for BlueAbel AIOS

This script thoroughly tests content retrieval and display functionality.
It identifies exactly what's happening with the content detail and view content pages,
checking everything from data structure to template rendering.
"""

import os
import sys
import json
import pprint
import inspect
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    # Flask imports for testing rendering
    from flask import Flask, render_template, request

    # Import the app but protect against import errors
    try:
        from flask_ui.app import app, format_date, get_content_item, get_content_items, NAV_ITEMS, API_BASE_URL
        APP_IMPORTED = True
    except ImportError as e:
        print(f"Warning: Could not import Flask app: {e}")
        APP_IMPORTED = False
except ImportError as e:
    print(f"Warning: Could not import Flask: {e}")

# Console colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.END}\n")

def print_subsection(title):
    """Print a subsection header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'-' * 50}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'-' * 50}{Colors.END}\n")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def dump_obj(obj, title=None):
    """Print an object with pretty formatting"""
    if title:
        print(f"{Colors.YELLOW}{Colors.BOLD}{title}:{Colors.END}")
    
    if obj is None:
        print("None")
        return
    
    if isinstance(obj, (dict, list)):
        print(json.dumps(obj, indent=2, default=str))
    else:
        print(pprint.pformat(obj, indent=2))

# Create dummy functions for testing when app can't be imported
if not APP_IMPORTED:
    def format_date(date_str):
        try:
            d = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return d.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def get_content_item(content_id):
        print(f"Using dummy get_content_item with ID: {content_id}")
        return {
            "id": content_id,
            "title": f"Dummy Item {content_id}",
            "summary": "This is a dummy summary",
            "type": "text",
            "source": "Dummy Source",
            "created_at": datetime.now().isoformat(),
            "content": "This is dummy content",
            "tags": ["dummy", "test"],
            "entities": [{"name": "Entity", "type": "Type"}]
        }
    
    def get_content_items(limit=10, content_type=None, sort_by="date_desc", page=1, query=None):
        print("Using dummy get_content_items")
        items = [
            {
                "id": f"item{i}",
                "title": f"Dummy Item {i}",
                "summary": f"This is dummy summary {i}",
                "type": "text",
                "source": f"Dummy Source {i}",
                "created_at": datetime.now().isoformat(),
                "tags": ["dummy", "test"]
            }
            for i in range(1, limit+1)
        ]
        return {
            "items": items,
            "total": 20,
            "pages": 2,
            "current_page": page
        }
    
    API_BASE_URL = "http://localhost:9001"
    NAV_ITEMS = {}

    # Create a temporary Flask app for testing
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, "flask_ui", "templates"),
                static_folder=os.path.join(project_root, "flask_ui", "static"))
    app.jinja_env.globals['format_date'] = format_date

# Helper function to render template directly
def render_template_test(template_name, **context):
    """Render a template for testing purposes"""
    try:
        # Add common variables
        context.setdefault('active_page', 'test')
        context.setdefault('nav_items', NAV_ITEMS)
        context.setdefault('format_date', format_date)
        
        # Try to render the template
        with app.app_context(), app.test_request_context():
            rendered = render_template(template_name, **context)
            return rendered
    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        traceback_str = traceback.format_exc()
        return f"Error rendering template: {error_type}: {error_message}\n\n{traceback_str}"

# Test actual content item
def test_content_item(content_id):
    """Test retrieving and rendering a content item"""
    print_subsection(f"Testing Content Item: {content_id}")
    
    # Try to retrieve the content item
    try:
        print(f"Attempting to retrieve content for ID: {content_id}")
        content = get_content_item(content_id)
        
        if not content:
            print_error("Content item is None")
            return
        
        print_success("Content item retrieved")
        print_info(f"Content type: {type(content)}")
        
        if isinstance(content, dict):
            print_info(f"Content keys: {list(content.keys())}")
            
            # Check for critical fields
            for field in ['id', 'title', 'type', 'content_type', 'summary', 'content', 'tags']:
                if field in content:
                    value = content[field]
                    print_info(f"{field}: {type(value).__name__} = {value}")
                else:
                    print_warning(f"Missing field: {field}")
            
            # Render the content detail template
            print_info("\nAttempting to render content_detail.html template...")
            rendered = render_template_test('content_detail.html', content=content)
            
            if "Error rendering template" in rendered:
                print_error("Template rendering failed")
                print(rendered)
            else:
                print_success("Template rendered successfully")
                
                # Check if any error messages are visible in the rendered template
                error_indicators = [
                    "No Content Available", 
                    "No summary available", 
                    "Source not available",
                    "No content is available for display"
                ]
                
                errors_found = False
                for indicator in error_indicators:
                    if indicator in rendered:
                        print_warning(f"Found error indicator in rendered template: '{indicator}'")
                        errors_found = True
                
                if not errors_found:
                    print_success("No error indicators found in rendered template")
        else:
            print_error(f"Content item is not a dictionary: {type(content)}")
            dump_obj(content, "Content")
    
    except Exception as e:
        print_error(f"Error testing content item: {str(e)}")
        traceback.print_exc()

# Test get_content_items function
def test_get_content_items():
    """Test the get_content_items function"""
    print_subsection("Testing get_content_items Function")
    
    try:
        content_data = get_content_items(limit=5)
        
        print_info(f"Content data type: {type(content_data)}")
        
        if isinstance(content_data, dict):
            print_info(f"Content data keys: {list(content_data.keys())}")
            
            if 'items' in content_data:
                items = content_data['items']
                print_success(f"Found {len(items)} items in the content data")
                
                if items:
                    first_item = items[0]
                    print_info(f"First item type: {type(first_item)}")
                    
                    if isinstance(first_item, dict):
                        print_info(f"First item keys: {list(first_item.keys())}")
                        
                        # Check for critical fields in the first item
                        for field in ['id', 'title', 'type', 'content_type', 'summary', 'tags']:
                            if field in first_item:
                                value = first_item[field]
                                print_info(f"{field}: {type(value).__name__} = {value}")
                            else:
                                print_warning(f"Missing field: {field}")
                    else:
                        print_error(f"First item is not a dictionary: {type(first_item)}")
                
                # Render the view_content template
                print_info("\nAttempting to render view_content.html template...")
                rendered = render_template_test('view_content.html', 
                                               content_items=items,
                                               selected_type=None,
                                               selected_sort="date_desc",
                                               pagination={"current_page": 1, "total_pages": 1, "has_prev": False, "has_next": False, "pages": [1]})
                
                if "Error rendering template" in rendered:
                    print_error("Template rendering failed")
                    print(rendered)
                else:
                    print_success("Template rendered successfully")
                    
                    # Check if any error messages are visible in the rendered template
                    error_indicators = [
                        "No content items found", 
                        "Untitled Content", 
                        "Unknown Date",
                        "No summary available"
                    ]
                    
                    errors_found = False
                    for indicator in error_indicators:
                        if indicator in rendered:
                            print_warning(f"Found error indicator in rendered template: '{indicator}'")
                            errors_found = True
                    
                    if not errors_found:
                        print_success("No error indicators found in rendered template")
            else:
                print_error("No 'items' key found in content data")
                dump_obj(content_data, "Content Data")
        else:
            print_error(f"Content data is not a dictionary: {type(content_data)}")
            dump_obj(content_data, "Content Data")
    
    except Exception as e:
        print_error(f"Error testing get_content_items: {str(e)}")
        traceback.print_exc()

# Inspect a function to understand its implementation
def inspect_function(func):
    """Inspect a function to understand its implementation"""
    print_subsection(f"Inspecting Function: {func.__name__}")
    
    try:
        # Get source code
        source = inspect.getsource(func)
        print_info(f"Source code for {func.__name__}:")
        print(source)
        
        return source
    except Exception as e:
        print_error(f"Error inspecting function {func.__name__}: {str(e)}")
        return None

# Check for template issues
def check_templates():
    """Check the templates for issues"""
    print_subsection("Checking Templates")
    
    templates_dir = project_root / "flask_ui" / "templates"
    
    # Find the content_detail.html template
    content_detail_path = templates_dir / "content_detail.html"
    
    if not content_detail_path.exists():
        print_error(f"Template not found: {content_detail_path}")
        return
    
    # Read and check the template
    with open(content_detail_path, 'r') as f:
        template_content = f.read()
        
        print_info(f"Template found: {content_detail_path} ({len(template_content)} bytes)")
        
        # Check for typical issues in the template
        issues = [
            "{{ content.title }}" # Direct access without checks
        ]
        
        for issue in issues:
            if issue in template_content:
                print_warning(f"Found potential issue in template: '{issue}'")
            else:
                print_success(f"No issue found for pattern: '{issue}'")
        
        # Count safety checks in the template
        safety_checks = [
            "{% if content is defined",
            "{% if content.",
            "|default("
        ]
        
        for check in safety_checks:
            count = template_content.count(check)
            print_info(f"Found {count} occurrences of safety check: '{check}'")

# Test direct function invocations
def test_direct_function(content_id="test"):
    """Test direct function invocations with a synthetic content ID"""
    print_subsection(f"Direct Function Test with ID: {content_id}")
    
    # Define a fixed test item
    test_item = {
        "id": content_id,
        "title": f"Test Item {content_id}",
        "summary": "This is a test summary that should display correctly",
        "type": "text",
        "content_type": "text", 
        "source": "Test Source",
        "created_at": datetime.now().isoformat(),
        "content": "This is test content that should display correctly",
        "tags": ["test", "debug"],
        "entities": [{"name": "Test Entity", "type": "Test Type"}]
    }
    
    try:
        # Create a mini Flask app for testing
        mini_app = Flask("test_app")
        
        @mini_app.route('/test_content')
        def test_content():
            """Test content detail rendering"""
            # Add format_date function
            return render_template('content_detail.html', 
                                  content=test_item,
                                  format_date=format_date,
                                  active_page='test',
                                  nav_items={})
                                  
        @mini_app.route('/test_list')
        def test_list():
            """Test content list rendering"""
            return render_template('view_content.html',
                                  content_items=[test_item, test_item],
                                  format_date=format_date,
                                  active_page='test',
                                  nav_items={},
                                  selected_type=None,
                                  selected_sort="date_desc",
                                  pagination={"current_page": 1, "total_pages": 1, "has_prev": False, "has_next": False, "pages": [1]})
        
        # Update template folder for mini app
        mini_app.template_folder = os.path.join(project_root, "flask_ui", "templates")
        
        # Test rendering with mini app
        with mini_app.app_context(), mini_app.test_request_context():
            content_rendered = mini_app.view_functions['test_content']()
            list_rendered = mini_app.view_functions['test_list']()
            
            print_info(f"Content detail rendered: {len(content_rendered)} bytes")
            print_info(f"Content list rendered: {len(list_rendered)} bytes")
            
            if "Error" in content_rendered or "Error" in list_rendered:
                print_error("Rendering error detected")
                if "Error" in content_rendered:
                    print(content_rendered[:500])
                if "Error" in list_rendered:
                    print(list_rendered[:500])
            else:
                print_success("Both templates rendered successfully with test data")
                
                # Check for test item content in the rendered output
                if test_item["title"] in content_rendered:
                    print_success(f"Title '{test_item['title']}' found in rendered content detail")
                else:
                    print_error(f"Title '{test_item['title']}' NOT found in rendered content detail")
                
                if test_item["title"] in list_rendered:
                    print_success(f"Title '{test_item['title']}' found in rendered content list")
                else:
                    print_error(f"Title '{test_item['title']}' NOT found in rendered content list")
    
    except Exception as e:
        print_error(f"Error in direct function test: {str(e)}")
        traceback.print_exc()

def test_data_shapes():
    """Test various data shapes to see where the issues might be"""
    print_subsection("Testing Data Shape Compatibility")
    
    test_data_variants = [
        {
            "name": "Minimal valid item",
            "data": {
                "id": "minimal",
                "title": "Minimal Item",
                "content": "Minimal content"
            }
        },
        {
            "name": "Item with title accessed as method",
            "data": {
                "id": "method_title",
                "title": str.title,  # This will cause the issue seen in the screenshot
                "content": "Content with method title"
            }
        },
        {
            "name": "Item with None values",
            "data": {
                "id": "none_values",
                "title": None,
                "summary": None,
                "content": None,
                "tags": None
            }
        },
        {
            "name": "Item with empty string values",
            "data": {
                "id": "empty_strings",
                "title": "",
                "summary": "",
                "content": "",
                "tags": []
            }
        },
        {
            "name": "Item with incorrect types",
            "data": {
                "id": "wrong_types",
                "title": 123,
                "summary": {"complex": "object"},
                "content": ["list", "instead", "of", "string"],
                "tags": "not a list"
            }
        }
    ]
    
    for variant in test_data_variants:
        print_info(f"\nTesting variant: {variant['name']}")
        
        try:
            rendered = render_template_test('content_detail.html', content=variant['data'])
            
            if "Error rendering template" in rendered:
                print_error(f"Template rendering failed for {variant['name']}")
                print(rendered[:500])
            else:
                print_success(f"Template rendered successfully for {variant['name']}")
        except Exception as e:
            print_error(f"Error testing variant {variant['name']}: {str(e)}")

def main():
    """Main function to run all tests"""
    print_section("BlueAbel AIOS Content Display Debugger")
    
    # Check if Flask app was imported
    if APP_IMPORTED:
        print_success("Successfully imported Flask app")
    else:
        print_warning("Using dummy functions since Flask app import failed")
    
    # Check templates for issues
    check_templates()
    
    # Test content items function
    test_get_content_items()
    
    # Test content item with real ID from logs
    test_content_item("df347171-39a0-4617-b4df-74fd93b20d56")
    
    # Inspect the get_content_item function
    if APP_IMPORTED:
        inspect_function(get_content_item)
    
    # Test direct function invocation with synthetic data
    test_direct_function()
    
    # Test data shape compatibility
    test_data_shapes()
    
    print_section("Debug Complete")
    print("Based on the results above, you should be able to identify and fix the issue.")
    print("Look for any issues with data structure or template rendering that were found.")

if __name__ == "__main__":
    main()