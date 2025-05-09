from typing import Dict, Any
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class TestAgent:
    """Test agent that bypasses LLM calls for debugging"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process content without LLM calls"""
        content_type = request.get("content_type")
        content = request.get("content")
        
        logger.info(f"Test agent processing content type: {content_type}")
        
        if not content_type or not content:
            return {
                "status": "error",
                "message": "Missing content_type or content in request"
            }
        
        # Create a simple successful response
        extracted_content = {
            "title": f"Test {content_type.capitalize()} Content",
            "summary": f"This is a test summary for {content_type} content.",
            "author": "Test Author",
            "published_date": datetime.now().isoformat(),
            "source": str(content)[:50] + "..." if len(str(content)) > 50 else str(content),
            "text": f"Test text content for {content_type}",
            "extracted_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "content_type": content_type,
            "original_content": str(content),
            "processed_content": {
                "title": extracted_content["title"],
                "summary": extracted_content["summary"],
                "author": extracted_content["author"],
                "published_date": extracted_content["published_date"],
                "source": extracted_content["source"],
                "tags": ["test", "debug", content_type],
                "entities": {"test_entity": ["Entity1", "Entity2"]}
            },
            "providers_used": {
                "summary": "test",
                "entity_extraction": "test",
                "tagging": "test"
            }
        }