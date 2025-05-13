# app/main.py
import os
print(f"[DEBUG] Running main.py from: {os.path.abspath(__file__)}")
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any, List, Optional
import traceback

from app.core.config import settings
from app.core.model_router.router import ModelRouter
from app.agents.contentmind.agent import ContentMindAgent
from app.db.database import get_db, create_tables
from app.db.vector_store import VectorStore
from app.services.knowledge.knowledge_service import KnowledgeService
from app.services.llm.ollama_client import OllamaClient
from app.core.registry.service_provider import initialize_mcp_system

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

# Include API routes
try:
    from app.api.routes.gateway import router as gateway_router
    app.include_router(gateway_router)
    logger.info("Gateway API routes included")
except ImportError as e:
    logger.warning(f"Could not import gateway routes: {e}")

try:
    from app.api.routes.scheduler import router as scheduler_router
    app.include_router(scheduler_router)
    logger.info("Scheduler API routes included")
except ImportError as e:
    logger.warning(f"Could not import scheduler routes: {e}")

try:
    from app.api.routes.components import router as components_router
    app.include_router(components_router)
    logger.info("Component API routes included")
except ImportError as e:
    logger.warning(f"Could not import component routes: {e}")

# Initialize MCP system
try:
    initialize_mcp_system()
    logger.info("MCP system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP system: {str(e)}")

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
        "LOCAL_LLM_MODEL": settings.LOCAL_LLM_MODEL
    })
    logger.info("Model router initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize model router: {str(e)}")
    # Continue without the model router
    model_router = None

try:
    # Initialize agent registry and discover available agents
    from app.core.registry.agent_registry import get_agent_registry
    agent_registry = get_agent_registry()

    # Discover available agent classes
    discovered_agents = agent_registry.discover_agents("app.agents")
    logger.info(f"Discovered {len(discovered_agents)} agent classes: {', '.join(discovered_agents)}")

    # Load agent configurations
    agent_registry.load_all_configs()

    # Initialize ContentMind agent
    content_mind = None
    if "contentmind" in agent_registry.list_agent_classes():
        content_mind = agent_registry.create_agent("contentmind", model_router)
        if content_mind:
            logger.info("ContentMind agent initialized successfully")
        else:
            logger.error("Failed to create ContentMind agent instance")
    else:
        # Fallback to direct instantiation if discovery failed
        content_mind = ContentMindAgent({"id": "contentmind"}, model_router) if model_router else None
        if content_mind:
            logger.info("ContentMind agent initialized successfully (direct instantiation)")
            # Register the instance in the registry
            agent_registry.register_agent("contentmind", content_mind)

    # Initialize Digest agent
    digest_agent = None
    if "digest" in agent_registry.list_agent_classes():
        digest_agent = agent_registry.create_agent("digest", model_router)
        if digest_agent:
            logger.info("Digest agent initialized successfully")
        else:
            logger.error("Failed to create Digest agent instance")
    else:
        # Import directly if needed
        try:
            from app.agents.digest.agent import DigestAgent
            digest_agent = DigestAgent({"id": "digest"}, model_router) if model_router else None
            if digest_agent:
                logger.info("Digest agent initialized successfully (direct instantiation)")
                # Register the instance in the registry
                agent_registry.register_agent("digest", digest_agent)
        except Exception as e:
            logger.error(f"Failed to directly instantiate Digest agent: {str(e)}")

    # Initialize Gateway agent
    gateway_agent = None
    try:
        from app.agents.gateway.agent import GatewayAgent
        # Register the Gateway agent class first
        agent_registry.register_class("gateway", GatewayAgent)
        
        # Get the Gateway agent configuration
        gateway_config = agent_registry.get_agent_config("gateway")
        if not gateway_config:
            logger.warning("No configuration found for Gateway agent, using default")
            gateway_config = {"id": "gateway"}
        
        # Create Gateway agent with configuration
        gateway_agent = GatewayAgent(gateway_config, model_router) if model_router else None
        if gateway_agent:
            logger.info("Gateway agent initialized successfully (direct instantiation)")
            # Register the instance in the registry
            agent_registry.register_agent("gateway", gateway_agent)
            logger.info(f"[DEBUG] main.py: Registry id: {id(agent_registry)}, Gateway agent id: {id(gateway_agent)}")
        else:
            logger.error("Failed to create Gateway agent instance")
    except Exception as e:
        logger.error(f"Failed to initialize Gateway agent: {str(e)}")
        logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"Failed to initialize agent registry or ContentMind agent: {str(e)}")
    # Continue without the agent
    content_mind = None

