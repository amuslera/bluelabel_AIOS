# app/services/gateway/controller.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, List, Optional
import logging

from app.services.gateway.email_processor import EmailProcessor
from app.services.gateway.email_settings import email_settings
from app.services.gateway.whatsapp_processor import WhatsAppProcessor
from app.services.gateway.whatsapp_settings import whatsapp_settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/gateway",
    tags=["gateway"],
    responses={404: {"description": "Not found"}},
)

# Global variables to track background tasks
email_monitor_task = None
email_processor = None
whatsapp_processor = None

class EmailMonitorStatus(BaseModel):
    """Status of the email monitoring service"""
    running: bool
    check_interval: int
    inbox: str
    last_check_time: Optional[str] = None
    emails_processed: int = 0

class EmailConfig(BaseModel):
    """Email configuration settings"""
    mail_server: str
    mail_port: int
    mail_username: str
    mail_password: str
    mail_folder: str = "INBOX"
    check_interval: int = 300  # Seconds
    allowed_senders: Optional[List[str]] = None
    subject_keywords: Optional[List[str]] = None
    reply_to_sender: bool = True

class WhatsAppStatus(BaseModel):
    """Status of the WhatsApp integration"""
    enabled: bool
    phone_id: str
    webhook_configured: bool
    allowed_numbers: List[str] = []

class WhatsAppConfig(BaseModel):
    """WhatsApp configuration settings"""
    phone_id: str
    business_account_id: str
    api_token: str
    verify_token: str
    enabled: bool = True
    allowed_numbers: Optional[List[str]] = None
    auto_reply: bool = True

class WhatsAppMessage(BaseModel):
    """Model for sending a WhatsApp message"""
    recipient: str
    message: str

@router.get("/email/status")
async def get_email_status() -> EmailMonitorStatus:
    """Get the status of the email monitoring service"""
    global email_monitor_task, email_processor
    
    running = email_monitor_task is not None and not email_monitor_task.done()
    
    return EmailMonitorStatus(
        running=running,
        check_interval=email_settings.MAIL_CHECK_INTERVAL,
        inbox=email_settings.MAIL_FOLDER,
        last_check_time=None,  # TODO: Track last check time
        emails_processed=0  # TODO: Track processed count
    )

