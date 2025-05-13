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
        if not template or not template.strip():
            errors.append("Template cannot be empty")
            return False, errors, warnings

        # Check for minimum content length
        if len(template.strip()) < 10:
            warnings.append("Template is very short, might not be useful")

        # Extract placeholders
        placeholder_pattern = r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}'
        placeholders = re.findall(placeholder_pattern, template)

        if not placeholders:
            warnings.append("Template contains no placeholders - this will be a static prompt")

        # Check for unclosed braces
        open_count = template.count("{")
        close_count = template.count("}")
        if open_count != close_count:
            errors.append(f"Mismatched braces: {open_count} opening and {close_count} closing braces")

            # Attempt to locate the position of the mismatched brace
            if open_count > close_count:
                # Find unmatched opening braces
                remaining = open_count - close_count
                lines = template.split('\n')
                line_num = 1
                char_count = 0
                brace_positions = []

                for i, line in enumerate(lines):
                    brace_count = 0
                    for j, char in enumerate(line):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            if brace_count > 0:
                                brace_count -= 1

                    if brace_count > 0:
                        brace_positions.append(f"line {i+1}")

                if brace_positions:
                    errors.append(f"Unclosed opening braces found near: {', '.join(brace_positions[:3])}")

        # Check for invalid placeholder syntax
        invalid_placeholders = re.findall(r'\{([^a-zA-Z0-9_:{}].*?)\}', template)
        if invalid_placeholders:
            for invalid in invalid_placeholders:
                errors.append(f"Invalid placeholder syntax: {{{invalid}}}")

        # Check for potentially problematic whitespace
        whitespace_placeholders = re.findall(r'\{\s+([a-zA-Z0-9_]+)\s*\}', template)
        if whitespace_placeholders:
            for placeholder in whitespace_placeholders:
                warnings.append(f"Placeholder '{placeholder}' contains extra whitespace which may cause issues")

        # Check for duplicate placeholders that have inconsistent optional marking
        placeholder_map = {}
        for match in placeholders:
            var_name = match[0]
            is_optional = match[1] == 'optional'

            if var_name in placeholder_map and placeholder_map[var_name] != is_optional:
                warnings.append(f"Placeholder '{var_name}' is marked as both required and optional in different places")
            else:
                placeholder_map[var_name] = is_optional

        # Check for potentially problematic characters in placeholders
        for placeholder, _ in placeholders:
            if not placeholder.isalnum() and '_' not in placeholder:
                warnings.append(f"Placeholder '{placeholder}' contains only numbers or special characters")

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
                                  inputs: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
        """Preview the rendered template with the given inputs.

        Args:
            template: The template to render.
            inputs: Dictionary of input variable names and values.

        Returns:
            A tuple containing (rendered_template, missing_inputs, warnings).
        """
        warnings = []

        # Validate template first
        is_valid, errors, template_warnings = self.validate_template(template)
        warnings.extend(template_warnings)

        if errors:
            return f"Cannot render template due to errors: {'; '.join(errors)}", [], warnings

        # Extract required and optional inputs
        required_inputs, optional_inputs = self.extract_inputs_from_template(template)

        # Check for missing inputs
        missing_inputs = [req for req in required_inputs if req not in inputs]

        # Check for empty inputs
        for key, value in inputs.items():
            if key in required_inputs and (value is None or (isinstance(value, str) and value.strip() == "")):
                warnings.append(f"Required input '{key}' has an empty value")

        # Check for inputs provided but not used in the template
        unused_inputs = [key for key in inputs if key not in required_inputs and key not in optional_inputs]
        if unused_inputs:
            warnings.append(f"Some provided inputs are not used in the template: {', '.join(unused_inputs)}")

        # Create a temporary component for rendering
        temp_component = MCPComponent(
            name="Preview",
            description="Temporary component for preview",
            template=template,
            required_inputs=required_inputs,
            optional_inputs=optional_inputs
        )

        # Render the template, providing placeholder values for missing inputs
        render_inputs = inputs.copy()
        for missing in missing_inputs:
            render_inputs[missing] = f"[{missing}]"
            warnings.append(f"Using placeholder '[{missing}]' for missing required input")

        try:
            rendered = temp_component.render(render_inputs)

            # Check for any remaining placeholders
            remaining_placeholders = re.findall(r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}', rendered)
            if remaining_placeholders:
                standard_placeholders = [p[0] for p in remaining_placeholders if p[1] != 'optional']
                if standard_placeholders:
                    warnings.append(f"Some placeholders were not replaced: {', '.join(standard_placeholders)}")

            return rendered, missing_inputs, warnings

        except ValueError as e:
            error_msg = str(e)
            return f"Error rendering template: {error_msg}", missing_inputs, warnings
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error during template preview: {error_msg}")
            return f"Unexpected error during preview: {error_msg}", missing_inputs, warnings
    
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

        # Validate ID
        if not component.id or not component.id.strip():
            errors.append("Component ID cannot be empty")

        # Validate name
        if not component.name or not component.name.strip():
            errors.append("Component name cannot be empty")
        elif len(component.name.strip()) < 3:
            warnings.append("Component name is very short, consider using a more descriptive name")

        # Validate description
        if not component.description or not component.description.strip():
            warnings.append("Component has no description")
        elif len(component.description.strip()) < 10:
            warnings.append("Component description is very short, consider adding more detail")

        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+$', component.version):
            errors.append(f"Invalid version format: {component.version}. Expected format: X.Y.Z (e.g. 1.0.0)")

        # Validate template
        is_valid, template_errors, template_warnings = self.validate_template(component.template)
        errors.extend(template_errors)
        warnings.extend(template_warnings)

        # Verify placeholder consistency with required_inputs and optional_inputs
        req_inputs, opt_inputs = self.extract_inputs_from_template(component.template)

        # Check if component has inputs not in template
        missing_required_inputs = []
        for input_name in component.required_inputs:
            if input_name not in req_inputs and input_name not in opt_inputs:
                missing_required_inputs.append(input_name)

        if missing_required_inputs:
            if len(missing_required_inputs) > 3:
                warnings.append(f"Several required inputs not found in template ({len(missing_required_inputs)} total)")
                warnings.append(f"First few missing inputs: {', '.join(missing_required_inputs[:3])}")
            else:
                warnings.append(f"Required input(s) not found in template: {', '.join(missing_required_inputs)}")

        missing_optional_inputs = []
        for input_name in component.optional_inputs:
            if input_name not in req_inputs and input_name not in opt_inputs:
                missing_optional_inputs.append(input_name)

        if missing_optional_inputs:
            if len(missing_optional_inputs) > 3:
                warnings.append(f"Several optional inputs not found in template ({len(missing_optional_inputs)} total)")
                warnings.append(f"First few missing inputs: {', '.join(missing_optional_inputs[:3])}")
            else:
                warnings.append(f"Optional input(s) not found in template: {', '.join(missing_optional_inputs)}")

        # Check if template has variables not in component inputs
        unlisted_inputs = []
        for input_name in req_inputs:
            if input_name not in component.required_inputs and input_name not in component.optional_inputs:
                unlisted_inputs.append(input_name)

        if unlisted_inputs:
            if len(unlisted_inputs) > 3:
                warnings.append(f"Several template variables not listed in component inputs ({len(unlisted_inputs)} total)")
                warnings.append(f"First few unlisted variables: {', '.join(unlisted_inputs[:3])}")
            else:
                warnings.append(f"Template variable(s) not listed in component inputs: {', '.join(unlisted_inputs)}")

        # Validate tags
        if not component.tags:
            warnings.append("Component has no tags. Tags help with organization and discoverability")
        else:
            # Check for very short tags
            short_tags = [tag for tag in component.tags if len(tag) < 3]
            if short_tags:
                warnings.append(f"Some tags are very short: {', '.join(short_tags)}")

        # Check for duplicate inputs in both required and optional
        duplicate_inputs = set(component.required_inputs) & set(component.optional_inputs)
        if duplicate_inputs:
            errors.append(f"Input(s) listed as both required and optional: {', '.join(duplicate_inputs)}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings