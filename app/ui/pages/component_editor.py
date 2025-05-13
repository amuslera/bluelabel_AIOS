"""
Streamlit page for editing MCP components.

This module provides a Streamlit UI for creating, editing, and testing
MCP components.
"""

import streamlit as st
import json
import requests
from typing import Dict, Any, List, Optional
import time

# API endpoint
API_ENDPOINT = "http://localhost:8081"  # Update as needed

def component_editor_page():
    """Render the component editor page."""
    st.title("Component Editor")
    
    # Initialize session state
    if 'component_id' not in st.session_state:
        st.session_state.component_id = None
    if 'component_version' not in st.session_state:
        st.session_state.component_version = None
    if 'test_inputs' not in st.session_state:
        st.session_state.test_inputs = {}
    if 'test_result' not in st.session_state:
        st.session_state.test_result = None
    
    # Create tabs for different sections
    editor_tab, test_tab, history_tab = st.tabs(["Editor", "Test", "History"])
    
    with editor_tab:
        render_editor_tab()
    
    with test_tab:
        render_test_tab()
    
    with history_tab:
        render_history_tab()

def render_editor_tab():
    """Render the component editor tab."""
    # Component selector
    st.subheader("Select Component")
    
    # Fetch components from API
    components = fetch_components()
    component_names = ["Create New Component"] + [f"{c['name']} ({c['id']})" for c in components]
    
    selected_index = 0
    if st.session_state.component_id:
        # Find the index of the currently selected component
        for i, name in enumerate(component_names):
            if f"({st.session_state.component_id})" in name:
                selected_index = i
                break
    
    selected_component = st.selectbox(
        "Component",
        component_names,
        index=selected_index
    )
    
    # Handle component selection
    if selected_component == "Create New Component":
        render_new_component_form()
    else:
        # Extract component ID from the selected option
        component_id = selected_component.split("(")[-1].rstrip(")")
        if component_id != st.session_state.component_id:
            st.session_state.component_id = component_id
            st.session_state.component_version = None  # Reset version when changing component
        
        # Show the component editor
        render_component_editor(component_id)

