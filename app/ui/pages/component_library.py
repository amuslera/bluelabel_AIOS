"""
Streamlit page for browsing and managing MCP components.

This module provides a Streamlit UI for browsing, filtering, and managing
the library of MCP components.
"""

import streamlit as st
import json
import requests
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime
import io
import zipfile

# API endpoint
API_ENDPOINT = "http://localhost:8080"  # Update as needed

def component_library_page():
    """Render the component library page."""
    st.title("Component Library")
    
    # Create tabs for different sections
    library_tab, import_tab, export_tab = st.tabs(["Browse Library", "Import Components", "Export Components"])
    
    with library_tab:
        render_library_tab()
    
    with import_tab:
        render_import_tab()
    
    with export_tab:
        render_export_tab()

def render_library_tab():
    """Render the component library browser tab."""
    st.subheader("Component Browser")
    
    # Fetch components from API
    components = fetch_components()
    
    # Filter and search options
    col1, col2 = st.columns(2)
    
    with col1:
        # Extract all tags from components
        all_tags = set()
        for comp in components:
            all_tags.update(comp.get("tags", []))
        
        tag_filter = st.multiselect(
            "Filter by Tags",
            sorted(list(all_tags)),
            key="library_tag_filter"
        )
    
    with col2:
        search_query = st.text_input("Search Components", placeholder="Enter search term")
    
    # Apply filters
    filtered_components = components
    
    # Filter by tags
    if tag_filter:
        filtered_components = [
            comp for comp in filtered_components
            if any(tag in comp.get("tags", []) for tag in tag_filter)
        ]
    
    # Filter by search query
    if search_query:
        search_query = search_query.lower()
        filtered_components = [
            comp for comp in filtered_components
            if (
                search_query in comp["name"].lower() or
                search_query in comp.get("description", "").lower() or
                any(search_query in tag.lower() for tag in comp.get("tags", []))
            )
        ]
    
    # Display component count
    st.write(f"Showing {len(filtered_components)} of {len(components)} components")
    
    # Display components
    if filtered_components:
        # Convert to DataFrame for better display
        df_data = []
        for comp in filtered_components:
            df_data.append({
                "Name": comp["name"],
                "Description": comp.get("description", "")[:50] + ("..." if len(comp.get("description", "")) > 50 else ""),
                "Tags": ", ".join(comp.get("tags", [])),
                "Version": comp["version"],
                "Updated": comp.get("updated_at", ""),
                "ID": comp["id"]
            })
        
        df = pd.DataFrame(df_data)
        
        # Add edit/view buttons
        st.dataframe(
            df,
            column_config={
                "Name": st.column_config.TextColumn("Name"),
                "Description": st.column_config.TextColumn("Description"),
                "Tags": st.column_config.TextColumn("Tags"),
                "Version": st.column_config.TextColumn("Version"),
                "Updated": st.column_config.DatetimeColumn("Updated", format="MM/DD/YYYY"),
                "ID": st.column_config.TextColumn("ID", width="small")
            },
            hide_index=True
        )
        
        # Component selection for details
        selected_component = st.selectbox(
            "Select Component to View Details",
            [""] + [f"{comp['name']} ({comp['id']})" for comp in filtered_components]
        )
        
        # Display component details
        if selected_component:
            component_id = selected_component.split("(")[-1].rstrip(")")
            render_component_details(component_id)
    else:
        st.info("No components found matching the filters")

