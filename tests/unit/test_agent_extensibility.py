import unittest
import asyncio
from unittest.mock import patch, MagicMock
import sys
import os
import importlib

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.registry.agent_registry import AgentRegistry, get_agent_registry
from app.agents.base.agent import BluelabelAgent, AgentTool


class TestAgentExtensibility(unittest.TestCase):
    """Test cases for agent extensibility"""

    def setUp(self):
        """Set up test environment"""
        # Create a fresh registry for each test
        self.registry = AgentRegistry()
        
        # Clear class-level registries
        AgentRegistry._agent_classes = {}
        AgentRegistry._agent_configs = {}
        
        # Mock the model router
        self.model_router = MagicMock()
        
        # Create a mock logger for testing
        self.mock_logger = MagicMock()

    def test_register_agent_class(self):
        """Test registering an agent class"""
        # Define a mock agent class
        class MockAgent(BluelabelAgent):
            def _register_tools(self):
                return []
            
            async def process(self, request):
                return {"status": "success"}
        
        # Register the agent class
        AgentRegistry.register_class("mock", MockAgent)
        
        # Check if the class was registered
        self.assertIn("mock", AgentRegistry._agent_classes)
        self.assertEqual(AgentRegistry._agent_classes["mock"], MockAgent)

    def test_register_agent_config(self):
        """Test registering an agent configuration"""
        # Define a mock configuration
        config = {
            "id": "mock",
            "name": "Mock Agent",
            "description": "A mock agent for testing"
        }
        
        # Register the configuration
        AgentRegistry.register_config("mock", config)
        
        # Check if the configuration was registered
        self.assertIn("mock", AgentRegistry._agent_configs)
        self.assertEqual(AgentRegistry._agent_configs["mock"], config)

    def test_create_agent(self):
        """Test creating an agent instance"""
        # Define a mock agent class
        class MockAgent(BluelabelAgent):
            def __init__(self, config, model_router):
                self.model_router = model_router
                super().__init__(config)
            
            def _register_tools(self):
                return []
            
            async def process(self, request):
                return {"status": "success"}
        
        # Register the agent class and config
        AgentRegistry.register_class("mock", MockAgent)
        AgentRegistry.register_config("mock", {"id": "mock", "name": "Mock Agent"})
        
        # Create an agent instance
        agent = self.registry.create_agent("mock", self.model_router)
        
        # Check if the instance was created and registered
        self.assertIsNotNone(agent)
        self.assertIn("mock", self.registry.agents)
        self.assertEqual(self.registry.agents["mock"], agent)

    def test_discover_agents(self):
        """Test discovering agents from the package"""
        # This test verifies that agents can be discovered
        discovered = AgentRegistry.discover_agents("app.agents")
        
        # Verify that at least contentmind and researcher agents are discovered
        self.assertIn("contentmind", discovered)
        self.assertIn("researcher", discovered)

    def test_agent_processing(self):
        """Test processing with an agent"""
        # Define a mock agent class with a simple process method
        class MockAgent(BluelabelAgent):
            def __init__(self, config, model_router):
                self.model_router = model_router
                super().__init__(config)
            
            def _register_tools(self):
                return []
            
            async def process(self, request):
                if "fail" in request:
                    return {"status": "error", "message": "Failed as requested"}
                return {
                    "status": "success",
                    "processed_content": {"result": f"Processed {request.get('query', 'unknown')}"}
                }
        
        # Register and create the agent
        AgentRegistry.register_class("mock", MockAgent)
        agent = self.registry.create_agent("mock", self.model_router)
        
        # Test successful processing
        result = asyncio.run(agent.process({"query": "test query"}))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed_content"]["result"], "Processed test query")
        
        # Test error handling
        result = asyncio.run(agent.process({"fail": True}))
        self.assertEqual(result["status"], "error")
    
    def test_registry_singleton(self):
        """Test that get_agent_registry returns a singleton"""
        registry1 = get_agent_registry()
        registry2 = get_agent_registry()
        
        # Verify both references point to the same object
        self.assertIs(registry1, registry2)


if __name__ == "__main__":
    unittest.main()