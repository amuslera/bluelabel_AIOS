from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TestProcessor:
    """A simple test processor that returns success without LLM calls"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract(self, content: str) -> dict:
        """Extract content without LLM processing"""
        try:
            logger.info(f"Processing test content: {content[:30]}...")
            
            # Create a simple response
            return {
                "status": "success",
                "title": "Test Content",
                "text": content,
                "summary": "This is a test summary.",
                "source": "Test Source",
                "author": "Test Author",
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in test processor: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in test processor: {str(e)}"
            }