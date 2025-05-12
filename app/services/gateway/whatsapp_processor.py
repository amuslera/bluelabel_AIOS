# app/services/gateway/whatsapp_processor.py
import logging
import os
import tempfile
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import asyncio
import aiohttp
from pydantic import BaseModel

# WhatsApp API client class stub (replaced with direct HTTP requests)
# The wa_me library has compatibility issues, so we'll use direct API calls
class WhatsAppClient:
    """Wrapper for WhatsApp API calls using direct HTTP requests"""

    def __init__(self, token: str, phone_number_id: str):
        self.token = token
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send a text message to a WhatsApp user

        Args:
            recipient: The WhatsApp ID of the recipient
            message: The message content

        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {"error": str(e)}

    async def get_media_url(self, media_id: str) -> Dict[str, Any]:
        """Get the URL for a media item

        Args:
            media_id: The ID of the media

        Returns:
            Media URL response
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://graph.facebook.com/v18.0/{media_id}",
                    headers=self.headers
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting media URL: {str(e)}")
            return {"error": str(e)}

from app.services.gateway.whatsapp_settings import whatsapp_settings

# Configure logging
logger = logging.getLogger(__name__)

class WhatsAppContent(BaseModel):
    """Represents content extracted from a WhatsApp message"""
    wa_id: str  # WhatsApp ID of the sender
    phone_number: str  # Phone number of the sender
    message_id: str  # WhatsApp message ID
    timestamp: str  # Message timestamp
    message_type: str  # Type of message (text, image, document, etc)
    content_type: str  # Type of content (text, url, pdf, audio, etc)
    content: Union[str, bytes, None] = None  # The actual content
    content_filename: Optional[str] = None  # Filename if it's a document
    metadata: Dict[str, Any] = {}  # Additional metadata

class WhatsAppProcessor:
    """Service for processing WhatsApp messages and extracting content for AIOS"""
    
    def __init__(self):
        """Initialize the WhatsApp processor with configuration settings"""
        self.settings = whatsapp_settings
        self.logger = logging.getLogger(__name__)

        # Initialize the WhatsApp API client
        if self.settings.WHATSAPP_API_TOKEN and self.settings.WHATSAPP_PHONE_ID:
            self.whatsapp = WhatsAppClient(
                token=self.settings.WHATSAPP_API_TOKEN,
                phone_number_id=self.settings.WHATSAPP_PHONE_ID
            )
        else:
            self.whatsapp = None
            self.logger.warning("WhatsApp API credentials not configured")
    
    async def process_webhook_event(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook events from WhatsApp
        
        Args:
            body: The webhook event body from WhatsApp
            
        Returns:
            Processing result with status and message count
        """
        if not self.whatsapp:
            return {"status": "error", "message": "WhatsApp API not configured"}
        
        try:
            # Extract messages from the webhook payload
            entry = body.get("entry", [])
            messages_processed = 0
            
            for entry_item in entry:
                changes = entry_item.get("changes", [])
                for change in changes:
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    # Process each message
                    for message_data in messages:
                        # Process the message
                        message_id = message_data.get("id")
                        from_id = value.get("contacts", [{}])[0].get("wa_id") if value.get("contacts") else None
                        
                        if not from_id or not message_id:
                            continue
                        
                        # Check if sender is allowed
                        if self.settings.WHATSAPP_ALLOWED_NUMBERS and from_id not in self.settings.WHATSAPP_ALLOWED_NUMBERS:
                            self.logger.warning(f"Message from unauthorized sender: {from_id}")
                            continue
                        
                        # Extract the message content
                        whatsapp_content = await self._extract_content(message_data, from_id, value)
                        
                        if not whatsapp_content:
                            continue
                        
                        # Process the content
                        process_result = await self._process_content_for_aios(whatsapp_content)
                        
                        # Send a reply if configured
                        if self.settings.WHATSAPP_AUTO_REPLY:
                            await self._send_processing_notification(whatsapp_content, process_result)
                        
                        messages_processed += 1
                        
            return {
                "status": "success",
                "messages_processed": messages_processed
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WhatsApp webhook: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing webhook: {str(e)}"
            }
    
    async def _extract_content(self, message_data: Dict[str, Any], from_id: str, value: Dict[str, Any]) -> Optional[WhatsAppContent]:
        """Extract content from a WhatsApp message
        
        Args:
            message_data: The message data from the webhook
            from_id: The WhatsApp ID of the sender
            value: The value object from the webhook
            
        Returns:
            Extracted WhatsApp content or None if extraction failed
        """
        try:
            message_id = message_data.get("id")
            timestamp = message_data.get("timestamp", str(int(datetime.now().timestamp())))
            
            # Get sender's profile information
            phone_number = from_id  # Default to the WhatsApp ID
            profile_name = None
            
            if value.get("contacts") and len(value["contacts"]) > 0:
                contact = value["contacts"][0]
                profile_name = contact.get("profile", {}).get("name")
            
            # Initialize metadata
            metadata = {
                "source": "whatsapp",
                "sender": from_id,
                "sender_name": profile_name,
                "timestamp": timestamp
            }
            
            # Determine message type and extract content
            message_type = next(iter(message_data.keys() & {"text", "image", "document", "audio", "video", "sticker"}), None)
            
            if not message_type:
                self.logger.warning(f"Unsupported message type for message {message_id}")
                return None
            
            # Process based on message type
            if message_type == "text":
                # Extract text content
                text = message_data.get("text", {}).get("body", "")
                
                # Check if it's a URL
                if text.strip().startswith(("http://", "https://")):
                    return WhatsAppContent(
                        wa_id=from_id,
                        phone_number=phone_number,
                        message_id=message_id,
                        timestamp=timestamp,
                        message_type="text",
                        content_type="url",
                        content=text.strip(),
                        metadata=metadata
                    )
                else:
                    return WhatsAppContent(
                        wa_id=from_id,
                        phone_number=phone_number,
                        message_id=message_id,
                        timestamp=timestamp,
                        message_type="text",
                        content_type="text",
                        content=text,
                        metadata=metadata
                    )
            
            elif message_type == "image":
                # Get the image data
                image_id = message_data.get("image", {}).get("id")
                if not image_id:
                    return None
                
                # Download the media
                media_data = await self._download_media(image_id)
                if not media_data:
                    return None
                
                return WhatsAppContent(
                    wa_id=from_id,
                    phone_number=phone_number,
                    message_id=message_id,
                    timestamp=timestamp,
                    message_type="image",
                    content_type="image",
                    content=media_data,
                    content_filename=f"image_{message_id}.jpg",
                    metadata=metadata
                )
            
            elif message_type == "document":
                # Get the document data
                document = message_data.get("document", {})
                document_id = document.get("id")
                filename = document.get("filename", f"document_{message_id}")
                
                if not document_id:
                    return None
                
                # Download the media
                media_data = await self._download_media(document_id)
                if not media_data:
                    return None
                
                # Determine content type from filename
                if filename.lower().endswith(".pdf"):
                    content_type = "pdf"
                elif filename.lower().endswith((".txt", ".md", ".csv")):
                    content_type = "text"
                else:
                    content_type = "document"
                
                return WhatsAppContent(
                    wa_id=from_id,
                    phone_number=phone_number,
                    message_id=message_id,
                    timestamp=timestamp,
                    message_type="document",
                    content_type=content_type,
                    content=media_data,
                    content_filename=filename,
                    metadata=metadata
                )
            
            elif message_type == "audio":
                # Get the audio data
                audio_id = message_data.get("audio", {}).get("id")
                if not audio_id:
                    return None
                
                # Download the media
                media_data = await self._download_media(audio_id)
                if not media_data:
                    return None
                
                return WhatsAppContent(
                    wa_id=from_id,
                    phone_number=phone_number,
                    message_id=message_id,
                    timestamp=timestamp,
                    message_type="audio",
                    content_type="audio",
                    content=media_data,
                    content_filename=f"audio_{message_id}.mp3",
                    metadata=metadata
                )
            
            elif message_type == "video":
                # Get the video data
                video_id = message_data.get("video", {}).get("id")
                if not video_id:
                    return None
                
                # Download the media
                media_data = await self._download_media(video_id)
                if not media_data:
                    return None
                
                return WhatsAppContent(
                    wa_id=from_id,
                    phone_number=phone_number,
                    message_id=message_id,
                    timestamp=timestamp,
                    message_type="video",
                    content_type="video",
                    content=media_data,
                    content_filename=f"video_{message_id}.mp4",
                    metadata=metadata
                )
            
            elif message_type == "sticker":
                # Stickers are not processed for content
                # but we can acknowledge receipt
                return WhatsAppContent(
                    wa_id=from_id,
                    phone_number=phone_number,
                    message_id=message_id,
                    timestamp=timestamp,
                    message_type="sticker",
                    content_type="image",
                    content=None,
                    metadata=metadata
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting WhatsApp content: {str(e)}")
            return None
    
    async def _download_media(self, media_id: str) -> Optional[bytes]:
        """Download media from WhatsApp
        
        Args:
            media_id: The ID of the media to download
            
        Returns:
            The media data as bytes or None if download failed
        """
        if not self.whatsapp:
            return None
        
        try:
            # Use the WhatsApp API to get media URL
            media_url_response = await self.whatsapp.get_media_url(media_id)
            
            if not media_url_response or not media_url_response.get("url"):
                self.logger.error(f"Failed to get media URL for media ID: {media_id}")
                return None
            
            media_url = media_url_response["url"]
            
            # Download the media file
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    media_url,
                    headers={"Authorization": f"Bearer {self.settings.WHATSAPP_API_TOKEN}"}
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to download media for ID {media_id}: Status {response.status}")
                        return None
                    
                    return await response.read()
                    
        except Exception as e:
            self.logger.error(f"Error downloading media {media_id}: {str(e)}")
            return None
    
    async def _process_content_for_aios(self, whatsapp_content: WhatsAppContent) -> Dict[str, Any]:
        """Process the extracted content through the Gateway agent

        Args:
            whatsapp_content: Extracted WhatsApp content

        Returns:
            Processing result
        """
        try:
            # Determine content to process
            content_to_process = whatsapp_content.content

            # If it's bytes data (like for PDFs or audio), save to a temp file and encode as base64
            if isinstance(content_to_process, bytes):
                # Create a temporary file
                suffix = ""
                if whatsapp_content.content_filename:
                    suffix = os.path.splitext(whatsapp_content.content_filename)[1]

                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    temp_file.write(content_to_process)
                    temp_path = temp_file.name

                try:
                    # Read the file and encode as base64
                    with open(temp_path, "rb") as file:
                        file_content = file.read()
                        mime_prefix = "application/octet-stream"

                        # Determine mime type
                        if whatsapp_content.content_type == "pdf":
                            mime_prefix = "application/pdf"
                        elif whatsapp_content.content_type == "audio":
                            mime_prefix = "audio/mpeg"
                        elif whatsapp_content.content_type == "image":
                            mime_prefix = "image/jpeg"
                        elif whatsapp_content.content_type == "video":
                            mime_prefix = "video/mp4"

                        content_to_process = f"data:{mime_prefix};base64,{base64.b64encode(file_content).decode('utf-8')}"

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

            async with aiohttp.ClientSession() as session:
                async with session.post(api_endpoint, json=gateway_request) as response:
                    result = await response.json()

                    # Add some metadata for the reply
                    if not result.get("whatsapp_metadata"):
                        result["whatsapp_metadata"] = {}

                    result["whatsapp_metadata"]["wa_id"] = whatsapp_content.wa_id
                    result["whatsapp_metadata"]["message_id"] = whatsapp_content.message_id
                    result["whatsapp_metadata"]["processed_at"] = datetime.now().isoformat()

                    return result
                
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
                    
                    title = processed_content.get("title", "Untitled")
                    summary = processed_content.get("summary", "No summary available")
                    
                    # Format the success message
                    success_message = f"""✅ Content Processing Completed

*Title:* {title}
*Type:* {content_type}
*ID:* {content_id}

*Summary:*
{summary}

_This is an automated response from the Bluelabel AIOS system._"""
                    
                    # Send the message
                    await self.whatsapp.send_message(
                        whatsapp_content.wa_id,
                        success_message
                    )
                else:
                    # Processing succeeded but content was not stored
                    error_reason = process_result.get("storage", {}).get("error", "Unknown error")
                    partial_success_message = f"""⚠️ Content Processing Partial Success

Your content was processed but could not be stored.

*Reason:* {error_reason}

_This is an automated response from the Bluelabel AIOS system._"""
                    
                    # Send the message
                    await self.whatsapp.send_message(
                        whatsapp_content.wa_id,
                        partial_success_message
                    )
            else:
                # Error message
                error_message = process_result.get("message", "Unknown error")
                
                error_notification = f"""❌ Content Processing Failed

There was an error processing your content.

*Error:* {error_message}

_This is an automated response from the Bluelabel AIOS system._"""
                
                # Send the message
                await self.whatsapp.send_message(
                    whatsapp_content.wa_id,
                    error_notification
                )
            
            self.logger.info(f"Sent processing notification to WhatsApp ID: {whatsapp_content.wa_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp notification: {str(e)}")
    
    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send a WhatsApp message
        
        Args:
            recipient: The recipient's WhatsApp ID or phone number
            message: The message text to send
            
        Returns:
            Result of the send operation
        """
        if not self.whatsapp:
            return {"status": "error", "message": "WhatsApp API not configured"}
        
        try:
            # Send the message
            result = await self.whatsapp.send_message(recipient, message)
            
            return {
                "status": "success",
                "message_id": result.get("messages", [{}])[0].get("id") if result.get("messages") else None
            }
        except Exception as e:
            self.logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send message: {str(e)}"
            }