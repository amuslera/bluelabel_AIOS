# app/services/llm/ollama_client.py
import aiohttp
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with local Ollama LLM service"""
    
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.api_base = f"{host}/api"
        logger.info(f"Initialized Ollama client with host: {host}")
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.host}") as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama service check failed: {str(e)}")
            return False
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/tags") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to list models: {response.status}")
                        return {"models": []}
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return {"models": []}
    
    async def generate(self, 
                      prompt: str, 
                      model: str = "llama3", 
                      system_prompt: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: int = 500) -> Dict[str, Any]:
        """Generate text with the local model"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base}/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "success",
                            "model": model,
                            "result": result.get("response", ""),
                            "finished": True
                        }
                    else:
                        error_text = await response.text()
                        logger.warning(f"Failed to generate: {response.status}, {error_text}")
                        return {
                            "status": "error",
                            "message": f"Failed to generate: {response.status}, {error_text}"
                        }
        except Exception as e:
            logger.error(f"Error generating with Ollama: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating with Ollama: {str(e)}"
            }