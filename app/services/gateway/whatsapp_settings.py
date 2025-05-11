# app/services/gateway/whatsapp_settings.py
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os

class WhatsAppSettings(BaseSettings):
    """WhatsApp API settings for Meta's WhatsApp Business Cloud API"""

    # WhatsApp API credentials
    WHATSAPP_PHONE_ID: str = os.environ.get("WHATSAPP_PHONE_ID", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.environ.get("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    WHATSAPP_API_TOKEN: str = os.environ.get("WHATSAPP_API_TOKEN", "")
    WHATSAPP_VERIFY_TOKEN: str = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")

    # Messaging settings
    WHATSAPP_ENABLED: bool = os.environ.get("WHATSAPP_ENABLED", "False").lower() == "true"
    WHATSAPP_ALLOWED_NUMBERS: List[str] = os.environ.get("WHATSAPP_ALLOWED_NUMBERS", "").split(",")
    WHATSAPP_AUTO_REPLY: bool = os.environ.get("WHATSAPP_AUTO_REPLY", "True").lower() == "true"

    # Webhook settings
    WHATSAPP_WEBHOOK_URL: str = os.environ.get("WHATSAPP_WEBHOOK_URL", "")

    # Template message IDs (for notifications)
    WHATSAPP_SUCCESS_TEMPLATE: str = os.environ.get("WHATSAPP_SUCCESS_TEMPLATE", "")
    WHATSAPP_ERROR_TEMPLATE: str = os.environ.get("WHATSAPP_ERROR_TEMPLATE", "")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields to support other app settings

whatsapp_settings = WhatsAppSettings()