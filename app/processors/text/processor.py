# app/processors/text/processor.py
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Processes plain text content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract(self, text_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract structured information from plain text
        
        Args:
            text_content: The text content to process
            metadata: Optional additional metadata
            
        Returns:
            Dict containing processed text content and metadata
        """
        try:
            if not text_content or not text_content.strip():
                return {
                    "status": "error",
                    "message": "Empty text content provided"
                }
            
            # Clean up the text (remove extra whitespace, normalize line breaks)
            cleaned_text = self._clean_text(text_content)
            
            # Extract a title from the text
            title = self._extract_title(cleaned_text, metadata)
            
            # Create a preview summary
            summary = self._create_preview(cleaned_text)
            
            # Get any provided metadata or create empty dict
            processed_metadata = metadata or {}
            
            return {
                "status": "success",
                "title": title,
                "text": cleaned_text,
                "summary": summary,
                "author": processed_metadata.get("author"),
                "source": processed_metadata.get("source", "Manual Input"),
                "extracted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error processing text content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing text content: {str(e)}"
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned text
        """
        # Replace multiple newlines with single newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace tabs with spaces
        cleaned = cleaned.replace('\t', '    ')
        
        # Normalize whitespace
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _extract_title(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Extract a title from the text or metadata
        
        Args:
            text: The text to extract title from
            metadata: Optional metadata that might contain a title
            
        Returns:
            Extracted title or default
        """
        # Check if metadata contains a title
        if metadata and metadata.get("title"):
            return metadata["title"]
        
        # Try to extract title from the first line or sentence
        lines = text.strip().split('\n')
        if lines and lines[0].strip():
            first_line = lines[0].strip()
            # If first line is short enough to be a title
            if len(first_line) <= 100:
                return first_line
            
            # Otherwise try to get the first sentence
            sentences = first_line.split('.')
            if sentences and len(sentences[0]) <= 100:
                return sentences[0]
            
            # If first sentence is too long, truncate
            return first_line[:97] + "..."
        
        # Default title if we can't extract one
        return "Text Note"
    
    def _create_preview(self, text: str, max_length: int = 500) -> str:
        """Create a preview/summary of the text
        
        Args:
            text: The text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Preview of the text
        """
        if not text:
            return "No content available"
        
        # For basic preview, truncate the text
        if len(text) <= max_length:
            return text
        
        # Find a good breaking point (end of sentence)
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        if last_period > 0:
            return truncated[:last_period + 1] + "..."
        
        return truncated + "..."