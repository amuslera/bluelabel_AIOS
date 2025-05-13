"""
Prompt Manager UI

Streamlit UI for managing Multi-Component Prompting (MCP) components.
"""

import streamlit as st
import requests
import json
import difflib
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# API Settings
API_BASE_URL = "http://localhost:8080"
COMPONENTS_URL = f"{API_BASE_URL}/components"

# Page configuration
st.set_page_config(
    page_title="Prompt Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
.diff-add {
    color: green;
    background-color: #e6ffec;
}
.diff-remove {
    color: red;
    background-color: #ffebe9;
}
.version-tag {
    background-color: #0969da;
    color: white;
    padding: 0.1rem 0.5rem;
    border-radius: 0.5rem;
    font-size: 0.8rem;
}
.sidebar-section {
    margin-bottom: 1.5rem;
}
.quality-high {
    color: #22863a;
    background-color: #e6ffec;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-weight: bold;
}
.quality-medium {
    color: #e36209;
    background-color: #fff8c5;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-weight: bold;
}
.quality-low {
    color: #cb2431;
    background-color: #ffeef0;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-weight: bold;
}
.suggestion-item {
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    background-color: #f6f8fa;
    border-left: 3px solid #0969da;
}
.structure-check {
    font-size: 1.2rem;
    margin-right: 0.5rem;
}
.structure-present {
    color: #22863a;
}
.structure-missing {
    color: #cb2431;
}
.template-example {
    border: 1px solid #ddd;
    border-radius: 0.3rem;
    padding: 1rem;
    margin-top: 0.5rem;
    background-color: #f6f8fa;
    font-family: monospace;
}
.tab-container {
    margin-top: 1rem;
}
.metric-card {
    background-color: #f6f8fa;
    border-radius: 0.3rem;
    padding: 1rem;
    margin-bottom: 1rem;
    border-left: 4px solid #0969da;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: bold;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# Utility functions
def get_components() -> List[Dict[str, Any]]:
    """Fetch all components from the API."""
    try:
        response = requests.get(COMPONENTS_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching components: {e}")
        return []

def analyze_template(template: str) -> Dict[str, Any]:
    """Analyze a template for quality and provide suggestions."""
    try:
        response = requests.post(f"{COMPONENTS_URL}/analyze-template", json={"template": template})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error analyzing template: {e}")
        return {"is_valid": False, "errors": [str(e)], "warnings": [], "suggestions": []}

def get_template_examples(task_type: Optional[str] = None) -> Dict[str, str]:
    """Get template examples from the API."""
    try:
        url = f"{COMPONENTS_URL}/template-examples"
        if task_type:
            url += f"?task_type={task_type}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching template examples: {e}")
        return {}

def get_component(component_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a specific component from the API."""
    try:
        response = requests.get(f"{COMPONENTS_URL}/{component_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching component: {e}")
        return None

def get_component_versions(component_id: str) -> List[Dict[str, Any]]:
    """Fetch versions of a component from the API."""
    try:
        response = requests.get(f"{COMPONENTS_URL}/{component_id}/versions")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching versions: {e}")
        return []

def get_component_version(component_id: str, version: str) -> Optional[Dict[str, Any]]:
    """Fetch a specific version of a component from the API."""
    try:
        response = requests.get(f"{COMPONENTS_URL}/{component_id}/version/{version}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching version: {e}")
        return None

def update_component(component_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a component using the API."""
    try:
        response = requests.put(f"{COMPONENTS_URL}/{component_id}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating component: {e}")
        return None

def create_component(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new component using the API."""
    try:
        response = requests.post(COMPONENTS_URL, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating component: {e}")
        return None

def validate_component(component_id: str) -> Dict[str, Any]:
    """Validate a component using the API."""
    try:
        response = requests.post(f"{COMPONENTS_URL}/{component_id}/validate")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error validating component: {e}")
        return {"is_valid": False, "errors": [str(e)], "warnings": []}

def test_render_component(component_id: str, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Test render a component using the API."""
    try:
        response = requests.post(f"{COMPONENTS_URL}/{component_id}/test-render", json=inputs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error testing component: {e}")
        return None

def format_diff(old_text: str, new_text: str) -> str:
    """Format a diff between two text blocks."""
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        lineterm=""
    )
    
    html_diff = []
    for line in diff:
        if line.startswith("+"):
            html_diff.append(f'<div class="diff-add">{line}</div>')
        elif line.startswith("-"):
            html_diff.append(f'<div class="diff-remove">{line}</div>')
        else:
            html_diff.append(f'<div>{line}</div>')
    
    return "".join(html_diff)

# Sidebar for component selection and main actions
st.sidebar.title("Prompt Manager")

# Component selector
st.sidebar.markdown("<div class='sidebar-section'><h3>Select Component</h3></div>", unsafe_allow_html=True)
components = get_components()
component_options = {comp["name"]: comp["id"] for comp in components}
component_names = list(component_options.keys())

selected_name = st.sidebar.selectbox("Select a component", component_names if component_names else ["No components found"])
selected_id = component_options.get(selected_name) if component_names else None

# Main actions
st.sidebar.markdown("<div class='sidebar-section'><h3>Actions</h3></div>", unsafe_allow_html=True)
action = st.sidebar.radio(
    "Choose action",
    ["View Component", "Edit Component", "View Versions", "Test Component", "Create New Component"],
    key="action"
)

# View Component Page
if action == "View Component" and selected_id:
    # Fetch the component
    component = get_component(selected_id)
    if not component:
        st.error(f"Could not fetch component {selected_id}")
    else:
        # Header
        st.title(f"{component['name']}")
        st.caption(f"ID: {component['id']}")
        
        # Version tag and updated time
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"<span class='version-tag'>v{component['version']}</span>", unsafe_allow_html=True)
        with col2:
            updated_at = datetime.fromisoformat(component['updated_at']).strftime("%Y-%m-%d %H:%M:%S")
            st.caption(f"Last updated: {updated_at}")
        
        # Description
        st.subheader("Description")
        st.text(component["description"])
        
        # Tags
        st.subheader("Tags")
        if component["tags"]:
            st.write(", ".join(component["tags"]))
        else:
            st.text("No tags")
        
        # Inputs
        st.subheader("Inputs")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Required Inputs")
            if component["required_inputs"]:
                for input_name in component["required_inputs"]:
                    st.text(f"• {input_name}")
            else:
                st.text("No required inputs")
        
        with col2:
            st.write("Optional Inputs")
            if component["optional_inputs"]:
                for input_name in component["optional_inputs"]:
                    st.text(f"• {input_name}")
            else:
                st.text("No optional inputs")
        
        # Template
        st.subheader("Template")
        st.code(component["template"], language="")
        
        # Additional metadata
        if component.get("metadata"):
            st.subheader("Metadata")
            st.json(component["metadata"])
            
# Edit Component Page
elif action == "Edit Component" and selected_id:
    # Fetch the component
    component = get_component(selected_id)
    if not component:
        st.error(f"Could not fetch component {selected_id}")
    else:
        st.title(f"Edit: {component['name']}")
        st.caption(f"ID: {component['id']} | Current Version: {component['version']}")
        
        # Create a form for editing
        with st.form("edit_component_form"):
            # Basic details
            name = st.text_input("Name", value=component["name"])
            description = st.text_area("Description", value=component["description"], height=100)
            tags = st.text_input("Tags (comma-separated)", value=", ".join(component["tags"]))
            
            # Template with larger editor
            st.subheader("Template")
            template = st.text_area("", value=component["template"], height=300, key="template_editor")
            
            # Version increment option
            increment_version = st.checkbox("Increment version number", value=True)
            
            # Submit button
            submitted = st.form_submit_button("Update Component")
            
            if submitted:
                # Format tags
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                
                # Check if anything has changed
                changed = (
                    name != component["name"] or
                    description != component["description"] or
                    tags_list != component["tags"] or
                    template != component["template"]
                )
                
                if not changed:
                    st.warning("No changes detected.")
                else:
                    # Create update data
                    update_data = {
                        "name": name,
                        "description": description,
                        "tags": tags_list,
                        "template": template,
                        "increment_version": increment_version
                    }
                    
                    # Update the component
                    result = update_component(selected_id, update_data)
                    if result:
                        st.success(f"Component updated to version {result['version']}")
                        
                        # Show diff of changes
                        if template != component["template"]:
                            st.subheader("Template Changes")
                            diff_html = format_diff(component["template"], template)
                            st.markdown(diff_html, unsafe_allow_html=True)
                            
                        # Add refresh button
                        if st.button("Refresh"):
                            st.experimental_rerun()

# View Versions Page
elif action == "View Versions" and selected_id:
    # Fetch the component
    component = get_component(selected_id)
    if not component:
        st.error(f"Could not fetch component {selected_id}")
    else:
        st.title(f"Versions: {component['name']}")
        st.caption(f"ID: {component['id']} | Current Version: {component['version']}")
        
        # Fetch versions
        versions = get_component_versions(selected_id)
        if not versions:
            st.info("No version history available for this component.")
        else:
            # Version selection
            st.subheader("Select a version to view")
            version_options = {f"v{v['version']} ({v['snapshot_timestamp'][:16]})": v["version"] for v in versions}
            selected_version = st.selectbox("Version", list(version_options.keys()))
            version_id = version_options[selected_version]
            
            # Fetch the selected version
            version_data = get_component_version(selected_id, version_id)
            if not version_data:
                st.error(f"Could not fetch version {version_id}")
            else:
                # Show version details
                st.markdown(f"### Version {version_id}")
                st.text(f"Snapshot created: {version_data.get('snapshot_timestamp', 'N/A')}")
                
                # Compare with current version
                st.subheader("Compare with current version")
                
                # Template diff
                if version_data["template"] != component["template"]:
                    st.markdown("#### Template Changes")
                    diff_html = format_diff(version_data["template"], component["template"])
                    st.markdown(diff_html, unsafe_allow_html=True)
                else:
                    st.info("No changes in template between this version and the current version.")
                
                # Restore version option
                if st.button("Restore to this version"):
                    # Create update data from the old version
                    update_data = {
                        "name": version_data["name"],
                        "description": version_data["description"],
                        "template": version_data["template"],
                        "tags": version_data["tags"],
                        "required_inputs": version_data["required_inputs"],
                        "optional_inputs": version_data["optional_inputs"],
                        "increment_version": True
                    }
                    
                    # Update the component
                    result = update_component(selected_id, update_data)
                    if result:
                        st.success(f"Component restored to version {version_id} (as new version {result['version']})")
                        time.sleep(2)  # Short delay to show the success message
                        st.experimental_rerun()

# Test Component Page
elif action == "Test Component" and selected_id:
    # Fetch the component
    component = get_component(selected_id)
    if not component:
        st.error(f"Could not fetch component {selected_id}")
    else:
        st.title(f"Test: {component['name']}")
        st.caption(f"ID: {component['id']} | Version: {component['version']}")
        
        # Show template
        st.subheader("Template")
        st.code(component["template"], language="")
        
        # Input form
        st.subheader("Provide Inputs")
        
        with st.form("test_inputs_form"):
            # Create input fields for each required and optional input
            inputs = {}
            
            # Required inputs
            if component["required_inputs"]:
                st.markdown("#### Required Inputs")
                for input_name in component["required_inputs"]:
                    inputs[input_name] = st.text_area(f"{input_name}", key=f"input_{input_name}", height=100)
            
            # Optional inputs
            if component["optional_inputs"]:
                st.markdown("#### Optional Inputs")
                for input_name in component["optional_inputs"]:
                    inputs[input_name] = st.text_area(f"{input_name} (optional)", key=f"input_{input_name}", height=100)
            
            # Submit button
            render_submitted = st.form_submit_button("Test Render")
            
            if render_submitted:
                # Filter out empty optional inputs
                filtered_inputs = {k: v for k, v in inputs.items() if v.strip() or k in component["required_inputs"]}
                
                # Check for missing required inputs
                missing = [name for name in component["required_inputs"] if not filtered_inputs.get(name, "").strip()]
                if missing:
                    st.error(f"Missing required inputs: {', '.join(missing)}")
                else:
                    # Test render
                    result = test_render_component(selected_id, filtered_inputs)
                    if result:
                        st.subheader("Rendered Result")
                        st.code(result["rendered_template"], language="")
        
        # LLM Test Form
        st.subheader("Test with LLM")
        with st.form("test_llm_form"):
            # Re-use the same inputs as above
            # Provider and model selection
            provider = st.selectbox("Provider", ["Default", "OpenAI", "Anthropic", "Local"])
            model = st.text_input("Model (optional)")
            
            # Add LLM test button
            llm_submitted = st.form_submit_button("Test with LLM")
            
            if llm_submitted:
                # Filter out empty optional inputs
                filtered_inputs = {k: v for k, v in inputs.items() if v.strip() or k in component["required_inputs"]}
                
                # Check for missing required inputs
                missing = [name for name in component["required_inputs"] if not filtered_inputs.get(name, "").strip()]
                if missing:
                    st.error(f"Missing required inputs: {', '.join(missing)}")
                else:
                    # Prepare test parameters
                    test_params = {
                        "inputs": filtered_inputs,
                        "task_type": "completion"
                    }
                    
                    if provider != "Default":
                        test_params["provider"] = provider
                    if model:
                        test_params["model"] = model
                    
                    # Show loading message
                    with st.spinner("Testing with LLM..."):
                        try:
                            response = requests.post(
                                f"{COMPONENTS_URL}/{selected_id}/test-llm",
                                json=test_params
                            )
                            response.raise_for_status()
                            result = response.json()
                            
                            st.subheader("LLM Response")
                            st.text(f"Provider: {result['provider']}")
                            st.text(f"Model: {result['model']}")
                            st.text(f"Time: {result['elapsed_time']:.2f} seconds")
                            st.text(f"Tokens: {result['token_count']}")
                            
                            st.markdown("#### Response")
                            st.code(result["completion"], language="")
                            
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error testing with LLM: {e}")

# Create New Component Page
elif action == "Create New Component":
    st.title("Create New Component")
    
    with st.form("create_component_form"):
        # Basic details
        name = st.text_input("Name")
        description = st.text_area("Description", height=100)
        tags = st.text_input("Tags (comma-separated)")
        
        # Template with larger editor
        st.subheader("Template")
        template = st.text_area("", height=300, key="new_template_editor")
        
        # Submit button
        submitted = st.form_submit_button("Create Component")
        
        if submitted:
            if not name or not template:
                st.error("Name and template are required.")
            else:
                # Format tags
                tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                
                # Create component data
                component_data = {
                    "name": name,
                    "description": description,
                    "template": template,
                    "tags": tags_list
                }
                
                # Create the component
                result = create_component(component_data)
                if result:
                    st.success(f"Component created with ID: {result['id']}")
                    
                    # Add view button
                    if st.button("View Component"):
                        # Redirect to view page
                        st.session_state.action = "View Component"
                        # Need to refresh components list to include the new one
                        st.experimental_rerun()

# If no component is selected
elif not selected_id and action != "Create New Component":
    st.title("Prompt Manager")
    st.info("Select a component from the sidebar or create a new one.")
    
    if not components:
        st.warning("No components found. Create a new component to get started.")
    else:
        st.subheader("Available Components")
        # Show a table of all components
        component_data = []
        for comp in components:
            component_data.append({
                "Name": comp["name"],
                "Version": comp["version"],
                "Description": comp["description"][:50] + "..." if len(comp["description"]) > 50 else comp["description"],
                "Last Updated": datetime.fromisoformat(comp["updated_at"]).strftime("%Y-%m-%d %H:%M")
            })
        
        st.table(component_data)