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
    
    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        return [
            URLProcessorTool(),
            PDFProcessorTool(),
            AudioProcessorTool(),
            TextProcessorTool(),
            SummarizerTool(self.model_router),
            EntityExtractorTool(self.model_router),
            TaggerTool(self.model_router)
        ]
    
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
                        try:
                            entities = json.loads(entity_text)
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse entity result as JSON")
                            entities = {"error": "Failed to parse entities", "raw": entity_text}
                    else:
                        entities = entity_text
                except Exception as e:
                    logger.error(f"Error processing entity result: {str(e)}")
                    entities = {}
        
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