#!/usr/bin/env python3
"""
Script to check the Gateway agent registration and instantiation
"""

import asyncio
from app.core.registry.agent_registry import get_agent_registry
from app.agents.gateway.agent import GatewayAgent
from app.core.model_router.router import ModelRouter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    """Manually register and test the Gateway agent"""
    
    logger.info("Getting agent registry...")
    agent_registry = get_agent_registry()
    
    logger.info("Available agent classes: %s", agent_registry.list_agent_classes())
    logger.info("Instantiated agents: %s", agent_registry.list_agent_instances())
    
    # Check for gateway agent
    gateway_agent = agent_registry.get_agent("gateway")
    if gateway_agent:
        logger.info("Gateway agent is already registered")
    else:
        logger.info("Gateway agent not found, manually registering...")
        
        # Create a model router
        try:
            model_router = ModelRouter({
                "LOCAL_LLM_ENABLED": True,
                "LOCAL_LLM_HOST": "http://localhost:11434",
                "LOCAL_LLM_MODEL": "mistral"
            })
        except Exception as e:
            logger.error("Failed to create model router: %s", str(e))
            model_router = None
        
        # Register the Gateway agent class
        try:
            agent_registry.register_class("gateway", GatewayAgent)
            logger.info("Gateway agent class registered")
        except Exception as e:
            logger.error("Failed to register Gateway agent class: %s", str(e))
            
        # Create a Gateway agent instance
        try:
            gateway_agent = GatewayAgent({"id": "gateway"}, model_router)
            agent_registry.register_agent("gateway", gateway_agent)
            logger.info("Gateway agent created and registered successfully")
        except Exception as e:
            logger.error("Failed to create Gateway agent: %s", str(e))
            
    # Check instantiated agents again
    logger.info("Instantiated agents after registration: %s", agent_registry.list_agent_instances())
    
    # Test with a sample email
    if "gateway" in agent_registry.list_agent_instances():
        gateway_agent = agent_registry.get_agent("gateway")
        logger.info("Testing email processing...")
        
        try:
            email_data = {
                "subject": "Test Email",
                "sender": "test@example.com",
                "recipient": "a@bluelabel.ventures",
                "date": "2025-05-13T00:00:00",
                "body_text": "This is a test email body.",
                "body_html": "<p>This is a test email body.</p>",
                "content_type": "text",
                "content": "This is a test email body.",
                "attachments": []
            }
            
            result = await gateway_agent.process_email(email_data)
            logger.info("Email processing result: %s", result)
        except Exception as e:
            logger.error("Error processing test email: %s", str(e))

if __name__ == "__main__":
    asyncio.run(main())