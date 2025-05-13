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
            # First get the current component information
            component_response = requests.get(f"{self.components_url}/{component_id}")
            component_response.raise_for_status()
            current = component_response.json()

            # Then get version history
            response = requests.get(f"{self.components_url}/{component_id}/versions")
            response.raise_for_status()
            versions = response.json()

            # Display component header information
            print(f"Component: {current['name']} ({current['id']})")
            print(f"Current version: {current['version']}")
            print(f"Description: {current['description']}")
            print()

            if not versions:
                print("No version history available.")
                return

            # Add history summary
            total_versions = len(versions)
            first_version_date = None
            latest_version_date = None

            if total_versions > 0:
                # Process timestamps
                for version in versions:
                    if version["snapshot_timestamp"]:
                        try:
                            dt = datetime.fromisoformat(version["snapshot_timestamp"])
                            version["formatted_date"] = dt.strftime("%Y-%m-%d %H:%M")
                            version["datetime"] = dt
                        except (ValueError, TypeError):
                            version["formatted_date"] = version["snapshot_timestamp"]
                            version["datetime"] = None
                    else:
                        version["formatted_date"] = "N/A"
                        version["datetime"] = None

                # Sort by datetime if available
                date_versions = [v for v in versions if v["datetime"] is not None]
                if date_versions:
                    date_versions.sort(key=lambda x: x["datetime"])
                    first_version_date = date_versions[0]["formatted_date"]
                    latest_version_date = date_versions[-1]["formatted_date"]

            # Print history summary
            print(f"Version History Summary:")
            print(f"  Total versions: {total_versions}")
            if first_version_date and latest_version_date:
                print(f"  First version: {first_version_date}")
                print(f"  Latest version: {latest_version_date}")
            print()

            # Print version table header
            print(f"{'VERSION':<10} | {'CREATED':<16} | {'CHANGES':<50}")
            print(f"{'-' * 10}-+-{'-' * 16}-+-{'-' * 50}")

            # Print versions with additional change information
            for i, version in enumerate(versions):
                # Get change description
                change_desc = "Initial version"
                if i < len(versions) - 1:
                    prev_version = versions[i+1]["version"]  # Assuming versions are sorted newest first
                    change_desc = f"Changes from {prev_version}"

                # Truncate change description if too long
                if len(change_desc) > 50:
                    change_desc = change_desc[:47] + "..."

                # Print version info
                print(f"{version['version']:<10} | {version.get('formatted_date', 'N/A'):<16} | {change_desc:<50}")

            # Print help text for comparing versions
            print("\nTo compare versions:")
            print(f"  prompt_manager.py compare {component_id} <version1> <version2>")
            print("To view a specific version:")
            print(f"  prompt_manager.py view-version {component_id} <version>")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing versions: {e}")

            # Provide helpful error message if component not found
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                print(f"Error: Component '{component_id}' not found")
                print("\nTip: Use the list command to see available components:")
                print("  prompt_manager.py list")
            else:
                print(f"Error: {str(e)}")

            sys.exit(1)
    
    def view_version(self, component_id: str, version: str) -> None:
        """View a specific version of a component.

        Args:
            component_id: ID of the component.
            version: Version to view.
        """
        try:
            # First get current component for comparison
            current_response = requests.get(f"{self.components_url}/{component_id}")
            current_response.raise_for_status()
            current = current_response.json()

            # Special handling for "current" version
            if version == "current":
                component = current
                display_version = current["version"] + " (current)"
            else:
                # Get the requested version
                response = requests.get(f"{self.components_url}/{component_id}/version/{version}")
                response.raise_for_status()
                component = response.json()

                # Check if this is the current version
                if component["version"] == current["version"]:
                    display_version = component["version"] + " (current)"
                else:
                    display_version = component["version"]

            # Format timestamp
            timestamp = component.get("snapshot_timestamp", component.get("updated_at", "Unknown"))
            try:
                formatted_time = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = timestamp

            # Print header
            print("=" * 80)
            print(f"COMPONENT VERSION: {component['name']} (Version {display_version})")
            print("=" * 80)

            # Print component details
            print(f"ID: {component['id']}")
            print(f"Created: {formatted_time}")

            # Print description with wrapping for long text
            if len(component['description']) > 80:
                print(f"Description:")
                print(textwrap.fill(component['description'], 70, initial_indent="  ", subsequent_indent="  "))
            else:
                print(f"Description: {component['description']}")

            # Print tags
            print(f"Tags: {', '.join(component['tags']) or 'None'}")

            # Print inputs
            print("\nINPUTS:")
            print("-" * 80)
            if component['required_inputs']:
                print("Required inputs:")
                for input_name in component['required_inputs']:
                    print(f"  - {input_name}")
            else:
                print("Required inputs: None")

            if component['optional_inputs']:
                print("\nOptional inputs:")
                for input_name in component['optional_inputs']:
                    print(f"  - {input_name}")
            else:
                print("\nOptional inputs: None")

            # Print template
            print("\nTEMPLATE:")
            print("=" * 80)
            print(component['template'])
            print("=" * 80)

            # Print additional version info
            other_versions = []
            try:
                versions_response = requests.get(f"{self.components_url}/{component_id}/versions")
                if versions_response.status_code == 200:
                    versions = versions_response.json()
                    for v in versions:
                        if v["version"] != component["version"]:
                            other_versions.append(v["version"])
            except:
                pass  # Ignore errors in getting other versions

            if other_versions:
                print("\nOther available versions:")
                print(", ".join(other_versions[:5]))
                if len(other_versions) > 5:
                    print(f"...and {len(other_versions) - 5} more")

            # Print suggestions
            print("\nCOMMANDS:")
            print("-" * 80)
            print(f"To compare with current version:")
            print(f"  prompt_manager.py compare {component_id} current {version}")
            print(f"To compare with another version:")
            print(f"  prompt_manager.py compare {component_id} <other_version> {version}")
            if version != "current" and display_version != current["version"] + " (current)":
                print(f"To restore to this version:")
                print(f"  prompt_manager.py restore {component_id} {version}")
            print(f"To test this component:")
            print(f"  prompt_manager.py test-render {component_id} --inputs key1=value1,key2=value2")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error viewing version: {e}")

            # Provide helpful error message if component or version not found
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    error_text = e.response.text.lower()
                    if "component" in error_text and "not found" in error_text:
                        print(f"Error: Component '{component_id}' not found")
                        print("\nTip: Use the list command to see available components:")
                        print("  prompt_manager.py list")
                    elif "version" in error_text and "not found" in error_text:
                        print(f"Error: Version '{version}' not found for component '{component_id}'")
                        print("\nTip: Use the versions command to see available versions:")
                        print(f"  prompt_manager.py versions {component_id}")
                else:
                    print(f"Error: {str(e)}")
            else:
                print(f"Error: {str(e)}")

            sys.exit(1)
    
    def compare_versions(self, component_id: str, version1: str, version2: str) -> None:
        """Compare two versions of a component.

        Args:
            component_id: ID of the component.
            version1: First version to compare.
            version2: Second version to compare.
        """
        try:
            # First get current component to make sure it exists
            response = requests.get(f"{self.components_url}/{component_id}")
            response.raise_for_status()
            current = response.json()

            # Special case for comparing with current version
            if version1 == "current":
                component1 = current
                version1_display = current["version"] + " (current)"
            else:
                version1_display = version1
                # Get version 1
                try:
                    response1 = requests.get(f"{self.components_url}/{component_id}/version/{version1}")
                    response1.raise_for_status()
                    component1 = response1.json()
                except requests.exceptions.RequestException as e:
                    if e.response and e.response.status_code == 404:
                        # If version1 is not found in version history but matches current version
                        if current["version"] == version1:
                            component1 = current
                            version1_display += " (current)"
                        else:
                            print(f"Error: Version {version1} not found in version history.")
                            print("\nAvailable versions:")
                            self.list_versions(component_id)
                            return
                    else:
                        raise

            # Special case for comparing with current version
            if version2 == "current":
                component2 = current
                version2_display = current["version"] + " (current)"
            else:
                version2_display = version2
                # Get version 2
                try:
                    response2 = requests.get(f"{self.components_url}/{component_id}/version/{version2}")
                    response2.raise_for_status()
                    component2 = response2.json()
                except requests.exceptions.RequestException as e:
                    if e.response and e.response.status_code == 404:
                        # If version2 is not found in version history but matches current version
                        if current["version"] == version2:
                            component2 = current
                            version2_display += " (current)"
                        else:
                            print(f"Error: Version {version2} not found in version history.")
                            print("\nAvailable versions:")
                            self.list_versions(component_id)
                            return
                    else:
                        raise

            # Get version timestamps
            version1_time = component1.get("snapshot_timestamp", component1.get("updated_at", "Unknown"))
            version2_time = component2.get("snapshot_timestamp", component2.get("updated_at", "Unknown"))

            # Format timestamps if possible
            try:
                version1_time = datetime.fromisoformat(version1_time).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

            try:
                version2_time = datetime.fromisoformat(version2_time).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

            # Print header with detailed information
            print(f"COMPONENT COMPARISON: {component1['name']} ({component_id})")
            print(f"Comparing version {version1_display} with {version2_display}")
            print(f"Version {version1_display} created: {version1_time}")
            print(f"Version {version2_display} created: {version2_time}")
            print("\n" + "-" * 80)

            # Compare templates with improved diff handling
            template1 = component1["template"].splitlines()
            template2 = component2["template"].splitlines()

            diff = difflib.unified_diff(
                template2,
                template1,
                fromfile=f"Version {version2_display}",
                tofile=f"Version {version1_display}",
                lineterm=""
            )

            print("\nTEMPLATE CHANGES:")
            print("=" * 80)
            diff_lines = list(diff)
            if not diff_lines:
                print("No changes in template.")
            else:
                # Count the changes for summary
                additions = 0
                deletions = 0
                for line in diff_lines:
                    if line.startswith("+") and not line.startswith("+++"):
                        additions += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deletions += 1

                # Print change summary
                print(f"Template changes: {additions} additions, {deletions} deletions")

                # Print the diff
                for line in diff_lines:
                    if line.startswith("+"):
                        print(f"\033[92m{line}\033[0m")  # Green for additions
                    elif line.startswith("-"):
                        print(f"\033[91m{line}\033[0m")  # Red for deletions
                    else:
                        print(line)
            print("=" * 80)

            # Compare metadata with improved formatting
            print("\nMETADATA CHANGES:")
            print("-" * 80)

            has_metadata_changes = False

            # Compare name
            if component1["name"] != component2["name"]:
                has_metadata_changes = True
                print(f"Name:")
                print(f"  - {version2_display}: {component2['name']}")
                print(f"  + {version1_display}: {component1['name']}")
                print()

            # Compare description
            if component1["description"] != component2["description"]:
                has_metadata_changes = True
                print(f"Description:")
                if len(component2["description"]) > 80 or len(component1["description"]) > 80:
                    # For long descriptions, show them on separate lines
                    print(f"  - {version2_display}:")
                    print(f"    {textwrap.fill(component2['description'], 70)}")
                    print(f"  + {version1_display}:")
                    print(f"    {textwrap.fill(component1['description'], 70)}")
                else:
                    # For short descriptions, show inline
                    print(f"  - {version2_display}: {component2['description']}")
                    print(f"  + {version1_display}: {component1['description']}")
                print()

            # Compare tags
            if component1["tags"] != component2["tags"]:
                has_metadata_changes = True
                added_tags = [t for t in component1["tags"] if t not in component2["tags"]]
                removed_tags = [t for t in component2["tags"] if t not in component1["tags"]]

                print(f"Tags:")
                if removed_tags:
                    print(f"  - Removed: {', '.join(removed_tags)}")
                if added_tags:
                    print(f"  + Added: {', '.join(added_tags)}")
                if not added_tags and not removed_tags:
                    print(f"  - {version2_display}: {', '.join(component2['tags'])}")
                    print(f"  + {version1_display}: {', '.join(component1['tags'])}")
                print()

            # Compare required inputs
            if component1["required_inputs"] != component2["required_inputs"]:
                has_metadata_changes = True
                added_inputs = [i for i in component1["required_inputs"] if i not in component2["required_inputs"]]
                removed_inputs = [i for i in component2["required_inputs"] if i not in component1["required_inputs"]]

                print(f"Required inputs:")
                if removed_inputs:
                    print(f"  - Removed: {', '.join(removed_inputs)}")
                if added_inputs:
                    print(f"  + Added: {', '.join(added_inputs)}")
                if not added_inputs and not removed_inputs:
                    print(f"  - {version2_display}: {', '.join(component2['required_inputs']) or 'None'}")
                    print(f"  + {version1_display}: {', '.join(component1['required_inputs']) or 'None'}")
                print()

            # Compare optional inputs
            if component1["optional_inputs"] != component2["optional_inputs"]:
                has_metadata_changes = True
                added_inputs = [i for i in component1["optional_inputs"] if i not in component2["optional_inputs"]]
                removed_inputs = [i for i in component2["optional_inputs"] if i not in component1["optional_inputs"]]

                print(f"Optional inputs:")
                if removed_inputs:
                    print(f"  - Removed: {', '.join(removed_inputs)}")
                if added_inputs:
                    print(f"  + Added: {', '.join(added_inputs)}")
                if not added_inputs and not removed_inputs:
                    print(f"  - {version2_display}: {', '.join(component2['optional_inputs']) or 'None'}")
                    print(f"  + {version1_display}: {', '.join(component1['optional_inputs']) or 'None'}")
                print()

            if not has_metadata_changes:
                print("No changes in metadata.")

            # Print suggestions
            print("\nSUGGESTIONS:")
            print("-" * 80)
            print(f"To restore to version {version2}:")
            print(f"  prompt_manager.py restore {component_id} {version2}")
            print()
            print(f"To view complete version details:")
            print(f"  prompt_manager.py view-version {component_id} {version1}")
            print(f"  prompt_manager.py view-version {component_id} {version2}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error comparing versions: {e}")

            # Provide helpful error message if component not found
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                print(f"Error: Component '{component_id}' not found")
                print("\nTip: Use the list command to see available components:")
                print("  prompt_manager.py list")
            else:
                print(f"Error: {str(e)}")

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

            # Check if the version to restore is already the current version
            if old_version["version"] == current["version"] and old_version["template"] == current["template"]:
                print(f"Component {component_id} is already at version {version}")
                print("No restoration needed.")
                return

            # Calculate timestamp differences
            current_time = None
            old_time = None

            try:
                if "updated_at" in current:
                    current_time = datetime.fromisoformat(current["updated_at"])
                elif "snapshot_timestamp" in current:
                    current_time = datetime.fromisoformat(current["snapshot_timestamp"])

                if "snapshot_timestamp" in old_version:
                    old_time = datetime.fromisoformat(old_version["snapshot_timestamp"])
                elif "updated_at" in old_version:
                    old_time = datetime.fromisoformat(old_version["updated_at"])

                if current_time and old_time:
                    time_diff = current_time - old_time
                    days = time_diff.days
                    hours, remainder = divmod(time_diff.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)

                    time_diff_str = ""
                    if days > 0:
                        time_diff_str += f"{days} days, "
                    if hours > 0 or days > 0:
                        time_diff_str += f"{hours} hours, "
                    time_diff_str += f"{minutes} minutes"

                    # Print time difference warning for old versions
                    if time_diff.days > 30:
                        print(f"WARNING: You are restoring a version that is {time_diff_str} old!")
                    elif time_diff.days > 7:
                        print(f"Note: You are restoring a version that is {time_diff_str} old.")
            except (ValueError, TypeError, KeyError):
                # If any error occurs during time calculation, just skip it
                pass

            # Print restoration header
            print(f"RESTORING COMPONENT: {current['name']} ({component_id})")
            print(f"From version: {current['version']} (current)")
            print(f"To version: {version}")
            print("\n" + "-" * 80)

            # Show template diff
            print("\nTEMPLATE CHANGES:")
            print("=" * 80)

            # Compare templates with improved diff handling
            template1 = old_version["template"].splitlines()
            template2 = current["template"].splitlines()

            diff = difflib.unified_diff(
                template2,
                template1,
                fromfile=f"Current ({current['version']})",
                tofile=f"Version {version}",
                lineterm=""
            )

            diff_lines = list(diff)
            if not diff_lines:
                print("No changes in template.")
            else:
                # Count the changes for summary
                additions = 0
                deletions = 0
                for line in diff_lines:
                    if line.startswith("+") and not line.startswith("+++"):
                        additions += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deletions += 1

                # Print change summary
                print(f"Template changes: {additions} additions, {deletions} deletions")

                # Print the diff
                for line in diff_lines:
                    if line.startswith("+"):
                        print(f"\033[92m{line}\033[0m")  # Green for additions
                    elif line.startswith("-"):
                        print(f"\033[91m{line}\033[0m")  # Red for deletions
                    else:
                        print(line)
            print("=" * 80)

            # Show metadata changes
            print("\nMETADATA CHANGES:")
            print("-" * 80)

            has_metadata_changes = False

            # Compare name
            if old_version["name"] != current["name"]:
                has_metadata_changes = True
                print(f"Name: {current['name']} -> {old_version['name']}")

            # Compare description
            if old_version["description"] != current["description"]:
                has_metadata_changes = True
                if len(old_version['description']) > 80 or len(current['description']) > 80:
                    print(f"Description changing from:")
                    print(f"  Current: {textwrap.fill(current['description'], 70, initial_indent='    ', subsequent_indent='    ')}")
                    print(f"  To: {textwrap.fill(old_version['description'], 70, initial_indent='    ', subsequent_indent='    ')}")
                else:
                    print(f"Description: {current['description']} -> {old_version['description']}")

            # Compare tags
            if old_version["tags"] != current["tags"]:
                has_metadata_changes = True
                added_tags = [t for t in old_version["tags"] if t not in current["tags"]]
                removed_tags = [t for t in current["tags"] if t not in old_version["tags"]]

                if added_tags:
                    print(f"Tags added: {', '.join(added_tags)}")
                if removed_tags:
                    print(f"Tags removed: {', '.join(removed_tags)}")
                if not added_tags and not removed_tags:
                    print(f"Tags: {', '.join(current['tags'])} -> {', '.join(old_version['tags'])}")

            # Compare inputs
            if old_version["required_inputs"] != current["required_inputs"]:
                has_metadata_changes = True
                added_inputs = [i for i in old_version["required_inputs"] if i not in current["required_inputs"]]
                removed_inputs = [i for i in current["required_inputs"] if i not in old_version["required_inputs"]]

                if added_inputs:
                    print(f"Required inputs added: {', '.join(added_inputs)}")
                if removed_inputs:
                    print(f"Required inputs removed: {', '.join(removed_inputs)}")
                if not added_inputs and not removed_inputs:
                    print(f"Required inputs: {', '.join(current['required_inputs'])} -> {', '.join(old_version['required_inputs'])}")

            if old_version["optional_inputs"] != current["optional_inputs"]:
                has_metadata_changes = True
                added_inputs = [i for i in old_version["optional_inputs"] if i not in current["optional_inputs"]]
                removed_inputs = [i for i in current["optional_inputs"] if i not in old_version["optional_inputs"]]

                if added_inputs:
                    print(f"Optional inputs added: {', '.join(added_inputs)}")
                if removed_inputs:
                    print(f"Optional inputs removed: {', '.join(removed_inputs)}")
                if not added_inputs and not removed_inputs:
                    print(f"Optional inputs: {', '.join(current['optional_inputs'])} -> {', '.join(old_version['optional_inputs'])}")

            if not has_metadata_changes:
                print("No changes in metadata.")

            # Important notes
            if additions > 10 or deletions > 10:
                print("\nIMPORTANT NOTE: This restoration will make significant changes to the template.")
                print("Consider testing the restored version before using it in production.")

            # Confirm restore with more details
            version_info = f"version {version}"
            if "snapshot_timestamp" in old_version:
                try:
                    timestamp = datetime.fromisoformat(old_version["snapshot_timestamp"]).strftime("%Y-%m-%d")
                    version_info += f" from {timestamp}"
                except:
                    pass

            confirm = input(f"\nRestore to {version_info}? [y/N] ").lower()
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

            print(f"\nSuccess! Component restored to content from version {version}")
            print(f"Created as new version: {updated['version']}")
            print(f"\nTo test this version:")
            print(f"  prompt_manager.py test-render {component_id} --inputs key1=value1,key2=value2")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error restoring version: {e}")

            # Provide helpful error message if component or version not found
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    error_text = e.response.text.lower()
                    if "component" in error_text and "not found" in error_text:
                        print(f"Error: Component '{component_id}' not found")
                        print("\nTip: Use the list command to see available components:")
                        print("  prompt_manager.py list")
                    elif "version" in error_text and "not found" in error_text:
                        print(f"Error: Version '{version}' not found for component '{component_id}'")
                        print("\nTip: Use the versions command to see available versions:")
                        print(f"  prompt_manager.py versions {component_id}")
                else:
                    print(f"Error: {str(e)}")
            else:
                print(f"Error: {str(e)}")

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

            # Make sure the API call was successful
            if isinstance(result, dict) and "status" in result and result["status"] == "error":
                print(f"Error: {result.get('message', 'Unknown API error')}")

                # Provide helpful advice if it's a common error
                error_message = result.get('message', '').lower()
                if "component not found" in error_message:
                    print("\nTip: Use the 'list' command to see available components:")
                    print("  prompt_manager.py list")
                elif "missing" in error_message and "input" in error_message:
                    print("\nTip: View the component to see its required inputs:")
                    print(f"  prompt_manager.py view {component_id}")

                return

            print("Rendered template:")
            print("=" * 80)
            print(result.get("result", "No result returned"))
            print("=" * 80)

            # Check for errors first
            if "error" in result and result["error"]:
                print(f"\nError: {result['error']}")

                # Check for detailed missing inputs in metrics
                metrics = result.get("metrics", {})
                if "missing_inputs" in metrics and metrics["missing_inputs"]:
                    missing_inputs = metrics["missing_inputs"]
                    print("\nMissing Required Inputs:")
                    for input_name in missing_inputs:
                        print(f"- {input_name}")
                    print("\nTip: Provide these inputs using --inputs key1=value1,key2=value2")

            # Report any warnings
            metrics = result.get("metrics", {})
            if "warnings" in metrics and metrics["warnings"]:
                print("\nWarnings:")
                for warning in metrics["warnings"]:
                    print(f"- {warning}")

            # Report unused inputs
            if "unused_inputs" in metrics and metrics["unused_inputs"]:
                print("\nUnused inputs:")
                for input_name in metrics["unused_inputs"]:
                    print(f"- {input_name}")

            # Display metrics if available
            metrics = result.get("metrics", {})
            if metrics:
                print("\nMetrics:")
                for key, value in metrics.items():
                    print(f"- {key}: {value}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing component: {e}")

            # Provide more helpful error messages for common issues
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 404:
                    print(f"Error: Component '{component_id}' not found")
                elif status_code == 400:
                    try:
                        error_json = e.response.json()
                        print(f"Error: {error_json.get('detail', str(e))}")
                    except:
                        print(f"Error: {str(e)}")
                else:
                    print(f"Error: {str(e)}")
            else:
                print(f"Error connecting to API: {str(e)}")

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

            # Make sure the API call was successful
            if isinstance(result, dict) and "status" in result and result["status"] == "error":
                print(f"Error: {result.get('message', 'Unknown API error')}")

                # Provide helpful advice if it's a common error
                error_message = result.get('message', '').lower()
                if "component not found" in error_message:
                    print("\nTip: Use the 'list' command to see available components:")
                    print("  prompt_manager.py list")
                elif "missing" in error_message and "input" in error_message:
                    print("\nTip: View the component to see its required inputs:")
                    print(f"  prompt_manager.py view {component_id}")

                return

            # Check for errors first
            if "error" in result and result["error"]:
                print(f"\nError: {result['error']}")

                # Check for missing inputs in metrics or error message
                metrics = result.get("metrics", {})
                if "missing_inputs" in metrics and metrics["missing_inputs"]:
                    missing_inputs = metrics["missing_inputs"]
                    print("\nMissing Required Inputs:")
                    for input_name in missing_inputs:
                        print(f"- {input_name}")
                    print("\nTip: Provide these inputs using --inputs key1=value1,key2=value2")
                else:
                    # Try to extract missing inputs from error message
                    error_message = result["error"].lower()
                    if "missing" in error_message and "input" in error_message:
                        print("\nTip: View the component to see its required inputs:")
                        print(f"  prompt_manager.py view {component_id}")

                # Suggest provider/model options if that's the issue
                if "provider" in error_message or "model" in error_message:
                    print("\nTip: Specify a provider or model using:")
                    print("  --provider openai --model gpt-3.5-turbo")
                    print("  or")
                    print("  --provider anthropic --model claude-3-opus-20240229")

                return

            # Get provider and model info from metrics
            metrics = result.get("metrics", {})
            provider = metrics.get("provider", result.get("provider", "unknown"))
            model = metrics.get("model", result.get("model", "unknown"))

            print(f"\nLLM response ({provider}/{model}):")
            print("=" * 80)
            print(result.get("result", "No result returned"))
            print("=" * 80)

            # Calculate and display elapsed time
            llm_time = metrics.get("llm_time_ms", 0) / 1000  # Convert to seconds
            render_time = metrics.get("render_time_ms", 0) / 1000  # Convert to seconds
            total_time = llm_time + render_time

            print(f"\nElapsed time: {total_time:.2f} seconds")

            # Get token information from metrics
            tokens = metrics.get("tokens", {})
            if tokens:
                if isinstance(tokens, dict):
                    for token_type, count in tokens.items():
                        print(f"{token_type.capitalize()} tokens: {count}")
                else:
                    print(f"Token count: {tokens}")

            # Display other metrics if available
            for key, value in metrics.items():
                if key not in ["provider", "model", "llm_time_ms", "render_time_ms", "tokens"]:
                    print(f"{key}: {value}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error testing with LLM: {e}")

            # Provide more helpful error messages for common issues
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                if status_code == 404:
                    print(f"Error: Component '{component_id}' not found")
                elif status_code == 503:
                    print("Error: LLM service is unavailable. Check if the model is running and accessible.")
                elif status_code == 400:
                    try:
                        error_json = e.response.json()
                        print(f"Error: {error_json.get('detail', str(e))}")
                    except:
                        print(f"Error: {str(e)}")
                else:
                    print(f"Error: {str(e)}")
            else:
                print(f"Error connecting to API: {str(e)}")

            sys.exit(1)

    def analyze_template(self, template: str) -> None:
        """Analyze a template for quality and provide improvement suggestions.

        Args:
            template: The template to analyze, either text or a file path.
        """
        # If template is a file path, read the template from the file
        if os.path.exists(template):
            try:
                with open(template, 'r') as f:
                    template = f.read()
                print(f"Analyzing template from file: {template}")
            except Exception as e:
                logger.error(f"Error reading template file: {e}")
                print(f"Error: Could not read template file: {str(e)}")
                sys.exit(1)

        try:
            # Send template for analysis
            response = requests.post(
                f"{self.api_url}/components/analyze-template",
                json={"template": template}
            )
            response.raise_for_status()
            analysis = response.json()

            # Print analysis results
            print("TEMPLATE ANALYSIS RESULTS")
            print("=" * 80)

            # Print basic metrics
            if "metrics" in analysis:
                metrics = analysis["metrics"]
                if "overall_quality" in metrics:
                    quality = metrics["overall_quality"] * 100
                    print(f"Overall Quality: {quality:.1f}%")

                    # Quality assessment
                    if quality < 50:
                        print("Assessment: Needs significant improvement")
                    elif quality < 70:
                        print("Assessment: Could be improved")
                    elif quality < 90:
                        print("Assessment: Good quality")
                    else:
                        print("Assessment: Excellent quality")

                if "complexity" in metrics:
                    complexity = metrics["complexity"]
                    print(f"\nComplexity Metrics:")
                    print(f"- Word count: {complexity.get('word_count', 'N/A')}")
                    print(f"- Readability score: {complexity.get('readability_score', 'N/A'):.1f}/100")

                    # List repeated words if any
                    repeated = complexity.get("repeated_words", {})
                    if repeated:
                        print("\nRepeated words:")
                        for word, count in list(repeated.items())[:5]:  # Show top 5
                            print(f"- '{word}' appears {count} times")

            # Print structure analysis
            if "structure_analysis" in analysis:
                structure = analysis["structure_analysis"]
                print("\nStructure Assessment:")

                components = [
                    ("Role definition", structure.get("has_role_definition", False)),
                    ("Task specification", structure.get("has_task_specification", False)),
                    ("Context section", structure.get("has_context_section", False)),
                    ("Output format", structure.get("has_output_format", False)),
                    ("Examples", structure.get("has_examples", False))
                ]

                for component, present in components:
                    status = "✓" if present else "✗"
                    print(f"- {component}: {status}")

                # Show identified sections
                if "identified_sections" in structure:
                    sections = structure["identified_sections"]
                    if sections:
                        print("\nIdentified sections:")
                        for section in sections:
                            print(f"- {section.replace('_', ' ').title()}")

            # Print suggestions
            if "suggestions" in analysis and analysis["suggestions"]:
                print("\nImprovement Suggestions:")
                for i, suggestion in enumerate(analysis["suggestions"], 1):
                    print(f"{i}. {suggestion}")

            # Print warnings
            if "warnings" in analysis and analysis["warnings"]:
                print("\nWarnings:")
                for warning in analysis["warnings"]:
                    print(f"- {warning}")

            # Print errors
            if "errors" in analysis and analysis["errors"]:
                print("\nErrors:")
                for error in analysis["errors"]:
                    print(f"- {error}")

            # Get template examples based on improvement areas
            if "improvement_areas" in analysis and analysis["improvement_areas"]:
                print("\nSuggested Templates:")
                print("For examples of well-structured templates, use:")
                print("  prompt_manager.py template-examples [task_type]")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing template: {e}")
            print(f"Error: Could not analyze template: {str(e)}")
            sys.exit(1)

    def get_template_examples(self, task_type: Optional[str] = None) -> None:
        """Get examples of well-structured templates.

        Args:
            task_type: Optional task type to get specific examples for.
        """
        try:
            url = f"{self.api_url}/components/template-examples"
            if task_type:
                url += f"?task_type={task_type}"

            response = requests.get(url)
            response.raise_for_status()
            examples = response.json()

            if not examples:
                print("No template examples found.")
                return

            if task_type and task_type in examples:
                # Show specific example
                print(f"TEMPLATE EXAMPLE: {task_type.title()}")
                print("=" * 80)
                print(examples[task_type])
                print("=" * 80)
            else:
                # Show available task types
                print("AVAILABLE TEMPLATE EXAMPLES")
                print("=" * 80)
                print("Available task types:")
                for task in examples.keys():
                    print(f"- {task}")
                print("\nTo view a specific example, use:")
                print("  prompt_manager.py template-examples <task_type>")

                # If there are few examples, show the first one
                if len(examples) == 1:
                    task = next(iter(examples.keys()))
                    print(f"\nExample for {task}:")
                    print("-" * 80)
                    print(examples[task])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting template examples: {e}")
            print(f"Error: Could not get template examples: {str(e)}")
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

    # Analyze template
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a template for quality and get improvement suggestions")
    analyze_parser.add_argument("template", help="Template text or file path to analyze")

    # Get template examples
    examples_parser = subparsers.add_parser("template-examples", help="Get examples of well-structured templates")
    examples_parser.add_argument("task_type", nargs="?", help="Optional specific task type to get examples for")
    
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

    elif args.command == "analyze":
        manager.analyze_template(args.template)

    elif args.command == "template-examples":
        manager.get_template_examples(args.task_type)

if __name__ == "__main__":
    main()