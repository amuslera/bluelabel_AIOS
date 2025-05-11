"""
Editor module for Multi-Component Prompting (MCP) framework.

This module defines the ComponentEditor class for creating, modifying,
and testing MCP components.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import re
import json
from datetime import datetime

from .component import MCPComponent
from .registry import ComponentRegistry

# Configure logging
logger = logging.getLogger(__name__)

class ComponentEditor:
    """Editor for creating and modifying MCP components.
    
    Provides a high-level interface for component editing operations,
    including template validation, input extraction, and version management.
    """
    
    def __init__(self, registry: ComponentRegistry):
        """Initialize a new component editor.
        
        Args:
            registry: Component registry to use for component management.
        """
        self.registry = registry
    
    def create_component(self, 
                         name: str, 
                         description: str, 
                         template: str,
                         tags: Optional[List[str]] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         id: Optional[str] = None) -> MCPComponent:
        """Create a new component.
        
        Args:
            name: Human-readable name for the component.
            description: Detailed description of the component's purpose.
            template: The prompt template text with placeholders.
            tags: Optional list of tags for categorizing the component.
            metadata: Optional additional metadata for the component.
            id: Optional fixed ID for the component.
            
        Returns:
            The newly created component.
        """
        # Create a new component
        component = MCPComponent(
            name=name,
            description=description,
            template=template,
            tags=tags or [],
            metadata=metadata or {},
            id=id
        )
        
        # Register the component
        self.registry.register_component(component)
        logger.info(f"Created new component: {component.id} - {name}")
        
        return component
    
    def update_component(self,
                         component_id: str,
                         name: Optional[str] = None,
                         description: Optional[str] = None,
                         template: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         increment_version: bool = True) -> Optional[MCPComponent]:
        """Update an existing component.
        
        Args:
            component_id: ID of the component to update.
            name: New name for the component.
            description: New description for the component.
            template: New template for the component.
            tags: New tags for the component.
            metadata: New metadata for the component.
            increment_version: Whether to increment the component version.
            
        Returns:
            The updated component if successful, None otherwise.
        """
        # Get the existing component
        component = self.registry.get_component(component_id)
        if component is None:
            logger.error(f"Component not found: {component_id}")
            return None
        
        # Check if anything is actually changed
        is_changed = False
        if name is not None and name != component.name:
            is_changed = True
        if description is not None and description != component.description:
            is_changed = True
        if template is not None and template != component.template:
            is_changed = True
        if tags is not None and set(tags) != set(component.tags):
            is_changed = True
        if metadata is not None:
            # Check if metadata is different
            for key, value in metadata.items():
                if key not in component.metadata or component.metadata[key] != value:
                    is_changed = True
            for key in component.metadata:
                if key not in metadata:
                    is_changed = True
        
        if not is_changed:
            logger.info(f"No changes detected for component: {component_id}")
            return component
        
        # Increment version if requested
        if increment_version:
            # Parse the current version
            major, minor, patch = [int(x) for x in component.version.split(".")]
            # Increment the patch version
            patch += 1
            component.version = f"{major}.{minor}.{patch}"
        
        # Update the component
        component.update(
            name=name,
            description=description,
            template=template,
            tags=tags,
            metadata=metadata
        )
        
        # Save the updated component
        self.registry.update_component(component)
        logger.info(f"Updated component: {component_id} to version {component.version}")
        
        return component
    
    def validate_template(self, template: str) -> Tuple[bool, List[str], List[str]]:
        """Validate a template for correctness.
        
        Args:
            template: The template to validate.
            
        Returns:
            A tuple containing (is_valid, errors, warnings).
        """
        errors = []
        warnings = []
        
        # Check for empty template
        if not template.strip():
            errors.append("Template cannot be empty")
            return False, errors, warnings
        
        # Extract placeholders
        placeholder_pattern = r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}'
        placeholders = re.findall(placeholder_pattern, template)
        
        if not placeholders:
            warnings.append("Template contains no placeholders")
        
        # Check for unclosed braces
        open_count = template.count("{")
        close_count = template.count("}")
        if open_count != close_count:
            errors.append(f"Mismatched braces: {open_count} opening and {close_count} closing braces")
        
        # Check for invalid placeholder syntax
        invalid_placeholders = re.findall(r'\{([^a-zA-Z0-9_:{}].*?)\}', template)
        if invalid_placeholders:
            for invalid in invalid_placeholders:
                errors.append(f"Invalid placeholder syntax: {{{invalid}}}")
        
        # Check for potentially problematic whitespace
        if re.search(r'\{\s+[a-zA-Z0-9_]+\s*\}', template):
            warnings.append("Some placeholders contain whitespace which may cause issues")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def extract_inputs_from_template(self, template: str) -> Tuple[List[str], List[str]]:
        """Extract input variables from a template.
        
        Args:
            template: The template to extract inputs from.
            
        Returns:
            A tuple containing (required_inputs, optional_inputs).
        """
        # Extract placeholders
        placeholder_pattern = r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}'
        placeholders = re.findall(placeholder_pattern, template)
        
        required_inputs = []
        optional_inputs = []
        
        for match in placeholders:
            var_name = match[0]
            is_optional = match[1] == 'optional'
            
            if is_optional:
                if var_name not in optional_inputs:
                    optional_inputs.append(var_name)
            else:
                if var_name not in required_inputs and var_name not in optional_inputs:
                    required_inputs.append(var_name)
        
        return required_inputs, optional_inputs
    
    def preview_rendered_template(self, 
                                  template: str, 
                                  inputs: Dict[str, str]) -> Tuple[str, List[str]]:
        """Preview the rendered template with the given inputs.
        
        Args:
            template: The template to render.
            inputs: Dictionary of input variable names and values.
            
        Returns:
            A tuple containing (rendered_template, missing_inputs).
        """
        # Extract required inputs
        required_inputs, _ = self.extract_inputs_from_template(template)
        
        # Check for missing inputs
        missing_inputs = [req for req in required_inputs if req not in inputs]
        
        # Create a temporary component for rendering
        temp_component = MCPComponent(
            name="Preview",
            description="Temporary component for preview",
            template=template
        )
        
        # Render the template, providing placeholder values for missing inputs
        render_inputs = inputs.copy()
        for missing in missing_inputs:
            render_inputs[missing] = f"[{missing}]"
        
        try:
            rendered = temp_component.render(render_inputs)
            return rendered, missing_inputs
        except ValueError as e:
            return f"Error rendering template: {str(e)}", missing_inputs
    
    def duplicate_component(self, 
                           component_id: str, 
                           new_name: Optional[str] = None) -> Optional[MCPComponent]:
        """Duplicate an existing component.
        
        Args:
            component_id: ID of the component to duplicate.
            new_name: Optional new name for the duplicate.
            
        Returns:
            The duplicated component if successful, None otherwise.
        """
        # Get the existing component
        component = self.registry.get_component(component_id)
        if component is None:
            logger.error(f"Component not found: {component_id}")
            return None
        
        # Create a new component with the same attributes
        new_component = MCPComponent(
            name=new_name or f"{component.name} (Copy)",
            description=component.description,
            template=component.template,
            required_inputs=component.required_inputs.copy(),
            optional_inputs=component.optional_inputs.copy(),
            outputs=component.outputs.copy(),
            tags=component.tags.copy(),
            metadata=component.metadata.copy()
        )
        
        # Reset version to 1.0.0
        new_component.version = "1.0.0"
        
        # Register the new component
        self.registry.register_component(new_component)
        logger.info(f"Duplicated component {component_id} to {new_component.id}")
        
        return new_component
    
    def validate_component(self, component: MCPComponent) -> Tuple[bool, List[str], List[str]]:
        """Validate a component for correctness.
        
        Args:
            component: The component to validate.
            
        Returns:
            A tuple containing (is_valid, errors, warnings).
        """
        errors = []
        warnings = []
        
        # Validate name
        if not component.name.strip():
            errors.append("Component name cannot be empty")
        
        # Validate description
        if not component.description.strip():
            warnings.append("Component has no description")
        
        # Validate template
        is_valid, template_errors, template_warnings = self.validate_template(component.template)
        errors.extend(template_errors)
        warnings.extend(template_warnings)
        
        # Verify placeholder consistency with required_inputs and optional_inputs
        req_inputs, opt_inputs = self.extract_inputs_from_template(component.template)
        
        # Check if component has inputs not in template
        for input_name in component.required_inputs:
            if input_name not in req_inputs and input_name not in opt_inputs:
                warnings.append(f"Required input '{input_name}' not found in template")
        
        for input_name in component.optional_inputs:
            if input_name not in req_inputs and input_name not in opt_inputs:
                warnings.append(f"Optional input '{input_name}' not found in template")
        
        # Check if template has inputs not in component
        for input_name in req_inputs:
            if input_name not in component.required_inputs and input_name not in component.optional_inputs:
                warnings.append(f"Template variable '{input_name}' not listed in component inputs")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings