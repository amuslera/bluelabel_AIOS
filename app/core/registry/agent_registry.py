# app/core/registry/agent_registry.py
from typing import Dict, Any, Optional
import logging
from app.agents.base.agent import BluelabelAgent

# Configure logging
logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for discovering and managing agents"""
    
    def __init__(self):
        self.agents = {}
        logger.info("Agent Registry initialized")
    
    def register_agent(self, agent_name: str, agent_instance: BluelabelAgent):
        """Register an agent in the system"""
        self.agents[agent_name] = agent_instance
        logger.info(f"Agent '{agent_name}' registered")
    
    async def process_with_agent(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request with a specific agent"""
        if agent_name not in self.agents:
            logger.warning(f"Agent '{agent_name}' not found")
            return {"status": "error", "message": f"Agent {agent_name} not found"}
        
        logger.info(f"Processing request with agent '{agent_name}'")
        return await self.agents[agent_name].process(request)
    
    def list_available_agents(self) -> Dict[str, Any]:
        """List all available agents and their capabilities"""
        return {name: agent.get_capabilities() for name, agent in self.agents.items()}

    def get_agent(self, agent_name: str) -> Optional[BluelabelAgent]:
        """Get agent by name"""
        return self.agents.get(agent_name)