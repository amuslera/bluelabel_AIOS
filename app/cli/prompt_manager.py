#!/usr/bin/env python3
"""
Prompt Manager CLI for BlueAbel AIOS

This command-line tool provides easy access to the Multi-Component Prompting (MCP)
framework for creating, editing, versioning, and testing prompt components.
"""

import argparse
import json
import os
import sys
import logging
import tempfile
import subprocess
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import difflib
import textwrap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default API URL
DEFAULT_API_URL = "http://localhost:8080"

class PromptManager:
    """Command-line tool for managing prompt components"""
    
    def __init__(self, api_url: str = DEFAULT_API_URL):
        """Initialize the prompt manager.
        
        Args:
            api_url: URL of the BlueAbel AIOS API.
        """
        self.api_url = api_url
        self.components_url = f"{api_url}/components"
    
    def list_components(self, tag: Optional[str] = None) -> None:
        """List all registered components.
        
        Args:
            tag: Optional tag to filter components by.
        """
        url = self.components_url
        if tag:
            url += f"?tag={tag}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            components = response.json()
            
            if not components:
                print("No components found.")
                return
            
            # Calculate column widths
            id_width = max(len("ID"), max(len(c["id"]) for c in components))
            name_width = max(len("NAME"), max(len(c["name"]) for c in components))
            version_width = max(len("VERSION"), max(len(c["version"]) for c in components))
            
            # Print header
            print(f"{'ID':<{id_width}} | {'NAME':<{name_width}} | {'VERSION':<{version_width}} | DESCRIPTION")
            print(f"{'-' * id_width}-+-{'-' * name_width}-+-{'-' * version_width}-+-------------")
            
            # Print components
            for component in components:
                desc = component["description"]
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                
                print(f"{component['id']:<{id_width}} | {component['name']:<{name_width}} | {component['version']:<{version_width}} | {desc}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing components: {e}")
            sys.exit(1)
    
    def view_component(self, component_id: str) -> None:
        """View a component's details.
        
        Args:
            component_id: ID of the component to view.
        """
        try:
            response = requests.get(f"{self.components_url}/{component_id}")
            response.raise_for_status()
            component = response.json()
            
            print(f"ID: {component['id']}")
            print(f"Name: {component['name']}")
            print(f"Version: {component['version']}")
            print(f"Description: {component['description']}")
            print(f"Tags: {', '.join(component['tags'])}")
            print(f"Created: {component['created_at']}")
            print(f"Updated: {component['updated_at']}")
            print("\nInputs:")
            print(f"  Required: {', '.join(component['required_inputs']) or 'None'}")
            print(f"  Optional: {', '.join(component['optional_inputs']) or 'None'}")
            print("\nTemplate:")
            print("=" * 80)
            print(component['template'])
            print("=" * 80)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error viewing component: {e}")
            sys.exit(1)
    
    def create_component(self, name: str, description: str, template: str, 
                        tags: Optional[List[str]] = None) -> None:
        """Create a new component.
        
        Args:
            name: Name of the component.
            description: Description of the component.
            template: Template text of the component.
            tags: Optional list of tags for the component.
        """
        # If template is a file path, read the template from the file
        if os.path.exists(template):
            with open(template, 'r') as f:
                template = f.read()
        
        component_data = {
            "name": name,
            "description": description,
            "template": template,
            "tags": tags or []
        }
        
        try:
            response = requests.post(
                self.components_url,
                json=component_data
            )
            response.raise_for_status()
            component = response.json()
            
            print(f"Component created with ID: {component['id']}")
            print(f"Name: {component['name']}")
            print(f"Version: {component['version']}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating component: {e}")
            sys.exit(1)
    
    def edit_component(self, component_id: str) -> None:
        """Edit a component with the default text editor.
        
        Args:
            component_id: ID of the component to edit.
        """
        try:
            # Get the component
            response = requests.get(f"{self.components_url}/{component_id}")
            response.raise_for_status()
            component = response.json()
            
            # Create a temporary file with the component data
            with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as temp:
                temp_filename = temp.name
                json.dump(component, temp, indent=2)
            
            # Get the default editor from environment or use a fallback
            editor = os.environ.get("EDITOR", "vim")
            
            # Open the file in the editor
            try:
                subprocess.run([editor, temp_filename], check=True)
            except subprocess.SubprocessError:
                logger.error(f"Error opening editor {editor}")
                os.unlink(temp_filename)
                sys.exit(1)
            
            # Read the edited file
            with open(temp_filename, "r") as f:
                edited_data = json.load(f)
            
            # Clean up
            os.unlink(temp_filename)
            
            # Check for changes
            if (edited_data["name"] == component["name"] and 
                edited_data["description"] == component["description"] and 
                edited_data["template"] == component["template"] and 
                edited_data["tags"] == component["tags"]):
                print("No changes made.")
                return
            
            # Confirm update
            print("\nChanges detected:")
            if edited_data["name"] != component["name"]:
                print(f"  Name: {component['name']} -> {edited_data['name']}")
            if edited_data["description"] != component["description"]:
                print(f"  Description: Changed")
            if edited_data["template"] != component["template"]:
                print(f"  Template: Changed")
            if edited_data["tags"] != component["tags"]:
                print(f"  Tags: {component['tags']} -> {edited_data['tags']}")
            
            confirm = input("\nUpdate component? [y/N] ").lower()
            if confirm != "y" and confirm != "yes":
                print("Update cancelled.")
                return
            
            # Update the component
            update_data = {
                "name": edited_data["name"],
                "description": edited_data["description"],
                "template": edited_data["template"],
                "tags": edited_data["tags"],
                "increment_version": True
            }
            
            response = requests.put(
                f"{self.components_url}/{component_id}",
                json=update_data
            )
            response.raise_for_status()
            updated = response.json()
            
            print(f"Component updated to version {updated['version']}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error editing component: {e}")
            sys.exit(1)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in editor. Update cancelled.")
            sys.exit(1)
    
    def edit_template(self, component_id: str) -> None:
        """Edit only the template portion of a component.
        
        Args:
            component_id: ID of the component to edit.
        """
        try:
            # Get the component
            response = requests.get(f"{self.components_url}/{component_id}")
            response.raise_for_status()
            component = response.json()
            
            # Create a temporary file with just the template
            with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as temp:
                temp_filename = temp.name
                temp.write(component["template"])
            
            # Get the default editor from environment or use a fallback
            editor = os.environ.get("EDITOR", "vim")
            
            # Open the file in the editor
            try:
                subprocess.run([editor, temp_filename], check=True)
            except subprocess.SubprocessError:
                logger.error(f"Error opening editor {editor}")
                os.unlink(temp_filename)
                sys.exit(1)
            
            # Read the edited file
            with open(temp_filename, "r") as f:
                edited_template = f.read()
            
            # Clean up
            os.unlink(temp_filename)
            
            # Check for changes
            if edited_template == component["template"]:
                print("No changes made to template.")
                return
            
            # Validate template
            response = requests.post(
                f"{self.components_url}/{component_id}/validate",
                json={"template": edited_template}
            )
            validation = response.json()
            
            if not validation["is_valid"]:
                print("Template validation failed:")
                for error in validation["errors"]:
                    print(f"- {error}")
                
                confirm = input("\nUpdate anyway? [y/N] ").lower()
                if confirm != "y" and confirm != "yes":
                    print("Update cancelled.")
                    return
            
            # Show diff
            diff = difflib.unified_diff(
                component["template"].splitlines(),
                edited_template.splitlines(),
                lineterm=""
            )
            print("\nChanges:")
            for line in diff:
                if line.startswith("+"):
                    print(f"\033[92m{line}\033[0m")  # Green for additions
                elif line.startswith("-"):
                    print(f"\033[91m{line}\033[0m")  # Red for deletions
                else:
                    print(line)
            
            # Confirm update
            confirm = input("\nUpdate template? [y/N] ").lower()
            if confirm != "y" and confirm != "yes":
                print("Update cancelled.")
                return
            
            # Update the component
            update_data = {
                "template": edited_template,
                "increment_version": True
            }
            
            response = requests.put(
                f"{self.components_url}/{component_id}",
                json=update_data
            )
            response.raise_for_status()
            updated = response.json()
            
            print(f"Template updated to version {updated['version']}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error editing template: {e}")
            sys.exit(1)
    
    def list_versions(self, component_id: str) -> None:
        """List all versions of a component.
        
        Args:
            component_id: ID of the component to list versions for.
        """
        try:
            response = requests.get(f"{self.components_url}/{component_id}/versions")
            response.raise_for_status()
            versions = response.json()
            
            if not versions:
                print("No version history available.")
                return
            
            # Print header
            print(f"{'VERSION':<10} | {'SNAPSHOT ID':<36} | {'TIMESTAMP'}")
            print(f"{'-' * 10}-+-{'-' * 36}-+------------")
            
            # Print versions
            for version in versions:
                timestamp = version["snapshot_timestamp"]
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        pass
                
                print(f"{version['version']:<10} | {version['snapshot_id']:<36} | {timestamp}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing versions: {e}")
            sys.exit(1)
    
    def view_version(self, component_id: str, version: str) -> None:
        """View a specific version of a component.
        
        Args:
            component_id: ID of the component.
            version: Version to view.
        """
        try:
            response = requests.get(f"{self.components_url}/{component_id}/version/{version}")
            response.raise_for_status()
            component = response.json()
            
            print(f"ID: {component['id']}")
            print(f"Name: {component['name']}")
            print(f"Version: {component['version']}")
            print(f"Description: {component['description']}")
            print(f"Tags: {', '.join(component['tags'])}")
            print(f"Snapshot timestamp: {component.get('snapshot_timestamp', 'N/A')}")
            print(f"Updated: {component['updated_at']}")
            print("\nInputs:")
            print(f"  Required: {', '.join(component['required_inputs']) or 'None'}")
            print(f"  Optional: {', '.join(component['optional_inputs']) or 'None'}")
            print("\nTemplate:")
            print("=" * 80)
            print(component['template'])
            print("=" * 80)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error viewing version: {e}")
            sys.exit(1)
    
    def compare_versions(self, component_id: str, version1: str, version2: str) -> None:
        """Compare two versions of a component.
        
        Args:
            component_id: ID of the component.
            version1: First version to compare.
            version2: Second version to compare.
        """
        try:
            # Get both versions
            response1 = requests.get(f"{self.components_url}/{component_id}/version/{version1}")
            response1.raise_for_status()
            component1 = response1.json()
            
            response2 = requests.get(f"{self.components_url}/{component_id}/version/{version2}")
            response2.raise_for_status()
            component2 = response2.json()
            
            # Print header
            print(f"Comparing versions {version1} and {version2} of component {component_id}")
            print(f"Name: {component1['name']}")
            
            # Compare templates
            diff = difflib.unified_diff(
                component2["template"].splitlines(),
                component1["template"].splitlines(),
                fromfile=f"version {version2}",
                tofile=f"version {version1}",
                lineterm=""
            )
            
            print("\nTemplate changes:")
            print("=" * 80)
            diff_lines = list(diff)
            if not diff_lines:
                print("No changes in template.")
            else:
                for line in diff_lines:
                    if line.startswith("+"):
                        print(f"\033[92m{line}\033[0m")  # Green for additions
                    elif line.startswith("-"):
                        print(f"\033[91m{line}\033[0m")  # Red for deletions
                    else:
                        print(line)
            print("=" * 80)
            
            # Compare metadata
            print("\nMetadata changes:")
            if component1["name"] != component2["name"]:
                print(f"Name: {component2['name']} -> {component1['name']}")
            if component1["description"] != component2["description"]:
                print(f"Description changed")
            if component1["tags"] != component2["tags"]:
                print(f"Tags: {component2['tags']} -> {component1['tags']}")
            if component1["required_inputs"] != component2["required_inputs"]:
                print(f"Required inputs: {component2['required_inputs']} -> {component1['required_inputs']}")
            if component1["optional_inputs"] != component2["optional_inputs"]:
                print(f"Optional inputs: {component2['optional_inputs']} -> {component1['optional_inputs']}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error comparing versions: {e}")
            sys.exit(1)
    
    def restore_version(self, component_id: str, version: str) -> None:
        """Restore a component to a previous version.
        
        Args:
            component_id: ID of the component.
            version: Version to restore.
        """
        try:
            # Get the version to restore
            response = requests.get(f"{self.components_url}/{component_id}/version/{version}")
            response.raise_for_status()
            old_version = response.json()
            
            # Get the current version
            response = requests.get(f"{self.components_url}/{component_id}")
            response.raise_for_status()
            current = response.json()
            
            # Show diff
            diff = difflib.unified_diff(
                current["template"].splitlines(),
                old_version["template"].splitlines(),
                fromfile="current",
                tofile=f"version {version}",
                lineterm=""
            )
            
            print(f"Restoring component {component_id} to version {version}")
            print("\nChanges that will be applied:")
            diff_lines = list(diff)
            if not diff_lines:
                print("No changes in template.")
            else:
                for line in diff_lines:
                    if line.startswith("+"):
                        print(f"\033[92m{line}\033[0m")  # Green for additions
                    elif line.startswith("-"):
                        print(f"\033[91m{line}\033[0m")  # Red for deletions
                    else:
                        print(line)
            
            # Confirm restore
            confirm = input("\nRestore to this version? [y/N] ").lower()
            if confirm != "y" and confirm != "yes":
                print("Restore cancelled.")
                return
            
            # Update the component
            update_data = {
                "name": old_version["name"],
                "description": old_version["description"],
                "template": old_version["template"],
                "tags": old_version["tags"],
                "required_inputs": old_version["required_inputs"],
                "optional_inputs": old_version["optional_inputs"],
                "increment_version": True
            }
            
            response = requests.put(
                f"{self.components_url}/{component_id}",
                json=update_data
            )
            response.raise_for_status()
            updated = response.json()
            
            print(f"Component restored to version {version} (as new version {updated['version']})")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error restoring version: {e}")
            sys.exit(1)
    
    def test_render(self, component_id: str, inputs: Dict[str, Any]) -> None:
        """Test render a component with the given inputs.
        
        Args:
            component_id: ID of the component to test.
            inputs: Input values for the component.
        """
        try:
            response = requests.post(
                f"{self.components_url}/{component_id}/test-render",
                json=inputs
            )
            response.raise_for_status()
            result = response.json()
            
            print("Rendered template:")
            print("=" * 80)
            print(result["rendered_template"])
            print("=" * 80)
            
            if result["missing_inputs"]:
                print("\nMissing inputs:")
                for input_name in result["missing_inputs"]:
                    print(f"- {input_name}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing component: {e}")
            sys.exit(1)
    
    def test_llm(self, component_id: str, inputs: Dict[str, Any], 
                provider: Optional[str] = None, model: Optional[str] = None) -> None:
        """Test a component with an LLM provider.
        
        Args:
            component_id: ID of the component to test.
            inputs: Input values for the component.
            provider: Optional LLM provider to use.
            model: Optional model to use.
        """
        test_params = {
            "inputs": inputs,
            "task_type": "completion"
        }
        
        if provider:
            test_params["provider"] = provider
        if model:
            test_params["model"] = model
        
        try:
            print("Testing with LLM, please wait...")
            response = requests.post(
                f"{self.components_url}/{component_id}/test-llm",
                json=test_params
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\nLLM response ({result['provider']}/{result['model']}):")
            print("=" * 80)
            print(result["completion"])
            print("=" * 80)
            
            print(f"\nElapsed time: {result['elapsed_time']:.2f} seconds")
            print(f"Token count: {result['token_count']}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing with LLM: {e}")
            sys.exit(1)

def parse_key_value_pairs(pairs_str: str) -> Dict[str, str]:
    """Parse key=value pairs from a string.
    
    Args:
        pairs_str: String containing key=value pairs separated by commas.
        
    Returns:
        Dictionary of key-value pairs.
    """
    if not pairs_str:
        return {}
    
    result = {}
    pairs = pairs_str.split(",")
    
    for pair in pairs:
        if "=" not in pair:
            continue
        
        key, value = pair.split("=", 1)
        result[key.strip()] = value.strip()
    
    return result

def main():
    """Main entry point for the prompt manager CLI."""
    parser = argparse.ArgumentParser(description="Prompt Manager CLI for BlueAbel AIOS")
    parser.add_argument("--api", default=DEFAULT_API_URL, help="API endpoint URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List components
    list_parser = subparsers.add_parser("list", help="List all components")
    list_parser.add_argument("--tag", help="Filter components by tag")
    
    # View component
    view_parser = subparsers.add_parser("view", help="View a component")
    view_parser.add_argument("id", help="Component ID")
    
    # Create component
    create_parser = subparsers.add_parser("create", help="Create a new component")
    create_parser.add_argument("--name", required=True, help="Component name")
    create_parser.add_argument("--description", required=True, help="Component description")
    create_parser.add_argument("--template", required=True, help="Template text or file path")
    create_parser.add_argument("--tags", help="Comma-separated list of tags")
    
    # Edit component
    edit_parser = subparsers.add_parser("edit", help="Edit a component")
    edit_parser.add_argument("id", help="Component ID")
    
    # Edit template
    edit_template_parser = subparsers.add_parser("edit-template", help="Edit only the template of a component")
    edit_template_parser.add_argument("id", help="Component ID")
    
    # List versions
    versions_parser = subparsers.add_parser("versions", help="List all versions of a component")
    versions_parser.add_argument("id", help="Component ID")
    
    # View version
    view_version_parser = subparsers.add_parser("view-version", help="View a specific version of a component")
    view_version_parser.add_argument("id", help="Component ID")
    view_version_parser.add_argument("version", help="Version to view")
    
    # Compare versions
    compare_parser = subparsers.add_parser("compare", help="Compare two versions of a component")
    compare_parser.add_argument("id", help="Component ID")
    compare_parser.add_argument("version1", help="First version to compare")
    compare_parser.add_argument("version2", help="Second version to compare")
    
    # Restore version
    restore_parser = subparsers.add_parser("restore", help="Restore a component to a previous version")
    restore_parser.add_argument("id", help="Component ID")
    restore_parser.add_argument("version", help="Version to restore")
    
    # Test render
    test_render_parser = subparsers.add_parser("test-render", help="Test render a component")
    test_render_parser.add_argument("id", help="Component ID")
    test_render_parser.add_argument("--inputs", required=True, help="Comma-separated key=value pairs")
    
    # Test LLM
    test_llm_parser = subparsers.add_parser("test-llm", help="Test a component with an LLM")
    test_llm_parser.add_argument("id", help="Component ID")
    test_llm_parser.add_argument("--inputs", required=True, help="Comma-separated key=value pairs")
    test_llm_parser.add_argument("--provider", help="LLM provider to use")
    test_llm_parser.add_argument("--model", help="Model to use")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = PromptManager(api_url=args.api)
    
    if args.command == "list":
        manager.list_components(tag=args.tag)
    
    elif args.command == "view":
        manager.view_component(args.id)
    
    elif args.command == "create":
        tags = args.tags.split(",") if args.tags else []
        manager.create_component(args.name, args.description, args.template, tags)
    
    elif args.command == "edit":
        manager.edit_component(args.id)
    
    elif args.command == "edit-template":
        manager.edit_template(args.id)
    
    elif args.command == "versions":
        manager.list_versions(args.id)
    
    elif args.command == "view-version":
        manager.view_version(args.id, args.version)
    
    elif args.command == "compare":
        manager.compare_versions(args.id, args.version1, args.version2)
    
    elif args.command == "restore":
        manager.restore_version(args.id, args.version)
    
    elif args.command == "test-render":
        inputs = parse_key_value_pairs(args.inputs)
        manager.test_render(args.id, inputs)
    
    elif args.command == "test-llm":
        inputs = parse_key_value_pairs(args.inputs)
        manager.test_llm(args.id, inputs, provider=args.provider, model=args.model)

if __name__ == "__main__":
    main()