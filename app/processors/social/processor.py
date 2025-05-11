# app/processors/social/processor.py
import asyncio
import json
import logging
import re
import base64
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)

class SocialMediaProcessor:
    """Processor for extracting content from social media platforms"""
    
    SUPPORTED_PLATFORMS = {
        "twitter": ["twitter.com", "x.com"],
        "linkedin": ["linkedin.com"],
        "instagram": ["instagram.com"],
        "facebook": ["facebook.com", "fb.com"],
        "threads": ["threads.net"],
        "reddit": ["reddit.com"],
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract(self, url_or_content: str) -> Dict[str, Any]:
        """Extract content from social media post

        Args:
            url_or_content: URL or content ID for social media post

        Returns:
            Dictionary with extracted content
        """
        try:
            # Check if this is a thread collection (multiple URLs separated by newlines)
            if "\n" in url_or_content:
                return await self._process_thread(url_or_content)

            # Determine if input is URL or content ID
            if url_or_content.startswith("http"):
                platform = self._detect_platform(url_or_content)

                if not platform:
                    return {
                        "status": "error",
                        "message": f"Unsupported social media platform or invalid URL: {url_or_content}"
                    }

                # Process based on platform
                if platform == "twitter":
                    return await self._process_twitter(url_or_content)
                elif platform == "linkedin":
                    return await self._process_linkedin(url_or_content)
                elif platform == "reddit":
                    return await self._process_reddit(url_or_content)
                else:
                    # Generic fallback for other platforms
                    return await self._process_generic_social(url_or_content, platform)
            else:
                # Treat as content ID (not URL)
                if ":" in url_or_content:
                    # Format: platform:id (e.g., "twitter:1234567890")
                    parts = url_or_content.split(":", 1)
                    if len(parts) == 2:
                        platform, content_id = parts

                        if platform in self.SUPPORTED_PLATFORMS:
                            if platform == "twitter":
                                url = f"https://twitter.com/i/web/status/{content_id}"
                                return await self._process_twitter(url)
                            elif platform == "linkedin":
                                url = f"https://www.linkedin.com/posts/{content_id}"
                                return await self._process_linkedin(url)
                            elif platform == "reddit":
                                url = f"https://www.reddit.com/comments/{content_id}"
                                return await self._process_reddit(url)

                return {
                    "status": "error",
                    "message": f"Invalid social media content ID format. Use 'platform:id' format or a full URL."
                }
                
        except Exception as e:
            logger.error(f"Error extracting social media content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting social media content: {str(e)}"
            }
    
    def _detect_platform(self, url: str) -> Optional[str]:
        """Detect social media platform from URL
        
        Args:
            url: URL to analyze
            
        Returns:
            Platform name or None if not supported
        """
        # Parse URL and extract domain
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove 'www.' prefix if present
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Check against supported platforms
            for platform, domains in self.SUPPORTED_PLATFORMS.items():
                for platform_domain in domains:
                    if domain.endswith(platform_domain):
                        return platform
            
            return None
        except Exception as e:
            logger.error(f"Error detecting platform from URL {url}: {str(e)}")
            return None
    
    async def _process_twitter(self, url: str) -> Dict[str, Any]:
        """Process Twitter/X post
        
        Args:
            url: Twitter/X post URL
            
        Returns:
            Dictionary with extracted content
        """
        try:
            # Extract tweet ID from URL
            tweet_id = self._extract_twitter_id(url)
            
            if not tweet_id:
                return {
                    "status": "error",
                    "message": f"Could not extract tweet ID from URL: {url}"
                }
            
            # Fetch HTML content (public access)
            html = await self._fetch_url(url)
            
            if not html:
                return {
                    "status": "error", 
                    "message": "Failed to fetch Twitter content"
                }
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract available metadata
            title = self._extract_twitter_title(soup)
            author = self._extract_twitter_author(soup)
            date = self._extract_twitter_date(soup)
            text = self._extract_twitter_text(soup)
            
            # Check if we have minimum viable data
            if not text:
                return {
                    "status": "error",
                    "message": "Could not extract tweet content"
                }
            
            # Add hashtags and mentions
            hashtags = self._extract_twitter_hashtags(text)
            mentions = self._extract_twitter_mentions(text)
            
            # Construct result
            return {
                "status": "success",
                "platform": "twitter",
                "title": title or f"Tweet by {author or 'Unknown'}",
                "author": author,
                "published_date": date,
                "text": text,
                "source": url,
                "content_id": tweet_id,
                "metadata": {
                    "hashtags": hashtags,
                    "mentions": mentions,
                    "platform": "twitter"
                },
                "summary": text[:200] + "..." if len(text) > 200 else text,
                "extracted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing Twitter content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing Twitter content: {str(e)}"
            }
    
    async def _process_linkedin(self, url: str) -> Dict[str, Any]:
        """Process LinkedIn post
        
        Args:
            url: LinkedIn post URL
            
        Returns:
            Dictionary with extracted content
        """
        try:
            # Fetch HTML content
            html = await self._fetch_url(url)
            
            if not html:
                return {
                    "status": "error", 
                    "message": "Failed to fetch LinkedIn content"
                }
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract available metadata
            title = self._extract_linkedin_title(soup)
            author = self._extract_linkedin_author(soup)
            date = self._extract_linkedin_date(soup)
            text = self._extract_linkedin_text(soup)
            
            # Check if we have minimum viable data
            if not text:
                return {
                    "status": "error",
                    "message": "Could not extract LinkedIn post content"
                }
            
            # Construct result
            return {
                "status": "success",
                "platform": "linkedin",
                "title": title or f"LinkedIn post by {author or 'Unknown'}",
                "author": author,
                "published_date": date,
                "text": text,
                "source": url,
                "metadata": {
                    "platform": "linkedin"
                },
                "summary": text[:200] + "..." if len(text) > 200 else text,
                "extracted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing LinkedIn content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing LinkedIn content: {str(e)}"
            }
    
    async def _process_reddit(self, url: str) -> Dict[str, Any]:
        """Process Reddit post
        
        Args:
            url: Reddit post URL
            
        Returns:
            Dictionary with extracted content
        """
        try:
            # Ensure URL ends with .json for API access
            if not url.endswith(".json"):
                if url.endswith("/"):
                    json_url = f"{url}.json"
                else:
                    json_url = f"{url}/.json"
            else:
                json_url = url
            
            # Fetch JSON content
            async with aiohttp.ClientSession() as session:
                async with session.get(json_url, headers={
                    "User-Agent": "Bluelabel AIOS Content Extractor"
                }) as response:
                    if response.status != 200:
                        return {
                            "status": "error", 
                            "message": f"Failed to fetch Reddit content: Status {response.status}"
                        }
                    
                    data = await response.json()
            
            # Extract post content
            if not data or len(data) < 1 or not isinstance(data, list):
                return {
                    "status": "error", 
                    "message": "Invalid Reddit API response"
                }
            
            # Get post data
            post_data = data[0]["data"]["children"][0]["data"]
            
            title = post_data.get("title", "")
            author = post_data.get("author", "")
            text = post_data.get("selftext", "")
            created_utc = post_data.get("created_utc")
            subreddit = post_data.get("subreddit", "")
            
            # Format date
            date = None
            if created_utc:
                date = datetime.fromtimestamp(created_utc).isoformat()
            
            # Combine title and text
            full_text = f"{title}\n\n{text}" if text else title
            
            return {
                "status": "success",
                "platform": "reddit",
                "title": title,
                "author": author,
                "published_date": date,
                "text": full_text,
                "source": url,
                "metadata": {
                    "subreddit": subreddit,
                    "platform": "reddit"
                },
                "summary": full_text[:200] + "..." if len(full_text) > 200 else full_text,
                "extracted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing Reddit content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing Reddit content: {str(e)}"
            }
    
    async def _process_generic_social(self, url: str, platform: str) -> Dict[str, Any]:
        """Process social media from platforms without specific extractors
        
        Args:
            url: Social media post URL
            platform: Platform name
            
        Returns:
            Dictionary with extracted content
        """
        try:
            # Fetch HTML content
            html = await self._fetch_url(url)
            
            if not html:
                return {
                    "status": "error", 
                    "message": f"Failed to fetch {platform} content"
                }
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract generic metadata
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            date = self._extract_published_date(soup)
            description = self._extract_description(soup)
            
            # Use og:description as text if available
            og_description = soup.find("meta", property="og:description")
            text = og_description["content"] if og_description and og_description.get("content") else description
            
            # Fallback to title if no text available
            if not text:
                text = title
            
            if not text:
                return {
                    "status": "error",
                    "message": f"Could not extract content from {platform}"
                }
            
            return {
                "status": "success",
                "platform": platform,
                "title": title or f"{platform.capitalize()} post",
                "author": author,
                "published_date": date,
                "text": text,
                "source": url,
                "metadata": {
                    "platform": platform
                },
                "summary": text[:200] + "..." if len(text) > 200 else text,
                "extracted_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing {platform} content: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing {platform} content: {str(e)}"
            }
    
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        self.logger.warning(f"Failed to fetch URL {url}: Status {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching URL {url}: {str(e)}")
            return None
    
    def _extract_twitter_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from Twitter URL"""
        # Match patterns like /status/1234567890 or /statuses/1234567890
        pattern = r"(?:status|statuses)/(\d+)"
        match = re.search(pattern, url)
        
        if match:
            return match.group(1)
        
        return None
    
    def _extract_twitter_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from Twitter HTML"""
        # Try meta title
        if soup.title:
            title = soup.title.string
            # Remove " / Twitter" suffix
            if title and " / Twitter" in title:
                return title.split(" / Twitter")[0]
            # Remove " / X" suffix
            if title and " / X" in title:
                return title.split(" / X")[0]
            return title
        
        return None
    
    def _extract_twitter_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from Twitter HTML"""
        # Try various metadata patterns
        # Meta by Twitter
        author = soup.find("meta", attrs={"name": "twitter:creator"})
        if author and author.get("content"):
            return author["content"]
        
        # Look for author in title
        if soup.title:
            title = soup.title.string
            if title and "on Twitter" in title:
                parts = title.split("on Twitter", 1)[0]
                if ": " in parts:
                    return parts.split(": ", 1)[0].strip()
            if title and "on X" in title:
                parts = title.split("on X", 1)[0]
                if ": " in parts:
                    return parts.split(": ", 1)[0].strip()
        
        return None
    
    def _extract_twitter_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from Twitter HTML"""
        date = soup.find("meta", property="og:article:published_time")
        if date and date.get("content"):
            return date["content"]
        
        return None
    
    def _extract_twitter_text(self, soup: BeautifulSoup) -> str:
        """Extract text from Twitter HTML"""
        # Try meta description first
        description = soup.find("meta", property="og:description")
        if description and description.get("content"):
            return description["content"]
        
        # Try to extract from the page content
        # This is challenging due to Twitter's dynamic content,
        # so we'll rely mostly on metadata
        
        # If all else fails, extract from title
        if soup.title:
            title = soup.title.string
            if title and (": " in title):
                parts = title.split(": ", 1)
                if len(parts) > 1:
                    return parts[1].split(" / Twitter")[0].strip()
        
        return "No text could be extracted from this tweet"
    
    def _extract_twitter_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from tweet text"""
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags
    
    def _extract_twitter_mentions(self, text: str) -> List[str]:
        """Extract mentions from tweet text"""
        mentions = re.findall(r'@(\w+)', text)
        return mentions
    
    def _extract_linkedin_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from LinkedIn HTML"""
        title = soup.find("meta", property="og:title")
        if title and title.get("content"):
            return title["content"]
        
        if soup.title:
            return soup.title.string.split(" | LinkedIn")[0].strip()
        
        return None
    
    def _extract_linkedin_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from LinkedIn HTML"""
        author = soup.find("meta", property="article:author")
        if author and author.get("content"):
            return author["content"]
        
        # Try to extract from title
        if soup.title:
            title = soup.title.string
            if title and " on LinkedIn: " in title:
                return title.split(" on LinkedIn: ")[0].strip()
        
        return None
    
    def _extract_linkedin_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from LinkedIn HTML"""
        date = soup.find("meta", property="article:published_time")
        if date and date.get("content"):
            return date["content"]
        
        return None
    
    def _extract_linkedin_text(self, soup: BeautifulSoup) -> str:
        """Extract text from LinkedIn HTML"""
        description = soup.find("meta", property="og:description")
        if description and description.get("content"):
            return description["content"]
        
        # Fallback to title
        title = self._extract_linkedin_title(soup)
        return title or "No text could be extracted from this LinkedIn post"
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
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
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from HTML"""
        # Try various common author metadata patterns
        author = soup.find("meta", attrs={"name": "author"})
        if author and author.get("content"):
            return author["content"].strip()
        
        author = soup.find("meta", property="article:author")
        if author and author.get("content"):
            return author["content"].strip()
        
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
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from HTML"""
        description = soup.find("meta", property="og:description")
        if description and description.get("content"):
            return description["content"].strip()

        description = soup.find("meta", attrs={"name": "description"})
        if description and description.get("content"):
            return description["content"].strip()

        return None

    async def _process_thread(self, urls_text: str) -> Dict[str, Any]:
        """Process a thread of social media posts

        Args:
            urls_text: Newline-separated list of URLs in thread order

        Returns:
            Dictionary with combined thread content
        """
        # Split the input into individual URLs
        urls = [url.strip() for url in urls_text.split("\n") if url.strip()]

        if not urls:
            return {
                "status": "error",
                "message": "No valid URLs provided for thread processing"
            }

        # Process first URL to determine platform and get basic metadata
        first_url = urls[0]
        platform = self._detect_platform(first_url)

        if not platform:
            return {
                "status": "error",
                "message": f"Unsupported social media platform or invalid URL for thread: {first_url}"
            }

        # Process each URL in the thread
        thread_parts = []
        author = None
        first_date = None
        last_date = None
        combined_hashtags = set()
        combined_mentions = set()

        for url in urls:
            if not url.strip():
                continue

            # Check if all URLs are from the same platform
            url_platform = self._detect_platform(url)
            if url_platform != platform:
                logger.warning(f"URL {url} is from platform {url_platform} but thread is from {platform}")
                # Continue anyway, but log warning

            # Process the URL based on platform
            if platform == "twitter":
                result = await self._process_twitter(url)
            elif platform == "linkedin":
                result = await self._process_linkedin(url)
            elif platform == "reddit":
                result = await self._process_reddit(url)
            else:
                result = await self._process_generic_social(url, platform)

            # Skip failed extractions
            if result.get("status") != "success":
                logger.warning(f"Failed to process thread URL {url}: {result.get('message')}")
                continue

            # Add to thread parts
            thread_parts.append({
                "text": result.get("text", ""),
                "url": url,
                "date": result.get("published_date")
            })

            # Capture metadata from first post or update as needed
            if author is None and result.get("author"):
                author = result.get("author")

            # Track first and last dates
            date = result.get("published_date")
            if date:
                if first_date is None or date < first_date:
                    first_date = date
                if last_date is None or date > last_date:
                    last_date = date

            # Collect all hashtags and mentions
            if platform == "twitter" and result.get("metadata"):
                if result.get("metadata").get("hashtags"):
                    combined_hashtags.update(result.get("metadata").get("hashtags", []))
                if result.get("metadata").get("mentions"):
                    combined_mentions.update(result.get("metadata").get("mentions", []))

        # If we have no successful parts, return error
        if not thread_parts:
            return {
                "status": "error",
                "message": "Failed to process any URLs in the thread"
            }

        # Combine all thread parts into a single text
        combined_text = "\n\n---\n\n".join([
            f"Post {i+1} ({part.get('date', 'unknown date')}):\n{part.get('text')}"
            for i, part in enumerate(thread_parts)
        ])

        # Create thread summary based on first post
        summary = thread_parts[0].get("text", "")
        if len(summary) > 200:
            summary = summary[:197] + "..."

        # Generate an appropriate title
        if len(thread_parts) > 1:
            title = f"Thread by {author or 'Unknown'} ({len(thread_parts)} posts)"
        else:
            title = f"Post by {author or 'Unknown'}"

        # Combine metadata
        thread_metadata = {
            "platform": platform,
            "is_thread": True,
            "thread_length": len(thread_parts),
            "thread_urls": [part.get("url") for part in thread_parts]
        }

        # Add platform-specific metadata
        if platform == "twitter":
            thread_metadata["hashtags"] = list(combined_hashtags)
            thread_metadata["mentions"] = list(combined_mentions)

        return {
            "status": "success",
            "platform": platform,
            "title": title,
            "author": author,
            "published_date": first_date,
            "last_update_date": last_date,
            "text": combined_text,
            "source": first_url,
            "metadata": thread_metadata,
            "summary": f"Thread with {len(thread_parts)} posts. {summary}",
            "extracted_at": datetime.now().isoformat()
        }