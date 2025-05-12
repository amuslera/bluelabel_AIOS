# app/core/registry/agent_registry.py
from typing import Dict, Any, Optional, Type, List, Set
import logging
import os
import importlib
import inspect
from pathlib import Path
import yaml
from app.agents.base.agent import BluelabelAgent

# Configure logging
logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for discovering and managing agents in the system.

    This registry allows for dynamic discovery, registration, and instantiation
    of agents. It provides a centralized mechanism for accessing agent types and
    creating instances with appropriate configurations.
    """

    # Static storage for registered agent classes
    _agent_classes: Dict[str, Type[BluelabelAgent]] = {}

    # Static storage for agent configurations
    _agent_configs: Dict[str, Dict[str, Any]] = {}

    # Instance storage for agent instances
    def __init__(self):
        self.agents = {}
        logger.info("Agent Registry initialized")

    def register_agent(self, agent_name: str, agent_instance: BluelabelAgent):
        """Register an agent instance in the system"""
        self.agents[agent_name] = agent_instance
        logger.info(f"Agent instance '{agent_name}' registered")

    async def process_with_agent(self, agent_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request with a specific agent"""
        if agent_name not in self.agents:
            # Try to create the agent if we have the class but no instance
            if agent_name in self._agent_classes:
                logger.info(f"Agent '{agent_name}' not instantiated yet, attempting to create")
                agent_instance = self.create_agent(agent_name)
                if agent_instance:
                    self.register_agent(agent_name, agent_instance)
                else:
                    logger.warning(f"Failed to create agent '{agent_name}'")
                    return {"status": "error", "message": f"Failed to create agent {agent_name}"}
            else:
                logger.warning(f"Agent '{agent_name}' not found")
                return {"status": "error", "message": f"Agent {agent_name} not found"}

        logger.info(f"Processing request with agent '{agent_name}'")
        return await self.agents[agent_name].process(request)

    def list_available_agents(self) -> Dict[str, Any]:
        """List all available agent instances and their capabilities"""
        return {name: agent.get_capabilities() for name, agent in self.agents.items()}

    def get_agent(self, agent_name: str) -> Optional[BluelabelAgent]:
        """Get agent instance by name"""
        return self.agents.get(agent_name)

    @classmethod
    def register_class(cls, agent_id: str, agent_class: Type[BluelabelAgent]) -> None:
        """Register a new agent class.

        Args:
            agent_id: Unique identifier for the agent
            agent_class: The agent class to register
        """
        if agent_id in cls._agent_classes:
            logger.warning(f"Agent class {agent_id} already registered, overwriting")

        cls._agent_classes[agent_id] = agent_class
        logger.info(f"Registered agent class: {agent_id} -> {agent_class.__name__}")

    @classmethod
    def register_config(cls, agent_id: str, config: Dict[str, Any]) -> None:
        """Register a configuration for an agent.

        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary for the agent
        """
        if agent_id in cls._agent_configs:
            logger.warning(f"Agent config {agent_id} already registered, overwriting")

        cls._agent_configs[agent_id] = config
        logger.info(f"Registered agent config: {agent_id}")

    @classmethod
    def get_agent_class(cls, agent_id: str) -> Optional[Type[BluelabelAgent]]:
        """Get the agent class for an agent ID.

        Args:
            agent_id: The agent ID to look up

        Returns:
            The agent class or None if not found
        """
        return cls._agent_classes.get(agent_id)

    @classmethod
    def get_agent_config(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get the configuration for an agent.

        Args:
            agent_id: The agent ID to look up

        Returns:
            The agent configuration or None if not found
        """
        return cls._agent_configs.get(agent_id)

    def create_agent(self, agent_id: str, model_router=None, config: Optional[Dict[str, Any]] = None) -> Optional[BluelabelAgent]:
        """Create an agent instance.

        Args:
            agent_id: The agent ID to create
            model_router: Optional model router instance to pass to the agent
            config: Optional configuration override

        Returns:
            The created agent instance or None if the agent class is not found
        """
        # Check if we already have an instance
        if agent_id in self.agents:
            logger.info(f"Returning existing agent instance for {agent_id}")
            return self.agents[agent_id]

        # Get the agent class
        agent_class = self.get_agent_class(agent_id)
        if not agent_class:
            logger.error(f"Agent class not found for {agent_id}")
            return None

        # Get the agent configuration
        agent_config = config or self.get_agent_config(agent_id) or {"id": agent_id}

        # Create the agent instance
        try:
            # Inspect the constructor to see if it takes a model_router parameter
            signature = inspect.signature(agent_class.__init__)
            if "model_router" in signature.parameters:
                if model_router is None:
                    logger.error(f"Agent {agent_id} requires a model_router but none was provided")
                    return None
                agent_instance = agent_class(agent_config, model_router)
            else:
                agent_instance = agent_class(agent_config)

            # Register the instance
            self.register_agent(agent_id, agent_instance)
            logger.info(f"Created and registered agent instance for {agent_id}")

            return agent_instance
        except Exception as e:
            logger.error(f"Error creating agent instance for {agent_id}: {str(e)}")
            return None

    @classmethod
    def list_agent_classes(cls) -> List[str]:
        """List all registered agent class IDs.

        Returns:
            List of registered agent class IDs
        """
        return list(cls._agent_classes.keys())

    def list_agent_instances(self) -> List[str]:
        """List all instantiated agent IDs.

        Returns:
            List of agent IDs with active instances
        """
        return list(self.agents.keys())

    @classmethod
    def discover_agents(cls, package_path: str = "app.agents") -> Set[str]:
        """Discover and register agent classes from a package path.

        Args:
            package_path: Dot-notation path to the package to scan for agents

        Returns:
            Set of discovered agent IDs
        """
        discovered_agents = set()

        try:
            # Import the package
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            # Scan for subdirectories that represent agent types
            for item in package_dir.iterdir():
                if item.is_dir() and not item.name.startswith('__'):
                    agent_type = item.name

                    # Look for agent.py in the directory
                    agent_file = item / "agent.py"
                    if agent_file.exists():
                        # Import the module
                        module_path = f"{package_path}.{agent_type}.agent"
                        try:
                            module = importlib.import_module(module_path)

                            # Look for agent classes in the module
                            for name, obj in inspect.getmembers(module):
                                if (inspect.isclass(obj) and
                                    obj.__module__ == module_path and
                                    name.endswith("Agent")):

                                    # Register the agent class
                                    agent_id = agent_type.lower()
                                    cls.register_class(agent_id, obj)
                                    discovered_agents.add(agent_id)

                                    # Look for a config file
                                    config_file = item / "config.yaml"
                                    if config_file.exists():
                                        try:
                                            with open(config_file, 'r') as f:
                                                config = yaml.safe_load(f)
                                                cls.register_config(agent_id, config)
                                        except Exception as e:
                                            logger.error(f"Error loading config for {agent_id}: {str(e)}")
                        except Exception as e:
                            logger.error(f"Error importing {module_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error discovering agents in {package_path}: {str(e)}")

        return discovered_agents

    @classmethod
    def load_all_configs(cls, config_dir: str = None) -> None:
        """Load all agent configurations from a directory.

        Args:
            config_dir: Directory containing agent configuration files
        """
        if config_dir is None:
            config_dir = os.path.join(os.getcwd(), "config", "agents")

        if not os.path.exists(config_dir):
            logger.warning(f"Agent config directory {config_dir} does not exist")
            return

        for filename in os.listdir(config_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(config_dir, filename)
                agent_id = filename.split('.')[0]

                try:
                    with open(filepath, 'r') as f:
                        config = yaml.safe_load(f)
                        cls.register_config(agent_id, config)
                except Exception as e:
                    logger.error(f"Error loading config file {filepath}: {str(e)}")

# Singleton instance for global access
_registry_instance = AgentRegistry()

def get_agent_registry() -> AgentRegistry:
    """Get the singleton agent registry instance.

    Returns:
        AgentRegistry instance
    """
    return _registry_instance