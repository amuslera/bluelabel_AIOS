from typing import Optional, Dict, Any, List
import os
from pathlib import Path
import dotenv
import json

# Load .env file
dotenv.load_dotenv()

# Default config
DEFAULT_CONFIG = {
    "project_name": "Bluelabel AIOS",
    "api_v1_str": "/api/v1",

    # Database settings
    "database": {
        "url": "sqlite:///./bluelabel.db"
    },

    # LLM settings
    "llm": {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "local_llm_enabled": os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true",
        "local_llm_host": os.getenv("LOCAL_LLM_HOST"),
        "default_provider": os.getenv("DEFAULT_LLM_PROVIDER", "anthropic")
    },

    # Content processing settings
    "content": {
        "max_length": int(os.getenv("MAX_CONTENT_LENGTH", "100000")),
        "supported_types": ["url", "pdf", "text", "audio", "social"]
    },

    # Agent settings
    "agents": {
        "available": ["contentmind"]
    },

    # MCP settings
    "mcp": {
        "storage_dir": os.getenv("MCP_STORAGE_DIR", os.path.expanduser("~/.bluelabel/components")),
        "load_examples": os.getenv("MCP_LOAD_EXAMPLES", "true").lower() == "true"
    }
}

# Config singleton
_config = None

def get_config() -> Dict[str, Any]:
    """Get the application configuration.

    Returns:
        Dictionary with configuration values.
    """
    global _config

    if _config is None:
        # Check for config file
        config_path = os.getenv("CONFIG_FILE", "config.json")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)

                # Merge configs
                _config = _merge_configs(DEFAULT_CONFIG, file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
                _config = DEFAULT_CONFIG
        else:
            _config = DEFAULT_CONFIG

    return _config

def _merge_configs(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two configuration dictionaries.

    Args:
        default: Default configuration.
        override: Configuration to override defaults.

    Returns:
        Merged configuration.
    """
    result = default.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result

class Settings:
    """Settings class for backwards compatibility."""

    def __init__(self):
        """Initialize settings from config."""
        self._config = get_config()

    @property
    def PROJECT_NAME(self) -> str:
        return self._config["project_name"]

    @property
    def API_V1_STR(self) -> str:
        return self._config["api_v1_str"]

    @property
    def DATABASE_URL(self) -> str:
        return self._config["database"]["url"]

    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        return self._config["llm"]["openai_api_key"]

    @property
    def ANTHROPIC_API_KEY(self) -> Optional[str]:
        return self._config["llm"]["anthropic_api_key"]

    @property
    def LOCAL_LLM_ENABLED(self) -> bool:
        return self._config["llm"]["local_llm_enabled"]

    @property
    def LOCAL_LLM_HOST(self) -> Optional[str]:
        return self._config["llm"]["local_llm_host"]

    @property
    def MAX_CONTENT_LENGTH(self) -> int:
        return self._config["content"]["max_length"]

    @property
    def SUPPORTED_CONTENT_TYPES(self) -> List[str]:
        return self._config["content"]["supported_types"]

    @property
    def AVAILABLE_AGENTS(self) -> List[str]:
        return self._config["agents"]["available"]

    @property
    def MCP_STORAGE_DIR(self) -> str:
        return self._config["mcp"]["storage_dir"]

    @property
    def MCP_LOAD_EXAMPLES(self) -> bool:
        return self._config["mcp"]["load_examples"]

settings = Settings()