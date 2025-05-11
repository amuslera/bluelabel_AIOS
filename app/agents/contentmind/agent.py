# app/agents/contentmind/agent.py
from typing import Dict, Any, List, Optional, Union, BinaryIO
import logging
import json
import base64
from io import BytesIO
from app.agents.base.agent import BluelabelAgent, AgentTool
from app.processors.url.extractor import URLProcessor
from app.processors.pdf.processor import PDFProcessor
from app.processors.audio.processor import AudioProcessor
from app.processors.text.processor import TextProcessor
from app.processors.social.processor import SocialMediaProcessor
from app.core.model_router.router import ModelRouter, Provider

# Configure logging
logger = logging.getLogger(__name__)

class URLProcessorTool(AgentTool):
    """Tool for processing URLs and extracting content"""

    def __init__(self):
        super().__init__(
            name="url_processor",
            description="Extracts content from URLs"
        )
        self.processor = URLProcessor()

    async def execute(self, url: str, **kwargs) -> Dict[str, Any]:
        """Extract content from a URL"""
        logger.info(f"Processing URL: {url}")
        return await self.processor.extract(url)


class PDFProcessorTool(AgentTool):
    """Tool for processing PDF documents and extracting content"""

    def __init__(self):
        super().__init__(
            name="pdf_processor",
            description="Extracts content from PDF documents"
        )
        self.processor = PDFProcessor()

    async def execute(self, pdf_content: Union[str, bytes, BinaryIO], **kwargs) -> Dict[str, Any]:
        """Extract content from a PDF document

        Args:
            pdf_content: Either a file path, base64-encoded string, or file-like object
        """
        logger.info(f"Processing PDF content")

        # Handle base64-encoded content from the frontend
        if isinstance(pdf_content, str) and pdf_content.startswith("data:application/pdf;base64,"):
            # Extract the base64 data part
            base64_data = pdf_content.split(',')[1]
            # Decode base64 to bytes
            pdf_bytes = base64.b64decode(base64_data)
            # Process the bytes
            return await self.processor.extract(BytesIO(pdf_bytes))

        return await self.processor.extract(pdf_content)


class AudioProcessorTool(AgentTool):
    """Tool for processing audio files and extracting content through transcription"""

    def __init__(self):
        super().__init__(
            name="audio_processor",
            description="Transcribes audio content to text"
        )
        self.processor = AudioProcessor()

    async def execute(self, audio_content: Union[str, bytes, BinaryIO], **kwargs) -> Dict[str, Any]:
        """Transcribe audio content

        Args:
            audio_content: Either a file path, base64-encoded string, or file-like object
        """
        logger.info(f"Processing audio content")

        # Handle base64-encoded content from the frontend
        if isinstance(audio_content, str) and audio_content.startswith("data:audio"):
            # Process directly as base64
            return await self.processor.extract(audio_content)
        elif hasattr(audio_content, 'read'):
            # Already a file-like object
            return await self.processor.extract(audio_content)

        return await self.processor.extract(audio_content)