@router.post("/email/start")
async def start_email_monitor(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start the email monitoring service
    
    The service will check for new emails at regular intervals and process them.
    """
    global email_monitor_task, email_processor
    
    # Check if the service is already running
    if email_monitor_task is not None and not email_monitor_task.done():
        return {"status": "already_running", "message": "Email monitoring service is already running"}
    
    # Check if we have the necessary credentials
    if not email_settings.MAIL_SERVER or not email_settings.MAIL_USERNAME or not email_settings.MAIL_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing email credentials. Please set MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD."
        )
    
    try:
        # Initialize the email processor
        email_processor = EmailProcessor()
        
        # Start the monitoring service as a background task
        background_tasks.add_task(email_processor.start_monitoring)
        
        logger.info("Started email monitoring service")
        return {
            "status": "success",
            "message": "Email monitoring service started",
            "config": {
                "mail_server": email_settings.MAIL_SERVER,
                "mail_port": email_settings.MAIL_PORT,
                "mail_username": email_settings.MAIL_USERNAME,
                "mail_folder": email_settings.MAIL_FOLDER,
                "check_interval": email_settings.MAIL_CHECK_INTERVAL,
                "allowed_senders": email_settings.MAIL_ALLOWED_SENDERS,
            }
        }
    except Exception as e:
        logger.error(f"Error starting email monitoring service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start email monitoring service: {str(e)}"
        )

@router.post("/email/stop")
async def stop_email_monitor() -> Dict[str, Any]:
    """Stop the email monitoring service"""
    global email_monitor_task
    
    if email_monitor_task is None or email_monitor_task.done():
        return {"status": "not_running", "message": "Email monitoring service is not running"}
    
    try:
        # Cancel the background task
        email_monitor_task.cancel()
        
        logger.info("Stopped email monitoring service")
        return {"status": "success", "message": "Email monitoring service stopped"}
    except Exception as e:
        logger.error(f"Error stopping email monitoring service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop email monitoring service: {str(e)}"
        )

@router.post("/email/check-now")
async def check_emails_now() -> Dict[str, Any]:
    """Manually check for new emails right now"""
    global email_processor
    
    if email_processor is None:
        email_processor = EmailProcessor()
    
    try:
        # Process new emails
        processed_count = await email_processor.process_new_emails()
        
        return {
            "status": "success",
            "message": f"Processed {processed_count} emails",
            "emails_processed": processed_count
        }
    except Exception as e:
        logger.error(f"Error checking emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check emails: {str(e)}"
        )

@router.post("/email/config")
async def update_email_config(config: EmailConfig) -> Dict[str, Any]:
    """Update email configuration settings
    
    This will update the environment variables with the new settings.
    """
    try:
        # Update environment variables
        import os
        os.environ["MAIL_SERVER"] = config.mail_server
        os.environ["MAIL_PORT"] = str(config.mail_port)
        os.environ["MAIL_USERNAME"] = config.mail_username
        os.environ["MAIL_PASSWORD"] = config.mail_password
        os.environ["MAIL_FOLDER"] = config.mail_folder
        os.environ["MAIL_CHECK_INTERVAL"] = str(config.check_interval)
        
        if config.allowed_senders:
            os.environ["MAIL_ALLOWED_SENDERS"] = ",".join(config.allowed_senders)
        
        if config.subject_keywords:
            os.environ["MAIL_SUBJECT_KEYWORDS"] = ",".join(config.subject_keywords)
        
        os.environ["MAIL_REPLY_TO_SENDER"] = str(config.reply_to_sender).lower()
        
        # Reload settings
        from importlib import reload
        from app.services.gateway import email_settings as settings_module
        reload(settings_module)
        
        logger.info("Updated email configuration settings")
        return {"status": "success", "message": "Email configuration updated"}
    except Exception as e:
        logger.error(f"Error updating email configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email configuration: {str(e)}"
        )

# WhatsApp endpoints
@router.get("/whatsapp/status")
async def get_whatsapp_status() -> WhatsAppStatus:
    """Get the status of the WhatsApp integration"""
    global whatsapp_processor

    # Check if WhatsApp is enabled
    enabled = whatsapp_settings.WHATSAPP_ENABLED

    # Check if webhook is configured
    webhook_configured = bool(whatsapp_settings.WHATSAPP_WEBHOOK_URL)

    return WhatsAppStatus(
        enabled=enabled,
        phone_id=whatsapp_settings.WHATSAPP_PHONE_ID,
        webhook_configured=webhook_configured,
        allowed_numbers=whatsapp_settings.WHATSAPP_ALLOWED_NUMBERS
    )

@router.post("/whatsapp/config")
async def update_whatsapp_config(config: WhatsAppConfig) -> Dict[str, Any]:
    """Update WhatsApp configuration settings

    This will update the environment variables with the new settings.
    """
    try:
        # Update environment variables
        import os
        os.environ["WHATSAPP_PHONE_ID"] = config.phone_id
        os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = config.business_account_id
        os.environ["WHATSAPP_API_TOKEN"] = config.api_token
        os.environ["WHATSAPP_VERIFY_TOKEN"] = config.verify_token
        os.environ["WHATSAPP_ENABLED"] = str(config.enabled).lower()

        if config.allowed_numbers:
            os.environ["WHATSAPP_ALLOWED_NUMBERS"] = ",".join(config.allowed_numbers)

        os.environ["WHATSAPP_AUTO_REPLY"] = str(config.auto_reply).lower()

        # Reload settings
        from importlib import reload
        from app.services.gateway import whatsapp_settings as settings_module
        reload(settings_module)

        # Reset processor to use new settings
        global whatsapp_processor
        whatsapp_processor = None

        logger.info("Updated WhatsApp configuration settings")
        return {"status": "success", "message": "WhatsApp configuration updated"}
    except Exception as e:
        logger.error(f"Error updating WhatsApp configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update WhatsApp configuration: {str(e)}"
        )

@router.post("/whatsapp/message")
async def send_whatsapp_message(message_data: WhatsAppMessage) -> Dict[str, Any]:
    """Send a WhatsApp message to a recipient"""
    global whatsapp_processor

    # Check if WhatsApp is enabled
    if not whatsapp_settings.WHATSAPP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp integration is not enabled"
        )

    # Check if we have the necessary credentials
    if not whatsapp_settings.WHATSAPP_API_TOKEN or not whatsapp_settings.WHATSAPP_PHONE_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing WhatsApp API credentials. Please configure WHATSAPP_API_TOKEN and WHATSAPP_PHONE_ID."
        )

    try:
        # Initialize the WhatsApp processor if needed
        if whatsapp_processor is None:
            whatsapp_processor = WhatsAppProcessor()

        # Send the message
        result = await whatsapp_processor.send_message(
            message_data.recipient,
            message_data.message
        )

        if result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to send WhatsApp message")
            )

        return {
            "status": "success",
            "message": "WhatsApp message sent",
            "message_id": result.get("message_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request) -> Dict[str, Any]:
    """Webhook for receiving WhatsApp API events"""
    global whatsapp_processor

    # Initialize the WhatsApp processor if needed
    if whatsapp_processor is None:
        whatsapp_processor = WhatsAppProcessor()

    # Get the request body
    body = await request.json()

    # Process the webhook event
    result = await whatsapp_processor.process_webhook_event(body)

    return result

@router.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(
    request: Request,
    mode: str = None,
    challenge: str = None,
    verify_token: str = None
) -> Dict[str, Any]:
    """Verify the WhatsApp webhook

    This endpoint is used by Meta to verify the webhook URL.
    """
    if mode == "subscribe" and verify_token == whatsapp_settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return JSONResponse(content=int(challenge))
    else:
        logger.warning("WhatsApp webhook verification failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed"
        )