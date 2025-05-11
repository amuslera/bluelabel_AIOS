# app/core/config_file.py
from typing import Optional, Dict, Any, List
import os
import json
from pathlib import Path
import dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load .env file
dotenv.load_dotenv()

# Try to load server_config.json if available
CONFIG_FILE = Path(__file__).parent.parent.parent / "server_config.json"

class Settings:
    PROJECT_NAME: str = "Bluelabel AIOS"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./bluelabel.db")

    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    LOCAL_LLM_ENABLED: bool = os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"
    LOCAL_LLM_HOST: str = os.getenv("LOCAL_LLM_HOST", "http://localhost:11434")
    LOCAL_LLM_TIMEOUT: int = int(os.getenv("LOCAL_LLM_TIMEOUT", "30"))
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3")

    # Content processing settings
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "100000"))
    SUPPORTED_CONTENT_TYPES: List[str] = ["url", "pdf", "text", "audio", "social"]

    # Agent settings
    AVAILABLE_AGENTS: List[str] = ["contentmind"]

    # Server settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8080
    UI_HOST: str = "127.0.0.1"
    UI_PORT: int = 8502

    def __init__(self):
        # Try to load config from file
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {CONFIG_FILE}")

                    # Update settings from config file
                    self._update_from_config(config)

            except Exception as e:
                logger.warning(f"Failed to load config from {CONFIG_FILE}: {str(e)}")

    def _update_from_config(self, config: Dict[str, Any]):
        """Update settings from config file"""
        # Update API settings
        if "api" in config:
            self.API_HOST = config["api"].get("host", self.API_HOST)
            self.API_PORT = config["api"].get("port", self.API_PORT)

        # Update UI settings
        if "ui" in config:
            self.UI_HOST = config["ui"].get("host", self.UI_HOST)
            self.UI_PORT = config["ui"].get("port", self.UI_PORT)

        # Update database settings
        if "database" in config:
            self.DATABASE_URL = config["database"].get("url", self.DATABASE_URL)

        # Update LLM settings
        if "llm" in config:
            if "local" in config["llm"]:
                self.LOCAL_LLM_ENABLED = config["llm"]["local"].get("enabled", self.LOCAL_LLM_ENABLED)
                self.LOCAL_LLM_HOST = config["llm"]["local"].get("host", self.LOCAL_LLM_HOST)
                self.LOCAL_LLM_MODEL = config["llm"]["local"].get("default_model", self.LOCAL_LLM_MODEL)
                self.LOCAL_LLM_TIMEOUT = config["llm"]["local"].get("default_timeout", self.LOCAL_LLM_TIMEOUT)

# Create settings instance
settings = Settings()