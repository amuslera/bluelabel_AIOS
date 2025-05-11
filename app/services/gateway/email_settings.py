# app/services/gateway/email_settings.py
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os

class EmailSettings(BaseSettings):
    """Email settings for IMAP and SMTP connections"""

    # Inbound (IMAP) settings
    MAIL_SERVER: str = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT", "993"))
    MAIL_USERNAME: str = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.environ.get("MAIL_PASSWORD", "")
    MAIL_USE_SSL: bool = os.environ.get("MAIL_USE_SSL", "True").lower() == "true"
    MAIL_USE_TLS: bool = os.environ.get("MAIL_USE_TLS", "False").lower() == "true"

    # Outbound (SMTP) settings
    MAIL_FROM: str = os.environ.get("MAIL_FROM", "")
    MAIL_FROM_NAME: str = os.environ.get("MAIL_FROM_NAME", "Bluelabel AIOS")
    SMTP_SERVER: str = os.environ.get("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_SSL: bool = os.environ.get("SMTP_USE_SSL", "False").lower() == "true"
    SMTP_USE_TLS: bool = os.environ.get("SMTP_USE_TLS", "True").lower() == "true"

    # Processing settings
    MAIL_CHECK_INTERVAL: int = int(os.environ.get("MAIL_CHECK_INTERVAL", "300"))  # Seconds
    MAIL_FOLDER: str = os.environ.get("MAIL_FOLDER", "INBOX")
    MAIL_PROCESSED_FOLDER: str = os.environ.get("MAIL_PROCESSED_FOLDER", "Processed")
    MAIL_ERROR_FOLDER: str = os.environ.get("MAIL_ERROR_FOLDER", "Errors")

    # Special features
    MAIL_ALLOWED_SENDERS: List[str] = os.environ.get("MAIL_ALLOWED_SENDERS", "").split(",")
    MAIL_SUBJECT_KEYWORDS: List[str] = os.environ.get("MAIL_SUBJECT_KEYWORDS", "process,analyze").split(",")
    MAIL_REPLY_TO_SENDER: bool = os.environ.get("MAIL_REPLY_TO_SENDER", "True").lower() == "true"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields to support other app settings

email_settings = EmailSettings()