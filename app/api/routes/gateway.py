"""
API routes for configuring and managing gateway services.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
import json
import os
import time
from datetime import datetime
import logging

from app.services.gateway.email_settings import email_settings, EmailSettings
from app.services.gateway.email_processor import EmailProcessor
from app.services.gateway.google_oauth import google_oauth

# Configure logger
logger = logging.getLogger("gateway")
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/gateway", tags=["gateway"])

# --- Email Gateway Models ---

class EmailConfig(BaseModel):
    """Email gateway configuration"""
    email_address: EmailStr = Field(..., description="Email address to monitor")
    server: str = Field(..., description="IMAP server hostname")
    password: str = Field(..., description="Email account password")
    port: int = Field(993, description="IMAP server port")
    use_ssl: bool = Field(True, description="Use SSL for connection")
    use_tls: bool = Field(False, description="Use TLS for connection")
    check_interval: int = Field(300, description="Check interval in seconds")
    outgoing_server: Optional[str] = Field(None, description="SMTP server hostname")
    outgoing_port: Optional[int] = Field(None, description="SMTP server port")
    outgoing_use_ssl: Optional[bool] = Field(None, description="Use SSL for outgoing connection")
    outgoing_use_tls: Optional[bool] = Field(None, description="Use TLS for outgoing connection")
    enabled: bool = Field(True, description="Enable the email gateway")
    reply_to_sender: bool = Field(True, description="Reply to sender with processing status")

class EmailSimulationRequest(BaseModel):
    """Email simulation request for testing"""
    from_email: str = Field(..., alias="from", description="Sender email address")
    to_email: str = Field(..., alias="to", description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    date: Optional[str] = Field(None, description="Email date (ISO format)")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="List of attachments")

class GatewayStatusResponse(BaseModel):
    """Gateway status response"""
    status: str
    service: str
    enabled: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# --- WhatsApp Gateway Models ---

class WhatsAppConfig(BaseModel):
    """WhatsApp gateway configuration"""
    phone_id: str = Field(..., description="WhatsApp phone ID")
    business_account_id: str = Field(..., description="WhatsApp business account ID")
    api_token: str = Field(..., description="WhatsApp API token")
    verify_token: str = Field(..., description="WhatsApp verify token")
    enabled: bool = Field(True, description="Enable the WhatsApp gateway")

class WhatsAppSimulationRequest(BaseModel):
    """WhatsApp simulation request for testing"""
    from_number: str = Field(..., description="Sender phone number")
    text: str = Field(..., description="Message text")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    message_id: Optional[str] = Field(None, description="Message ID")
    media_url: Optional[str] = Field(None, description="URL to media content")
    media_type: Optional[str] = Field(None, description="Type of media (image, audio, document)")

# Global email processor instance
email_processor = None

# --- Email Gateway Endpoints ---

@router.get("/email/status", response_model=GatewayStatusResponse)
async def get_email_gateway_status():
    """Get the current status of the email gateway"""
    global email_processor
    
    # Check if email gateway is configured
    if not email_settings.MAIL_USERNAME or not email_settings.MAIL_SERVER:
        return GatewayStatusResponse(
            status="not_configured",
            service="email",
            enabled=False,
            message="Email gateway not configured"
        )
    
    # Check if email gateway is running
    is_running = email_processor is not None
    
    return GatewayStatusResponse(
        status="running" if is_running else "stopped",
        service="email",
        enabled=is_running,
        message=f"Email gateway is {'running' if is_running else 'stopped'}",
        details={
            "server": email_settings.MAIL_SERVER,
            "username": email_settings.MAIL_USERNAME,
            "check_interval": email_settings.MAIL_CHECK_INTERVAL,
            "folder": email_settings.MAIL_FOLDER
        }
    )

@router.post("/email/config")
async def configure_email_gateway(config: EmailConfig):
    """Configure the email gateway"""
    # Update environment variables
    os.environ["MAIL_SERVER"] = config.server
    os.environ["MAIL_PORT"] = str(config.port)
    os.environ["MAIL_USERNAME"] = config.email_address
    os.environ["MAIL_PASSWORD"] = config.password
    os.environ["MAIL_USE_SSL"] = str(config.use_ssl)
    os.environ["MAIL_USE_TLS"] = str(config.use_tls)
    os.environ["MAIL_CHECK_INTERVAL"] = str(config.check_interval)
    os.environ["MAIL_REPLY_TO_SENDER"] = str(config.reply_to_sender)
    
    # Update SMTP settings if provided
    if config.outgoing_server:
        os.environ["SMTP_SERVER"] = config.outgoing_server
    if config.outgoing_port:
        os.environ["SMTP_PORT"] = str(config.outgoing_port)
    if config.outgoing_use_ssl is not None:
        os.environ["SMTP_USE_SSL"] = str(config.outgoing_use_ssl)
    if config.outgoing_use_tls is not None:
        os.environ["SMTP_USE_TLS"] = str(config.outgoing_use_tls)
    
    # Update the email_settings object
    email_settings.__class__.Config.env_file = None  # Disable env file to reload from environment
    new_settings = EmailSettings()
    for key, value in new_settings.__dict__.items():
        setattr(email_settings, key, value)
    
    # Save configuration to .env file for persistence
    try:
        with open(".env", "r") as env_file:
            env_content = env_file.read()
    except FileNotFoundError:
        env_content = ""
    
    # Update or add each setting
    env_lines = env_content.split("\n")
    updated_env = {}
    
    for line in env_lines:
        if line.strip() and not line.startswith("#"):
            key, value = line.split("=", 1)
            updated_env[key.strip()] = value.strip()
    
    # Update with new values
    updated_env["MAIL_SERVER"] = config.server
    updated_env["MAIL_PORT"] = str(config.port)
    updated_env["MAIL_USERNAME"] = config.email_address
    updated_env["MAIL_PASSWORD"] = config.password
    updated_env["MAIL_USE_SSL"] = str(config.use_ssl)
    updated_env["MAIL_USE_TLS"] = str(config.use_tls)
    updated_env["MAIL_CHECK_INTERVAL"] = str(config.check_interval)
    updated_env["MAIL_REPLY_TO_SENDER"] = str(config.reply_to_sender)
    
    if config.outgoing_server:
        updated_env["SMTP_SERVER"] = config.outgoing_server
    if config.outgoing_port:
        updated_env["SMTP_PORT"] = str(config.outgoing_port)
    if config.outgoing_use_ssl is not None:
        updated_env["SMTP_USE_SSL"] = str(config.outgoing_use_ssl)
    if config.outgoing_use_tls is not None:
        updated_env["SMTP_USE_TLS"] = str(config.outgoing_use_tls)
    
    # Write back to .env file
    with open(".env", "w") as env_file:
        for key, value in updated_env.items():
            env_file.write(f"{key}={value}\n")
    
    return {
        "status": "success",
        "message": "Email gateway configuration updated",
        "details": {
            "server": config.server,
            "username": config.email_address,
            "check_interval": config.check_interval
        }
    }

@router.post("/email/start")
async def start_email_gateway(background_tasks: BackgroundTasks):
    """Start the email gateway monitoring service"""
    global email_processor
    
    # Check if already running
    if email_processor is not None:
        return {
            "status": "already_running",
            "message": "Email gateway is already running"
        }
    
    # Check if configured
    if not email_settings.MAIL_USERNAME or not email_settings.MAIL_SERVER:
        raise HTTPException(status_code=400, detail="Email gateway not configured")
    
    # Create and start email processor
    try:
        email_processor = EmailProcessor()
        background_tasks.add_task(email_processor.start_monitoring)
        
        return {
            "status": "success",
            "message": "Email gateway started successfully",
            "details": {
                "server": email_settings.MAIL_SERVER,
                "username": email_settings.MAIL_USERNAME,
                "check_interval": email_settings.MAIL_CHECK_INTERVAL
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start email gateway: {str(e)}")

@router.post("/email/stop")
async def stop_email_gateway():
    """Stop the email gateway monitoring service"""
    global email_processor
    
    # Check if running
    if email_processor is None:
        return {
            "status": "not_running",
            "message": "Email gateway is not running"
        }
    
    # Stop the processor
    try:
        # Set to None to indicate stopped service
        # The background task will complete its current iteration and then stop
        email_processor = None
        
        return {
            "status": "success",
            "message": "Email gateway stopped successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop email gateway: {str(e)}")

@router.post("/email/simulate")
async def simulate_email(simulation: EmailSimulationRequest):
    """Simulate receiving an email for testing"""
    from app.core.registry.agent_registry import get_agent_registry
    
    logger.debug(f"simulate_email: Received request = {simulation.dict()}")
    
    # Create a test email content object
    date_str = simulation.date or datetime.now().isoformat()
    
    # Create email content object
    email_content = {
        "subject": simulation.subject,
        "sender": simulation.from_email,
        "recipient": simulation.to_email,
        "date": date_str,
        "plain_text": simulation.body,
        "html_content": f"<p>{simulation.body}</p>",
        "message_id": f"test_{int(datetime.now().timestamp())}",
        "attachments": simulation.attachments or []
    }
    
    logger.debug(f"simulate_email: Created email_content = {json.dumps(email_content, default=str)}")
    
    # Process the email through the Gateway agent
    try:
        # Get the Gateway agent
        agent_registry = get_agent_registry()
        gateway_agent = agent_registry.get_agent("gateway")
        logger.debug(f"[DEBUG] gateway.py: Registry id: {id(agent_registry)}, Gateway agent id: {id(gateway_agent) if gateway_agent else None}")
        logger.debug(f"simulate_email: Got gateway_agent = {gateway_agent}")
        
        if not gateway_agent:
            raise HTTPException(status_code=404, detail="Gateway agent not found")
        
        # Process the email
        logger.debug("simulate_email: Calling gateway_agent.process_email")
        result = await gateway_agent.process_email(email_content)
        logger.debug(f"simulate_email: gateway_agent.process_email returned = {json.dumps(result, default=str)}")
        
        return {
            "status": "success",
            "message": "Email processed successfully",
            "result": result
        }
    except Exception as e:
        logger.error(f"simulate_email: Error = {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process simulated email: {str(e)}")

# --- WhatsApp Gateway Endpoints ---

@router.get("/whatsapp/status", response_model=GatewayStatusResponse)
async def get_whatsapp_gateway_status():
    """Get the current status of the WhatsApp gateway"""
    # Check WhatsApp configuration
    whatsapp_config_path = "config/whatsapp_config.json"
    
    try:
        with open(whatsapp_config_path, "r") as f:
            config = json.load(f)
        
        enabled = config.get("enabled", False)
        
        return GatewayStatusResponse(
            status="configured" if enabled else "disabled",
            service="whatsapp",
            enabled=enabled,
            details=config
        )
    except FileNotFoundError:
        return GatewayStatusResponse(
            status="not_configured",
            service="whatsapp",
            enabled=False,
            message="WhatsApp gateway not configured"
        )
    except Exception as e:
        return GatewayStatusResponse(
            status="error",
            service="whatsapp",
            enabled=False,
            message=f"Error checking WhatsApp gateway status: {str(e)}"
        )

@router.post("/whatsapp/config")
async def configure_whatsapp_gateway(config: WhatsAppConfig):
    """Configure the WhatsApp gateway"""
    whatsapp_config_path = "config/whatsapp_config.json"
    
    # Create config directory if it doesn't exist
    os.makedirs("config", exist_ok=True)
    
    # Save configuration to file
    try:
        config_dict = config.dict()
        
        with open(whatsapp_config_path, "w") as f:
            json.dump(config_dict, f, indent=2)
        
        return {
            "status": "success",
            "message": "WhatsApp gateway configuration updated",
            "details": config_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save WhatsApp configuration: {str(e)}")

@router.post("/whatsapp/simulate")
async def simulate_whatsapp(simulation: WhatsAppSimulationRequest):
    """Simulate receiving a WhatsApp message for testing"""
    from app.core.registry.agent_registry import get_agent_registry

    # Create message object
    timestamp = simulation.timestamp or datetime.now().isoformat()
    message_id = simulation.message_id or f"test_{int(datetime.now().timestamp())}"

    message = {
        "from": simulation.from_number,
        "text": simulation.text,
        "timestamp": timestamp,
        "message_id": message_id
    }

    # Add media if provided
    if simulation.media_url:
        message["media_url"] = simulation.media_url
        message["media_type"] = simulation.media_type or "unknown"

    # Process the message through the Gateway agent
    try:
        # Get the Gateway agent
        agent_registry = get_agent_registry()
        gateway_agent = agent_registry.get_agent("gateway")

        if not gateway_agent:
            raise HTTPException(status_code=404, detail="Gateway agent not found")

        # Process the message
        result = await gateway_agent.process_whatsapp(message)

        return {
            "status": "success",
            "message": "WhatsApp message processed successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process simulated WhatsApp message: {str(e)}")

# --- Google OAuth Endpoints ---

class GoogleOAuthConfig(BaseModel):
    """Google OAuth configuration"""
    client_id: str = Field(..., description="Google OAuth client ID")
    client_secret: str = Field(..., description="Google OAuth client secret")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI for OAuth callback")

@router.post("/google/config")
async def configure_google_oauth(config: GoogleOAuthConfig):
    """Configure Google OAuth credentials"""
    # Update environment variables
    os.environ["GOOGLE_CLIENT_ID"] = config.client_id
    os.environ["GOOGLE_CLIENT_SECRET"] = config.client_secret

    if config.redirect_uri:
        os.environ["GOOGLE_REDIRECT_URI"] = config.redirect_uri

    # Update .env file for persistence
    try:
        with open(".env", "r") as env_file:
            env_content = env_file.read()
    except FileNotFoundError:
        env_content = ""

    # Update or add each setting
    env_lines = env_content.split("\n")
    updated_env = {}

    for line in env_lines:
        if line.strip() and not line.startswith("#"):
            key, value = line.split("=", 1)
            updated_env[key.strip()] = value.strip()

    # Update with new values
    updated_env["GOOGLE_CLIENT_ID"] = config.client_id
    updated_env["GOOGLE_CLIENT_SECRET"] = config.client_secret

    if config.redirect_uri:
        updated_env["GOOGLE_REDIRECT_URI"] = config.redirect_uri

    # Write back to .env file
    with open(".env", "w") as env_file:
        for key, value in updated_env.items():
            env_file.write(f"{key}={value}\n")

    return {
        "status": "success",
        "message": "Google OAuth configuration updated"
    }

@router.get("/google/auth")
async def start_google_auth():
    """Start the Google OAuth authorization process"""
    try:
        # Generate the authorization URL
        auth_url = google_oauth.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")

@router.get("/google/callback")
async def google_auth_callback(request: Request):
    """Handle Google OAuth callback"""
    # Get the authorization code from the query parameters
    code = request.query_params.get("code")
    if not code:
        error = request.query_params.get("error", "Unknown error")
        error_description = request.query_params.get("error_description", "No description")
        raise HTTPException(
            status_code=400,
            detail=f"Authorization failed: {error} - {error_description}"
        )

    try:
        # Exchange the code for tokens
        result = await google_oauth.handle_callback(code)

        # Redirect to a success page
        return RedirectResponse(url="/gateway/google/success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete OAuth flow: {str(e)}")

@router.get("/google/success")
async def google_auth_success():
    """Success page for Google OAuth"""
    return {
        "status": "success",
        "message": "Google authentication successful. You can now use Gmail with OAuth."
    }

@router.get("/google/status")
async def google_oauth_status():
    """Check the status of Google OAuth"""
    try:
        # Check if we have tokens
        if not google_oauth.tokens or "access_token" not in google_oauth.tokens:
            return {
                "status": "not_authenticated",
                "message": "Not authenticated with Google"
            }

        # Check if token is expired
        created_at = google_oauth.tokens.get("created_at", 0)
        expires_in = google_oauth.tokens.get("expires_in", 3600)
        current_time = int(time.time())

        if current_time >= (created_at + expires_in):
            return {
                "status": "expired",
                "message": "Authentication expired, needs refresh"
            }

        return {
            "status": "authenticated",
            "message": "Authenticated with Google",
            "expires_in": (created_at + expires_in) - current_time
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking OAuth status: {str(e)}"
        }

@router.post("/google/revoke")
async def revoke_google_oauth():
    """Revoke Google OAuth tokens"""
    try:
        result = await google_oauth.revoke_tokens()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke tokens: {str(e)}")

@router.post("/email/google")
async def configure_email_with_google(background_tasks: BackgroundTasks):
    """Configure and start the email gateway using Google OAuth"""
    try:
        # Check if we're authenticated with Google
        if not google_oauth.tokens or "access_token" not in google_oauth.tokens:
            # Return the auth URL
            auth_url = google_oauth.get_authorization_url()
            return {
                "status": "not_authenticated",
                "message": "Authentication with Google required",
                "auth_url": auth_url
            }

        # Get email and auth string
        email, auth_string = await google_oauth.create_imap_access()

        # Set the email address to a@bluelabel.ventures regardless of what Google returns
        email = "a@bluelabel.ventures"
        logger.info(f"Using email address: {email} with Google OAuth")

        # Update environment variables for email settings
        os.environ["MAIL_SERVER"] = "imap.gmail.com"
        os.environ["MAIL_PORT"] = "993"
        os.environ["MAIL_USERNAME"] = email
        os.environ["MAIL_PASSWORD"] = auth_string  # This is actually the OAuth token
        os.environ["MAIL_USE_SSL"] = "True"
        os.environ["MAIL_USE_TLS"] = "False"
        os.environ["MAIL_USE_OAUTH"] = "True"  # Mark as using OAuth
        os.environ["MAIL_FROM"] = email  # Make sure this is set

        # Update SMTP settings
        os.environ["SMTP_SERVER"] = "smtp.gmail.com"
        os.environ["SMTP_PORT"] = "587"
        os.environ["SMTP_USERNAME"] = email
        os.environ["SMTP_PASSWORD"] = auth_string  # OAuth token
        os.environ["SMTP_USE_SSL"] = "False"
        os.environ["SMTP_USE_TLS"] = "True"
        os.environ["SMTP_USE_OAUTH"] = "True"

        # Update the email_settings object
        email_settings.__class__.Config.env_file = None  # Disable env file to reload from env
        new_settings = EmailSettings()
        for key, value in new_settings.__dict__.items():
            setattr(email_settings, key, value)

        # Create and start email processor
        global email_processor
        email_processor = EmailProcessor()
        background_tasks.add_task(email_processor.start_monitoring)

        return {
            "status": "success",
            "message": "Email gateway configured with Google OAuth and started",
            "email": email
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure email with Google OAuth: {str(e)}"
        )