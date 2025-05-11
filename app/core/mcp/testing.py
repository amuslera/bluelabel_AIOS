"""
Testing module for Multi-Component Prompting (MCP) framework.

This module defines the ComponentTester class for testing MCP components
against LLM providers.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import uuid

from .component import MCPComponent
from .registry import ComponentRegistry

# Configure logging
logger = logging.getLogger(__name__)

class TestResult:
    """Result of a component test.
    
    Stores the test inputs, outputs, and performance metrics.
    """
    
    def __init__(self, 
                component_id: str, 
                component_version: str,
                inputs: Dict[str, Any], 
                result: Optional[str] = None,
                error: Optional[str] = None,
                metrics: Optional[Dict[str, Any]] = None):
        """Initialize a new test result.
        
        Args:
            component_id: ID of the tested component.
            component_version: Version of the tested component.
            inputs: Input values used for the test.
            result: The test result if successful.
            error: The error message if the test failed.
            metrics: Performance metrics collected during the test.
        """
        self.id = str(uuid.uuid4())
        self.component_id = component_id
        self.component_version = component_version
        self.inputs = inputs
        self.result = result
        self.error = error
        self.metrics = metrics or {}
        self.timestamp = datetime.now().isoformat()
    
    @property
    def is_success(self) -> bool:
        """Check if the test was successful.
        
        Returns:
            True if the test was successful, False otherwise.
        """
        return self.error is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the test result to a dictionary.
        
        Returns:
            Dictionary representation of the test result.
        """
        return {
            "id": self.id,
            "component_id": self.component_id,
            "component_version": self.component_version,
            "inputs": self.inputs,
            "result": self.result,
            "error": self.error,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "is_success": self.is_success
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create a test result from a dictionary.
        
        Args:
            data: Dictionary representation of the test result.
            
        Returns:
            New TestResult instance.
        """
        result = cls(
            component_id=data.get("component_id", ""),
            component_version=data.get("component_version", ""),
            inputs=data.get("inputs", {}),
            result=data.get("result"),
            error=data.get("error"),
            metrics=data.get("metrics", {})
        )
        
        # Preserve ID and timestamp if available
        if "id" in data:
            result.id = data["id"]
        if "timestamp" in data:
            result.timestamp = data["timestamp"]
            
        return result

class TestResultStore:
    """Storage for component test results.
    
    Maintains a history of test results for components.
    """
    
    def __init__(self):
        """Initialize a new test result store."""
        self.results: Dict[str, List[TestResult]] = {}
    
    def add_result(self, result: TestResult) -> None:
        """Add a test result to the store.
        
        Args:
            result: The test result to add.
        """
        component_id = result.component_id
        if component_id not in self.results:
            self.results[component_id] = []
        
        self.results[component_id].append(result)
        logger.debug(f"Added test result for component {component_id}: {result.id}")
    
    def get_results(self, component_id: str) -> List[TestResult]:
        """Get all test results for a component.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            List of test results.
        """
        return self.results.get(component_id, [])
    
    def get_result(self, result_id: str) -> Optional[TestResult]:
        """Get a specific test result.
        
        Args:
            result_id: ID of the test result.
            
        Returns:
            The test result if found, None otherwise.
        """
        for results in self.results.values():
            for result in results:
                if result.id == result_id:
                    return result
        return None
    
    def clear_results(self, component_id: str) -> None:
        """Clear all test results for a component.
        
        Args:
            component_id: ID of the component.
        """
        if component_id in self.results:
            self.results[component_id] = []
            logger.info(f"Cleared test results for component {component_id}")
    
    def compare_results(self, result_id1: str, result_id2: str) -> Dict[str, Any]:
        """Compare two test results.
        
        Args:
            result_id1: ID of the first test result.
            result_id2: ID of the second test result.
            
        Returns:
            Dictionary with comparison results.
            
        Raises:
            ValueError: If either result doesn't exist.
        """
        result1 = self.get_result(result_id1)
        result2 = self.get_result(result_id2)
        
        if result1 is None:
            raise ValueError(f"Test result {result_id1} not found")
        if result2 is None:
            raise ValueError(f"Test result {result_id2} not found")
        
        # Compare metrics
        metric_diffs = {}
        for key in set(result1.metrics.keys()) | set(result2.metrics.keys()):
            val1 = result1.metrics.get(key)
            val2 = result2.metrics.get(key)
            
            if val1 != val2:
                metric_diffs[key] = {
                    "from": val2,
                    "to": val1,
                    "change": val1 - val2 if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else None
                }
        
        # Compare outputs
        output_diff = None
        if result1.result != result2.result:
            output_diff = {
                "from": result2.result,
                "to": result1.result
            }
        
        return {
            "result_ids": {
                "from": result_id2,
                "to": result_id1
            },
            "component_id": result1.component_id,
            "metrics_diff": metric_diffs,
            "output_diff": output_diff,
            "has_changes": len(metric_diffs) > 0 or output_diff is not None
        }

class ComponentTester:
    """Tester for MCP components.
    
    Provides functionality for testing components with different LLM providers
    and tracking performance metrics.
    """
    
    def __init__(self, registry: ComponentRegistry, model_router=None):
        """Initialize a new component tester.
        
        Args:
            registry: Component registry to use for component retrieval.
            model_router: Model router to use for testing components.
            
        Note:
            If model_router is None, the tester will only support template
            rendering without LLM testing.
        """
        self.registry = registry
        self.model_router = model_router
        self.result_store = TestResultStore()
    
    def test_rendering(self, 
                      component_id: str, 
                      inputs: Dict[str, Any]) -> TestResult:
        """Test the rendering of a component.
        
        Args:
            component_id: ID of the component to test.
            inputs: Input values for the test.
            
        Returns:
            Test result with the rendered template.
        """
        # Get the component
        component = self.registry.get_component(component_id)
        if component is None:
            return TestResult(
                component_id=component_id,
                component_version="unknown",
                inputs=inputs,
                error=f"Component not found: {component_id}"
            )
        
        # Time the rendering
        start_time = time.time()
        try:
            rendered = component.render(inputs)
            end_time = time.time()
            
            # Create test result
            result = TestResult(
                component_id=component_id,
                component_version=component.version,
                inputs=inputs,
                result=rendered,
                metrics={
                    "render_time_ms": round((end_time - start_time) * 1000, 2)
                }
            )
            
            # Store the result
            self.result_store.add_result(result)
            return result
        
        except ValueError as e:
            end_time = time.time()
            
            # Create failed test result
            result = TestResult(
                component_id=component_id,
                component_version=component.version,
                inputs=inputs,
                error=str(e),
                metrics={
                    "render_time_ms": round((end_time - start_time) * 1000, 2)
                }
            )
            
            # Store the result
            self.result_store.add_result(result)
            return result
    
    async def test_with_llm(self,
                           component_id: str,
                           inputs: Dict[str, Any],
                           task_type: str,
                           provider: Optional[str] = None,
                           model: Optional[str] = None,
                           parameters: Optional[Dict[str, Any]] = None) -> TestResult:
        """Test a component with an LLM provider.
        
        Args:
            component_id: ID of the component to test.
            inputs: Input values for the test.
            task_type: Type of task to perform (e.g., "completion", "summarize").
            provider: Optional provider to use for the test.
            model: Optional model to use for the test.
            parameters: Optional model parameters for the test.
            
        Returns:
            Test result with the LLM response.
            
        Raises:
            ValueError: If model_router is not available.
        """
        if self.model_router is None:
            raise ValueError("Model router not available for LLM testing")
        
        # Get the component
        component = self.registry.get_component(component_id)
        if component is None:
            return TestResult(
                component_id=component_id,
                component_version="unknown",
                inputs=inputs,
                error=f"Component not found: {component_id}"
            )
        
        # Render the template
        try:
            rendered = component.render(inputs)
        except ValueError as e:
            return TestResult(
                component_id=component_id,
                component_version=component.version,
                inputs=inputs,
                error=f"Error rendering template: {str(e)}"
            )
        
        # Prepare model parameters
        llm_params = {
            "text": rendered
        }
        
        if parameters:
            llm_params.update(parameters)
        
        # Prepare requirements
        requirements = {}
        if provider:
            requirements["provider"] = provider
        if model:
            requirements["model"] = model
        
        # Send to model router
        start_time = time.time()
        try:
            response = await self.model_router.route_request(task_type, llm_params, requirements)
            end_time = time.time()
            
            # Check for errors
            if response.get("status") != "success":
                error_msg = response.get("message", "Unknown error")
                return TestResult(
                    component_id=component_id,
                    component_version=component.version,
                    inputs=inputs,
                    error=f"LLM error: {error_msg}",
                    metrics={
                        "render_time_ms": 0,  # We don't have this metric here
                        "llm_time_ms": round((end_time - start_time) * 1000, 2),
                        "provider": response.get("provider"),
                        "model": response.get("model")
                    }
                )
            
            # Extract result
            llm_result = response.get("result", "")
            
            # Create test result
            result = TestResult(
                component_id=component_id,
                component_version=component.version,
                inputs=inputs,
                result=llm_result,
                metrics={
                    "render_time_ms": 0,  # We don't have this metric here
                    "llm_time_ms": round((end_time - start_time) * 1000, 2),
                    "provider": response.get("provider"),
                    "model": response.get("model"),
                    "tokens": response.get("tokens", {})
                }
            )
            
            # Store the result
            self.result_store.add_result(result)
            return result
            
        except Exception as e:
            end_time = time.time()
            
            # Create failed test result
            result = TestResult(
                component_id=component_id,
                component_version=component.version,
                inputs=inputs,
                error=f"Exception during LLM request: {str(e)}",
                metrics={
                    "render_time_ms": 0,  # We don't have this metric here
                    "llm_time_ms": round((end_time - start_time) * 1000, 2),
                }
            )
            
            # Store the result
            self.result_store.add_result(result)
            return result
    
    def get_test_results(self, component_id: str) -> List[Dict[str, Any]]:
        """Get all test results for a component.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            List of test result dictionaries.
        """
        results = self.result_store.get_results(component_id)
        return [result.to_dict() for result in results]
    
    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific test result.
        
        Args:
            result_id: ID of the test result.
            
        Returns:
            The test result dictionary if found, None otherwise.
        """
        result = self.result_store.get_result(result_id)
        return result.to_dict() if result else None
    
    def compare_results(self, result_id1: str, result_id2: str) -> Dict[str, Any]:
        """Compare two test results.
        
        Args:
            result_id1: ID of the first test result.
            result_id2: ID of the second test result.
            
        Returns:
            Dictionary with comparison results.
        """
        return self.result_store.compare_results(result_id1, result_id2)