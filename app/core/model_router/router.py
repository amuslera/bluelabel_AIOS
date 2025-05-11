# app/core/model_router/router.py
from typing import Dict, Any, List, Optional
import logging
import os
import json
from datetime import datetime
from app.core.registry.service_provider import get_component_registry
from app.core.model_router import ModelType, Provider

# Configure logging
logger = logging.getLogger(__name__)

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

        # First check if Ollama server is reachable
        try:
            if not await self.ollama_client.is_available(timeout=3.0):
                logger.warning("Ollama server is not available")
                return False

            # Then check if the model exists
            models = await self.ollama_client.list_models(timeout=5.0)

            if not models:
                logger.warning("No models available in Ollama")
                return False

            if self.local_model not in models:
                logger.info(f"Local model {self.local_model} not found in {models}, attempting to pull it...")
                pull_result = await self.ollama_client.pull_model(self.local_model)

                if pull_result.get("status") != "success":
                    logger.error(f"Failed to pull model {self.local_model}: {pull_result.get('message')}")
                    return False

                logger.info(f"Successfully pulled model {self.local_model}")
            else:
                logger.info(f"Found model {self.local_model} in available models")

            return True

        except Exception as e:
            logger.error(f"Error checking/pulling local model: {str(e)}")
            return False
    
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
        try:
            # Starting a timed task
            logger.info(f"Beginning LLM routing for task: '{task}'")
            import asyncio
            import time
            start_time = time.time()

            requirements = requirements or {}
            model_preference = requirements.get("model_preference")
            provider_preference = requirements.get("provider")

            # Apply global timeout for the entire routing operation
            global_timeout = requirements.get("global_timeout", 60)  # Default to 60 seconds

            async def _do_routing():
                # If provider is explicitly specified, use it
                if provider_preference:
                    if provider_preference == Provider.OPENAI:
                        return await self._process_with_openai(task, content, requirements)
                    elif provider_preference == Provider.ANTHROPIC:
                        return await self._process_with_anthropic(task, content, requirements)
                    elif provider_preference == Provider.LOCAL:
                        # Use local with built-in fallback
                        return await self._process_with_local(task, content, requirements)

                # If model type is explicitly specified, respect it
                if model_preference:
                    if model_preference == ModelType.LOCAL:
                        # Use local with built-in fallback
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
                            # Use simplified result as last resort
                            return self._generate_simplified_result(task, content, "NO_CLOUD_PROVIDERS")

                # Otherwise, make routing decision based on availability, complexity, and task type
                try:
                    # Use fallback assessment with strict timeout
                    complexity = 0.5  # Default complexity
                    try:
                        complexity_future = self.assess_complexity(task, content)
                        complexity = await asyncio.wait_for(complexity_future, timeout=2.0)
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.warning(f"Complexity assessment timed out or failed: {str(e)}")

                    # Check local availability with strict timeout
                    is_local_available = False
                    try:
                        local_check = self.is_local_available()
                        is_local_available = await asyncio.wait_for(local_check, timeout=3.0)
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.warning(f"Local availability check timed out or failed: {str(e)}")

                    # For specific tasks, prefer certain providers
                    if task == "extract_entities" and self.anthropic_api_key:
                        # Claude is particularly good at structured data tasks
                        return await self._process_with_anthropic(task, content, requirements)

                    # Always try local first if available, with built-in fallback
                    if is_local_available:
                        logger.info(f"Attempting task '{task}' with local LLM first")
                        return await self._process_with_local(task, content, requirements)
                    else:
                        logger.info(f"Local LLM not available, routing task '{task}' to cloud or fallback")
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
                            # Use simplified result as last resort
                            return self._generate_simplified_result(task, content, "NO_PROVIDERS_AVAILABLE")
                except Exception as inner_e:
                    logger.error(f"Error during provider selection: {str(inner_e)}")
                    return self._generate_simplified_result(task, content, f"ROUTING_ERROR: {str(inner_e)}")

            # Execute the routing with a global timeout
            try:
                # Create a named task for better debugging
                routing_task = asyncio.create_task(_do_routing(), name=f"llm_routing_{task}")

                try:
                    # Wait for the task with a timeout
                    result = await asyncio.wait_for(routing_task, timeout=global_timeout)

                    # Log completion time
                    elapsed_time = time.time() - start_time
                    logger.info(f"LLM routing for task '{task}' completed in {elapsed_time:.2f} seconds")

                    return result
                except asyncio.TimeoutError:
                    # Properly cancel the task when timeout occurs to prevent orphaned tasks
                    if not routing_task.done():
                        logger.warning(f"Cancelling routing task due to timeout")
                        routing_task.cancel()

                        # Wait briefly for cancellation to complete, with a short timeout
                        try:
                            await asyncio.wait_for(routing_task, timeout=2.0)
                        except (asyncio.TimeoutError, asyncio.CancelledError):
                            pass

                    logger.error(f"Global timeout ({global_timeout}s) exceeded for task '{task}'")
                    return self._generate_simplified_result(task, content, "GLOBAL_TIMEOUT")
            except asyncio.CancelledError:
                logger.warning(f"LLM routing for task '{task}' was cancelled by parent")
                # Re-raise to allow proper cancellation propagation
                raise

        except Exception as e:
            # Last-resort error handling
            logger.error(f"Critical error in route_request: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process request: {str(e)}",
                "fallback_used": True
            }
    
    async def _process_with_local(self, task: str, content: Dict[str, Any],
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with local LLM"""
        if not self.ollama_client:
            logger.warning("Local LLM processing requested but client not initialized")
            # Try to provide a simplified result when possible rather than failing completely
            return self._generate_simplified_result(task, content, "LOCAL_LLM_NOT_INITIALIZED")

        # Check local availability directly, since is_local_available now handles timeouts internally
        try:
            # Use direct call - all timeouts handled within the method
            is_available = await self.is_local_available()
            logger.info(f"Local LLM availability check result: {is_available}")
        except Exception as e:
            logger.error(f"Error checking local LLM availability: {str(e)}")
            is_available = False

        if not is_available:
            logger.warning("Local LLM not available, using fallback")
            return self._generate_simplified_result(task, content, "LOCAL_LLM_UNAVAILABLE")

        # Prepare the prompt
        prompt = self._create_prompt(task, content)

        # Get parameters from requirements
        model = requirements.get("model", self.local_model)
        max_tokens = requirements.get("max_tokens", 500)
        temperature = requirements.get("temperature", 0.0)  # Lower for more deterministic outputs
        timeout = requirements.get("timeout", 30)  # Increased timeout to 30 seconds

        # Use specialized system prompts for different tasks
        system_prompt = self._create_system_prompt(task)

        try:
            # Generate response with Ollama with timeout
            logger.info(f"Generating with local model: {model}")
            import asyncio

            # Pass the timeout to the client directly instead of using wait_for+shield
            # which can lead to orphaned tasks
            logger.info(f"Sending Ollama generation request directly with {timeout}s timeout")
            response = await self.ollama_client.generate(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )

            logger.info(f"Ollama generation call completed with status: {response.get('status')}")

            if response.get("status") == "success":
                return {
                    "status": "success",
                    "provider": Provider.LOCAL,
                    "model": model,
                    "result": response.get("result", ""),
                    "processed_at": datetime.now().isoformat()
                }
            else:
                # If local fails, use simplified result
                logger.warning(f"Local LLM processing failed: {response.get('message')}. Using fallback.")
                return self._generate_simplified_result(task, content, f"LOCAL_PROCESSING_FAILED: {response.get('message')}")

        except asyncio.TimeoutError:
            logger.warning(f"Local LLM processing timed out after {timeout} seconds. Using fallback.")
            return self._generate_simplified_result(task, content, "TIMEOUT")
        except Exception as e:
            logger.error(f"Error in local LLM processing: {str(e)}. Using fallback.")
            return self._generate_simplified_result(task, content, f"ERROR: {str(e)}")

    def _generate_simplified_result(self, task: str, content: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Generate a simplified result when LLM processing is not available

        Args:
            task: The task type
            content: The content dictionary
            reason: The reason for using simplified processing

        Returns:
            A simplified result dictionary
        """
        logger.info(f"Generating simplified result for task '{task}' due to: {reason}")

        # Create appropriate fallback responses based on task type
        if task == "summarize":
            # Extract first few sentences as a simple summary
            text = content.get("text", "")
            sentences = text.split('.')
            simple_summary = '. '.join(sentences[:3]) + '.' if sentences else "No text available for summary."

            return {
                "status": "success",
                "provider": "fallback",
                "model": "none",
                "result": simple_summary,
                "processed_at": datetime.now().isoformat(),
                "fallback_reason": reason
            }

        elif task == "extract_entities":
            # Return an empty JSON object for entities
            return {
                "status": "success",
                "provider": "fallback",
                "model": "none",
                "result": "{}",  # Empty entities object
                "processed_at": datetime.now().isoformat(),
                "fallback_reason": reason
            }

        elif task == "tag_content":
            # Extract some words from the text as basic tags
            text = content.get("text", "")
            words = text.split()
            # Take some common words that might make reasonable tags
            potential_tags = [w.lower() for w in words if len(w) > 4][:10]
            # Remove duplicates
            unique_tags = list(set(potential_tags))
            # Take up to 5 tags
            simple_tags = ", ".join(unique_tags[:5])

            return {
                "status": "success",
                "provider": "fallback",
                "model": "none",
                "result": simple_tags,
                "processed_at": datetime.now().isoformat(),
                "fallback_reason": reason
            }

        else:
            # Generic fallback
            return {
                "status": "success",
                "provider": "fallback",
                "model": "none",
                "result": "Unable to process with LLM. Using fallback mechanism.",
                "processed_at": datetime.now().isoformat(),
                "fallback_reason": reason
            }
    
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
        """Create an appropriate system prompt for the task

        Attempts to use a system prompt component if available,
        otherwise falls back to the hardcoded prompts.
        """
        # Try to get component from registry
        component_id = f"system_prompt_{task}"
        registry = get_component_registry()

        if registry:
            component = registry.get_component(component_id)
            if component:
                try:
                    # Render the component with empty inputs (system prompts typically don't need inputs)
                    return component.render({})
                except Exception as e:
                    logger.warning(f"Error rendering system prompt component {component_id}: {str(e)}")

        # Fall back to hardcoded prompts
        if task == "summarize":
            return """You are a precise summarization assistant. Your task is to create concise, accurate summaries of content that capture the key points and main message. Focus on the most important information and maintain the original meaning. Be clear, factual, and objective."""

        elif task == "extract_entities":
            return """You are an entity extraction assistant. Your task is to identify and categorize key entities mentioned in the content. Focus on people, organizations, products, concepts, and technologies. Format your output as a valid JSON object with categories as keys and arrays of entities as values. Do not include any explanatory text - only output the JSON object."""

        elif task == "tag_content":
            return """You are a content tagging assistant. Your task is to generate relevant tags for content that accurately represent the topics, themes, and subjects covered. Create 5-10 tags that would help categorize and discover this content. Return only a comma-separated list of tags without any explanations or additional text."""

        else:
            return "You are a helpful assistant that processes content."

    def _create_prompt(self, task: str, content: Dict[str, Any]) -> str:
        """Create a prompt for the LLM based on the task and content

        Attempts to use a task component if available,
        otherwise falls back to the hardcoded prompts.
        """
        # Try to get component from registry
        component_id = f"task_{task}"
        registry = get_component_registry()

        if registry:
            component = registry.get_component(component_id)
            if component:
                try:
                    # Prepare inputs for the component
                    inputs = {"text": content.get("text", "")}

                    # Add any additional inputs from the content
                    for key, value in content.items():
                        if key != "text":
                            inputs[key] = value

                    # Render the component with the inputs
                    return component.render(inputs)
                except Exception as e:
                    logger.warning(f"Error rendering task component {component_id}: {str(e)}")

        # Fall back to hardcoded prompts
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