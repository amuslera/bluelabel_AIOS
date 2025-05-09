# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any, List, Optional

from app.core.config_file import settings
from app.core.model_router.router import ModelRouter
from app.agents.contentmind.agent import ContentMindAgent
from app.db.database import get_db, create_tables
from app.db.vector_store import VectorStore
from app.services.knowledge.knowledge_service import KnowledgeService
from app.services.llm.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title=settings.PROJECT_NAME)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Initialize vector store
    vector_store = VectorStore()
    logger.info("Vector store initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize vector store: {str(e)}")
    # Create a dummy vector store that logs errors but doesn't crash the app
    vector_store = None

try:
    # Initialize model router with settings
    model_router = ModelRouter({
        "LOCAL_LLM_ENABLED": settings.LOCAL_LLM_ENABLED,
        "LOCAL_LLM_HOST": settings.LOCAL_LLM_HOST,
        "LOCAL_LLM_MODEL": "llama3"
    })
    logger.info("Model router initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize model router: {str(e)}")
    # Continue without the model router
    model_router = None

try:
    # Initialize ContentMind agent
    content_mind = ContentMindAgent({"id": "contentmind"}, model_router) if model_router else None
    logger.info("ContentMind agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ContentMind agent: {str(e)}")
    # Continue without the agent
    content_mind = None

try:
    # Create database tables
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {str(e)}")

# Dependency for KnowledgeService
def get_knowledge_service(db: Session = Depends(get_db)):
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store is not available")
    return KnowledgeService(db, vector_store)

@app.get("/")
async def root():
    return {"message": "Welcome to Bluelabel AIOS API"}

@app.post("/agents/contentmind/process")
async def process_content(
    request: Dict[str, Any],
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Process content with ContentMind agent and store in knowledge repository"""
    if not content_mind:
        raise HTTPException(status_code=503, detail="ContentMind agent is not available")

    try:
        # Process the content with ContentMind
        result = await content_mind.process(request)

        if result.get("status") != "success":
            return result

        # Store the processed content in the knowledge repository
        content_type = request.get("content_type")
        processed_content = result.get("processed_content", {})

        # Store the content
        storage_result = await knowledge_service.store_content(processed_content, content_type)

        # Add the storage information to the result
        if storage_result.get("status") == "success":
            result["storage"] = {
                "stored": True,
                "content_id": storage_result.get("content_id")
            }
        else:
            result["storage"] = {
                "stored": False,
                "error": storage_result.get("message")
            }

        return result
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing content: {str(e)}"
        }

@app.post("/test/process")
async def test_process(
    request: Dict[str, Any],
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Process content with test agent that bypasses LLM calls"""
    from app.test_agent import TestAgent

    try:
        # Initialize test agent
        test_agent = TestAgent()

        # Process the content with test agent
        result = await test_agent.process(request)

        if result.get("status") != "success":
            return result

        # Store the processed content in the knowledge repository
        content_type = request.get("content_type")
        processed_content = result.get("processed_content", {})

        # Store the content
        storage_result = await knowledge_service.store_content(processed_content, content_type)

        # Add the storage information to the result
        if storage_result.get("status") == "success":
            result["storage"] = {
                "stored": True,
                "content_id": storage_result.get("content_id")
            }
        else:
            result["storage"] = {
                "stored": False,
                "error": storage_result.get("message")
            }

        return result
    except Exception as e:
        logger.error(f"Error in test processing: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in test processing: {str(e)}"
        }

@app.get("/knowledge/{content_id}")
async def get_content(
    content_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Retrieve content by ID"""
    result = await knowledge_service.retrieve_content(content_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@app.get("/knowledge/search")
async def search_knowledge(
    query: str,
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 10,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Search knowledge repository"""
    # Convert tags string to list if provided
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    result = await knowledge_service.search(
        query=query,
        content_type=content_type,
        tags=tags_list,
        limit=limit
    )
    return result

@app.get("/knowledge/list")
async def list_knowledge(
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """List content from knowledge repository"""
    # Convert tags string to list if provided
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    result = await knowledge_service.list_content(
        content_type=content_type,
        tags=tags_list,
        limit=limit,
        offset=offset
    )
    return result

@app.delete("/knowledge/{content_id}")
async def delete_content(
    content_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Delete content by ID"""
    result = await knowledge_service.delete_content(content_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@app.get("/test-local")
async def test_local_llm():
    """Test connection to local LLM"""
    try:
        ollama_client = OllamaClient()
        result = await ollama_client.test_connection() if hasattr(ollama_client, "test_connection") else await ollama_client.is_available()
        if result:
            return {"status": "success", "message": "Connected to local LLM successfully"}
        else:
            return {"status": "error", "message": "Could not connect to local LLM"}
    except Exception as e:
        logger.error(f"Error testing local LLM: {str(e)}")
        return {
            "status": "error",
            "message": f"Error connecting to local LLM: {str(e)}"
        }

@app.post("/test-local")
async def test_local_model_pull(request: Dict[str, Any]):
    """Pull a specific model from Ollama"""
    try:
        model = request.get("model", "llama3")
        ollama_client = OllamaClient()
        result = await ollama_client.pull_model(model)
        return result
    except Exception as e:
        logger.error(f"Error pulling model: {str(e)}")
        return {
            "status": "error",
            "message": f"Error pulling model: {str(e)}"
        }

@app.get("/list-local-models")
async def list_local_models():
    """List available local models"""
    try:
        ollama_client = OllamaClient()
        result = await ollama_client.list_models()
        return result
    except Exception as e:
        logger.error(f"Error listing local models: {str(e)}")
        return {
            "status": "error",
            "message": f"Error listing local models: {str(e)}"
        }