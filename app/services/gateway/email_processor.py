# app/services/gateway/email_processor.py
import asyncio
import email
import imaplib
import logging
import os
import tempfile
import time
from datetime import datetime
from email.message import Message
from typing import Dict, Any, List, Optional, Tuple, BinaryIO, Union
import base64

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr, BaseModel

from app.services.gateway.email_settings import email_settings

# Configure logging
logger = logging.getLogger(__name__)

class EmailContent(BaseModel):
    """Represents content extracted from an email"""
    subject: str
    sender: str
    recipient: str
    date: str
    body_text: str
    body_html: Optional[str] = None
    content_type: str
    content: Union[str, bytes, None] = None
    content_filename: Optional[str] = None
    original_message_id: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

class EmailProcessor:
    """Service for processing emails and extracting content for AIOS"""
    
    def __init__(self):
        """Initialize the email processor with configuration settings"""
        self.settings = email_settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize the SMTP configuration for sending status emails
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=self.settings.SMTP_USERNAME,
            MAIL_PASSWORD=self.settings.SMTP_PASSWORD,
            MAIL_FROM=self.settings.MAIL_FROM,
            MAIL_PORT=self.settings.SMTP_PORT,
            MAIL_SERVER=self.settings.SMTP_SERVER,
            MAIL_FROM_NAME=self.settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=self.settings.SMTP_USE_TLS,
            MAIL_SSL_TLS=self.settings.SMTP_USE_SSL,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        # Check if required folders exist, create them if they don't
        self._setup_imap_folders()
        
    def _setup_imap_folders(self) -> None:
        """Check if required folders exist, create them if they don't"""
        try:
            mail = imaplib.IMAP4_SSL(self.settings.MAIL_SERVER, self.settings.MAIL_PORT)
            mail.login(self.settings.MAIL_USERNAME, self.settings.MAIL_PASSWORD)
            
            # Check for "Processed" folder
            status, folders = mail.list("", self.settings.MAIL_PROCESSED_FOLDER)
            if status != "OK" or not folders[0]:
                mail.create(self.settings.MAIL_PROCESSED_FOLDER)
                logger.info(f"Created IMAP folder: {self.settings.MAIL_PROCESSED_FOLDER}")
            
            # Check for "Errors" folder
            status, folders = mail.list("", self.settings.MAIL_ERROR_FOLDER)
            if status != "OK" or not folders[0]:
                mail.create(self.settings.MAIL_ERROR_FOLDER)
                logger.info(f"Created IMAP folder: {self.settings.MAIL_ERROR_FOLDER}")
                
            mail.logout()
        except Exception as e:
            logger.error(f"Error setting up IMAP folders: {str(e)}")

    async def start_monitoring(self) -> None:
        """Start monitoring the IMAP inbox at regular intervals"""
        logger.info(f"Starting email monitoring service checking every {self.settings.MAIL_CHECK_INTERVAL} seconds")
        
        while True:
            try:
                # Process any new emails
                await self.process_new_emails()
                
                # Wait for the next check interval
                await asyncio.sleep(self.settings.MAIL_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in email monitoring loop: {str(e)}")
                # Continue monitoring even after errors
                await asyncio.sleep(self.settings.MAIL_CHECK_INTERVAL)
    
    async def process_new_emails(self) -> int:
        """Check for new emails and process them
        
        Returns:
            Number of emails processed
        """
        processed_count = 0
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.settings.MAIL_SERVER, self.settings.MAIL_PORT)
            mail.login(self.settings.MAIL_USERNAME, self.settings.MAIL_PASSWORD)
            mail.select(self.settings.MAIL_FOLDER)
            
            # Search for unread messages
            status, messages = mail.search(None, "UNSEEN")
            
            if status != "OK":
                logger.error(f"Error searching for unread messages: {status}")
                mail.logout()
                return 0
            
            # Get list of email IDs
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                try:
                    # Fetch email content
                    email_content = await self._fetch_email(mail, email_id)
                    
                    if not email_content:
                        continue
                    
                    # Check if the sender is in the allowed list
                    if self.settings.MAIL_ALLOWED_SENDERS and email_content.sender not in self.settings.MAIL_ALLOWED_SENDERS:
                        logger.warning(f"Email from unauthorized sender: {email_content.sender}")
                        # Move to error folder
                        mail.copy(email_id, self.settings.MAIL_ERROR_FOLDER)
                        mail.store(email_id, "+FLAGS", "\\Deleted")
                        continue
                    
                    # Check if subject contains required keywords
                    if self.settings.MAIL_SUBJECT_KEYWORDS and not any(keyword in email_content.subject.lower() for keyword in self.settings.MAIL_SUBJECT_KEYWORDS):
                        logger.info(f"Email subject doesn't contain any required keywords: {email_content.subject}")
                        # Skip this email, leave it in the inbox
                        continue
                    
                    # Process the content for AIOS
                    process_result = await self._process_content_for_aios(email_content)
                    
                    # Send a reply to the sender if configured
                    if self.settings.MAIL_REPLY_TO_SENDER:
                        await self._send_processing_notification(email_content, process_result)
                    
                    # Mark as processed and move to the Processed folder
                    mail.copy(email_id, self.settings.MAIL_PROCESSED_FOLDER)
                    mail.store(email_id, "+FLAGS", "\\Deleted")
                    
                    processed_count += 1
                    logger.info(f"Processed email from {email_content.sender} with subject: {email_content.subject}")
                
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}")
                    # Move to error folder
                    try:
                        mail.copy(email_id, self.settings.MAIL_ERROR_FOLDER)
                        mail.store(email_id, "+FLAGS", "\\Deleted")
                    except Exception as move_error:
                        logger.error(f"Error moving email to error folder: {str(move_error)}")
            
            # Commit the deletion of processed messages
            mail.expunge()
            mail.logout()
            
            return processed_count
        
        except Exception as e:
            logger.error(f"Error connecting to email server: {str(e)}")
            return 0
    
    async def _fetch_email(self, mail: imaplib.IMAP4_SSL, email_id: bytes) -> Optional[EmailContent]:
        """Fetch and parse an email from the IMAP server
        
        Args:
            mail: IMAP connection
            email_id: ID of the email to fetch
            
        Returns:
            Parsed email content object or None if parsing failed
        """
        try:
            # Fetch the email
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                logger.error(f"Error fetching email {email_id}: {status}")
                return None
            
            # Parse the email message
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract basic info
            subject = self._get_header(email_message, "Subject", "No Subject")
            sender = self._get_header(email_message, "From", "Unknown")
            recipient = self._get_header(email_message, "To", "Unknown")
            date = self._get_header(email_message, "Date", "Unknown")
            message_id = self._get_header(email_message, "Message-ID", None)
            
            # Extract body content and attachments
            body_text, body_html, attachments = self._extract_content(email_message)
            
            # Determine content type and content based on message and attachments
            content_type, content, content_filename = self._determine_content(body_text, body_html, attachments)
            
            return EmailContent(
                subject=subject,
                sender=sender,
                recipient=recipient,
                date=date,
                body_text=body_text,
                body_html=body_html,
                content_type=content_type,
                content=content,
                content_filename=content_filename,
                original_message_id=message_id,
                attachments=attachments,
                metadata={
                    "source": "email",
                    "sender": sender,
                    "date": date,
                    "subject": subject
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {str(e)}")
            return None
    
    def _get_header(self, message: Message, header_name: str, default: Optional[str] = None) -> str:
        """Extract and decode an email header
        
        Args:
            message: Email message
            header_name: Name of the header to extract
            default: Default value if header is not found
            
        Returns:
            Decoded header value or default
        """
        value = message.get(header_name, default)
        if value == default:
            return default
        
        return value
    
    def _extract_content(self, message: Message) -> Tuple[str, Optional[str], List[Dict[str, Any]]]:
        """Extract text, HTML, and attachments from an email message
        
        Args:
            message: Email message to extract content from
            
        Returns:
            Tuple of (text_content, html_content, attachments)
        """
        body_text = ""
        body_html = None
        attachments = []
        
        if message.is_multipart():
            # Handle multipart message
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Handle the body parts
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body_text = self._get_part_content(part)
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    body_html = self._get_part_content(part)
                elif "attachment" in content_disposition or "inline" in content_disposition:
                    # This is an attachment
                    filename = part.get_filename()
                    if not filename:
                        filename = f"attachment_{len(attachments) + 1}"
                    
                    # Get attachment data
                    attachment_data = part.get_payload(decode=True)
                    
                    if attachment_data:
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "data": attachment_data,
                            "size": len(attachment_data)
                        })
        else:
            # Handle non-multipart message
            content_type = message.get_content_type()
            if content_type == "text/plain":
                body_text = self._get_part_content(message)
            elif content_type == "text/html":
                body_html = self._get_part_content(message)
        
        return body_text, body_html, attachments
    
    def _get_part_content(self, part: Message) -> str:
        """Extract and decode content from a message part
        
        Args:
            part: Email message part
            
        Returns:
            Decoded content as string
        """
        content = part.get_payload(decode=True)
        if content is None:
            return ""
        
        # Try to decode with various encodings
        for encoding in ['utf-8', 'latin-1', 'ascii']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # If all else fails, use latin-1 as it can decode any byte stream
        return content.decode('latin-1', errors='replace')
    
    def _determine_content(self, 
                          body_text: str, 
                          body_html: Optional[str], 
                          attachments: List[Dict[str, Any]]) -> Tuple[str, Union[str, bytes, None], Optional[str]]:
        """Determine the primary content type and content for processing
        
        Args:
            body_text: Text body of the email
            body_html: HTML body of the email
            attachments: List of attachments
            
        Returns:
            Tuple of (content_type, content, filename)
        """
        # Check for attachments first
        if attachments:
            # Look for PDF
            for attachment in attachments:
                if attachment["content_type"] == "application/pdf":
                    return "pdf", attachment["data"], attachment["filename"]
            
            # Look for audio
            for attachment in attachments:
                if attachment["content_type"].startswith("audio/"):
                    return "audio", attachment["data"], attachment["filename"]
            
            # Look for text files
            for attachment in attachments:
                if attachment["content_type"] == "text/plain":
                    text_content = ""
                    try:
                        if isinstance(attachment["data"], bytes):
                            text_content = attachment["data"].decode('utf-8', errors='replace')
                        else:
                            text_content = str(attachment["data"])
                        return "text", text_content, attachment["filename"]
                    except Exception:
                        # If we can't decode, just use the first attachment
                        continue
            
            # If no specific types found but we have attachments, use the first one
            first_attachment = attachments[0]
            # Return the raw data and let the content processing pipeline handle it
            return first_attachment["content_type"].split("/")[0], first_attachment["data"], first_attachment["filename"]
        
        # Check if there's a URL in the body text (simplistic check)
        if body_text:
            lines = body_text.strip().split("\n")
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("http://") or stripped_line.startswith("https://"):
                    if len(stripped_line.split()) == 1:  # Likely a URL on its own line
                        return "url", stripped_line, None
        
        # If we have HTML content with no attachments, assume it's URL content
        # This is a heuristic - the person may have just sent HTML with no URLs
        if body_html and "<a href=" in body_html:
            # Try to extract the first URL from the HTML
            import re
            url_match = re.search(r'href=["\'](https?://[^"\']+)["\']', body_html)
            if url_match:
                return "url", url_match.group(1), None
        
        # Default to text content
        return "text", body_text, None
    
    async def _process_content_for_aios(self, email_content: EmailContent) -> Dict[str, Any]:
        """Process the extracted content through the AIOS processing pipeline
        
        Args:
            email_content: Extracted email content
            
        Returns:
            Processing result
        """
        try:
            import aiohttp
            import tempfile
            
            # Determine content to process
            content_to_process = email_content.content
            
            # If it's bytes data (like for PDFs or audio), save to a temp file and encode as base64
            if isinstance(content_to_process, bytes):
                # Create a temporary file
                suffix = f".{email_content.content_type}" if email_content.content_type in ["pdf", "audio"] else ""
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    temp_file.write(content_to_process)
                    temp_path = temp_file.name
                
                try:
                    # Read the file and encode as base64
                    with open(temp_path, "rb") as file:
                        file_content = file.read()
                        content_to_process = f"data:{email_content.content_type}/{suffix.lstrip('.')};base64,{base64.b64encode(file_content).decode('utf-8')}"
                    
                    # Remove the temporary file
                    os.unlink(temp_path)
                except Exception as e:
                    logger.error(f"Error processing temp file: {str(e)}")
                    # If there's an error, just use the content directly
                    content_to_process = email_content.body_text
            
            # Create the API request
            request_data = {
                "content_type": email_content.content_type,
                "content": content_to_process,
                "metadata": {
                    **email_content.metadata,
                    "email_subject": email_content.subject,
                    "email_sender": email_content.sender,
                    "email_date": email_content.date
                }
            }
            
            # Call the API to process the content
            api_endpoint = "http://localhost:8080/agents/contentmind/process"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_endpoint, json=request_data) as response:
                    result = await response.json()
                    
                    # Add some metadata for the reply
                    if not result.get("email_metadata"):
                        result["email_metadata"] = {}
                    
                    result["email_metadata"]["original_subject"] = email_content.subject
                    result["email_metadata"]["processed_at"] = datetime.now().isoformat()
                    
                    return result
                
        except Exception as e:
            logger.error(f"Error processing content for AIOS: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process content: {str(e)}",
                "email_metadata": {
                    "original_subject": email_content.subject,
                    "processed_at": datetime.now().isoformat()
                }
            }
    
    async def _send_processing_notification(self, email_content: EmailContent, process_result: Dict[str, Any]) -> None:
        """Send a notification email back to the sender with processing results
        
        Args:
            email_content: Original email content
            process_result: Result of content processing
        """
        try:
            status = process_result.get("status", "error")
            reply_subject = f"Re: {email_content.subject}"
            
            if status == "success":
                # Extract information for a success message
                content_type = process_result.get("content_type", "unknown")
                
                if "storage" in process_result and process_result["storage"].get("stored", False):
                    content_id = process_result["storage"].get("content_id", "unknown")
                    processed_content = process_result.get("processed_content", {})
                    
                    title = processed_content.get("title", "Untitled")
                    summary = processed_content.get("summary", "No summary available")
                    
                    # Format the success message
                    html_content = f"""
                    <html>
                        <body>
                            <h2>Content Processing Completed</h2>
                            <p>Your content has been successfully processed and added to the knowledge repository.</p>
                            
                            <h3>Content Details</h3>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Type:</strong> {content_type}</p>
                            <p><strong>ID:</strong> {content_id}</p>
                            
                            <h3>Summary</h3>
                            <p>{summary}</p>
                            
                            <hr>
                            <p><em>This is an automated response from the Bluelabel AIOS system.</em></p>
                        </body>
                    </html>
                    """
                    
                    text_content = f"""Content Processing Completed
                    
Your content has been successfully processed and added to the knowledge repository.

Content Details:
Title: {title}
Type: {content_type}
ID: {content_id}

Summary:
{summary}

--
This is an automated response from the Bluelabel AIOS system.
                    """
                else:
                    # Processing succeeded but content was not stored
                    html_content = f"""
                    <html>
                        <body>
                            <h2>Content Processing Completed</h2>
                            <p>Your content has been successfully processed but could not be stored in the repository.</p>
                            
                            <p>Reason: {process_result.get("storage", {}).get("error", "Unknown error")}</p>
                            
                            <hr>
                            <p><em>This is an automated response from the Bluelabel AIOS system.</em></p>
                        </body>
                    </html>
                    """
                    
                    text_content = f"""Content Processing Completed
                    
Your content has been successfully processed but could not be stored in the repository.

Reason: {process_result.get("storage", {}).get("error", "Unknown error")}

--
This is an automated response from the Bluelabel AIOS system.
                    """
            else:
                # Error message
                error_message = process_result.get("message", "Unknown error")
                
                html_content = f"""
                <html>
                    <body>
                        <h2>Content Processing Failed</h2>
                        <p>There was an error processing your content.</p>
                        
                        <p><strong>Error:</strong> {error_message}</p>
                        
                        <hr>
                        <p><em>This is an automated response from the Bluelabel AIOS system.</em></p>
                    </body>
                </html>
                """
                
                text_content = f"""Content Processing Failed
                
There was an error processing your content.

Error: {error_message}

--
This is an automated response from the Bluelabel AIOS system.
                """
            
            # Extract email address from the sender field
            # This is a simplistic extraction that might need improvement
            import re
            email_match = re.search(r'<([^>]+)>', email_content.sender)
            if email_match:
                sender_email = email_match.group(1)
            else:
                sender_email = email_content.sender.strip()
            
            # Create the email message
            message = MessageSchema(
                subject=reply_subject,
                recipients=[sender_email],
                body=text_content,
                html=html_content,
                subtype="html"
            )
            
            # Send the email
            fm = FastMail(self.mail_config)
            await fm.send_message(message)
            
            logger.info(f"Sent processing notification to {sender_email}")
            
        except Exception as e:
            logger.error(f"Error sending processing notification: {str(e)}")