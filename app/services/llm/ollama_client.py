# app/services/llm/ollama_client.py
import aiohttp
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with local Ollama LLM service"""
    
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.api_base = f"{host}/api"
        logger.info(f"Initialized Ollama client with host: {host}")
    
    async def test_connection(self) -> bool:
        """Alias for is_available for compatibility"""
        return await self.is_available()

    async def is_available(self, timeout: float = 5.0) -> bool:
        """Check if Ollama service is available

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if service is available, False otherwise
        """
        try:
            # Configure timeout for quick service check
            timeout_config = aiohttp.ClientTimeout(
                total=timeout,
                sock_connect=2.0,
                sock_read=3.0
            )

            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                try:
                    async with session.get(f"{self.host}") as response:
                        return response.status == 200
                except asyncio.TimeoutError:
                    logger.warning(f"Ollama service check timed out after {timeout}s")
                    return False
        except Exception as e:
            logger.warning(f"Ollama service check failed: {str(e)}")
            return False
    
    async def list_models(self, timeout: float = 5.0) -> List[str]:
        """List available models

        Args:
            timeout: Connection timeout in seconds

        Returns:
            List of available model names
        """
        try:
            # Configure timeout for quick list operation
            timeout_config = aiohttp.ClientTimeout(
                total=timeout,
                sock_connect=2.0,
                sock_read=3.0
            )

            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                try:
                    async with session.get(f"{self.api_base}/tags") as response:
                        if response.status == 200:
                            result = await response.json()

                            # Extract model names from the response
                            if isinstance(result, dict) and "models" in result:
                                # New API format
                                models = [m["name"] for m in result["models"] if isinstance(m, dict) and "name" in m]
                                return models
                            # If the API format is different, try to extract model names
                            return []
                        else:
                            logger.warning(f"Failed to list models: {response.status}")
                            return []
                except asyncio.TimeoutError:
                    logger.warning(f"Listing models timed out after {timeout}s")
                    return []
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    async def pull_model(self, model: str, timeout: float = 300.0) -> Dict[str, Any]:
        """Pull a model from Ollama

        Args:
            model: Name of the model to pull
            timeout: Connection timeout in seconds (longer for model downloads)

        Returns:
            Dictionary with pull result
        """
        try:
            payload = {"name": model}

            # Configure timeout with longer limits for model pulling
            # (downloading models can take a while)
            timeout_config = aiohttp.ClientTimeout(
                total=timeout,
                sock_connect=10.0,
                sock_read=timeout
            )

            logger.info(f"Pulling model {model} with {timeout}s timeout")
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                try:
                    async with session.post(f"{self.api_base}/pull", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Model {model} pulled successfully")
                            return {
                                "status": "success",
                                "model": model,
                                "message": "Model pulled successfully"
                            }
                        else:
                            error_text = await response.text()
                            logger.warning(f"Failed to pull model: {response.status}, {error_text}")
                            return {
                                "status": "error",
                                "message": f"Failed to pull model: {response.status}, {error_text}"
                            }
                except asyncio.TimeoutError:
                    logger.error(f"Timeout ({timeout}s) reached while pulling model {model}")
                    return {
                        "status": "error",
                        "message": f"Model pulling timed out after {timeout} seconds",
                        "error_type": "timeout"
                    }
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return {
                "status": "error",
                "message": f"Error pulling model: {str(e)}",
                "error_type": "exception"
            }
    
    async def generate(self,
                      prompt: str,
                      model: str = "llama3",
                      system_prompt: Optional[str] = None,
                      temperature: float = 0.7,
                      max_tokens: int = 500,
                      timeout: float = 30.0) -> Dict[str, Any]:
        """Generate text with the local model

        Args:
            prompt: The prompt to send to the model
            model: The model to use
            system_prompt: Optional system prompt
            temperature: Temperature for sampling (0-1)
            max_tokens: Maximum tokens to generate
            timeout: Timeout for the request in seconds

        Returns:
            Dictionary with generation result
        """
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

            # Configure timeout at the session and connection level
            timeout_config = aiohttp.ClientTimeout(
                total=timeout,
                sock_connect=10.0,  # Socket connection timeout
                sock_read=timeout   # Socket read timeout
            )

            logger.info(f"Sending generate request to Ollama with {timeout}s timeout")
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                try:
                    async with session.post(f"{self.api_base}/generate", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Ollama generation successful, received {len(result.get('response', ''))} chars")
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
                except asyncio.TimeoutError:
                    logger.error(f"Timeout ({timeout}s) reached while generating with Ollama")
                    return {
                        "status": "error",
                        "message": f"Generation timed out after {timeout} seconds",
                        "error_type": "timeout"
                    }
        except Exception as e:
            logger.error(f"Error generating with Ollama: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating with Ollama: {str(e)}",
                "error_type": "exception"
            }