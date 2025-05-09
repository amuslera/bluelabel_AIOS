# app/agents/base/agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AgentTool:
    """Base class for tools that agents can use"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass


class BluelabelAgent(ABC):
    """Base class for all Bluelabel AIOS agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = self._register_tools()
    
    @abstractmethod
    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        pass
    
    @abstractmethod
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using this agent"""
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for discovery"""
        return {
            "name": self.config.get("name", "unnamed_agent"),
            "description": self.config.get("description", "No description provided"),
            "supported_content_types": self.config.get("supported_content_types", []),
            "features": self.config.get("features", [])
        }