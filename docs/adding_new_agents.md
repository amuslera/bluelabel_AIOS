# Adding New Agents to BlueAbel AIOS

This guide explains how to add new agent types to the BlueAbel AIOS system.

## Overview

BlueAbel AIOS is designed with a modular agent architecture that allows for the addition of new agent types with different capabilities. Each agent can:

- Process different types of content
- Provide specialized tools for specific tasks
- Use different LLM prompting strategies via the MCP (Multi-Component Prompting) framework

## Agent Structure

A new agent should follow this directory structure:

```
app/
  agents/
    your_agent_name/
      __init__.py
      agent.py
      config.yaml (optional)
```

## Step 1: Create a New Agent Class

Create a new agent class by extending `BluelabelAgent` in `app/agents/your_agent_name/agent.py`:

```python
from typing import Dict, Any, List
from app.agents.base.agent import BluelabelAgent, AgentTool
from app.core.model_router.router import ModelRouter

class YourAgentTool(AgentTool):
    """Tool for your agent"""

    def __init__(self, model_router: ModelRouter):
        super().__init__(
            name="your_tool_name",
            description="Description of your tool"
        )
        self.model_router = model_router

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool functionality"""
        # Implement your tool logic here
        pass

class YourAgent(BluelabelAgent):
    """Your custom agent description"""

    def __init__(self, config: Dict[str, Any], model_router: ModelRouter):
        self.model_router = model_router
        super().__init__(config)

    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        return [
            YourAgentTool(self.model_router),
            # Add more tools as needed
        ]

    def _register_components(self) -> Dict[str, str]:
        """Register MCP components for your agent's tasks"""
        return {
            "task_name": "component_id",
            # Add more tasks/components as needed
        }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request with your agent"""
        # Implement your agent's processing logic here
        # Use tools as needed
        pass
```

## Step 2: Create a Configuration File

Create a YAML configuration file at `config/agents/your_agent_name.yaml`:

```yaml
# Your agent configuration
id: your_agent_name
name: Your Agent Name
description: "Description of what your agent does"
version: "1.0.0"

# Supported content types
supported_content_types:
  - text
  - query
  # Add more as needed

# Features
features:
  - feature1
  - feature2
  # Add more as needed

# Processing options
processing:
  # Add agent-specific options here
```

## Step 3: Create MCP Components

Add MCP components for your agent in `app/core/registry/service_provider.py`:

1. Create a new function to load your agent's components:

```python
def _load_your_agent_components(editor: ComponentEditor) -> None:
    """Load components used by your agent."""
    registry = get_component_registry()
    
    def upsert_component(id, **kwargs):
        if registry.get_component(id) is not None:
            editor.update_component(
                component_id=id,
                name=kwargs.get("name"),
                description=kwargs.get("description"),
                template=kwargs.get("template"),
                tags=kwargs.get("tags"),
                metadata=kwargs.get("metadata"),
                increment_version=False
            )
        else:
            editor.create_component(id=id, **kwargs)
    
    upsert_component(
        id="your_component_id",
        name="Your Component Name",
        description="Description of your component",
        template="""
        Your prompt template here with {placeholder} values
        """,
        tags=["agent", "your_agent_name", "task_type"],
        metadata={"agent": "your_agent_name", "task": "task_name"}
    )
    
    # Add more components as needed
```

2. Update the `_load_agent_components` function to call your function:

```python
def _load_agent_components() -> None:
    """Load components used by agents."""
    editor = get_component_editor()
    
    # ContentMind components
    _load_contentmind_components(editor)
    
    # Researcher components
    _load_researcher_components(editor)
    
    # Your agent components
    _load_your_agent_components(editor)
```

## Step 4: Test Your Agent

1. Start the application
2. Verify that your agent is discovered and registered
3. Test the agent API endpoint: `POST /agents/your_agent_name/process`

## Example: Using the Agent Registry

The agent registry automatically discovers and loads agents:

```python
from app.core.registry.agent_registry import get_agent_registry

# Get the agent registry
agent_registry = get_agent_registry()

# List available agent classes
available_agents = agent_registry.list_agent_classes()
print(f"Available agent classes: {available_agents}")

# Create an agent instance
your_agent = agent_registry.create_agent("your_agent_name", model_router)

# Process a request
result = await your_agent.process({"key": "value"})
```

## Best Practices

1. **Separation of Concerns**: Each agent should have a clear, focused purpose
2. **Reusable Tools**: Design tools that could be shared between agents when appropriate
3. **Standardized Response Format**: Follow the established response format for consistency
4. **Error Handling**: Implement robust error handling in both agent and tools
5. **Documentation**: Document your agent's purpose, capabilities, and API

## Agent Response Format

All agents should return responses in this standardized format:

```json
{
  "status": "success",
  "content_type": "your_content_type",
  "original_content": "original request content",
  "processed_content": {
    "key1": "value1",
    "key2": "value2"
  },
  "providers_used": {
    "task1": "provider_name",
    "task2": "provider_name"
  }
}
```