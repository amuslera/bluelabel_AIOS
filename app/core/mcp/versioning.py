"""
Versioning module for Multi-Component Prompting (MCP) framework.

This module defines the ComponentVersionStore class for managing
version history of MCP components.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil
import uuid

from .component import MCPComponent

# Configure logging
logger = logging.getLogger(__name__)

class ComponentVersionStore:
    """Storage system for component versions.
    
    Manages the version history of components, allowing retrieval of
    specific versions and tracking of changes over time.
    """
    
    def __init__(self, version_dir: str):
        """Initialize a new component version store.
        
        Args:
            version_dir: Directory for storing component versions.
        """
        self.version_dir = version_dir
        os.makedirs(version_dir, exist_ok=True)
    
    def _get_component_version_dir(self, component_id: str) -> str:
        """Get the directory for a component's versions.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            Directory path for the component's versions.
        """
        component_version_dir = os.path.join(self.version_dir, component_id)
        os.makedirs(component_version_dir, exist_ok=True)
        return component_version_dir
    
    def _get_version_path(self, component_id: str, version: str) -> str:
        """Get the file path for a specific component version.
        
        Args:
            component_id: ID of the component.
            version: Version string.
            
        Returns:
            File path for the version JSON file.
        """
        version_filename = f"{version.replace('.', '_')}.json"
        return os.path.join(self._get_component_version_dir(component_id), version_filename)
    
    def add_version(self, component: MCPComponent) -> None:
        """Add a component version to the store.
        
        Args:
            component: The component to add.
        """
        component_id = component.id
        version = component.version
        
        # Create version directory if it doesn't exist
        component_version_dir = self._get_component_version_dir(component_id)
        
        # Add snapshot metadata
        snapshot = component.to_dict()
        snapshot["snapshot_id"] = str(uuid.uuid4())
        snapshot["snapshot_timestamp"] = datetime.now().isoformat()
        
        # Save the version
        version_path = self._get_version_path(component_id, version)
        try:
            with open(version_path, "w") as f:
                json.dump(snapshot, f, indent=2)
            logger.debug(f"Added version {version} for component {component_id}")
        except Exception as e:
            logger.error(f"Error adding version {version} for component {component_id}: {e}")
            raise
    
    def get_version(self, component_id: str, version: str) -> Optional[MCPComponent]:
        """Retrieve a specific version of a component.
        
        Args:
            component_id: ID of the component.
            version: Version to retrieve.
            
        Returns:
            The component version if found, None otherwise.
        """
        version_path = self._get_version_path(component_id, version)
        if not os.path.exists(version_path):
            return None
        
        try:
            with open(version_path, "r") as f:
                data = json.load(f)
            return MCPComponent.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving version {version} for component {component_id}: {e}")
            return None
    
    def list_versions(self, component_id: str) -> List[Dict[str, Any]]:
        """List all versions of a component.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            List of version information dictionaries.
        """
        component_version_dir = self._get_component_version_dir(component_id)
        if not os.path.exists(component_version_dir):
            return []
        
        versions = []
        for filename in os.listdir(component_version_dir):
            if not filename.endswith(".json"):
                continue
            
            try:
                filepath = os.path.join(component_version_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                
                # Extract version information
                versions.append({
                    "version": data.get("version", "unknown"),
                    "snapshot_id": data.get("snapshot_id", ""),
                    "snapshot_timestamp": data.get("snapshot_timestamp", ""),
                    "updated_at": data.get("updated_at", "")
                })
            except Exception as e:
                logger.error(f"Error reading version file {filename}: {e}")
        
        # Sort by snapshot timestamp (newest first)
        return sorted(versions, key=lambda x: x.get("snapshot_timestamp", ""), reverse=True)
    
    def delete_version(self, component_id: str, version: str) -> bool:
        """Delete a specific version of a component.
        
        Args:
            component_id: ID of the component.
            version: Version to delete.
            
        Returns:
            True if the version was deleted, False otherwise.
        """
        version_path = self._get_version_path(component_id, version)
        if not os.path.exists(version_path):
            return False
        
        try:
            os.remove(version_path)
            logger.info(f"Deleted version {version} for component {component_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting version {version} for component {component_id}: {e}")
            return False
    
    def get_version_history(self, component_id: str) -> List[Dict[str, Any]]:
        """Get the full version history of a component.
        
        Args:
            component_id: ID of the component.
            
        Returns:
            List of version history entries with change details.
        """
        versions = self.list_versions(component_id)
        history = []
        
        # Load each version to extract change details
        for i, version_info in enumerate(versions):
            version = version_info["version"]
            current = self.get_version(component_id, version)
            
            # Skip if version couldn't be loaded
            if current is None:
                continue
            
            # For the first version, there's no previous version to compare with
            if i == len(versions) - 1:
                history.append({
                    "version": version,
                    "timestamp": version_info.get("snapshot_timestamp", ""),
                    "changes": ["Initial version"],
                    "metadata": current.metadata
                })
                continue
            
            # Get the next version (which is the previous in time since we're sorted newest first)
            next_version = versions[i + 1]["version"]
            previous = self.get_version(component_id, next_version)
            
            # Skip if previous version couldn't be loaded
            if previous is None:
                continue
            
            # Detect changes
            changes = []
            if current.name != previous.name:
                changes.append(f"Updated name: {previous.name} -> {current.name}")
            if current.description != previous.description:
                changes.append("Updated description")
            if current.template != previous.template:
                changes.append("Modified template")
            
            # Add to history
            history.append({
                "version": version,
                "timestamp": version_info.get("snapshot_timestamp", ""),
                "changes": changes,
                "metadata": current.metadata
            })
        
        return history
    
    def compare_versions(self, component_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions of a component.
        
        Args:
            component_id: ID of the component.
            version1: First version to compare.
            version2: Second version to compare.
            
        Returns:
            Dictionary with comparison results.
            
        Raises:
            ValueError: If either version doesn't exist.
        """
        comp1 = self.get_version(component_id, version1)
        comp2 = self.get_version(component_id, version2)
        
        if comp1 is None:
            raise ValueError(f"Version {version1} of component {component_id} not found")
        if comp2 is None:
            raise ValueError(f"Version {version2} of component {component_id} not found")
        
        # Compare attributes
        differences = {}
        
        # Compare simple attributes
        for attr in ["name", "description", "version"]:
            val1 = getattr(comp1, attr)
            val2 = getattr(comp2, attr)
            if val1 != val2:
                differences[attr] = {
                    "from": val2,  # version2 is the older version
                    "to": val1     # version1 is the newer version
                }
        
        # Compare template (with special handling for whitespace)
        if comp1.template.strip() != comp2.template.strip():
            differences["template"] = {
                "from": comp2.template,
                "to": comp1.template
            }
        
        # Compare lists
        for attr in ["required_inputs", "optional_inputs", "outputs", "tags"]:
            list1 = getattr(comp1, attr)
            list2 = getattr(comp2, attr)
            
            added = [item for item in list1 if item not in list2]
            removed = [item for item in list2 if item not in list1]
            
            if added or removed:
                differences[attr] = {
                    "added": added,
                    "removed": removed
                }
        
        # Compare metadata
        metadata_changes = {}
        for key in set(comp1.metadata.keys()) | set(comp2.metadata.keys()):
            val1 = comp1.metadata.get(key)
            val2 = comp2.metadata.get(key)
            
            if val1 != val2:
                metadata_changes[key] = {
                    "from": val2,
                    "to": val1
                }
        
        if metadata_changes:
            differences["metadata"] = metadata_changes
        
        return {
            "component_id": component_id,
            "versions": {
                "from": version2,
                "to": version1
            },
            "differences": differences,
            "has_changes": len(differences) > 0
        }