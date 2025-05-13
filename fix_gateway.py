#!/usr/bin/env python3
"""
Script to register the Gateway agent in the active registry
"""

import sys
import logging
import requests
import json
import time
from app.core.registry.agent_registry import get_agent_registry, AgentRegistry
from app.agents.gateway.agent import GatewayAgent
from app.core.model_router.router import ModelRouter
from app.agents.base.agent import BluelabelAgent
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Fix the Gateway agent registration"""
    try:
        # Force registerion of GatewayAgent class in the registry
        AgentRegistry.register_class("gateway", GatewayAgent)
        logger.info("Registered Gateway agent class")
        
        # Get the agent registry
        registry = get_agent_registry()
        logger.info(f"Current agent classes: {registry.list_agent_classes()}")
        logger.info(f"Current instantiated agents: {registry.list_agent_instances()}")
        
        # Create a model router
        model_router = ModelRouter({
            "LOCAL_LLM_ENABLED": True,
            "LOCAL_LLM_HOST": "http://localhost:11434",
            "LOCAL_LLM_MODEL": "mistral"
        })
        
        # Create a Gateway agent instance
        gateway_agent = GatewayAgent({"id": "gateway"}, model_router)
        
        # Register the Gateway agent
        registry.register_agent("gateway", gateway_agent)
        logger.info("Created and registered Gateway agent")
        
        # Check if it's registered
        logger.info(f"Updated instantiated agents: {registry.list_agent_instances()}")
        
        # Test the Gateway agent status
        response = requests.get("http://localhost:8081/agents")
        logger.info(f"Agents API response: {json.dumps(response.json(), indent=2)}")
        
        # Give the server a moment to recognize the agent
        time.sleep(2)
        
        # Test simulating an email
        email_data = {
            "from": "test@example.com",
            "to": "a@bluelabel.ventures",
            "subject": "Test Email",
            "body": "This is a test email to check gateway functionality."
        }
        
        response = requests.post(
            "http://localhost:8081/gateway/email/simulate",
            json=email_data
        )
        
        logger.info(f"Email simulation response: {response.status_code}")
        logger.info(f"Email simulation response: {json.dumps(response.json(), indent=2)}")
        
        logger.info("Gateway agent fix completed")
        return 0
    except Exception as e:
        logger.error(f"Error fixing Gateway agent: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())