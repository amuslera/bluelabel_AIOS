# Create a temporary file with the fixed version of get_content_item

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