class TextProcessorTool(AgentTool):
    """Tool for processing plain text content"""

    def __init__(self):
        super().__init__(
            name="text_processor",
            description="Processes plain text content"
        )
        self.processor = TextProcessor()

    async def execute(self, text_content: str, metadata: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Process plain text content

        Args:
            text_content: The text to process
            metadata: Optional metadata about the text
        """
        logger.info(f"Processing text content")
        return await self.processor.extract(text_content, metadata)


class SocialMediaProcessorTool(AgentTool):
    """Tool for processing social media content"""

    def __init__(self):
        super().__init__(
            name="social_processor",
            description="Processes social media content (Twitter/X, LinkedIn, Reddit, etc.)"
        )
        self.processor = SocialMediaProcessor()

    async def execute(self, social_url: str, **kwargs) -> Dict[str, Any]:
        """Process social media content

        Args:
            social_url: URL of social media post or content ID
        """
        logger.info(f"Processing social media content: {social_url}")
        return await self.processor.extract(social_url)


class SummarizerTool(AgentTool):
    """Tool for generating summaries using LLMs"""
    
    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="summarizer",
            description="Generates summaries of content"
        )
        self.model_router = model_router
    
    async def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        """Summarize content using LLM"""
        max_length = kwargs.get("max_length", 500)
        provider = kwargs.get("provider", None)
        
        # Check if text is too short to summarize
        if len(text) < 100:
            logger.info("Text too short for summarization, returning as is")
            return {
                "status": "success",
                "result": text,
                "provider": "direct",
                "model": "none"
            }
        
        # Prepare the content for the model router
        content = {"text": text}
        requirements = {
            "max_tokens": max_length,
            "temperature": 0.0
        }
        
        # Add provider preference if specified
        if provider:
            requirements["provider"] = provider
        
        try:
            # Use the model router to summarize the content
            logger.info(f"Generating summary with LLM (provider preference: {provider})")
            result = await self.model_router.route_request("summarize", content, requirements)
            logger.info(f"Summary generation result: {result.get('status')} with provider {result.get('provider')}")
            return result
        except Exception as e:
            logger.error(f"Error in SummarizerTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating summary: {str(e)}"
            }


class EntityExtractorTool(AgentTool):
    """Tool for extracting entities from content"""
    
    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="entity_extractor",
            description="Extracts entities from content"
        )
        self.model_router = model_router
    
    async def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        """Extract entities from content using LLM"""
        provider = kwargs.get("provider", None)
        
        # Prepare the content for the model router
        content = {"text": text}
        requirements = {
            "max_tokens": 500,
            "temperature": 0.0
        }
        
        # Add provider preference if specified
        if provider:
            requirements["provider"] = provider
        
        try:
            # Use the model router to extract entities
            logger.info(f"Extracting entities with LLM (provider preference: {provider})")
            result = await self.model_router.route_request("extract_entities", content, requirements)
            logger.info(f"Entity extraction result: {result.get('status')} with provider {result.get('provider')}")
            return result
        except Exception as e:
            logger.error(f"Error in EntityExtractorTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting entities: {str(e)}"
            }


class TaggerTool(AgentTool):
    """Tool for generating tags for content"""
    
    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="tagger",
            description="Generates tags for content"
        )
        self.model_router = model_router
    
    async def execute(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate tags for content using LLM"""
        provider = kwargs.get("provider", None)
        
        # Prepare the content for the model router
        content = {"text": text}
        requirements = {
            "max_tokens": 100,
            "temperature": 0.0
        }
        
        # Add provider preference if specified
        if provider:
            requirements["provider"] = provider
        
        try:
            # Use the model router to generate tags
            logger.info(f"Generating tags with LLM (provider preference: {provider})")
            result = await self.model_router.route_request("tag_content", content, requirements)
            logger.info(f"Tag generation result: {result.get('status')} with provider {result.get('provider')}")
            return result
        except Exception as e:
            logger.error(f"Error in TaggerTool: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating tags: {str(e)}"
            }


class ContentMindAgent(BluelabelAgent):
    """Agent for processing and organizing content"""

    def __init__(self, config: Dict[str, Any], model_router: ModelRouter):
        self.model_router = model_router
        super().__init__(config)

    def _parse_entity_text(self, text: str) -> Dict[str, List[str]]:
        """Parse entity text from LLM output when it's not valid JSON

        Tries to handle structured text like:
        People: Alice, Bob
        Organizations: Acme Inc., XYZ Corp.

        Returns:
            Dict with entity categories as keys and lists of entities as values
        """
        result = {}

        # Handle case with no content
        if not text or text.strip() == "":
            return {}

        # First, see if the text has category headings
        lines = text.strip().split('\n')
        current_category = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a category line (ends with a colon)
            if ":" in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    category = parts[0].strip()
                    items_text = parts[1].strip()

                    # If category is valid and has content
                    if category and items_text:
                        # Split by commas, then clean up each item
                        items = [item.strip().rstrip('.') for item in items_text.split(',')]
                        items = [item for item in items if item]  # Filter out empty items

                        if items:
                            result[category] = items

                    # If only the category is on this line, remember it for the next line
                    elif category and not items_text:
                        current_category = category

            # This line continues the previous category
            elif current_category:
                items = [item.strip().rstrip('.') for item in line.split(',')]
                items = [item for item in items if item]  # Filter out empty items

                if items:
                    if current_category in result:
                        result[current_category].extend(items)
                    else:
                        result[current_category] = items

        # If we found at least one valid category, return the result
        if result:
            return result

        # If no structured format was detected, try to extract entities by splitting sentences
        sentences = text.split('.')
        return {"entities": [sentence.strip() for sentence in sentences if sentence.strip()]}        

    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        return [
            URLProcessorTool(),
            PDFProcessorTool(),
            AudioProcessorTool(),
            TextProcessorTool(),
            SocialMediaProcessorTool(),
            SummarizerTool(self.model_router),
            EntityExtractorTool(self.model_router),
            TaggerTool(self.model_router)
        ]

    def _register_components(self) -> Dict[str, str]:
        """Register MCP components for ContentMind agent tasks"""
        return {
            "summarize_content": "agent_contentmind_summarize",
            "extract_entities": "agent_contentmind_extract_entities",
            "tag_content": "agent_contentmind_tag_content",
            "process_url": "agent_contentmind_process_url",
            "process_pdf": "agent_contentmind_process_pdf",
            "process_audio": "agent_contentmind_process_audio",
            "process_text": "agent_contentmind_process_text",
            "process_social": "agent_contentmind_process_social"
        }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process content with ContentMind agent"""
        content_type = request.get("content_type")
        content = request.get("content")
        
        # Get provider preferences
        provider_preferences = request.get("provider_preferences", {})
        summary_provider = provider_preferences.get("summary", None)
        entity_provider = provider_preferences.get("entity_extraction", None)
        tag_provider = provider_preferences.get("tagging", None)
        
        logger.info(f"Processing content type: {content_type}")
        logger.info(f"Provider preferences: {provider_preferences}")
        
        if not content_type or not content:
            return {
                "status": "error",
                "message": "Missing content_type or content in request"
            }
        
        # Process content based on content type
        extracted = None

        if content_type == "url":
            # Process URL content
            url_tool = next((t for t in self.tools if t.name == "url_processor"), None)
            if not url_tool:
                return {"status": "error", "message": "URL processor tool not available"}

            extracted = await url_tool.execute(url=content)

        elif content_type == "pdf":
            # Process PDF content
            pdf_tool = next((t for t in self.tools if t.name == "pdf_processor"), None)
            if not pdf_tool:
                return {"status": "error", "message": "PDF processor tool not available"}

            extracted = await pdf_tool.execute(pdf_content=content)

        elif content_type == "audio":
            # Process audio content
            audio_tool = next((t for t in self.tools if t.name == "audio_processor"), None)
            if not audio_tool:
                return {"status": "error", "message": "Audio processor tool not available"}

            extracted = await audio_tool.execute(audio_content=content)

        elif content_type == "text":
            # Process text content
            text_tool = next((t for t in self.tools if t.name == "text_processor"), None)
            if not text_tool:
                return {"status": "error", "message": "Text processor tool not available"}

            # Prepare metadata if available
            metadata = request.get("metadata", {})

            extracted = await text_tool.execute(text_content=content, metadata=metadata)

        elif content_type == "social":
            # Process social media content
            social_tool = next((t for t in self.tools if t.name == "social_processor"), None)
            if not social_tool:
                return {"status": "error", "message": "Social media processor tool not available"}

            # Check if this is a thread by looking for multiple URLs
            is_thread = "\n" in content and len([u for u in content.split("\n") if u.strip()]) > 1

            # Get metadata if provided
            metadata = request.get("metadata", {})
            if is_thread:
                # Set thread flag for display purposes
                if not metadata:
                    metadata = {}
                metadata["is_thread"] = True

            extracted = await social_tool.execute(social_url=content)

        # Stop here if extraction failed or content type not supported
        if not extracted or extracted.get("status") != "success":
            if extracted:
                return extracted  # Return the specific error
            return {"status": "error", "message": f"Content type '{content_type}' not yet implemented"}

        logger.info(f"Content extraction result status: {extracted.get('status')}")
        logger.info(f"Extracted text length: {len(extracted.get('text', ''))}")
            
        # Step 2: Generate a better summary with LLM
        summary_result = None
        summary = extracted.get("summary", "No summary available")
        summarizer_tool = next((t for t in self.tools if t.name == "summarizer"), None)
        
        logger.info(f"Found summarizer tool: {summarizer_tool is not None}")
        
        if summarizer_tool and extracted.get("text"):
            summary_result = await summarizer_tool.execute(
                text=extracted.get("text"),
                provider=summary_provider
            )
            if summary_result.get("status") == "success":
                summary = summary_result.get("result", "No summary available")
                logger.info(f"Summary result status: {summary_result.get('status')}")
                logger.info(f"Summary result provider: {summary_result.get('provider')}")
                logger.info(f"Summary result model: {summary_result.get('model')}")
            else:
                logger.warning(f"Summary generation failed: {summary_result.get('message')}")
        
        # Step 3: Extract entities (if text is available)
        entities = {}
        entity_result = None
        entity_tool = next((t for t in self.tools if t.name == "entity_extractor"), None)
        if entity_tool and extracted.get("text"):
            entity_result = await entity_tool.execute(
                text=extracted.get("text"),
                provider=entity_provider
            )
            if entity_result.get("status") == "success":
                try:
                    # The result might be a JSON string or already parsed
                    entity_text = entity_result.get("result", "{}")
                    if isinstance(entity_text, str):
                        # Try to clean up the string before parsing
                        entity_text = entity_text.strip()
                        # Make sure it's not just plain text
                        if entity_text.startswith("{") and entity_text.endswith("}"):
                            try:
                                entities = json.loads(entity_text)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse entity result as JSON: {str(e)}")
                                # Try to clean up common issues
                                # Replace single quotes with double quotes
                                entity_text = entity_text.replace("'", "\"")
                                # Try parsing again
                                try:
                                    entities = json.loads(entity_text)
                                except json.JSONDecodeError:
                                    # Last resort: create a formatted entities dict
                                    logger.warning("Failed to parse entity result as JSON after cleanup")
                                    entities = {"error": "Failed to parse entities", "extracted_text": entity_text}
                        else:
                            # If it's not JSON at all, try to parse it as a structured text
                            logger.info("Entity result doesn't appear to be JSON, trying to parse structured text")
                            parsed_entities = self._parse_entity_text(entity_text)
                            if parsed_entities:
                                entities = parsed_entities
                            else:
                                entities = {"unstructured": entity_text.split("\n")}
                    else:
                        entities = entity_text
                except Exception as e:
                    logger.error(f"Error processing entity result: {str(e)}")
                    entities = {"error": str(e)}
        
        # Step 4: Generate tags
        tags = []
        tag_result = None
        tagger_tool = next((t for t in self.tools if t.name == "tagger"), None)
        if tagger_tool and extracted.get("text"):
            tag_result = await tagger_tool.execute(
                text=extracted.get("text"),
                provider=tag_provider
            )
            if tag_result.get("status") == "success":
                tags_text = tag_result.get("result", "")
                # Split by comma and clean up
                tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        
        # Prepare source information based on content type
        source_info = content
        if content_type == "pdf":
            source_info = "PDF Document"
            if isinstance(content, str) and not content.startswith("data:"):
                # If it's a filepath
                source_info = content
        elif content_type == "audio":
            source_info = "Audio Recording"
            if isinstance(content, str) and not content.startswith("data:"):
                # If it's a filepath
                source_info = content
        elif content_type == "text":
            source_info = "Text Note"
            # If we have source info in the metadata, use that
            metadata = request.get("metadata", {})
            if metadata.get("source"):
                source_info = metadata.get("source")

        # Return the processed content
        return {
            "status": "success",
            "content_type": content_type,
            "original_content": source_info,
            "processed_content": {
                "title": extracted.get("title", "Untitled"),
                "summary": summary,
                "author": extracted.get("author"),
                "published_date": extracted.get("published_date") or extracted.get("creation_date"),
                "source": source_info,
                "page_count": extracted.get("page_count"),  # Only for PDFs
                "duration": extracted.get("duration"),      # Only for audio
                "extracted_at": extracted.get("extracted_at"),
                "entities": entities,
                "tags": tags
            },
            "providers_used": {
                "summary": summary_result.get("provider") if summary_result and summary_result.get("status") == "success" else None,
                "entity_extraction": entity_result.get("provider") if entity_result and entity_result.get("status") == "success" else None,
                "tagging": tag_result.get("provider") if tag_result and tag_result.get("status") == "success" else None,
            }
        }