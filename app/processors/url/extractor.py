# app/processors/url/extractor.py
import aiohttp
from bs4 import BeautifulSoup
import trafilatura
from datetime import datetime
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLProcessor:
    """Extracts content from URLs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract(self, url: str) -> Dict[str, Any]:
        """Extract content from a URL"""
        try:
            html = await self._fetch_url(url)
            if not html:
                return {
                    "status": "error", 
                    "message": "Failed to fetch URL content",
                    "url": url
                }
            
            # Extract main content using trafilatura
            text = trafilatura.extract(html)
            
            # Parse HTML for metadata using BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract other metadata
            author = self._extract_author(soup)
            published_date = self._extract_published_date(soup)
            
            # Extract summary (this is a placeholder; we'll use LLM for this later)
            summary = self._create_preview(text, 500) if text else "No content extracted"
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "author": author,
                "published_date": published_date,
                "text": text,
                "summary": summary,
                "html": html,  # Include original HTML for potential further processing
                "extracted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error extracting content from URL {url}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting content: {str(e)}",
                "url": url
            }
    
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        self.logger.warning(f"Failed to fetch URL {url}: Status {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching URL {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML"""
        if soup.title:
            return soup.title.string.strip()
        
        # Try Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()
        
        return "Untitled"
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from HTML"""
        # Try various common author metadata patterns
        author = soup.find("meta", attrs={"name": "author"})
        if author and author.get("content"):
            return author["content"].strip()
        
        author = soup.find("meta", property="article:author")
        if author and author.get("content"):
            return author["content"].strip()
        
        # Look for common author class names
        for class_name in ["author", "byline", "writer"]:
            author_elem = soup.find(class_=class_name)
            if author_elem:
                return author_elem.get_text().strip()
        
        return None
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract published date from HTML"""
        # Try various common date metadata patterns
        date = soup.find("meta", property="article:published_time")
        if date and date.get("content"):
            return date["content"]
        
        date = soup.find("meta", attrs={"name": "pubdate"})
        if date and date.get("content"):
            return date["content"]
        
        date = soup.find("meta", attrs={"name": "publication_date"})
        if date and date.get("content"):
            return date["content"]
        
        # Look for time elements
        time_elem = soup.find("time")
        if time_elem and time_elem.get("datetime"):
            return time_elem["datetime"]
        
        return None
    
    def _create_preview(self, text: str, max_length: int = 500) -> str:
        """Create a preview/summary of the extracted text"""
        if not text:
            return "No content available"
        
        # For now, we'll just return the first part of the text
        # Later, we'll implement proper summarization using LLMs
        if len(text) <= max_length:
            return text
        
        # Find a good breaking point (end of sentence)
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        if last_period > 0:
            return truncated[:last_period + 1] + "..."
        
        return truncated + "..."