def render_new_component_form():
    """Render the form for creating a new component."""
    st.subheader("Create New Component")
    
    with st.form("new_component_form"):
        name = st.text_input("Name", placeholder="Component name")
        description = st.text_area("Description", placeholder="Component description")
        template = st.text_area("Template", placeholder="Template with {placeholders}", height=300)
        tags = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2, tag3")
        
        # Submit button
        submitted = st.form_submit_button("Create Component")
        
        if submitted:
            if not name:
                st.error("Component name is required")
                return
            
            if not template:
                st.error("Template is required")
                return
            
            # Parse tags
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            
            # Create component
            try:
                response = requests.post(
                    f"{API_ENDPOINT}/components/",
                    json={
                        "name": name,
                        "description": description,
                        "template": template,
                        "tags": tag_list,
                        "metadata": {}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Component created: {result['id']}")
                    
                    # Update session state
                    st.session_state.component_id = result['id']
                    st.experimental_rerun()
                else:
                    st.error(f"Error creating component: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def render_component_editor(component_id: str):
    """Render the editor for an existing component.
    
    Args:
        component_id: ID of the component to edit.
    """
    # Fetch component details
    component = fetch_component(component_id)
    if not component:
        st.error(f"Component {component_id} not found")
        return
    
    st.subheader(f"Edit Component: {component['name']}")
    
    # Display component metadata
    col1, col2 = st.columns(2)
    with col1:
        st.text(f"ID: {component['id']}")
        st.text(f"Version: {component['version']}")
    with col2:
        st.text(f"Created: {component['created_at']}")
        st.text(f"Updated: {component['updated_at']}")
    
    # Create a form for editing the component
    with st.form("edit_component_form"):
        name = st.text_input("Name", value=component['name'])
        description = st.text_area("Description", value=component['description'])
        
        # Template editor with syntax highlighting
        st.markdown("### Template")
        template = st.text_area(
            "Edit template with {placeholders}",
            value=component['template'],
            height=300,
            key="template_editor",
            help="Use {variable} for required inputs and {variable:optional} for optional inputs"
        )
        
        # Tags
        tags = st.text_input(
            "Tags (comma-separated)",
            value=", ".join(component.get('tags', []))
        )
        
        # Metadata as JSON
        st.markdown("### Metadata (JSON)")
        metadata_str = json.dumps(component.get('metadata', {}), indent=2)
        metadata_json = st.text_area("Metadata", value=metadata_str, height=150)
        
        # Version increment option
        increment_version = st.checkbox("Increment version", value=True)
        
        # Submit button
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("Update Component")
        with col2:
            validate_button = st.form_submit_button("Validate Only")
        
        if validate_button or submitted:
            # Parse metadata JSON
            try:
                metadata = json.loads(metadata_json)
            except json.JSONDecodeError as e:
                st.error(f"Invalid metadata JSON: {str(e)}")
                return
            
            # Parse tags
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            
            # Validate component
            validation = validate_component(component_id, template)
            
            # Display validation results
            if validation.get("is_valid", False):
                st.success("Template is valid")
            else:
                st.error("Template validation failed")
            
            if validation.get("errors", []):
                st.error("Errors:")
                for error in validation["errors"]:
                    st.write(f"- {error}")
            
            if validation.get("warnings", []):
                st.warning("Warnings:")
                for warning in validation["warnings"]:
                    st.write(f"- {warning}")
            
            # Update component if submitted and valid
            if submitted and validation.get("is_valid", False):
                try:
                    response = requests.put(
                        f"{API_ENDPOINT}/components/{component_id}",
                        json={
                            "name": name,
                            "description": description,
                            "template": template,
                            "tags": tag_list,
                            "metadata": metadata,
                            "increment_version": increment_version
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Component updated to version {result['version']}")
                        
                        # Refresh component in session state
                        st.experimental_rerun()
                    else:
                        st.error(f"Error updating component: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Actions outside the form
    st.subheader("Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Duplicate Component"):
            new_name = component['name'] + " (Copy)"
            try:
                response = requests.post(
                    f"{API_ENDPOINT}/components/duplicate/{component_id}",
                    params={"new_name": new_name}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Component duplicated: {result['id']}")
                    
                    # Update session state
                    st.session_state.component_id = result['id']
                    st.experimental_rerun()
                else:
                    st.error(f"Error duplicating component: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("Export Component"):
            try:
                response = requests.get(f"{API_ENDPOINT}/components/{component_id}/export")
                
                if response.status_code == 200:
                    result = response.json()
                    # Create a download button
                    st.download_button(
                        label="Download JSON",
                        data=json.dumps(result, indent=2),
                        file_name=f"component_{component_id}.json",
                        mime="application/json"
                    )
                else:
                    st.error(f"Error exporting component: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("Delete Component", type="primary", key="delete_button"):
            st.session_state.show_delete_confirmation = True
        
        if st.session_state.get("show_delete_confirmation", False):
            st.warning("Are you sure you want to delete this component? This action cannot be undone.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel"):
                    st.session_state.show_delete_confirmation = False
            with col2:
                if st.button("Confirm Delete"):
                    try:
                        response = requests.delete(f"{API_ENDPOINT}/components/{component_id}")
                        
                        if response.status_code == 200:
                            st.success("Component deleted")
                            
                            # Reset session state
                            st.session_state.component_id = None
                            st.session_state.component_version = None
                            st.session_state.show_delete_confirmation = False
                            st.experimental_rerun()
                        else:
                            st.error(f"Error deleting component: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

def render_test_tab():
    """Render the component testing tab."""
    st.subheader("Test Component")
    
    if not st.session_state.component_id:
        st.info("Select a component to test")
        return
    
    # Fetch component details
    component = fetch_component(st.session_state.component_id)
    if not component:
        st.error(f"Component {st.session_state.component_id} not found")
        return
    
    st.write(f"Testing: **{component['name']}** (version {component['version']})")
    
    # Get required and optional inputs
    required_inputs = component.get('required_inputs', [])
    optional_inputs = component.get('optional_inputs', [])
    
    # Initialize test inputs if needed
    if not st.session_state.test_inputs:
        st.session_state.test_inputs = {input_name: "" for input_name in required_inputs}
        for input_name in optional_inputs:
            st.session_state.test_inputs[input_name] = ""
    
    # Add any new inputs that weren't previously in the session state
    for input_name in required_inputs + optional_inputs:
        if input_name not in st.session_state.test_inputs:
            st.session_state.test_inputs[input_name] = ""
    
    # Test input form
    with st.form("test_input_form"):
        st.markdown("### Inputs")
        
        # Required inputs
        if required_inputs:
            st.markdown("**Required Inputs:**")
            for input_name in required_inputs:
                st.session_state.test_inputs[input_name] = st.text_area(
                    f"{input_name}",
                    value=st.session_state.test_inputs.get(input_name, ""),
                    height=100 if len(st.session_state.test_inputs.get(input_name, "")) > 50 else 70
                )
        
        # Optional inputs
        if optional_inputs:
            st.markdown("**Optional Inputs:**")
            for input_name in optional_inputs:
                st.session_state.test_inputs[input_name] = st.text_area(
                    f"{input_name} (optional)",
                    value=st.session_state.test_inputs.get(input_name, ""),
                    height=100 if len(st.session_state.test_inputs.get(input_name, "")) > 50 else 70
                )
        
        # Test options
        st.markdown("### Test Options")
        
        col1, col2 = st.columns(2)
        with col1:
            test_type = st.radio(
                "Test Type",
                ["Template Only", "With LLM"],
                index=0
            )
        
        llm_options = {}
        if test_type == "With LLM":
            with col2:
                task_type = st.selectbox(
                    "Task Type",
                    ["completion", "summarize", "extract_entities", "tag_content"],
                    index=0
                )
            
            col1, col2 = st.columns(2)
            with col1:
                provider = st.selectbox(
                    "Provider",
                    ["Auto", "anthropic", "openai", "local"],
                    index=0
                )
            with col2:
                if provider == "anthropic":
                    model = st.selectbox(
                        "Model",
                        ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                        index=1
                    )
                elif provider == "openai":
                    model = st.selectbox(
                        "Model",
                        ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                        index=2
                    )
                elif provider == "local":
                    model = st.text_input("Model", value="llama3")
                else:
                    model = None
            
            # Temperature
            temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
            
            # Set LLM options
            llm_options = {
                "task_type": task_type,
                "provider": None if provider == "Auto" else provider,
                "model": model,
                "parameters": {
                    "temperature": temperature
                }
            }
        
        # Submit buttons
        test_render = st.form_submit_button("Test")
        
        if test_render:
            # Remove empty optional inputs
            test_inputs = {k: v for k, v in st.session_state.test_inputs.items() if v or k in required_inputs}
            
            # Test the component
            if test_type == "Template Only":
                test_render_only(st.session_state.component_id, test_inputs)
            else:
                test_with_llm(st.session_state.component_id, test_inputs, llm_options)
    
    # Display test results
    if st.session_state.get("test_result"):
        st.subheader("Test Results")
        
        result = st.session_state.test_result
        
        # Display metrics
        if "metrics" in result:
            st.markdown("**Metrics:**")
            metrics = result["metrics"]
            
            # Create a better metrics display
            cols = st.columns(3)
            
            with cols[0]:
                if "render_time_ms" in metrics:
                    st.metric("Render Time", f"{metrics['render_time_ms']:.2f} ms")
            
            with cols[1]:
                if "llm_time_ms" in metrics:
                    st.metric("LLM Time", f"{metrics['llm_time_ms'] / 1000:.2f} s")
            
            with cols[2]:
                if "provider" in metrics:
                    st.metric("Provider", metrics["provider"])
            
            # If tokens info is available
            if "tokens" in metrics:
                tokens = metrics["tokens"]
                st.markdown("**Token Usage:**")
                token_cols = st.columns(3)
                
                with token_cols[0]:
                    if "input" in tokens:
                        st.metric("Input Tokens", tokens["input"])
                
                with token_cols[1]:
                    if "output" in tokens:
                        st.metric("Output Tokens", tokens["output"])
                
                with token_cols[2]:
                    if "input" in tokens and "output" in tokens:
                        st.metric("Total Tokens", tokens["input"] + tokens["output"])
        
        # Success or error
        if result.get("error"):
            st.error(f"Test failed: {result['error']}")
        else:
            st.success("Test succeeded")
            
            # Display rendered template or LLM result
            st.markdown("**Output:**")
            st.text_area("", value=result.get("result", ""), height=300, disabled=True)

def render_history_tab():
    """Render the component history tab."""
    st.subheader("Version History")
    
    if not st.session_state.component_id:
        st.info("Select a component to view history")
        return
    
    # Fetch component versions
    versions = fetch_component_versions(st.session_state.component_id)
    if not versions:
        st.info("No version history available")
        return
    
    # Display versions
    st.write(f"Component has {len(versions)} versions")
    
    # Create a table of versions
    version_data = []
    for version_info in versions:
        version_data.append({
            "Version": version_info["version"],
            "Timestamp": version_info["snapshot_timestamp"],
            "ID": version_info["snapshot_id"]
        })
    
    st.table(version_data)
    
    # Version comparison
    st.subheader("Compare Versions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        version1 = st.selectbox(
            "Version 1",
            [v["version"] for v in versions],
            index=0
        )
    
    with col2:
        version2 = st.selectbox(
            "Version 2",
            [v["version"] for v in versions],
            index=min(1, len(versions) - 1)
        )
    
    if st.button("Compare Versions"):
        if version1 == version2:
            st.warning("Please select different versions to compare")
            return
        
        # Fetch the two versions
        component1 = fetch_component_version(st.session_state.component_id, version1)
        component2 = fetch_component_version(st.session_state.component_id, version2)
        
        if not component1 or not component2:
            st.error("Error fetching component versions")
            return
        
        # Compare templates
        st.subheader("Template Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Version {version1}**")
            st.text_area("", value=component1["template"], height=300, disabled=True)
        
        with col2:
            st.markdown(f"**Version {version2}**")
            st.text_area("", value=component2["template"], height=300, disabled=True)
        
        # Compare other attributes
        st.subheader("Attribute Comparison")
        
        # Create a comparison table
        comparison = []
        
        # Simple attributes
        for attr in ["name", "description"]:
            if component1[attr] != component2[attr]:
                comparison.append({
                    "Attribute": attr,
                    version1: component1[attr],
                    version2: component2[attr]
                })
        
        # List attributes (show differences)
        for attr in ["required_inputs", "optional_inputs", "tags"]:
            list1 = set(component1.get(attr, []))
            list2 = set(component2.get(attr, []))
            
            if list1 != list2:
                added = list1 - list2
                removed = list2 - list1
                
                comparison.append({
                    "Attribute": attr,
                    version1: f"Added: {', '.join(added) if added else 'none'}\nRemoved: {', '.join(removed) if removed else 'none'}",
                    version2: ", ".join(component2.get(attr, []))
                })
        
        if comparison:
            st.table(comparison)
        else:
            st.info("No differences found in attributes")

def fetch_components() -> List[Dict[str, Any]]:
    """Fetch all components from the API.
    
    Returns:
        List of component metadata dictionaries.
    """
    try:
        response = requests.get(f"{API_ENDPOINT}/components/")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching components: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def fetch_component(component_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a component from the API.
    
    Args:
        component_id: ID of the component to fetch.
        
    Returns:
        Component dictionary if found, None otherwise.
    """
    try:
        response = requests.get(f"{API_ENDPOINT}/components/{component_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching component: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def fetch_component_versions(component_id: str) -> List[Dict[str, Any]]:
    """Fetch all versions of a component from the API.
    
    Args:
        component_id: ID of the component.
        
    Returns:
        List of version information dictionaries.
    """
    try:
        response = requests.get(f"{API_ENDPOINT}/components/{component_id}/versions")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching component versions: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []

def fetch_component_version(component_id: str, version: str) -> Optional[Dict[str, Any]]:
    """Fetch a specific version of a component from the API.
    
    Args:
        component_id: ID of the component.
        version: Version to fetch.
        
    Returns:
        Component dictionary if found, None otherwise.
    """
    try:
        response = requests.get(f"{API_ENDPOINT}/components/{component_id}/version/{version}")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching component version: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def validate_component(component_id: str, template: str) -> Dict[str, Any]:
    """Validate a component template.
    
    Args:
        component_id: ID of the component.
        template: Template to validate.
        
    Returns:
        Validation result dictionary.
    """
    try:
        response = requests.post(f"{API_ENDPOINT}/components/{component_id}/validate")
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error validating component: {response.text}")
            return {"is_valid": False, "errors": [response.text], "warnings": []}
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return {"is_valid": False, "errors": [str(e)], "warnings": []}

def test_render_only(component_id: str, inputs: Dict[str, Any]) -> None:
    """Test the rendering of a component.
    
    Args:
        component_id: ID of the component to test.
        inputs: Input values for the test.
    """
    try:
        response = requests.post(
            f"{API_ENDPOINT}/components/{component_id}/test-render",
            json=inputs
        )
        
        if response.status_code == 200:
            st.session_state.test_result = response.json()
        else:
            st.error(f"Error testing component: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def test_with_llm(component_id: str, inputs: Dict[str, Any], llm_options: Dict[str, Any]) -> None:
    """Test a component with an LLM provider.
    
    Args:
        component_id: ID of the component to test.
        inputs: Input values for the test.
        llm_options: LLM options for the test.
    """
    try:
        # Create test parameters
        test_params = {
            "inputs": inputs,
            "task_type": llm_options["task_type"],
            "provider": llm_options["provider"],
            "model": llm_options["model"],
            "parameters": llm_options["parameters"]
        }
        
        response = requests.post(
            f"{API_ENDPOINT}/components/{component_id}/test-llm",
            json=test_params
        )
        
        if response.status_code == 200:
            st.session_state.test_result = response.json()
        else:
            st.error(f"Error testing component with LLM: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def render_component_editor_page():
    """Main entry point for the component editor page."""
    component_editor_page()

if __name__ == "__main__":
    render_component_editor_page()