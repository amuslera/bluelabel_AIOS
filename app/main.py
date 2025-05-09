# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import logging
import os
from dotenv import load_dotenv

from app.core.registry.agent_registry import AgentRegistry
from app.agents.contentmind.agent import ContentMindAgent
from app.core.model_router.router import ModelRouter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bluelabel AIOS",
    description="Agentic Intelligence Operating System",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model router
model_router_config = {
    "LOCAL_LLM_ENABLED": os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true",
    "LOCAL_LLM_HOST": os.getenv("LOCAL_LLM_HOST", "http://localhost:11434"),
    "LOCAL_LLM_MODEL": os.getenv("LOCAL_LLM_MODEL", "llama3")
}
model_router = ModelRouter(config=model_router_config)

# Initialize agent registry
agent_registry = AgentRegistry()

# Register ContentMind agent
content_mind_config = {
    "name": "contentmind",
    "description": "Processes and organizes content from various sources",
    "supported_content_types": ["url"],
    "features": ["content extraction", "summarization", "entity extraction", "tagging"]
}
content_mind_agent = ContentMindAgent(config=content_mind_config, model_router=model_router)
agent_registry.register_agent("contentmind", content_mind_agent)


# Dependency to get agent registry
def get_agent_registry():
    return agent_registry


@app.get("/")
async def root():
    return {"message": "Welcome to Bluelabel AIOS API"}


@app.get("/agents")
async def list_agents(registry: AgentRegistry = Depends(get_agent_registry)):
    """List all available agents"""
    return registry.list_available_agents()


@app.post("/agents/{agent_name}/process")
async def process_with_agent(
    agent_name: str,
    request: Dict[str, Any],
    registry: AgentRegistry = Depends(get_agent_registry)
):
    """Process a request with a specific agent"""
    try:
        result = await registry.process_with_agent(agent_name, request)
        return result
    except Exception as e:
        logger.error(f"Error processing with agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-openai")
async def test_openai():
    """Test the OpenAI integration"""
    try:
        # Create a simple request to test the model router
        test_content = {"text": "This is a test message. Please summarize it."}
        result = await model_router._process_with_openai(
            task="summarize", 
            content=test_content, 
            requirements={"model": "gpt-3.5-turbo", "max_tokens": 100}
        )
        return {
            "status": "success",
            "test_result": result
        }
    except Exception as e:
        logger.error(f"Error testing OpenAI: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/test-anthropic")
async def test_anthropic():
    """Test the Anthropic integration"""
    try:
        # Create a simple request to test the model router
        test_content = {"text": "This is a test message. Please summarize it."}
        result = await model_router._process_with_anthropic(
            task="summarize", 
            content=test_content, 
            requirements={"model": "claude-3-sonnet", "max_tokens": 100}
        )
        return {
            "status": "success",
            "test_result": result
        }
    except Exception as e:
        logger.error(f"Error testing Anthropic: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/test-local")
async def test_local(model: Optional[str] = None):
    """Test the local LLM integration"""
    try:
        # First check if local LLM is available
        is_available = await model_router.is_local_available()
        if not is_available:
            return {
                "status": "error",
                "message": "Local LLM is not available"
            }
        
        # If a model is specified, try to pull it
        if model:
            if not model_router.ollama_client:
                return {
                    "status": "error",
                    "message": "Local LLM client not initialized"
                }
            
            # Try to pull the model
            pull_result = await model_router.ollama_client.pull_model(model)
            if pull_result.get("status") != "success":
                return pull_result
        
        # Create a simple request to test the model router
        test_content = {"text": "This is a test message. Please summarize it."}
        result = await model_router._process_with_local(
            task="summarize", 
            content=test_content, 
            requirements={"model": model} if model else {}
        )
        return {
            "status": "success",
            "test_result": result
        }
    except Exception as e:
        logger.error(f"Error testing local LLM: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/list-local-models")
async def list_local_models():
    """List available local LLM models"""
    try:
        if not model_router.ollama_client:
            return {
                "status": "error",
                "message": "Local LLM client not initialized"
            }
        
        models = await model_router.ollama_client.list_models()
        return {
            "status": "success",
            "models": models
        }
    except Exception as e:
        logger.error(f"Error listing local models: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/test-anthropic-simple")
async def test_anthropic_simple():
    """Simple test for Anthropic API key"""
    try:
        from anthropic import Anthropic
        
        if not os.getenv("ANTHROPIC_API_KEY"):
            return {
                "status": "error",
                "message": "ANTHROPIC_API_KEY not found in environment variables"
            }
            
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Just retrieve available models to verify the API key works
        try:
            # Simple test message
            response = client.messages.create(
                model="claude-3-sonnet",
                max_tokens=10,
                system="Be very brief",
                messages=[
                    {"role": "user", "content": "Say hello"}
                ]
            )
            return {
                "status": "success",
                "message": "Anthropic API key is valid",
                "response": response.content[0].text if response.content else "No content",
                "model": "claude-3-sonnet"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing Anthropic API: {str(e)}",
                "details": str(e)
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error importing or initializing Anthropic: {str(e)}"
        }


@app.post("/pull-model")
async def pull_model(model: str):
    """Pull a specific model from Ollama"""
    try:
        if not model_router.ollama_client:
            return {
                "status": "error",
                "message": "Local LLM client not initialized"
            }
        
        result = await model_router.ollama_client.pull_model(model)
        return result
    except Exception as e:
        logger.error(f"Error pulling model: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }