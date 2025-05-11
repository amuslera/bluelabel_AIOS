# app/core/model_router/__init__.py
# Import will be done at usage site to avoid circular imports

# Define enums here to avoid circular imports
from enum import Enum

class ModelType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"

class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

__all__ = ["ModelType", "Provider"]