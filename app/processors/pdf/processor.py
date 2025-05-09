# app/processors/pdf/processor.py
import logging
from typing import Dict, Any, Optional, BinaryIO, Union
import pypdf
from datetime import datetime
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    """Extracts content from PDF documents"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract(self, pdf_content: Union[str, bytes, BinaryIO]) -> Dict[str, Any]:
        """Extract content from a PDF document
        
        Args:
            pdf_content: Either a file path, bytes content, or file-like object
            
        Returns:
            Dict containing extracted PDF content and metadata
        """
        try:
            # Process the PDF content based on what was provided
            if isinstance(pdf_content, str):
                # Treat as file path
                return self._process_from_path(pdf_content)
            elif isinstance(pdf_content, bytes) or hasattr(pdf_content, 'read'):
                # Treat as bytes content or file-like object
                return self._process_from_bytes(pdf_content)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported PDF content type: {type(pdf_content)}"
                }
        
        except Exception as e:
            self.logger.error(f"Error extracting content from PDF: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting content: {str(e)}"
            }
    
    def _process_from_path(self, file_path: str) -> Dict[str, Any]:
        """Process PDF from a file path"""
        try:
            with open(file_path, "rb") as file:
                return self._extract_pdf_content(file)
        except Exception as e:
            self.logger.error(f"Error opening PDF file {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error opening PDF file: {str(e)}"
            }
    
    def _process_from_bytes(self, content: Union[bytes, BinaryIO]) -> Dict[str, Any]:
        """Process PDF from bytes or file-like object"""
        try:
            # If it's bytes, wrap in BytesIO
            if isinstance(content, bytes):
                content = BytesIO(content)
            
            return self._extract_pdf_content(content)
        except Exception as e:
            self.logger.error(f"Error processing PDF from bytes: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing PDF content: {str(e)}"
            }
    
    def _extract_pdf_content(self, file_obj: BinaryIO) -> Dict[str, Any]:
        """Extract text and metadata from PDF file object"""
        try:
            # Create PDF reader
            pdf = pypdf.PdfReader(file_obj)
            
            # Extract metadata
            metadata = pdf.metadata or {}
            
            # Extract title
            title = self._extract_title(pdf, metadata)
            
            # Extract author
            author = self._extract_author(metadata)
            
            # Extract creation date
            creation_date = self._extract_creation_date(metadata)
            
            # Extract text from all pages
            text = ""
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                text += page.extract_text() + "\n\n"
            
            # Create basic preview/summary
            summary = self._create_preview(text)
            
            return {
                "status": "success",
                "title": title,
                "author": author,
                "creation_date": creation_date,
                "page_count": len(pdf.pages),
                "text": text,
                "summary": summary,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting content from PDF: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting content: {str(e)}"
            }
    
    def _extract_title(self, pdf: pypdf.PdfReader, metadata: Dict) -> str:
        """Extract title from PDF metadata"""
        # Try to get title from metadata
        if metadata.get("/Title"):
            return metadata.get("/Title")
        
        # If no title in metadata, try to extract from first page text
        if len(pdf.pages) > 0:
            first_page_text = pdf.pages[0].extract_text()
            # Take first non-empty line as potential title
            if first_page_text:
                lines = first_page_text.split('\n')
                for line in lines:
                    if line.strip():
                        # Use first 50 chars max for title from text
                        title = line.strip()
                        if len(title) > 50:
                            title = title[:50] + "..."
                        return title
        
        return "Untitled PDF"
    
    def _extract_author(self, metadata: Dict) -> Optional[str]:
        """Extract author from PDF metadata"""
        if metadata.get("/Author"):
            return metadata.get("/Author")
        return None
    
    def _extract_creation_date(self, metadata: Dict) -> Optional[str]:
        """Extract creation date from PDF metadata"""
        if metadata.get("/CreationDate"):
            # PDF dates are in a specific format, we'll return it as is for now
            return metadata.get("/CreationDate")
        return None
    
    def _create_preview(self, text: str, max_length: int = 500) -> str:
        """Create a preview/summary of the extracted text"""
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