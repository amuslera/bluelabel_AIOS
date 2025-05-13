import os
import asyncio
import logging
import tempfile
import json
import base64
import aiohttp
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime
from pydantic import BaseModel

class WhatsAppContent(BaseModel):
    """Represents content extracted from a WhatsApp message"""
    wa_id: str
    message_id: str
    message_type: str  # text, image, video, audio, document
    timestamp: str
    text: Optional[str] = None
    content_type: Optional[str] = None  # MIME type or general type (pdf, audio, etc.)
    content: Optional[bytes] = None  # Binary content for files
    content_filename: Optional[str] = None
    metadata: Dict[str, Any] = {}

class WhatsAppProcessor:
    """Process WhatsApp messages for AIOS"""

    def __init__(self):
        """Initialize WhatsApp processor"""
        self.logger = logging.getLogger(__name__)
        self.whatsapp = None  # Will be set with the WhatsApp client implementation

    async def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a WhatsApp webhook event

        Args:
            event_data: Webhook event data from Meta API

        Returns:
            Processing result
        """
        try:
            # Check if this is a valid WhatsApp webhook event
            if "object" not in event_data:
                return {"status": "error", "message": "Invalid webhook event"}

            # Meta sends different types of events, we're only interested in WhatsApp messages
            if event_data["object"] != "whatsapp_business_account":
                return {"status": "ignored", "message": f"Ignoring non-WhatsApp event: {event_data['object']}"}

            # Process all entries in the webhook event
            processed_messages = 0
            for entry in event_data.get("entry", []):
                # Each entry can have multiple changes (e.g., multiple messages)
                for change in entry.get("changes", []):
                    value = change.get("value", {})

                    # Check if this is a message event
                    if "messages" in value:
                        # Process each message in the event
                        for message in value["messages"]:
                            # Extract basic info
                            from_number = message.get("from", "")

                            # Process the message
                            result = await self.process_message({
                                "from": from_number,
                                "id": message.get("id", ""),
                                "timestamp": message.get("timestamp", ""),
                                **{message.get("type", "text"): message}
                            })

                            if result.get("status") == "success":
                                processed_messages += 1

            return {
                "status": "success",
                "message": f"Processed {processed_messages} messages",
                "processed_count": processed_messages
            }
        except Exception as e:
            self.logger.error(f"Error processing webhook event: {str(e)}")
            return {"status": "error", "message": f"Failed to process webhook event: {str(e)}"}

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send a WhatsApp message to a recipient

        Args:
            recipient: WhatsApp ID (phone number)
            message: Message text

        Returns:
            Result of the send operation
        """
        from app.services.gateway.whatsapp_settings import whatsapp_settings

        try:
            # Check if WhatsApp is enabled
            if not whatsapp_settings.WHATSAPP_ENABLED:
                return {"status": "error", "message": "WhatsApp integration is not enabled"}

            # Check if we have the necessary credentials
            if not whatsapp_settings.WHATSAPP_API_TOKEN or not whatsapp_settings.WHATSAPP_PHONE_ID:
                return {"status": "error", "message": "Missing WhatsApp API credentials"}

            # Prepare the API request
            url = f"https://graph.facebook.com/v18.0/{whatsapp_settings.WHATSAPP_PHONE_ID}/messages"
            headers = {
                "Authorization": f"Bearer {whatsapp_settings.WHATSAPP_API_TOKEN}",
                "Content-Type": "application/json"
            }

            # Construct the message data
            data = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {
                    "body": message
                }
            }

            # Send the message
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"WhatsApp API error: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "message": f"WhatsApp API error: {response.status}"
                        }

                    result = await response.json()

                    # Check if the message was sent successfully
                    if "messages" in result and len(result["messages"]) > 0:
                        message_id = result["messages"][0].get("id", "unknown")
                        return {
                            "status": "success",
                            "message": "WhatsApp message sent successfully",
                            "message_id": message_id
                        }
                    else:
                        return {
                            "status": "error",
                            "message": "WhatsApp API returned an unexpected response",
                            "api_response": result
                        }
        except aiohttp.ClientError as e:
            self.logger.error(f"WhatsApp API client error: {str(e)}")
            return {"status": "error", "message": f"WhatsApp API client error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {"status": "error", "message": f"Failed to send WhatsApp message: {str(e)}"}
    
    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a WhatsApp message
        
        Args:
            message_data: Raw WhatsApp message data
            
        Returns:
            Processing result
        """
        try:
            # Extract content from the message
            whatsapp_content = await self._extract_content(message_data)
            
            # Skip if content extraction failed
            if not whatsapp_content:
                return {
                    "status": "error",
                    "message": "Failed to extract content from WhatsApp message"
                }
            
            # Process the extracted content
            result = await self._process_content_for_aios(whatsapp_content)
            
            # Send a notification back to the user if configured
            if result.get("status") == "success":
                await self._send_processing_notification(whatsapp_content, result)
            
            return result
        except Exception as e:
            self.logger.error(f"Error processing WhatsApp message: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process WhatsApp message: {str(e)}"
            }
    
    async def _extract_content(self, message_data: Dict[str, Any]) -> Optional[WhatsAppContent]:
        """Extract content from a WhatsApp message
        
        Args:
            message_data: Raw WhatsApp message data
            
        Returns:
            Extracted WhatsApp content
        """
        try:
            # Extract basic message metadata
            wa_id = message_data.get("from", "unknown")
            message_id = message_data.get("id", "unknown")
            timestamp = message_data.get("timestamp", datetime.now().isoformat())
            
            # Determine message type and extract content
            if "text" in message_data:
                # Text message
                return WhatsAppContent(
                    wa_id=wa_id,
                    message_id=message_id,
                    message_type="text",
                    timestamp=timestamp,
                    text=message_data["text"].get("body", ""),
                    content_type="text"
                )
            elif "image" in message_data:
                # Image message
                image_data = message_data["image"]
                return WhatsAppContent(
                    wa_id=wa_id,
                    message_id=message_id,
                    message_type="image",
                    timestamp=timestamp,
                    text=image_data.get("caption", ""),
                    content_type="image",
                    content_filename=image_data.get("filename", "image.jpg"),
                    metadata={
                        "mime_type": image_data.get("mime_type", "image/jpeg"),
                        "sha256": image_data.get("sha256", ""),
                        "id": image_data.get("id", "")
                    }
                )
            elif "document" in message_data:
                # Document message (PDF, etc.)
                document_data = message_data["document"]
                mime_type = document_data.get("mime_type", "")
                
                # Determine content type from MIME type
                content_type = "document"
                if mime_type.startswith("application/pdf"):
                    content_type = "pdf"
                
                return WhatsAppContent(
                    wa_id=wa_id,
                    message_id=message_id,
                    message_type="document",
                    timestamp=timestamp,
                    text=document_data.get("caption", ""),
                    content_type=content_type,
                    content_filename=document_data.get("filename", "document"),
                    metadata={
                        "mime_type": mime_type,
                        "sha256": document_data.get("sha256", ""),
                        "id": document_data.get("id", "")
                    }
                )
            elif "audio" in message_data:
                # Audio message
                audio_data = message_data["audio"]
                return WhatsAppContent(
                    wa_id=wa_id,
                    message_id=message_id,
                    message_type="audio",
                    timestamp=timestamp,
                    content_type="audio",
                    content_filename=audio_data.get("filename", "audio"),
                    metadata={
                        "mime_type": audio_data.get("mime_type", "audio/mpeg"),
                        "sha256": audio_data.get("sha256", ""),
                        "id": audio_data.get("id", ""),
                        "voice": audio_data.get("voice", False)
                    }
                )
            else:
                # Unsupported message type
                self.logger.warning(f"Unsupported WhatsApp message type: {message_data}")
                return WhatsAppContent(
                    wa_id=wa_id,
                    message_id=message_id,
                    message_type="unknown",
                    timestamp=timestamp,
                    text="Unsupported message type"
                )
        except Exception as e:
            self.logger.error(f"Error extracting content from WhatsApp message: {str(e)}")
            return None
    
    async def _process_content_for_aios(self, whatsapp_content: WhatsAppContent) -> Dict[str, Any]:
        """Process the extracted content through AIOS
        
        Args:
            whatsapp_content: WhatsApp content to process
            
        Returns:
            Processing result
        """
        try:
            # Prepare content for processing
            content_to_process = ""
            
            if whatsapp_content.message_type == "text":
                # Text content
                content_to_process = whatsapp_content.text
            elif whatsapp_content.content and whatsapp_content.content_type:
                # Process binary content if available
                try:
                    # Write content to a temporary file
                    suffix = os.path.splitext(whatsapp_content.content_filename)[1] if whatsapp_content.content_filename else ""
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                        temp_path = temp_file.name
                        temp_file.write(whatsapp_content.content)
                    
                    # Read the file and convert to base64
                    with open(temp_path, "rb") as file:
                        file_content = file.read()
                    
                    # Create a data URL
                    mime_type = whatsapp_content.metadata.get("mime_type", f"{whatsapp_content.content_type}/{suffix.lstrip('.')}")
                    content_to_process = f"data:{mime_type};base64,{base64.b64encode(file_content).decode('utf-8')}"
                    
                    # Remove the temporary file
                    os.unlink(temp_path)
                except Exception as e:
                    self.logger.error(f"Error processing temp file: {str(e)}")
                    # If there's an error, fall back to text content if available
                    if hasattr(whatsapp_content, 'text'):
                        content_to_process = whatsapp_content.text
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to process media content: {str(e)}"
                        }
            
            # Prepare the message data for the Gateway agent
            message_data = {
                "from": whatsapp_content.wa_id,
                "text": content_to_process if whatsapp_content.message_type == "text" else "",
                "message_id": whatsapp_content.message_id,
                "timestamp": whatsapp_content.timestamp,
                "media_type": whatsapp_content.content_type,
                "media_url": content_to_process if whatsapp_content.content_type in ["pdf", "audio", "image", "video"] else None,
                "filename": whatsapp_content.content_filename,
                "metadata": whatsapp_content.metadata
            }
            
            # Create the API request for the Gateway agent
            gateway_request = {
                "source": "whatsapp",
                "message_data": message_data
            }
            
            # Call the Gateway agent API endpoint
            api_endpoint = "http://localhost:8080/agents/gateway/process"
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_endpoint, json=gateway_request) as response:
                        if response.status != 200:
                            self.logger.error(f"Gateway API returned non-200 status: {response.status}")
                            return {
                                "status": "error",
                                "message": f"Gateway API error: {response.status}"
                            }
                        result = await response.json()
                        
                        # Add some metadata for the reply
                        if not result.get("whatsapp_metadata"):
                            result["whatsapp_metadata"] = {}
                            
                        result["whatsapp_metadata"]["wa_id"] = whatsapp_content.wa_id
                        result["whatsapp_metadata"]["message_id"] = whatsapp_content.message_id
                        result["whatsapp_metadata"]["processed_at"] = datetime.now().isoformat()
                        
                        return result
            except aiohttp.ClientConnectorError as ce:
                self.logger.error(f"Connection error to Gateway API: {str(ce)}")
                return {
                    "status": "error",
                    "message": "Failed to connect to Gateway API service"
                }
            except aiohttp.ClientError as ce:
                self.logger.error(f"Client error with Gateway API: {str(ce)}")
                return {
                    "status": "error",
                    "message": f"API client error: {str(ce)}"
                }
        except Exception as e:
            self.logger.error(f"Error processing content for AIOS: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process content: {str(e)}",
                "whatsapp_metadata": {
                    "wa_id": whatsapp_content.wa_id,
                    "message_id": whatsapp_content.message_id,
                    "processed_at": datetime.now().isoformat()
                }
            }
    
    async def _send_processing_notification(self, whatsapp_content: WhatsAppContent, process_result: Dict[str, Any]) -> None:
        """Send a notification back to the sender with processing results
        
        Args:
            whatsapp_content: Original WhatsApp content
            process_result: Result of content processing
        """
        if not self.whatsapp:
            return
        
        try:
            status = process_result.get("status", "error")
            
            if status == "success":
                # Extract information for a success message
                content_type = process_result.get("content_type", "unknown")
                
                if "storage" in process_result and process_result["storage"].get("stored", False):
                    content_id = process_result["storage"].get("content_id", "unknown")
                    processed_content = process_result.get("processed_content", {})
                    
                    # Construct a success message
                    title = processed_content.get("title", "Untitled")
                    
                    message = f"✅ Successfully processed your {content_type} content!\n\n"
                    message += f"*{title}*\n\n"
                    
                    # Add a summary if available
                    if processed_content.get("summary"):
                        summary = processed_content["summary"]
                        if len(summary) > 150:
                            summary = summary[:147] + "..."
                        message += f"Summary: {summary}\n\n"
                    
                    # Add tags if available
                    if processed_content.get("tags"):
                        tags = ", ".join([f"#{tag}" for tag in processed_content["tags"]])
                        message += f"Tags: {tags}\n\n"
                    
                    # Add info for viewing
                    message += "Your content has been added to the AIOS knowledge repository."
                else:
                    message = "✅ Your message has been processed, but could not be stored in the knowledge repository."
            else:
                # Error message
                error_msg = process_result.get("message", "Unknown error")
                message = f"❌ Sorry, I couldn't process your message: {error_msg}"
            
            # Send the notification
            await self.whatsapp.send_message(whatsapp_content.wa_id, message)
        except Exception as e:
            self.logger.error(f"Error sending processing notification: {str(e)}")
            
    async def simulate_message(self, wa_id: str, text: str) -> Dict[str, Any]:
        """Simulate receiving a WhatsApp message (for testing)
        
        Args:
            wa_id: WhatsApp ID (phone number)
            text: Message text
            
        Returns:
            Processing result
        """
        message_data = {
            "from": wa_id,
            "id": f"test_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "text": {
                "body": text
            }
        }
        
        return await self.process_message(message_data)

# Create a singleton instance
whatsapp_processor = WhatsAppProcessor()