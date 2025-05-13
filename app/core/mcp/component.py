"""
Component module for Multi-Component Prompting (MCP) framework.

This module defines the core MCPComponent class for managing prompt templates 
and associated metadata within the Bluelabel AIOS.
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime
import uuid
import os

# Configure logging
logger = logging.getLogger(__name__)

class MCPComponent:
    """Base class for MCP components.
    
    An MCP component represents a reusable prompt template with metadata,
    input validation, and rendering capabilities.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "",
        description: str = "",
        version: str = "1.0.0",
        template: str = "",
        required_inputs: Optional[List[str]] = None,
        optional_inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a new MCP component.
        
        Args:
            id: Unique identifier for the component. Generated if not provided.
            name: Human-readable name for the component.
            description: Detailed description of the component's purpose.
            version: Semantic version of the component.
            template: The prompt template text with placeholders.
            required_inputs: List of required input variable names.
            optional_inputs: List of optional input variable names.
            outputs: List of expected output formats.
            tags: List of tags for categorizing the component.
            metadata: Additional metadata for the component.
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.version = version
        self.template = template
        self.required_inputs = required_inputs or []
        self.optional_inputs = optional_inputs or []
        self.outputs = outputs or []
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
        # Extract placeholders from template
        self._extract_placeholders()
    
    def _extract_placeholders(self) -> None:
        """Extract placeholders from the template.
        
        Updates the required_inputs and optional_inputs based on
        the placeholders found in the template.
        """
        # Find all unique placeholders in the template
        # Format: {placeholder} or {placeholder:optional}
        placeholder_pattern = r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}'
        matches = re.findall(placeholder_pattern, self.template)
        
        # Extract all placeholders from the template
        template_vars = set()
        for match in matches:
            var_name = match[0]
            template_vars.add(var_name)
            
            # Check if this is an optional placeholder with default value
            if match[1] == 'optional' and var_name not in self.optional_inputs:
                if var_name in self.required_inputs:
                    self.required_inputs.remove(var_name)
                if var_name not in self.optional_inputs:
                    self.optional_inputs.append(var_name)
        
        # Check for required inputs not in template
        for req_input in list(self.required_inputs):
            if req_input not in template_vars:
                logger.warning(f"Required input '{req_input}' not found in template")
                
        # Check for optional inputs not in template
        for opt_input in list(self.optional_inputs):
            if opt_input not in template_vars:
                logger.warning(f"Optional input '{opt_input}' not found in template")
        
        # Add template variables not in inputs to required_inputs
        for var in template_vars:
            if var not in self.required_inputs and var not in self.optional_inputs:
                self.required_inputs.append(var)
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate that all required inputs are provided.
        
        Args:
            inputs: Dictionary of input variable names and values.
            
        Returns:
            True if all required inputs are provided, False otherwise.
        """
        for req_input in self.required_inputs:
            if req_input not in inputs:
                logger.error(f"Missing required input: {req_input}")
                return False
        return True
    
    def render(self, inputs: Dict[str, Any]) -> str:
        """Render the template with the provided inputs.

        Args:
            inputs: Dictionary of input variable names and values.

        Returns:
            The rendered template with placeholders replaced.

        Raises:
            ValueError: If required inputs are missing or other issues occur.
        """
        # Check for None or empty inputs
        if inputs is None:
            raise ValueError("Inputs dictionary cannot be None")

        # Validate all required inputs are present
        if not self.validate_inputs(inputs):
            missing = [req for req in self.required_inputs if req not in inputs]
            if len(missing) == 1:
                raise ValueError(f"Missing required input: {missing[0]}")
            else:
                raise ValueError(f"Missing required inputs: {', '.join(missing)}")

        # Check for None or empty values for required inputs
        for key, value in inputs.items():
            if key in self.required_inputs and (value is None or (isinstance(value, str) and value.strip() == "")):
                raise ValueError(f"Required input '{key}' has an empty value")

        # Create a copy of the template
        rendered = self.template

        try:
            # First pass: handle optional placeholders with format {var:optional}
            optional_pattern = r'\{([a-zA-Z0-9_]+):optional\}'

            def optional_replace(match):
                var_name = match.group(1)
                if var_name in inputs:
                    value = inputs[var_name]
                    if value is None:
                        return ""
                    return str(value)
                return ""

            rendered = re.sub(optional_pattern, optional_replace, rendered)

            # Second pass: handle standard placeholders with format {var}
            for var_name, value in inputs.items():
                placeholder = f"{{{var_name}}}"
                if placeholder in rendered:
                    # Convert the value to string, handle None values
                    str_value = "" if value is None else str(value)
                    rendered = rendered.replace(placeholder, str_value)

            # Check for any remaining placeholders that weren't replaced
            remaining_placeholders = re.findall(r'\{([a-zA-Z0-9_]+)(?::([a-zA-Z0-9_]+))?\}', rendered)
            if remaining_placeholders:
                # Only warn about standard placeholders, not optional ones that were intentionally left empty
                standard_placeholders = [p[0] for p in remaining_placeholders if p[1] != 'optional']
                if standard_placeholders:
                    logger.warning(f"Component {self.id}: Some placeholders were not replaced: {', '.join(standard_placeholders)}")

            return rendered

        except Exception as e:
            # Catch any unexpected errors during rendering
            logger.error(f"Error rendering template for component {self.id}: {str(e)}")
            raise ValueError(f"Error rendering template: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the component to a dictionary.
        
        Returns:
            Dictionary representation of the component.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "template": self.template,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
            "outputs": self.outputs,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_json(self) -> str:
        """Convert the component to a JSON string.
        
        Returns:
            JSON string representation of the component.
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPComponent':
        """Create a component from a dictionary.
        
        Args:
            data: Dictionary representation of the component.
            
        Returns:
            New MCPComponent instance.
        """
        component = cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            template=data.get("template", ""),
            required_inputs=data.get("required_inputs", []),
            optional_inputs=data.get("optional_inputs", []),
            outputs=data.get("outputs", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        
        # Preserve creation and update timestamps if available
        if "created_at" in data:
            component.created_at = data["created_at"]
        if "updated_at" in data:
            component.updated_at = data["updated_at"]
            
        return component
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPComponent':
        """Create a component from a JSON string.

        Args:
            json_str: JSON string representation of the component.

        Returns:
            New MCPComponent instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, file_path: str) -> 'MCPComponent':
        """Create a component from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            New MCPComponent instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid JSON.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Component file not found: {file_path}")

        with open(file_path, 'r') as f:
            json_str = f.read()

        return cls.from_json(json_str)

    def save_to_file(self, file_path: str) -> None:
        """Save the component to a JSON file.

        Args:
            file_path: Path to save the JSON file.

        Raises:
            IOError: If the file could not be written.
        """
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(file_path, 'w') as f:
            f.write(self.to_json())
    
    def update(self, 
               name: Optional[str] = None,
               description: Optional[str] = None,
               template: Optional[str] = None,
               required_inputs: Optional[List[str]] = None,
               optional_inputs: Optional[List[str]] = None,
               outputs: Optional[List[str]] = None,
               tags: Optional[List[str]] = None,
               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update the component attributes.
        
        Only updates the provided attributes, leaving others unchanged.
        
        Args:
            name: New name for the component.
            description: New description for the component.
            template: New template for the component.
            required_inputs: New required inputs for the component.
            optional_inputs: New optional inputs for the component.
            outputs: New outputs for the component.
            tags: New tags for the component.
            metadata: New metadata for the component.
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if template is not None:
            self.template = template
            self._extract_placeholders()
        if required_inputs is not None:
            self.required_inputs = required_inputs
        if optional_inputs is not None:
            self.optional_inputs = optional_inputs
        if outputs is not None:
            self.outputs = outputs
        if tags is not None:
            self.tags = tags
        if metadata is not None:
            self.metadata = metadata
        
        # Update the timestamp
        self.updated_at = datetime.now().isoformat()