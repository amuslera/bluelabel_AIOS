# app/agents/gateway/agent.py
from typing import Dict, Any, List, Optional
import logging
import json
import os
import base64
import traceback
from datetime import datetime

from app.agents.base.agent import BluelabelAgent, AgentTool
from app.core.model_router.router import ModelRouter
from app.core.registry.agent_registry import get_agent_registry

# Configure logging
logger = logging.getLogger(__name__)

class EmailProcessingTool(AgentTool):
    """Tool for processing content from emails"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="email_processor",
            description="Processes content from emails and routes to appropriate agents"
        )
        self.model_router = model_router

    async def execute(self, email_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process content from an email and route to appropriate agent"""
        try:
            logger.info(f"Processing email with subject: {email_data.get('subject', 'Unknown')}")
            
            # Extract content from email
            content = await self._extract_content(email_data)
            if not content:
                logger.warning("No processable content found in email")
                return {
                    "status": "error",
                    "message": "No processable content found in email"
                }
            
            # Determine content type
            content_type = self._determine_content_type(content, email_data)
            
            # Determine target agent
            target_agent_id = self._determine_target_agent(content_type, email_data)
            
            # Package the request for the target agent
            agent_request = {
                "content_type": content_type,
                "content": content,
                "metadata": {
                    "source": "email",
                    "sender": email_data.get("sender", "Unknown"),
                    "subject": email_data.get("subject", "No subject"),
                    "date": email_data.get("date", datetime.now().isoformat()),
                    "gateway_agent": "gateway",
                    "original_email": email_data.get("message_id", "Unknown")
                }
            }
            
            # Get agent registry
            agent_registry = get_agent_registry()
            
            # Get target agent
            target_agent = agent_registry.get_agent(target_agent_id)
            if not target_agent:
                logger.info(f"Target agent {target_agent_id} not instantiated, creating...")
                target_agent = agent_registry.create_agent(target_agent_id, self.model_router)
            
            if not target_agent:
                logger.error(f"Failed to get or create agent {target_agent_id}")
                return {
                    "status": "error",
                    "message": f"Failed to route to agent {target_agent_id}"
                }
            
            # Process with target agent
            logger.info(f"Routing content to {target_agent_id} agent")
            result = await target_agent.process(agent_request)
            
            return {
                "status": "success",
                "original_email": email_data,
                "processed_by": target_agent_id,
                "content_type": content_type,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in EmailProcessingTool: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error processing email: {str(e)}"
            }
    
    async def _extract_content(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Extract content from email data"""
        # First, check for attachments
        attachments = email_data.get("attachments", [])
        if attachments:
            for attachment in attachments:
                # Check if it's a PDF
                if attachment.get("mime_type") == "application/pdf":
                    # Return as data URL
                    b64_content = attachment.get("content", "")
                    return f"data:application/pdf;base64,{b64_content}"
                
                # Check if it's an audio file
                if attachment.get("mime_type", "").startswith("audio/"):
                    mime_type = attachment.get("mime_type", "audio/mpeg")
                    b64_content = attachment.get("content", "")
                    return f"data:{mime_type};base64,{b64_content}"
        
        # Check for links in plain text or HTML content
        text_content = email_data.get("plain_text", "")
        html_content = email_data.get("html_content", "")
        
        # Extract URL from text content
        import re
        url_pattern = r'https?://[^\s]+'
        
        # Try plain text first
        if text_content:
            urls = re.findall(url_pattern, text_content)
            if urls:
                # Return the first URL (we could be more sophisticated here)
                return urls[0]
        
        # Try HTML content
        if html_content:
            urls = re.findall(url_pattern, html_content)
            if urls:
                return urls[0]
        
        # If we found neither attachments nor URLs, return the text content
        if text_content:
            return text_content
        
        # If all else fails, use HTML content
        if html_content:
            return html_content
        
        # No processable content found
        return None
    
    def _determine_content_type(self, content: str, email_data: Dict[str, Any]) -> str:
        """Determine the content type based on the extracted content"""
        # Check if it's a data URL
        if content.startswith("data:"):
            # Check the MIME type
            if "application/pdf" in content:
                return "pdf"
            if "audio/" in content:
                return "audio"
        
        # Check if it's a URL
        if content.startswith("http"):
            return "url"
        
        # Check if it seems like a research query
        subject = email_data.get("subject", "").lower()
        if any(term in subject for term in ["research", "query", "question", "investigate"]):
            return "query"
        
        # Default to text
        return "text"
    
    def _determine_target_agent(self, content_type: str, email_data: Dict[str, Any]) -> str:
        """Determine which agent should process this content"""
        # Check for explicit agent routing in the subject
        subject = email_data.get("subject", "").lower()
        
        # Look for explicit agent mentions
        if "researcher" in subject or "research" in subject:
            return "researcher"
        
        # Route based on content type
        if content_type == "query":
            return "researcher"
        
        # Default to ContentMind for most content types
        return "contentmind"

class WhatsAppProcessingTool(AgentTool):
    """Tool for processing content from WhatsApp"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="whatsapp_processor",
            description="Processes content from WhatsApp messages and routes to appropriate agents"
        )
        self.model_router = model_router

    async def execute(self, message_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process content from a WhatsApp message and route to appropriate agent"""
        try:
            logger.info(f"Processing WhatsApp message from: {message_data.get('from', 'Unknown')}")
            
            # Extract content from message
            content = await self._extract_content(message_data)
            if not content:
                logger.warning("No processable content found in WhatsApp message")
                return {
                    "status": "error",
                    "message": "No processable content found in WhatsApp message"
                }
            
            # Determine content type
            content_type = self._determine_content_type(content, message_data)
            
            # Determine target agent
            target_agent_id = self._determine_target_agent(content_type, message_data)
            
            # Package the request for the target agent
            agent_request = {
                "content_type": content_type,
                "content": content,
                "metadata": {
                    "source": "whatsapp",
                    "sender": message_data.get("from", "Unknown"),
                    "date": message_data.get("timestamp", datetime.now().isoformat()),
                    "gateway_agent": "gateway",
                    "original_message_id": message_data.get("message_id", "Unknown")
                }
            }
            
            # Get agent registry
            agent_registry = get_agent_registry()
            
            # Get target agent
            target_agent = agent_registry.get_agent(target_agent_id)
            if not target_agent:
                logger.info(f"Target agent {target_agent_id} not instantiated, creating...")
                target_agent = agent_registry.create_agent(target_agent_id, self.model_router)
            
            if not target_agent:
                logger.error(f"Failed to get or create agent {target_agent_id}")
                return {
                    "status": "error",
                    "message": f"Failed to route to agent {target_agent_id}"
                }
            
            # Process with target agent
            logger.info(f"Routing content to {target_agent_id} agent")
            result = await target_agent.process(agent_request)
            
            return {
                "status": "success",
                "original_message": message_data,
                "processed_by": target_agent_id,
                "content_type": content_type,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in WhatsAppProcessingTool: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": f"Error processing WhatsApp message: {str(e)}"
            }
    
    async def _extract_content(self, message_data: Dict[str, Any]) -> Optional[str]:
        """Extract content from WhatsApp message data"""
        # First, check for media
        if message_data.get("media_url"):
            media_url = message_data.get("media_url")
            media_type = message_data.get("media_type", "")
            
            # Return as URL for further processing
            return media_url
        
        # Check for text content
        text_content = message_data.get("text", "")
        
        # Extract URL from text content
        import re
        url_pattern = r'https?://[^\s]+'
        
        if text_content:
            urls = re.findall(url_pattern, text_content)
            if urls:
                # Return the first URL
                return urls[0]
            
            # If no URL, return the text content
            return text_content
        
        # No processable content found
        return None
    
    def _determine_content_type(self, content: str, message_data: Dict[str, Any]) -> str:
        """Determine the content type based on the extracted content"""
        # Check the media type if available
        media_type = message_data.get("media_type", "")
        
        if media_type.startswith("audio/"):
            return "audio"
        
        if media_type == "application/pdf":
            return "pdf"
        
        # Check if it's a URL
        if content.startswith("http"):
            return "url"
        
        # Check if it seems like a research query
        text = message_data.get("text", "").lower()
        if text.startswith("research:") or text.startswith("query:") or "?" in text:
            return "query"
        
        # Default to text
        return "text"
    
    def _determine_target_agent(self, content_type: str, message_data: Dict[str, Any]) -> str:
        """Determine which agent should process this content"""
        # Check for explicit agent routing in the message
        text = message_data.get("text", "").lower()
        
        # Look for explicit agent mentions
        if "researcher" in text or text.startswith("research:"):
            return "researcher"
        
        # Route based on content type
        if content_type == "query":
            return "researcher"
        
        # Default to ContentMind for most content types
        return "contentmind"

class GatewayAgent(BluelabelAgent):
    """Agent for routing content from various sources to appropriate processing agents"""

    def __init__(self, config: Dict[str, Any], model_router: ModelRouter):
        self.model_router = model_router
        super().__init__(config)
        logger.info("Gateway Agent initialized")

    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        return [
            EmailProcessingTool(self.model_router),
            WhatsAppProcessingTool(self.model_router)
        ]

    def _register_components(self) -> Dict[str, str]:
        """Register MCP components for Gateway agent tasks"""
        return {
            "classify_content": "gateway_classify_content",
            "route_content": "gateway_route_content"
        }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming request and route to appropriate agent"""
        # Determine the source of the content
        source = request.get("source", "unknown")
        
        if source == "email":
            # Process email content
            email_tool = next((t for t in self.tools if t.name == "email_processor"), None)
            if not email_tool:
                return {"status": "error", "message": "Email processing tool not available"}
            
            return await email_tool.execute(request.get("email_data", {}))
        
        elif source == "whatsapp":
            # Process WhatsApp content
            whatsapp_tool = next((t for t in self.tools if t.name == "whatsapp_processor"), None)
            if not whatsapp_tool:
                return {"status": "error", "message": "WhatsApp processing tool not available"}
            
            return await whatsapp_tool.execute(request.get("message_data", {}))
        
        else:
            # Unknown source
            return {
                "status": "error",
                "message": f"Unsupported content source: {source}"
            }
    
    async def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method for processing email content"""
        request = {
            "source": "email",
            "email_data": email_data
        }
        return await self.process(request)
    
    async def process_whatsapp(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method for processing WhatsApp content"""
        request = {
            "source": "whatsapp",
            "message_data": message_data
        }
        return await self.process(request)