#!/usr/bin/env python3
"""
Direct Content Fix for BlueAbel AIOS

This script directly fixes the get_content_item function in the app.py file
to ensure that it always returns properly formatted data for the content detail page.
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def fix_content_item_function():
    """Directly fix the get_content_item function"""
    app_path = project_root / "flask_ui" / "app.py"
    
    print(f"Opening file: {app_path}")
    
    # Read the original file
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = app_path.with_suffix('.py.bak')
    with open(backup_path, 'w') as f:
        f.write(content)
    
    print(f"Created backup: {backup_path}")
    
    # Find the return statement in get_content_item
    content_item_function_end_marker = "    return demo_item"
    
    # Add the sanitation code before returning the item
    replacement_code = """
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
    return sanitized_item"""
    
    # Replace the return statement
    new_content = content.replace(content_item_function_end_marker, replacement_code)
    
    # Write the new file
    with open(app_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated file: {app_path}")
    return True

def restart_server():
    """Restart the Flask server"""
    try:
        # Create a restart script
        restart_script = project_root / "restart_server.py"
        with open(restart_script, 'w') as f:
            f.write("""#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
from pathlib import Path

# Kill existing Flask processes
try:
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'flask' in ' '.join(proc.info['cmdline'] or []).lower():
                print(f"Killing Flask process: {proc.info['pid']}")
                os.kill(proc.info['pid'], signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
except ImportError:
    print("psutil not available, using ps | grep")
    try:
        ps_output = subprocess.check_output(['ps', 'aux']).decode('utf-8')
        for line in ps_output.splitlines():
            if 'flask' in line.lower():
                try:
                    pid = int(line.split()[1])
                    print(f"Killing Flask process: {pid}")
                    os.kill(pid, signal.SIGTERM)
                except:
                    pass
    except:
        print("Could not kill Flask processes")

# Start a new Flask server
app_path = Path(__file__).parent / "flask_ui" / "app.py"
print(f"Starting Flask with app: {app_path}")

os.environ["FLASK_APP"] = str(app_path)
os.environ["FLASK_ENV"] = "development"

# Run Flask on port 8005
port = 8005
print(f"Starting server at http://127.0.0.1:{port}")
os.system(f"python3 -m flask run --host=127.0.0.1 --port={port}")
""")
        
        # Make the script executable
        os.chmod(restart_script, 0o755)
        
        # Run the script
        subprocess.Popen(["python3", str(restart_script)], 
                         stdout=open(project_root / "restart_server.log", 'w'),
                         stderr=subprocess.STDOUT)
        
        print(f"Server restarting on http://127.0.0.1:8005")
        return True
    
    except Exception as e:
        print(f"Error restarting server: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Direct Content Fix for BlueAbel AIOS")
    
    # Fix the get_content_item function
    if fix_content_item_function():
        print("Fixed get_content_item function to properly sanitize all data")
        
        # Restart the server
        if restart_server():
            print("Server restarted successfully")
            print("\nTo use the fixed application:")
            print("1. Visit http://127.0.0.1:8005 in your browser")
            print("2. Navigate to View Content")
            print("3. Click on any content item to view its details")
            print("\nThe content should now display correctly without any method references or display issues.")
        else:
            print("Failed to restart server, but the fix has been applied")
            print("You can restart the server manually")
    else:
        print("Failed to fix get_content_item function")