try:
    # Create database tables
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {str(e)}")

# Initialize and start scheduler service
try:
    from app.services.scheduler.scheduler_service import scheduler_service

    @app.on_event("startup")
    async def start_scheduler():
        logger.info("Starting scheduler service")
        await scheduler_service.start()

        # Register digest agent callback
        agent_registry = get_agent_registry()
        digest_agent = agent_registry.get_agent("digest")

        if digest_agent:
            # Register callbacks for different digest types
            for digest_type in ["daily", "weekly", "monthly", "custom"]:
                scheduler_service.register_callback(
                    f"digest_{digest_type}",
                    digest_agent.process
                )
            logger.info("Registered digest agent callbacks with scheduler")
        else:
            logger.warning("Digest agent not available for scheduler callbacks")

    @app.on_event("shutdown")
    async def stop_scheduler():
        logger.info("Stopping scheduler service")
        await scheduler_service.stop()

    logger.info("Scheduler service initialized")
except Exception as e:
    logger.error(f"Failed to initialize scheduler service: {str(e)}")

# Dependency for KnowledgeService
def get_knowledge_service(db: Session = Depends(get_db)):
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store is not available")
    return KnowledgeService(db, vector_store)

# Helper function for processing and storing content
async def process_and_store_content(agent, request, knowledge_service, logger):
    result = await agent.process(request)
    if result.get("status") != "success":
        return result
    content_type = request.get("content_type")
    processed_content = result.get("processed_content", {})
    storage_result = await knowledge_service.store_content(processed_content, content_type)
    result["storage"] = {
        "stored": storage_result.get("status") == "success",
        "content_id": storage_result.get("content_id"),
        "error": storage_result.get("message") if storage_result.get("status") != "success" else None
    }
    return result

@app.get("/")
async def root():
    return {"message": "Welcome to Bluelabel AIOS API"}

@app.get("/agents")
async def list_agents():
    """List all available agents and their capabilities"""
    agent_registry = get_agent_registry()
    logger.info(f"[DEBUG] /agents endpoint: Registry id: {id(agent_registry)}, agent instances: {list(agent_registry.agents.keys())}")

    # Get available agent classes
    available_classes = agent_registry.list_agent_classes()

    # Get instantiated agents and their capabilities
    agent_instances = agent_registry.list_available_agents()

    # Build response
    response = {
        "agent_types": [],
        "status": "success"
    }

    # Add agents from both classes and instances
    for agent_id in set(available_classes) | set(agent_instances.keys()):
        agent_info = {"id": agent_id}

        # Check if agent is instantiated in the registry
        if agent_id in agent_registry.agents:
            agent_info["status"] = "instantiated"
            # Get agent instance
            agent_instance = agent_registry.agents[agent_id]
            # Add capabilities from instance
            agent_info.update({
                "name": agent_instance.name if hasattr(agent_instance, "name") else agent_id,
                "description": agent_instance.description if hasattr(agent_instance, "description") else "No description",
                "supported_content_types": agent_instance.supported_content_types if hasattr(agent_instance, "supported_content_types") else [],
                "features": agent_instance.features if hasattr(agent_instance, "features") else []
            })
        else:
            # Add basic info for non-instantiated agent classes
            agent_info["status"] = "not_instantiated"
            config = agent_registry.get_agent_config(agent_id)
            if config:
                agent_info.update({
                    "name": config.get("name", agent_id),
                    "description": config.get("description", "No description"),
                    "supported_content_types": config.get("supported_content_types", []),
                    "features": config.get("features", [])
                })

        response["agent_types"].append(agent_info)

    return response

