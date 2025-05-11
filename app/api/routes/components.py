"""
API routes for MCP component management.

This module defines the FastAPI routes for CRUD operations on MCP components.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import List, Dict, Any, Optional
import json

from app.core.mcp import MCPComponent, ComponentRegistry, ComponentEditor, ComponentTester
from app.core.model_router import ModelRouter

# Initialize router
router = APIRouter(
    prefix="/components",
    tags=["components"],
    responses={404: {"description": "Component not found"}}
)

# Dependency for getting the component registry
async def get_registry() -> ComponentRegistry:
    # This would typically come from a service provider or app state
    # For now, we'll create a singleton registry
    from app.core.registry.service_provider import get_component_registry
    return get_component_registry()

# Dependency for getting the component editor
async def get_editor(registry: ComponentRegistry = Depends(get_registry)) -> ComponentEditor:
    return ComponentEditor(registry)

# Dependency for getting the component tester
async def get_tester(registry: ComponentRegistry = Depends(get_registry),
                    model_router: ModelRouter = Depends(get_model_router)) -> ComponentTester:
    return ComponentTester(registry, model_router)

# Dependency for getting the model router
async def get_model_router() -> ModelRouter:
    # Get the model router from the service provider
    from app.core.registry.service_provider import get_model_router
    router = get_model_router()
    if not router:
        raise HTTPException(
            status_code=503,
            detail="Model router is not available. LLM testing features will not work."
        )
    return router

@router.get("/", response_model=List[Dict[str, Any]])
async def list_components(
    registry: ComponentRegistry = Depends(get_registry),
    tag: Optional[str] = Query(None, description="Filter components by tag")
):
    """List all registered components."""
    return registry.list_components(tag=tag)

@router.get("/{component_id}", response_model=Dict[str, Any])
async def get_component(
    component_id: str = Path(..., description="ID of the component"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Get a specific component by ID."""
    component = registry.get_component(component_id)
    if component is None:
        raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
    
    return component.to_dict()

@router.post("/", response_model=Dict[str, Any])
async def create_component(
    component_data: Dict[str, Any] = Body(..., description="Component data"),
    editor: ComponentEditor = Depends(get_editor)
):
    """Create a new component."""
    try:
        component = editor.create_component(
            name=component_data.get("name", ""),
            description=component_data.get("description", ""),
            template=component_data.get("template", ""),
            tags=component_data.get("tags", []),
            metadata=component_data.get("metadata", {})
        )
        return component.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{component_id}", response_model=Dict[str, Any])
async def update_component(
    component_id: str = Path(..., description="ID of the component"),
    component_data: Dict[str, Any] = Body(..., description="Component data"),
    editor: ComponentEditor = Depends(get_editor)
):
    """Update an existing component."""
    try:
        component = editor.update_component(
            component_id=component_id,
            name=component_data.get("name"),
            description=component_data.get("description"),
            template=component_data.get("template"),
            tags=component_data.get("tags"),
            metadata=component_data.get("metadata"),
            increment_version=component_data.get("increment_version", True)
        )
        
        if component is None:
            raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
        
        return component.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{component_id}", response_model=Dict[str, str])
async def delete_component(
    component_id: str = Path(..., description="ID of the component"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Delete a component."""
    if not registry.delete_component(component_id):
        raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
    
    return {"status": "success", "message": f"Component {component_id} deleted"}

@router.get("/{component_id}/versions", response_model=List[Dict[str, Any]])
async def list_component_versions(
    component_id: str = Path(..., description="ID of the component"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """List all versions of a component."""
    if registry.get_component(component_id) is None:
        raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
    
    return registry.get_component_versions(component_id)

@router.get("/{component_id}/history", response_model=List[Dict[str, Any]])
async def get_component_history(
    component_id: str = Path(..., description="ID of the component"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Get the version history of a component."""
    if registry.get_component(component_id) is None:
        raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
    
    version_store = registry.version_store
    return version_store.get_version_history(component_id)

@router.get("/{component_id}/version/{version}", response_model=Dict[str, Any])
async def get_component_version(
    component_id: str = Path(..., description="ID of the component"),
    version: str = Path(..., description="Version of the component"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Get a specific version of a component."""
    component = registry.get_component_version(component_id, version)
    if component is None:
        raise HTTPException(status_code=404, detail=f"Component {component_id} version {version} not found")
    
    return component.to_dict()

@router.post("/{component_id}/validate", response_model=Dict[str, Any])
async def validate_component(
    component_id: str = Path(..., description="ID of the component"),
    editor: ComponentEditor = Depends(get_editor),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Validate a component for correctness."""
    component = registry.get_component(component_id)
    if component is None:
        raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
    
    is_valid, errors, warnings = editor.validate_component(component)
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }

@router.post("/{component_id}/test-render", response_model=Dict[str, Any])
async def test_render_component(
    component_id: str = Path(..., description="ID of the component"),
    inputs: Dict[str, Any] = Body(..., description="Input values for the component"),
    tester: ComponentTester = Depends(get_tester)
):
    """Test the rendering of a component."""
    result = tester.test_rendering(component_id, inputs)
    return result.to_dict()

@router.post("/{component_id}/test-llm", response_model=Dict[str, Any])
async def test_llm_component(
    component_id: str = Path(..., description="ID of the component"),
    test_params: Dict[str, Any] = Body(..., description="Test parameters"),
    tester: ComponentTester = Depends(get_tester)
):
    """Test a component with an LLM provider."""
    inputs = test_params.get("inputs", {})
    task_type = test_params.get("task_type", "completion")
    provider = test_params.get("provider")
    model = test_params.get("model")
    parameters = test_params.get("parameters")
    
    try:
        result = await tester.test_with_llm(
            component_id=component_id,
            inputs=inputs,
            task_type=task_type,
            provider=provider,
            model=model,
            parameters=parameters
        )
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{component_id}/test-results", response_model=List[Dict[str, Any]])
async def get_test_results(
    component_id: str = Path(..., description="ID of the component"),
    tester: ComponentTester = Depends(get_tester)
):
    """Get all test results for a component."""
    return tester.get_test_results(component_id)

@router.post("/import", response_model=Dict[str, str])
async def import_component(
    component_json: Dict[str, Any] = Body(..., description="Component JSON data"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Import a component from JSON data."""
    try:
        component_id = registry.import_component(json.dumps(component_json))
        return {"status": "success", "component_id": component_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{component_id}/export", response_model=Dict[str, Any])
async def export_component(
    component_id: str = Path(..., description="ID of the component"),
    registry: ComponentRegistry = Depends(get_registry)
):
    """Export a component as JSON data."""
    try:
        json_str = registry.export_component(component_id)
        return json.loads(json_str)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/duplicate/{component_id}", response_model=Dict[str, Any])
async def duplicate_component(
    component_id: str = Path(..., description="ID of the component to duplicate"),
    new_name: Optional[str] = Query(None, description="New name for the duplicate"),
    editor: ComponentEditor = Depends(get_editor)
):
    """Duplicate an existing component."""
    try:
        component = editor.duplicate_component(component_id, new_name)
        if component is None:
            raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
        
        return component.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))