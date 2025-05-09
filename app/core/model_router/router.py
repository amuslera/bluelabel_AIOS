# app/core/model_router/router.py
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import os
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"

class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"

class ModelRouter:
    """Routes requests to appropriate LLM based on context"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.local_enabled = config.get("LOCAL_LLM_ENABLED", False)
        self.local_host = config.get("LOCAL_LLM_HOST", "http://localhost:11434")
        self.local_model = config.get("LOCAL_LLM_MODEL", "llama3")
        
        # Initialize local client if enabled
        self.ollama_client = None
        if self.local_enabled:
            from app.services.llm.ollama_client import OllamaClient
            self.ollama_client = OllamaClient(host=self.local_host)
        
        # Set up API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Initialize available models
        self.available_anthropic_models = []
        
        logger.info(f"Model Router initialized. Local LLM enabled: {self.local_enabled}")
        logger.info(f"OpenAI API key available: {self.openai_api_key is not None}")
        logger.info(f"Anthropic API key available: {self.anthropic_api_key is not None}")
    
    async def is_local_available(self) -> bool:
        """Check if local LLM is available"""
        if not self.local_enabled or not self.ollama_client:
            return False
        
        # First check if the model exists
        try:
            models = await self.ollama_client.list_models()
            if self.local_model not in models:
                logger.info(f"Local model {self.local_model} not found, attempting to pull it...")
                await self.ollama_client.pull_model(self.local_model)
                logger.info(f"Successfully pulled model {self.local_model}")
        except Exception as e:
            logger.error(f"Error checking/pulling local model: {str(e)}")
            return False
        
        return await self.ollama_client.is_available()
    
    async def assess_complexity(self, task: str, content: Dict[str, Any]) -> float:
        """Assess the complexity of a task (0.0-1.0)"""
        # Simple mapping of tasks to complexity
        complexity_mapping = {
            "summarize": 0.3,
            "extract_entities": 0.4,
            "generate_insights": 0.7,
            "tag_content": 0.5
        }
        
        # For now, we'll use a simple lookup.
        # Later, we could implement a more sophisticated approach.
        return complexity_mapping.get(task, 0.5)
    
    async def route_request(self, task: str, content: Dict[str, Any], 
                           requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route the request to appropriate LLM based on context"""
        
        requirements = requirements or {}
        model_preference = requirements.get("model_preference")
        provider_preference = requirements.get("provider")
        
        # If provider is explicitly specified, use it
        if provider_preference:
            if provider_preference == Provider.OPENAI:
                return await self._process_with_openai(task, content, requirements)
            elif provider_preference == Provider.ANTHROPIC:
                return await self._process_with_anthropic(task, content, requirements)
            elif provider_preference == Provider.LOCAL:
                # Try local first, with automatic fallback to cloud
                return await self._process_with_local(task, content, requirements)
        
        # If model type is explicitly specified, respect it
        if model_preference:
            if model_preference == ModelType.LOCAL:
                # Try local first, with automatic fallback to cloud
                return await self._process_with_local(task, content, requirements)
            else:  # CLOUD is requested
                # Use preferred cloud provider
                if provider_preference == Provider.ANTHROPIC and self.anthropic_api_key:
                    return await self._process_with_anthropic(task, content, requirements)
                elif provider_preference == Provider.OPENAI and self.openai_api_key:
                    return await self._process_with_openai(task, content, requirements)
                # Or fall back to available provider
                elif self.openai_api_key:
                    return await self._process_with_openai(task, content, requirements)
                elif self.anthropic_api_key:
                    return await self._process_with_anthropic(task, content, requirements)
                else:
                    return {"status": "error", "message": "No cloud providers configured"}
        
        # Otherwise, make routing decision based on availability, complexity, and task type
        complexity = await self.assess_complexity(task, content)
        is_local_available = await self.is_local_available()
        
        # For specific tasks, prefer certain providers
        if task == "extract_entities" and self.anthropic_api_key:
            # Claude is particularly good at structured data tasks
            return await self._process_with_anthropic(task, content, requirements)
        
        # Always try local first if available, regardless of complexity
        if is_local_available:
            logger.info(f"Attempting task '{task}' with local LLM first")
            return await self._process_with_local(task, content, requirements)
        else:
            logger.info(f"Local LLM not available, routing task '{task}' to cloud LLM")
            # Choose cloud provider based on preference, availability, and task
            if provider_preference == Provider.ANTHROPIC and self.anthropic_api_key:
                return await self._process_with_anthropic(task, content, requirements)
            elif provider_preference == Provider.OPENAI and self.openai_api_key:
                return await self._process_with_openai(task, content, requirements)
            elif self.anthropic_api_key and (complexity > 0.6 or task in ["extract_entities", "tag_content"]):
                # Prefer Anthropic for complex tasks or specific task types
                return await self._process_with_anthropic(task, content, requirements)
            elif self.openai_api_key:
                return await self._process_with_openai(task, content, requirements)
            elif self.anthropic_api_key:
                return await self._process_with_anthropic(task, content, requirements)
            else:
                return {"status": "error", "message": "No cloud providers configured"}
    
    async def _process_with_local(self, task: str, content: Dict[str, Any], 
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with local LLM"""
        if not self.ollama_client:
            logger.warning("Local LLM processing requested but client not initialized")
            return await self._process_with_cloud(task, content, requirements)
        
        # Check local availability
        is_available = await self.is_local_available()
        if not is_available:
            logger.warning("Local LLM not available, falling back to cloud")
            return await self._process_with_cloud(task, content, requirements)
        
        # Prepare the prompt
        prompt = self._create_prompt(task, content)
        
        # Get parameters from requirements
        model = requirements.get("model", self.local_model)
        max_tokens = requirements.get("max_tokens", 500)
        temperature = requirements.get("temperature", 0.0)  # Lower for more deterministic outputs
        timeout = requirements.get("timeout", 10)  # Default timeout of 10 seconds
        
        # Use specialized system prompts for different tasks
        system_prompt = self._create_system_prompt(task)
        
        try:
            # Generate response with Ollama with timeout
            logger.info(f"Generating with local model: {model}")
            import asyncio
            response = await asyncio.wait_for(
                self.ollama_client.generate(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=timeout
            )
            
            if response.get("status") == "success":
                return {
                    "status": "success",
                    "provider": Provider.LOCAL,
                    "model": model,
                    "result": response.get("result", ""),
                    "processed_at": datetime.now().isoformat()
                }
            else:
                # If local fails, fall back to cloud
                logger.warning(f"Local LLM processing failed: {response.get('message')}. Falling back to cloud.")
                return await self._process_with_cloud(task, content, requirements)
                
        except asyncio.TimeoutError:
            logger.warning(f"Local LLM processing timed out after {timeout} seconds. Falling back to cloud.")
            return await self._process_with_cloud(task, content, requirements)
        except Exception as e:
            logger.error(f"Error in local LLM processing: {str(e)}. Falling back to cloud.")
            return await self._process_with_cloud(task, content, requirements)
    
    async def _process_with_cloud(self, task: str, content: Dict[str, Any], 
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with cloud LLM"""
        provider = requirements.get("provider", Provider.OPENAI if self.openai_api_key else Provider.ANTHROPIC)
        
        logger.info(f"Processing task '{task}' with cloud provider '{provider}'")
        
        if provider == Provider.OPENAI and self.openai_api_key:
            return await self._process_with_openai(task, content, requirements)
        elif provider == Provider.ANTHROPIC and self.anthropic_api_key:
            return await self._process_with_anthropic(task, content, requirements)
        elif self.openai_api_key:
            # Fall back to OpenAI if specified provider not available
            return await self._process_with_openai(task, content, requirements)
        elif self.anthropic_api_key:
            # Fall back to Anthropic if specified provider not available
            return await self._process_with_anthropic(task, content, requirements)
        else:
            return {
                "status": "error",
                "message": "No cloud providers configured"
            }
    
    async def _process_with_openai(self, task: str, content: Dict[str, Any], 
                                  requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with OpenAI API"""
        if not self.openai_api_key:
            return {
                "status": "error",
                "message": "OpenAI API key not configured"
            }
        
        try:
            # Import OpenAI client
            from openai import OpenAI
            
            # Initialize client
            client = OpenAI(api_key=self.openai_api_key)
            
            # Get parameters from requirements
            model = requirements.get("model", "gpt-3.5-turbo")
            max_tokens = requirements.get("max_tokens", 500)
            temperature = requirements.get("temperature", 0.0)  # Lower for more deterministic outputs
            
            # Create prompts
            prompt = self._create_prompt(task, content)
            system_prompt = self._create_system_prompt(task)
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API with model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract the response text
            result = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "provider": Provider.OPENAI,
                "model": model,
                "result": result,
                "processed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing with OpenAI: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing with OpenAI: {str(e)}"
            }
    
    async def _process_with_anthropic(self, task: str, content: Dict[str, Any], 
                                     requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with Anthropic API"""
        if not self.anthropic_api_key:
            return {
                "status": "error",
                "message": "Anthropic API key not configured"
            }
        
        try:
            # Import Anthropic client
            from anthropic import Anthropic
            
            # Initialize client
            client = Anthropic(api_key=self.anthropic_api_key)
            
            # Get available models if not already fetched
            if not self.available_anthropic_models:
                self.available_anthropic_models = await self._get_available_anthropic_models()
            
            # Get parameters from requirements
            requested_model = requirements.get("model", "").lower()
            
            # Try to find a matching model from available models
            model = None
            if requested_model in self.available_anthropic_models:
                model = requested_model
            else:
                # Try to find a model that starts with the requested name
                matching_models = [m for m in self.available_anthropic_models if m.startswith(requested_model)]
                if matching_models:
                    model = matching_models[0]  # Use the first matching model
                else:
                    # If no match found, use the first available model
                    model = self.available_anthropic_models[0] if self.available_anthropic_models else None
            
            if not model:
                return {
                    "status": "error",
                    "message": "No available Anthropic models found"
                }
            
            # Log the model selection for debugging
            logger.info(f"Requested Anthropic model: {requested_model}")
            logger.info(f"Using Anthropic model: {model}")
            
            max_tokens = requirements.get("max_tokens", 500)
            temperature = requirements.get("temperature", 0.0)
            
            # Create prompts
            system_prompt = self._create_system_prompt(task)
            prompt = self._create_prompt(task, content)
            
            # Call Anthropic API
            logger.info(f"Calling Anthropic API with model: {model}")
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the response text
            result = response.content[0].text
            
            return {
                "status": "success",
                "provider": Provider.ANTHROPIC,
                "model": model,
                "result": result,
                "processed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing with Anthropic: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing with Anthropic: {str(e)}"
            }
    
    def _create_system_prompt(self, task: str) -> str:
        """Create an appropriate system prompt for the task"""
        if task == "summarize":
            return """You are a precise summarization assistant. Your task is to create concise, accurate summaries of content that capture the key points and main message. Focus on the most important information and maintain the original meaning. Be clear, factual, and objective."""
            
        elif task == "extract_entities":
            return """You are an entity extraction assistant. Your task is to identify and categorize key entities mentioned in the content. Focus on people, organizations, products, concepts, and technologies. Format your output as a valid JSON object with categories as keys and arrays of entities as values. Do not include any explanatory text - only output the JSON object."""
            
        elif task == "tag_content":
            return """You are a content tagging assistant. Your task is to generate relevant tags for content that accurately represent the topics, themes, and subjects covered. Create 5-10 tags that would help categorize and discover this content. Return only a comma-separated list of tags without any explanations or additional text."""
            
        else:
            return "You are a helpful assistant that processes content."
    
    def _create_prompt(self, task: str, content: Dict[str, Any]) -> str:
        """Create a prompt for the LLM based on the task and content"""
        if task == "summarize":
            text = content.get("text", "")
            return f"""Summarize the following content in a concise way that captures the key points:

{text}

Summary:"""
        
        elif task == "extract_entities":
            text = content.get("text", "")
            return f"""Extract the key entities from the following content. Focus on people, organizations, products, concepts, and technologies.
Format the output as a JSON object with categories as keys and arrays of entities as values.

{text}

Entities (in JSON format):"""
        
        elif task == "tag_content":
            text = content.get("text", "")
            return f"""Generate appropriate tags for the following content. Tags should be relevant keywords that categorize the content.
Return a comma-separated list of 5-10 tags.

{text}

Tags:"""
        
        else:
            return f"Process the following content for task '{task}':\n\n{content.get('text', '')}"

    async def _get_available_anthropic_models(self) -> List[str]:
        """Fetch available models from Anthropic API"""
        if not self.anthropic_api_key:
            return []
        
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self.anthropic_api_key)
            
            # Fetch available models
            response = client.models.list()
            models = [model.id for model in response.data]
            logger.info(f"Available Anthropic models: {models}")
            return models
        except Exception as e:
            logger.error(f"Error fetching Anthropic models: {str(e)}")
            return []