def render_component_details(component_id: str):
    """Render detailed view of a component.
    
    Args:
        component_id: ID of the component to display.
    """
    # Fetch component details
    component = fetch_component(component_id)
    if not component:
        st.error(f"Component {component_id} not found")
        return
    
    st.subheader(f"Component Details: {component['name']}")
    
    # Display component metadata
    col1, col2 = st.columns(2)
    with col1:
        st.text(f"ID: {component['id']}")
        st.text(f"Version: {component['version']}")
    with col2:
        try:
            created_date = datetime.fromisoformat(component['created_at'].replace('Z', '+00:00'))
            st.text(f"Created: {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            st.text(f"Created: {component['created_at']}")
        
        try:
            updated_date = datetime.fromisoformat(component['updated_at'].replace('Z', '+00:00'))
            st.text(f"Updated: {updated_date.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            st.text(f"Updated: {component['updated_at']}")
    
    # Description
    st.markdown("### Description")
    st.write(component['description'])
    
    # Tags
    if component.get("tags"):
        st.markdown("### Tags")
        tags_html = " ".join([
            f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>'
            for tag in component.get("tags", [])
        ])
        st.markdown(tags_html, unsafe_allow_html=True)
    
    # Inputs
    st.markdown("### Inputs")
    if component.get("required_inputs") or component.get("optional_inputs"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Required Inputs:**")
            for input_name in component.get("required_inputs", []):
                st.write(f"- {input_name}")
        
        with col2:
            st.markdown("**Optional Inputs:**")
            for input_name in component.get("optional_inputs", []):
                st.write(f"- {input_name}")
    else:
        st.info("No inputs defined")
    
    # Template
    st.markdown("### Template")
    st.text_area("", value=component['template'], height=300, disabled=True, key="component_template")
    
    # Metadata
    if component.get("metadata"):
        st.markdown("### Metadata")
        st.json(component.get("metadata", {}))
    
    # Actions
    st.markdown("### Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Edit in Component Editor"):
            st.session_state.page = "component_editor"
            st.session_state.component_id = component_id
            st.experimental_rerun()
    
    with col2:
        if st.button("View Test Results"):
            # Redirect to testing page
            st.session_state.page = "component_editor"
            st.session_state.component_id = component_id
            st.session_state.editor_tab = "test"
            st.experimental_rerun()
    
    with col3:
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

def render_import_tab():
    """Render the component import tab."""
    st.subheader("Import Components")
    
    import_option = st.radio("Import Source", ["Upload JSON File", "Paste JSON"])
    
    if import_option == "Upload JSON File":
        uploaded_file = st.file_uploader("Upload Component JSON", type=["json", "zip"])
        
        if uploaded_file:
            # Check if it's a JSON file or a ZIP archive
            if uploaded_file.name.endswith(".json"):
                try:
                    content = uploaded_file.read()
                    component_data = json.loads(content)
                    
                    # Display component info
                    st.write(f"Component Name: {component_data.get('name', 'Unknown')}")
                    st.write(f"Version: {component_data.get('version', 'Unknown')}")
                    
                    # Import button
                    if st.button("Import Component"):
                        import_component(component_data)
                except Exception as e:
                    st.error(f"Error parsing JSON: {str(e)}")
            
            elif uploaded_file.name.endswith(".zip"):
                try:
                    # Extract ZIP contents
                    with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as zip_file:
                        json_files = [f for f in zip_file.namelist() if f.endswith(".json")]
                        
                        if not json_files:
                            st.error("No JSON files found in the ZIP archive")
                            return
                        
                        st.write(f"Found {len(json_files)} components in ZIP archive")
                        
                        # List the components
                        components_to_import = []
                        for json_file in json_files:
                            try:
                                with zip_file.open(json_file) as f:
                                    component_data = json.loads(f.read())
                                    components_to_import.append({
                                        "filename": json_file,
                                        "name": component_data.get("name", "Unknown"),
                                        "id": component_data.get("id", "Unknown"),
                                        "version": component_data.get("version", "Unknown"),
                                        "data": component_data
                                    })
                            except Exception as e:
                                st.warning(f"Error parsing {json_file}: {str(e)}")
                        
                        # Display components
                        if components_to_import:
                            df = pd.DataFrame([
                                {
                                    "Name": comp["name"],
                                    "ID": comp["id"],
                                    "Version": comp["version"],
                                    "Filename": comp["filename"]
                                }
                                for comp in components_to_import
                            ])
                            
                            st.dataframe(df, hide_index=True)
                            
                            # Import all button
                            if st.button("Import All Components"):
                                success_count = 0
                                for comp in components_to_import:
                                    try:
                                        import_component(comp["data"])
                                        success_count += 1
                                    except Exception as e:
                                        st.error(f"Error importing {comp['name']}: {str(e)}")
                                
                                st.success(f"Successfully imported {success_count} of {len(components_to_import)} components")
                except Exception as e:
                    st.error(f"Error extracting ZIP file: {str(e)}")
    
    else:  # Paste JSON
        json_text = st.text_area("Paste Component JSON", height=300)
        
        if json_text:
            try:
                component_data = json.loads(json_text)
                
                # Display component info
                st.write(f"Component Name: {component_data.get('name', 'Unknown')}")
                st.write(f"Version: {component_data.get('version', 'Unknown')}")
                
                # Import button
                if st.button("Import Component"):
                    import_component(component_data)
            except Exception as e:
                st.error(f"Error parsing JSON: {str(e)}")

def render_export_tab():
    """Render the component export tab."""
    st.subheader("Export Components")
    
    # Fetch components from API
    components = fetch_components()
    
    # Create checkboxes for each component
    if not components:
        st.info("No components available to export")
        return
    
    # Extract all tags for filtering
    all_tags = set()
    for comp in components:
        all_tags.update(comp.get("tags", []))
    
    # Filter options
    filter_tags = st.multiselect(
        "Filter by Tags",
        sorted(list(all_tags)),
        key="export_tag_filter"
    )
    
    # Apply tag filter
    if filter_tags:
        filtered_components = [
            comp for comp in components
            if any(tag in comp.get("tags", []) for tag in filter_tags)
        ]
    else:
        filtered_components = components
    
    st.write(f"Showing {len(filtered_components)} of {len(components)} components")
    
    # Component selection
    selected_components = []
    select_all = st.checkbox("Select All Components")
    
    if select_all:
        selected_components = [comp["id"] for comp in filtered_components]
    else:
        # Group by tags for easier selection
        if filter_tags:
            for tag in filter_tags:
                st.subheader(f"Components tagged with '{tag}'")
                for comp in filtered_components:
                    if tag in comp.get("tags", []):
                        if st.checkbox(f"{comp['name']} (v{comp['version']})", key=f"select_{comp['id']}_{tag}"):
                            if comp["id"] not in selected_components:
                                selected_components.append(comp["id"])
        else:
            # Just list all components
            for comp in filtered_components:
                if st.checkbox(f"{comp['name']} (v{comp['version']})", key=f"select_{comp['id']}"):
                    selected_components.append(comp["id"])
    
    # Display selection count
    st.write(f"Selected {len(selected_components)} components")
    
    # Export options
    export_format = st.radio("Export Format", ["JSON Files (ZIP)", "Single Component JSON"])
    
    if len(selected_components) > 0:
        if export_format == "JSON Files (ZIP)" or len(selected_components) > 1:
            if st.button("Export Selected Components (ZIP)"):
                export_components_zip(selected_components)
        else:
            if st.button("Export Component JSON"):
                export_component_json(selected_components[0])

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

def import_component(component_data: Dict[str, Any]) -> None:
    """Import a component.
    
    Args:
        component_data: Component data to import.
    """
    try:
        response = requests.post(
            f"{API_ENDPOINT}/components/import",
            json=component_data
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"Component imported successfully: {result.get('component_id')}")
        else:
            st.error(f"Error importing component: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def export_component_json(component_id: str) -> None:
    """Export a single component as JSON.
    
    Args:
        component_id: ID of the component to export.
    """
    try:
        response = requests.get(f"{API_ENDPOINT}/components/{component_id}/export")
        
        if response.status_code == 200:
            result = response.json()
            component_name = result.get("name", "component").replace(" ", "_").lower()
            
            # Create a download button
            st.download_button(
                label="Download JSON",
                data=json.dumps(result, indent=2),
                file_name=f"{component_name}_{component_id}.json",
                mime="application/json"
            )
        else:
            st.error(f"Error exporting component: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def export_components_zip(component_ids: List[str]) -> None:
    """Export multiple components as a ZIP file.
    
    Args:
        component_ids: List of component IDs to export.
    """
    if not component_ids:
        st.warning("No components selected for export")
        return
    
    try:
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for component_id in component_ids:
                # Fetch the component
                response = requests.get(f"{API_ENDPOINT}/components/{component_id}/export")
                
                if response.status_code == 200:
                    result = response.json()
                    component_name = result.get("name", "component").replace(" ", "_").lower()
                    
                    # Add the component to the ZIP file
                    zip_file.writestr(
                        f"{component_name}_{component_id}.json",
                        json.dumps(result, indent=2)
                    )
                else:
                    st.error(f"Error exporting component {component_id}: {response.text}")
        
        # Reset buffer position
        zip_buffer.seek(0)
        
        # Create a download button
        st.download_button(
            label=f"Download {len(component_ids)} Components (ZIP)",
            data=zip_buffer,
            file_name="components_export.zip",
            mime="application/zip"
        )
    except Exception as e:
        st.error(f"Error exporting components: {str(e)}")

def render_component_library_page():
    """Main entry point for the component library page."""
    component_library_page()

if __name__ == "__main__":
    render_component_library_page()