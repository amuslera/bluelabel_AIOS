# app/agents/base/agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
import logging

from app.core.registry.service_provider import get_component_registry
from app.core.mcp import MCPComponent

# Configure logging
logger = logging.getLogger(__name__)


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
    """Base class for all Bluelabel AIOS agents

    Provides MCP component support for agent prompts.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize a Bluelabel agent.

        Args:
            config: Agent configuration dictionary.
        """
        self.config = config
        self.tools = self._register_tools()

        # Component mapping for agent tasks
        self.component_mapping = self._register_components()

        # Initialize component registry reference
        self._component_registry = None

    @abstractmethod
    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent.

        Returns:
            List of AgentTool instances.
        """
        pass

    def _register_components(self) -> Dict[str, str]:
        """Register MCP components for agent tasks.

        This maps task names to component IDs. Override this method
        to provide agent-specific component mappings.

        Returns:
            Dictionary mapping task names to component IDs.
        """
        # Default implementation returns an empty mapping
        return {}

    @property
    def component_registry(self):
        """Get the component registry singleton.

        Returns:
            ComponentRegistry instance or None if not available.
        """
        if self._component_registry is None:
            self._component_registry = get_component_registry()
        return self._component_registry

    def get_component(self, task: str) -> Optional[MCPComponent]:
        """Get the MCP component for a given task.

        Args:
            task: The task name.

        Returns:
            MCPComponent instance or None if not found.
        """
        if task not in self.component_mapping:
            return None

        component_id = self.component_mapping[task]

        if not self.component_registry:
            logger.warning(f"Component registry not available for task: {task}")
            return None

        return self.component_registry.get_component(component_id)

    def render_prompt(self, task: str, inputs: Dict[str, Any]) -> Optional[str]:
        """Render a prompt for a given task with the specified inputs.

        Args:
            task: The task name.
            inputs: Input values for rendering the prompt.

        Returns:
            Rendered prompt string or None if the component is not found.
        """
        component = self.get_component(task)
        if not component:
            logger.warning(f"No component found for task: {task}")
            return None

        try:
            return component.render(inputs)
        except Exception as e:
            logger.error(f"Error rendering prompt for task {task}: {str(e)}")
            return None

    @abstractmethod
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request using this agent.

        Args:
            request: The request to process.

        Returns:
            Processing result.
        """
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for discovery.

        Returns:
            Agent capabilities dictionary.
        """
        return {
            "name": self.config.get("name", "unnamed_agent"),
            "description": self.config.get("description", "No description provided"),
            "supported_content_types": self.config.get("supported_content_types", []),
            "features": self.config.get("features", []),
            "mcp_tasks": list(self.component_mapping.keys())
        }