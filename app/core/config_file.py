# app/core/config_file.py
from typing import Optional, Dict, Any, List
import os
from pathlib import Path
import dotenv

# Load .env file
dotenv.load_dotenv()

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
    
    # Content processing settings
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "100000"))
    SUPPORTED_CONTENT_TYPES: List[str] = ["url", "pdf", "text", "audio", "social"]
    
    # Agent settings
    AVAILABLE_AGENTS: List[str] = ["contentmind"]

settings = Settings()