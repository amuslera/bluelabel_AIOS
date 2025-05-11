#!/usr/bin/env python3
"""
Test script for the MCP framework.

This script tests the core functionality of the MCP framework.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

from app.core.mcp import MCPComponent, ComponentRegistry, ComponentEditor, ComponentTester
from app.core.registry.service_provider import initialize_mcp_system
from app.core.model_router.router import ModelRouter

async def main():
    """Main test function."""
    print("Initializing MCP system...")
    initialize_mcp_system()
    
    # Test component creation
    test_create_component()
    
    # Test component registry
    test_registry()
    
    # Test ModelRouter integration (requires API keys)
    await test_model_router()
    
    print("All tests completed successfully!")

def test_create_component():
    """Test creating and manipulating a component."""
    print("\n=== Testing Component Creation ===")
    
    # Create a test component
    component = MCPComponent(
        name="Test Component",
        description="A test component",
        template="This is a test template with {variable1} and {variable2:optional}.",
        tags=["test", "example"]
    )
    
    print(f"Created component: {component.id}")
    print(f"Required inputs: {component.required_inputs}")
    print(f"Optional inputs: {component.optional_inputs}")
    
    # Test rendering
    inputs = {"variable1": "value1", "variable2": "value2"}
    rendered = component.render(inputs)
    print(f"Rendered template: {rendered}")
    
    # Test JSON serialization
    json_str = component.to_json()
    print(f"JSON representation: {json_str[:100]}...")
    
    # Test deserialization
    component2 = MCPComponent.from_json(json_str)
    print(f"Deserialized component: {component2.id}")
    
    # Test updating
    component2.update(name="Updated Component")
    print(f"Updated name: {component2.name}")
    
    # Verify that placeholders were correctly extracted
    assert "variable1" in component.required_inputs
    assert "variable2" in component.optional_inputs
    
    # Verify that rendering works
    assert "value1" in rendered
    assert "value2" in rendered
    
    print("Component creation tests passed!")

def test_registry():
    """Test the component registry."""
    print("\n=== Testing Component Registry ===")
    
    # Create a registry
    registry = ComponentRegistry()
    
    # Create a component
    component = MCPComponent(
        name="Registry Test Component",
        description="A component for testing the registry",
        template="This is a test template with {variable}.",
        tags=["test", "registry"]
    )
    
    # Register the component
    registry.register_component(component)
    print(f"Registered component: {component.id}")
    
    # Retrieve the component
    retrieved = registry.get_component(component.id)
    print(f"Retrieved component: {retrieved.id}")
    
    # List components
    components = registry.list_components()
    print(f"Found {len(components)} components")
    
    # List components by tag
    tagged = registry.list_components(tag="system")
    print(f"Found {len(tagged)} system components")
    
    # Verify retrieval
    assert retrieved.id == component.id
    assert retrieved.name == component.name
    
    print("Registry tests passed!")

async def test_model_router():
    """Test ModelRouter integration with MCP."""
    print("\n=== Testing ModelRouter Integration ===")
    
    # Create a model router
    model_router = None
    try:
        model_router = ModelRouter({
            "LOCAL_LLM_ENABLED": os.environ.get("LOCAL_LLM_ENABLED", "false").lower() == "true",
            "LOCAL_LLM_HOST": os.environ.get("LOCAL_LLM_HOST", "http://localhost:11434"),
            "LOCAL_LLM_MODEL": "llama3"
        })
    except Exception as e:
        print(f"Warning: Could not initialize model router: {e}")
        print("Skipping ModelRouter integration tests.")
        return
    
    # Test system prompt generation
    system_prompt = model_router._create_system_prompt("summarize")
    print(f"System prompt: {system_prompt[:100]}...")
    
    # Test task prompt generation
    content = {"text": "This is a test text for summarization."}
    task_prompt = model_router._create_prompt("summarize", content)
    print(f"Task prompt: {task_prompt[:100]}...")
    
    # Test routing with a simple summarization task
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
        try:
            print("Testing actual routing to an LLM provider...")
            result = await model_router.route_request(
                "summarize", 
                {"text": "This is a short test text for summarization via MCP framework."}, 
                {"global_timeout": 15}  # Short timeout for testing
            )
            print(f"Result: {result.get('result', '')[:100]}...")
            print(f"Provider: {result.get('provider')}")
            print(f"Status: {result.get('status')}")
        except Exception as e:
            print(f"Warning: LLM test failed: {e}")
    else:
        print("Skipping LLM test (no API keys found)")
    
    print("ModelRouter integration tests completed!")

if __name__ == "__main__":
    asyncio.run(main())