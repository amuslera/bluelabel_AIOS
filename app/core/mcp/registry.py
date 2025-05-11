"""
Registry module for Multi-Component Prompting (MCP) framework.

This module defines the ComponentRegistry class for registering, 
retrieving, and managing MCP components.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import shutil
from pathlib import Path

from .component import MCPComponent
from .versioning import ComponentVersionStore

# Configure logging
logger = logging.getLogger(__name__)

class ComponentRegistry:
    """Registry for managing MCP components.
    
    The registry provides functionality for:
    - Registering new components
    - Retrieving components by ID
    - Listing available components
    - Managing component versions
    """
    
    def __init__(self, storage_dir: str = None):
        """Initialize a new component registry.
        
        Args:
            storage_dir: Directory for storing component files.
                If None, creates a default directory in the user's home directory.
        """
        # Set up storage directory
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".bluelabel", "components")
        
        self.storage_dir = storage_dir
        self._ensure_storage_dir()
        
        # Initialize version store
        self.version_store = ComponentVersionStore(os.path.join(storage_dir, "versions"))
        
        # Load existing components
        self.components: Dict[str, MCPComponent] = {}
        self._load_components()
    
    def _ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)
        # Create subdirectories
        os.makedirs(os.path.join(self.storage_dir, "components"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "versions"), exist_ok=True)
    
    def _get_component_path(self, component_id: str) -> str:
        """Get the file path for a component.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            File path for the component JSON file.
        """
        return os.path.join(self.storage_dir, "components", f"{component_id}.json")
    
    def _load_components(self) -> None:
        """Load all components from the storage directory."""
        components_dir = os.path.join(self.storage_dir, "components")
        if not os.path.exists(components_dir):
            return
        
        for filename in os.listdir(components_dir):
            if not filename.endswith(".json"):
                continue
            
            try:
                filepath = os.path.join(components_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                
                component = MCPComponent.from_dict(data)
                self.components[component.id] = component
                logger.debug(f"Loaded component: {component.id} - {component.name}")
            except Exception as e:
                logger.error(f"Error loading component {filename}: {e}")
    
    def save_component(self, component: MCPComponent) -> None:
        """Save a component to disk.
        
        Args:
            component: The component to save.
        """
        filepath = self._get_component_path(component.id)
        
        # Check if component exists to determine if this is a new version
        is_new = not os.path.exists(filepath)
        
        # If the component already exists, create a new version
        if not is_new:
            # Load the current version from disk
            try:
                with open(filepath, "r") as f:
                    current_data = json.load(f)
                current_component = MCPComponent.from_dict(current_data)
                
                # Store the current version in version history
                self.version_store.add_version(current_component)
            except Exception as e:
                logger.error(f"Error creating version for component {component.id}: {e}")
        
        # Save the component
        try:
            component.updated_at = datetime.now().isoformat()
            with open(filepath, "w") as f:
                json.dump(component.to_dict(), f, indent=2)
            
            # Update in-memory registry
            self.components[component.id] = component
            
            logger.info(f"{'Created' if is_new else 'Updated'} component: {component.id} - {component.name}")
        except Exception as e:
            logger.error(f"Error saving component {component.id}: {e}")
            raise
    
    def register_component(self, component: MCPComponent) -> str:
        """Register a new component.
        
        Args:
            component: The component to register.
            
        Returns:
            ID of the registered component.
            
        Raises:
            ValueError: If a component with the same ID already exists.
        """
        if component.id in self.components:
            raise ValueError(f"Component with ID {component.id} already exists")
        
        self.save_component(component)
        return component.id
    
    def update_component(self, component: MCPComponent) -> None:
        """Update an existing component.
        
        Args:
            component: The updated component.
            
        Raises:
            ValueError: If the component doesn't exist.
        """
        if component.id not in self.components:
            raise ValueError(f"Component with ID {component.id} does not exist")
        
        self.save_component(component)
    
    def get_component(self, component_id: str) -> Optional[MCPComponent]:
        """Retrieve a component by ID.
        
        Args:
            component_id: ID of the component to retrieve.
            
        Returns:
            The component if found, None otherwise.
        """
        return self.components.get(component_id)
    
    def get_component_version(self, component_id: str, version: str) -> Optional[MCPComponent]:
        """Retrieve a specific version of a component.
        
        Args:
            component_id: ID of the component.
            version: Version to retrieve.
            
        Returns:
            The component version if found, None otherwise.
        """
        return self.version_store.get_version(component_id, version)
    
    def delete_component(self, component_id: str) -> bool:
        """Delete a component.
        
        Args:
            component_id: ID of the component to delete.
            
        Returns:
            True if the component was deleted, False otherwise.
        """
        if component_id not in self.components:
            return False
        
        # Remove from memory
        component = self.components.pop(component_id)
        
        # Archive current version before deleting
        self.version_store.add_version(component)
        
        # Remove from disk
        filepath = self._get_component_path(component_id)
        try:
            os.remove(filepath)
            logger.info(f"Deleted component: {component_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting component {component_id}: {e}")
            # Restore to memory since deletion failed
            self.components[component_id] = component
            return False
    
    def list_components(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered components.
        
        Args:
            tag: Optional tag to filter components by.
            
        Returns:
            List of component metadata dictionaries.
        """
        result = []
        for component_id, component in self.components.items():
            if tag is None or tag in component.tags:
                # Return a summary view with essential metadata
                result.append({
                    "id": component.id,
                    "name": component.name,
                    "description": component.description,
                    "version": component.version,
                    "tags": component.tags,
                    "updated_at": component.updated_at
                })
        
        # Sort by name for consistent results
        return sorted(result, key=lambda x: x["name"])
    
    def get_component_versions(self, component_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a component.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            List of version information dictionaries.
        """
        return self.version_store.list_versions(component_id)
    
    def import_component(self, json_str: str, overwrite: bool = False) -> str:
        """Import a component from a JSON string.
        
        Args:
            json_str: JSON string representation of the component.
            overwrite: Whether to overwrite an existing component with the same ID.
            
        Returns:
            ID of the imported component.
            
        Raises:
            ValueError: If a component with the same ID exists and overwrite is False.
        """
        component = MCPComponent.from_json(json_str)
        
        if component.id in self.components and not overwrite:
            raise ValueError(f"Component with ID {component.id} already exists")
        
        self.save_component(component)
        return component.id
    
    def export_component(self, component_id: str) -> str:
        """Export a component as a JSON string.
        
        Args:
            component_id: ID of the component to export.
            
        Returns:
            JSON string representation of the component.
            
        Raises:
            ValueError: If the component doesn't exist.
        """
        component = self.get_component(component_id)
        if component is None:
            raise ValueError(f"Component with ID {component_id} does not exist")
        
        return component.to_json()
    
    def bulk_import(self, directory: str) -> Dict[str, Union[str, List[str]]]:
        """Import multiple components from a directory.
        
        Args:
            directory: Directory containing component JSON files.
            
        Returns:
            Dictionary with results of the import operation.
        """
        if not os.path.exists(directory) or not os.path.isdir(directory):
            raise ValueError(f"Directory does not exist: {directory}")
        
        results = {
            "imported": [],
            "failed": []
        }
        
        for filename in os.listdir(directory):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r") as f:
                    json_str = f.read()
                
                component_id = self.import_component(json_str, overwrite=False)
                results["imported"].append(component_id)
                logger.info(f"Imported component: {component_id}")
            except Exception as e:
                results["failed"].append(f"{filename}: {str(e)}")
                logger.error(f"Error importing component {filename}: {e}")
        
        return results
    
    def bulk_export(self, directory: str, tag: Optional[str] = None) -> List[str]:
        """Export multiple components to a directory.
        
        Args:
            directory: Directory to export components to.
            tag: Optional tag to filter components by.
            
        Returns:
            List of exported component IDs.
        """
        os.makedirs(directory, exist_ok=True)
        
        exported = []
        for component_id, component in self.components.items():
            if tag is None or tag in component.tags:
                filepath = os.path.join(directory, f"{component_id}.json")
                try:
                    with open(filepath, "w") as f:
                        f.write(component.to_json())
                    exported.append(component_id)
                except Exception as e:
                    logger.error(f"Error exporting component {component_id}: {e}")
        
        return exported