@app.post("/agents/{agent_id}/process")
async def process_with_agent(
    agent_id: str,
    request: Dict[str, Any],
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Process a request with any registered agent and store in knowledge repository"""
    # Get agent registry
    agent_registry = get_agent_registry()

    # Get agent instance (this will attempt to create it if needed)
    agent_instance = agent_registry.get_agent(agent_id)

    # If we don't have an instance yet, try to create it
    if not agent_instance and agent_id in agent_registry.list_agent_classes():
        agent_instance = agent_registry.create_agent(agent_id, model_router)

    # Check if agent exists
    if not agent_instance:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found or could not be instantiated")

    # Process request with agent
    try:
        return await process_and_store_content(agent_instance, request, knowledge_service, logger)
    except Exception as e:
        logger.error(f"Error processing with agent '{agent_id}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error processing with agent '{agent_id}': {str(e)}"
        }

@app.post("/agents/contentmind/process")
async def process_content(
    request: Dict[str, Any],
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    """Process content with ContentMind agent and store in knowledge repository (legacy endpoint)"""
    if not content_mind:
        raise HTTPException(status_code=503, detail="ContentMind agent is not available")
    try:
        return await process_and_store_content(content_mind, request, knowledge_service, logger)
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
        test_agent = TestAgent()
        return await process_and_store_content(test_agent, request, knowledge_service, logger)
    except Exception as e:
        logger.error(f"Error in test processing: {str(e)}")
        return {
            "status": "error",
            "message": f"Error in test processing: {str(e)}"
        }

# Knowledge repository endpoints
# IMPORTANT: Specific endpoints must come BEFORE parameter endpoints in FastAPI

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
        model = request.get("model", settings.LOCAL_LLM_MODEL)
        ollama_client = OllamaClient()
        result = await ollama_client.pull_model(model)
        # Ensure error messages are meaningful
        if result.get("status") != "success":
            if not result.get("message"):
                result["message"] = f"Failed to pull model: {model} (unknown error)"
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
        # Normalize output: always return a list of model names
        if isinstance(result, dict) and "models" in result:
            model_names = [m["name"] for m in result["models"] if isinstance(m, dict) and "name" in m]
            return {"models": model_names}
        else:
            return {"models": []}
    except Exception as e:
        logger.error(f"Error listing local models: {str(e)}")
        return {
            "status": "error",
            "message": f"Error listing local models: {str(e)}"
        }

@app.get("/health")
async def health():
    """Health check for all major components"""
    health_status = {}
    # Vector store
    health_status["vector_store"] = vector_store is not None
    # Model router
    health_status["model_router"] = model_router is not None
    # ContentMind agent
    health_status["content_mind"] = content_mind is not None
    # Local LLM
    try:
        ollama_client = OllamaClient()
        local_llm_ok = await ollama_client.is_available()
    except Exception:
        local_llm_ok = False
    health_status["local_llm"] = local_llm_ok
    # Overall
    health_status["ok"] = all(health_status.values())
    return health_status

@app.get("/debug/agents")
async def debug_agents():
    agent_registry = get_agent_registry()
    return {
        "registry_id": id(agent_registry),
        "agents": {k: str(v) + f" (id={id(v)})" for k, v in agent_registry.agents.items()}
    }

@app.get("/status")
async def status():
    return {"status": "ok"}

# Include API routes
from app.api.routes.components import router as components_router
app.include_router(components_router)

# Include Scheduler API routes
try:
    from app.api.routes.scheduler import router as scheduler_router
    app.include_router(scheduler_router)
    logger.info("Scheduler API routes included")
except ImportError as e:
    logger.warning(f"Scheduler API routes not included: {str(e)}")

# Include Gateway API routes (optional)
try:
    from app.services.gateway.controller import router as gateway_router
    app.include_router(gateway_router)
    logger.info("Gateway API routes included")
except ImportError as e:
    logger.warning(f"Gateway API routes not included due to missing dependencies: {str(e)}")