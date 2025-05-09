# app/ui/streamlit_app.py
import streamlit as st
import requests
import json
import base64
from datetime import datetime, timedelta
import os
from io import BytesIO
import pandas as pd
import altair as alt
import re

# Set Streamlit page configuration
st.set_page_config(
    page_title="Bluelabel AIOS - ContentMind",
    page_icon="🧠",
    layout="wide"
)

# Define API endpoint (FastAPI running on port 8080)
API_ENDPOINT = "http://localhost:8080"

# Define content type icons and colors
CONTENT_TYPE_ICONS = {
    "url": "🔗",
    "pdf": "📄",
    "text": "📝",
    "audio": "🔊"
}

CONTENT_TYPE_COLORS = {
    "url": "#c2e0f4",    # Light blue
    "pdf": "#f5d5cb",    # Light coral
    "text": "#d5f5d5",   # Light green
    "audio": "#e6d9f2"   # Light purple
}

# Cache for tag suggestions
if 'all_tags' not in st.session_state:
    st.session_state.all_tags = []

def get_all_tags(force_refresh=False):
    """Get all available tags for suggestions"""
    if not st.session_state.all_tags or force_refresh:
        try:
            # Fetch all content
            response = requests.get(f"{API_ENDPOINT}/knowledge/list", params={"limit": 100})
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    content_items = result.get("results", [])
                    # Extract all unique tags
                    all_tags = set()
                    for item in content_items:
                        if item.get("tags"):
                            all_tags.update(item.get("tags"))
                    st.session_state.all_tags = sorted(list(all_tags))
        except Exception as e:
            pass
    return st.session_state.all_tags

def format_date(date_str):
    """Format date string for display"""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str
    
def tag_selector(label, default=""):
    """Custom tag selector with autocomplete"""
    tags = get_all_tags()
    # Split existing tags
    current_tags = [tag.strip() for tag in default.split(",") if tag.strip()]
    
    # Create a container for tag selection
    tag_container = st.container()
    
    with tag_container:
        # Display currently selected tags
        if current_tags:
            st.write("Selected tags:")
            tags_html = " ".join([
                f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>'
                for tag in current_tags
            ])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        # Input for new tag
        new_tag = st.selectbox(
            f"{label} (select or type)",
            options=[""] + [tag for tag in tags if tag not in current_tags],
            key=f"tag_select_{label}"
        )
        
        # Add new tag button
        if new_tag and st.button("Add Tag", key=f"add_tag_{label}"):
            current_tags.append(new_tag)
    
    # Return comma-separated string of tags
    return ", ".join(current_tags)

def main():
    st.title("Bluelabel AIOS - ContentMind")
    
    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state.page = "Process Content"
    
    # Initialize content type session state
    if 'content_type' not in st.session_state:
        st.session_state.content_type = "url"
        
    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Process Content", "View Knowledge", "Search", "Settings", "Dashboard"],
        index=["Process Content", "View Knowledge", "Search", "Settings", "Dashboard"].index(st.session_state.page)
    )
    
    # Update session state
    st.session_state.page = page
    
    if page == "Process Content":
        process_content_page()
    elif page == "View Knowledge":
        view_knowledge_page()
    elif page == "Search":
        search_page()
    elif page == "Settings":
        settings_page()
    elif page == "Dashboard":
        dashboard_page()

def update_content_type():
    """Updates session state when content type changes"""
    st.session_state.content_type = st.session_state.content_type_selector

def process_content_page():
    st.header("Process New Content")
    
    # Get current provider preferences
    try:
        # In a real app, we would get this from the backend or local storage
        # For now, we'll use defaults
        summary_provider = "Auto (Based on Complexity)"
        entity_provider = "Auto (Based on Complexity)"
        tag_provider = "Auto (Based on Complexity)"
    except:
        summary_provider = "Auto (Based on Complexity)"
        entity_provider = "Auto (Based on Complexity)"
        tag_provider = "Auto (Based on Complexity)"
    
    # Add a collapsible section for advanced options
    with st.expander("Advanced Processing Options", expanded=False):
        st.subheader("Provider Preferences")
        
        summary_provider = st.selectbox(
            "Summarization Provider",
            ["Auto (Based on Complexity)", "OpenAI", "Anthropic", "Local (if available)"],
            index=0
        )
        
        entity_provider = st.selectbox(
            "Entity Extraction Provider",
            ["Auto (Based on Complexity)", "OpenAI", "Anthropic", "Local (if available)"],
            index=0
        )
        
        tag_provider = st.selectbox(
            "Content Tagging Provider",
            ["Auto (Based on Complexity)", "OpenAI", "Anthropic", "Local (if available)"],
            index=0
        )
    
    # Convert UI selections to API provider values
    provider_map = {
        "Auto (Based on Complexity)": None,
        "OpenAI": "openai",
        "Anthropic": "anthropic",
        "Local (if available)": "local"
    }
    
    # Content type selector OUTSIDE the form for immediate refresh
    st.selectbox(
        "Content Type",
        ["url", "text", "pdf", "audio"],
        index=["url", "text", "pdf", "audio"].index(st.session_state.content_type),
        key="content_type_selector",
        on_change=update_content_type
    )
    
    # Content input based on selected type
    content_type = st.session_state.content_type
    
    # Initialize variables for different content types
    content = None
    text_metadata = {}
    
    # Input form
    with st.form("content_form"):
        # Use current content type from session state
        st.text_input("Content Type", content_type, disabled=True, label_visibility="collapsed")
        
        if content_type == "url":
            content = st.text_input("URL", "https://example.com")
            
        elif content_type == "text":
            content = st.text_area("Text Content", "Paste your text here...", height=300)
            # Make sure we don't send the placeholder text
            if content == "Paste your text here...":
                content = ""

            # Optional metadata for text content
            with st.expander("Text Metadata (Optional)", expanded=False):
                title = st.text_input("Title (leave empty to auto-generate)", "")
                source = st.text_input("Source", "Manual Input")
                author = st.text_input("Author", "")

                # Collect metadata
                if title:
                    text_metadata["title"] = title
                if source != "Manual Input":
                    text_metadata["source"] = source
                if author:
                    text_metadata["author"] = author
                    
        elif content_type == "pdf":
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_uploader")
            if uploaded_file:
                # Convert uploaded file to base64 for API transmission
                bytes_data = uploaded_file.getvalue()
                b64_pdf = base64.b64encode(bytes_data).decode()
                content = f"data:application/pdf;base64,{b64_pdf}"
                st.success(f"Uploaded: {uploaded_file.name}")
                
                # Display PDF info if possible
                try:
                    from pypdf import PdfReader
                    pdf = PdfReader(BytesIO(bytes_data))
                    st.info(f"PDF Info: {len(pdf.pages)} pages")
                except Exception as e:
                    pass
                
        elif content_type == "audio":
            uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a"], key="audio_uploader")
            if uploaded_file:
                # Convert uploaded file to base64 for API transmission
                bytes_data = uploaded_file.getvalue()
                content_type_map = {
                    "audio/mpeg": "mp3",
                    "audio/wav": "wav",
                    "audio/x-m4a": "m4a",
                    "audio/mp4": "m4a"
                }
                mime_type = content_type_map.get(uploaded_file.type, "audio/mpeg")
                b64_audio = base64.b64encode(bytes_data).decode()
                content = f"data:{mime_type};base64,{b64_audio}"
                st.success(f"Uploaded: {uploaded_file.name}")
                st.audio(uploaded_file, format=f"audio/{mime_type}")
                
        # Optional tags for all content types
        suggested_tags = st.text_input("Suggested Tags (comma separated)", 
                                      help="Optional tags to suggest for the content. The AI will use these as hints.")
        
        submitted = st.form_submit_button("Process Content")
    
    if submitted:
        with st.spinner("Processing content..."):
            # Process content if we have valid content
            if content:
                try:
                    # Prepare the provider preferences
                    provider_preferences = {
                        "summary": provider_map[summary_provider],
                        "entity_extraction": provider_map[entity_provider],
                        "tagging": provider_map[tag_provider]
                    }
                    
                    # Remove None values
                    provider_preferences = {k: v for k, v in provider_preferences.items() if v is not None}

                    # Prepare API JSON
                    api_json = {
                        "content_type": content_type,
                        "content": content,
                        "provider_preferences": provider_preferences
                    }
                    
                    # Add metadata for text content if provided
                    if content_type == "text" and text_metadata:
                        api_json["metadata"] = text_metadata
                    
                    # Add suggested tags if provided
                    if suggested_tags:
                        tags_list = [tag.strip() for tag in suggested_tags.split(",") if tag.strip()]
                        if tags_list:
                            if "metadata" not in api_json:
                                api_json["metadata"] = {}
                            api_json["metadata"]["suggested_tags"] = tags_list

                    # Make the API request
                    with st.spinner(f"Processing {content_type} content..."):
                        response = requests.post(
                            f"{API_ENDPOINT}/agents/contentmind/process",
                            json=api_json
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            display_processing_result(result)
                            
                            # Refresh tag cache after adding new content
                            get_all_tags(force_refresh=True)
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
            else:
                st.warning("Please provide content to process.")

def display_processing_result(result):
    """Display content processing result"""
    if result.get("status") == "success":
        st.success("Content processed successfully!")
        
        # Check if content was stored
        storage_info = result.get("storage", {})
        if storage_info.get("stored"):
            st.success(f"Content saved to knowledge repository with ID: {storage_info.get('content_id')}")
            
            # Add button to view in knowledge repository
            if st.button("View in Knowledge Repository"):
                st.session_state.page = "View Knowledge"
                st.session_state.selected_content_id = storage_info.get("content_id")
                st.session_state.view_content_details = True
                st.experimental_rerun()
        
        # Processing Result container
        st.header("Processing Result")
            
        processed = result.get("processed_content", {})
        content_type = result.get("content_type", "unknown")
        
        # Title with content type icon
        icon = CONTENT_TYPE_ICONS.get(content_type, "📄")
        st.header(f"{icon} {processed.get('title', 'Untitled')}")

        # Metadata in expandable section
        with st.expander("Metadata", expanded=True):
            # Basic metadata (source, processing time)
            col1, col2 = st.columns(2)
            with col1:
                source = processed.get('source', 'Unknown')
                # Only make URLs clickable
                if source.startswith("http"):
                    st.markdown(f"**Source:** [{source}]({source})")
                else:
                    st.markdown(f"**Source:** {source}")
            with col2:
                processed_time = processed.get('extracted_at', datetime.now().isoformat())
                st.markdown(f"**Processed:** {format_date(processed_time)}")

            # Display content type specific metadata
            if content_type == "pdf" and processed.get("page_count"):
                st.markdown(f"**Pages:** {processed.get('page_count')}")
            elif content_type == "audio" and processed.get("duration"):
                st.markdown(f"**Duration:** {processed.get('duration')}")
                if processed.get("language"):
                    st.markdown(f"**Language:** {processed.get('language').title()}")
            
            # Author and date if available
            if processed.get("author") or processed.get("published_date"):
                col1, col2 = st.columns(2)
                if processed.get("author"):
                    with col1:
                        st.markdown(f"**Author:** {processed.get('author')}")
                if processed.get("published_date"):
                    with col2:
                        st.markdown(f"**Published:** {format_date(processed.get('published_date'))}")
        
        # Summary section
        st.subheader("Summary")
        st.markdown(processed.get("summary", "No summary available"))
        
        # Show which providers were used
        with st.expander("AI Models Used", expanded=False):
            providers_used = result.get("providers_used", {})
            if providers_used:
                st.markdown("The following AI models were used to process this content:")
                
                for task, provider in providers_used.items():
                    if provider:
                        st.markdown(f"- **{task.replace('_', ' ').title()}**: {provider.title()}")
                    else:
                        st.markdown(f"- **{task.replace('_', ' ').title()}**: Not used")
        
        # Tags
        if processed.get("tags"):
            st.subheader("Tags")
            tags_html = " ".join([
                f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>' 
                for tag in processed.get("tags", [])
            ])
            st.markdown(tags_html, unsafe_allow_html=True)
        
        # Entities
        if processed.get("entities"):
            st.subheader("Entities")
            entities = processed.get("entities", {})
            
            # Try to parse if it's a string
            if isinstance(entities, str):
                try:
                    entities = json.loads(entities)
                except:
                    st.warning("Could not parse entities")
                    entities = {}
            
            # Use tabs instead of nested expanders for entity categories
            if entities and len(entities) > 0:
                entity_tabs = st.tabs([category.title() for category in entities.keys()])
                for i, (category, items) in enumerate(entities.items()):
                    if items:
                        with entity_tabs[i]:
                            # Create clickable entity tags
                            entity_html = " ".join([
                                f'<span style="background-color: #e6f2ff; padding: 3px 8px; margin-right: 5px; border-radius: 10px; margin-bottom: 5px; display: inline-block;">{item}</span>'
                                for item in items
                            ])
                            st.markdown(entity_html, unsafe_allow_html=True)
    else:
        st.error(f"Processing error: {result.get('message', 'Unknown error')}")

def view_knowledge_page():
    st.header("Knowledge Repository")
    
    # Tabs for different views
    view_tab, calendar_tab, tag_tab = st.tabs(["List View", "Calendar View", "Tag Explorer"])
    
    with view_tab:
        # Advanced filters in an expander
        with st.expander("Filters", expanded=True):
            # Create columns for filters
            col1, col2 = st.columns(2)
            
            with col1:
                # Content type filter
                content_type = st.selectbox(
                    "Content Type",
                    ["All", "url", "pdf", "audio", "text"]
                )
                
                # Date range filter
                date_filter = st.selectbox(
                    "Date Filter",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
                )
                
                if date_filter == "Custom Range":
                    date_col1, date_col2 = st.columns(2)
                    with date_col1:
                        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                    with date_col2:
                        end_date = st.date_input("End Date", datetime.now())
            
            with col2:
                # Tag filter using custom tag selector
                tags = tag_selector("Filter by Tags")
                
                # Search within results
                filter_text = st.text_input("Filter by Text", 
                                           help="Filter results by text in title or summary")
        
        # Pagination controls
        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Results per page", min_value=5, max_value=50, value=10, step=5)
        with col2:
            page = st.number_input("Page", min_value=1, value=1, step=1)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Prepare query parameters
        params = {"limit": limit, "offset": offset}
        if content_type != "All":
            params["content_type"] = content_type
        if tags.strip():
            params["tags"] = tags
        
        # Prepare date filter
        date_query = None
        if date_filter == "Last 7 Days":
            date_query = (datetime.now() - timedelta(days=7)).isoformat()
        elif date_filter == "Last 30 Days":
            date_query = (datetime.now() - timedelta(days=30)).isoformat()
        elif date_filter == "Last 90 Days":
            date_query = (datetime.now() - timedelta(days=90)).isoformat()
        elif date_filter == "Custom Range" and start_date and end_date:
            date_query = f"{start_date.isoformat()},{end_date.isoformat()}"
        
        if date_query:
            params["date_range"] = date_query
        
        # Fetch content list
        try:
            response = requests.get(f"{API_ENDPOINT}/knowledge/list", params=params)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    content_items = result.get("results", [])
                    total = result.get("total", 0)
                    
                    # Filter by text if needed
                    if filter_text:
                        filter_text = filter_text.lower()
                        content_items = [
                            item for item in content_items 
                            if (filter_text in item.get('title', '').lower() or 
                                filter_text in item.get('summary', '').lower())
                        ]
                    
                    # Show pagination info
                    st.write(f"Showing {len(content_items)} of {total} items")
                    
                    # Display content items
                    if content_items:
                        for item in content_items:
                            item_type = item.get('content_type', 'unknown')
                            bg_color = CONTENT_TYPE_COLORS.get(item_type, "#f0f0f0")
                            icon = CONTENT_TYPE_ICONS.get(item_type, "📄")
                            
                            with st.container():
                                # Create a card-like container with background color
                                st.markdown(f"""
                                <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <h3 style="margin: 0;">{icon} {item.get('title', 'Untitled')}</h3>
                                        <div>{item_type} • {format_date(item.get('created_at', ''))}</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    # Show summary
                                    if item.get("summary"):
                                        st.write(item.get("summary")[:200] + "..." if len(item.get("summary", "")) > 200 else item.get("summary"))
                                
                                with col2:
                                    # Author if available
                                    if item.get("author"):
                                        st.write(f"Author: {item.get('author')}")
                                    
                                    # Source if it's a URL
                                    source = item.get('source', '')
                                    if source and source.startswith('http'):
                                        st.write(f"[Source]({source})")
                                
                                # Show tags if any
                                if item.get("tags"):
                                    tags_html = " ".join([
                                        f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>'
                                        for tag in item.get("tags", [])
                                    ])
                                    st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
                                
                                # Add view button
                                if st.button(f"View Details", key=f"view_{item.get('id')}"):
                                    st.session_state.selected_content_id = item.get("id")
                                    st.session_state.view_content_details = True
                                
                                st.markdown("---")
                        
                        # Display item details if requested
                        if hasattr(st.session_state, 'view_content_details') and st.session_state.view_content_details:
                            if hasattr(st.session_state, 'selected_content_id'):
                                display_content_details(st.session_state.selected_content_id)
                    else:
                        st.info("No content items found matching your filters.")
                else:
                    st.error(f"Error: {result.get('message')}")
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error connecting to API: {str(e)}")
    
    with calendar_tab:
        st.write("Coming soon: Calendar view of content by date")
        
    with tag_tab:
        st.subheader("Tag Explorer")
        
        # Get all tags for tag cloud
        all_tags = get_all_tags()
        
        if all_tags:
            # Create a simple tag cloud
            tag_cloud_html = " ".join([
                f'<span style="background-color: #f0f0f0; padding: 5px 10px; margin: 5px; '
                f'border-radius: 10px; font-size: {min(10 + len(tag)*2, 24)}px; display: inline-block;">{tag}</span>'
                for tag in all_tags
            ])
            st.markdown(tag_cloud_html, unsafe_allow_html=True)
            
            # Select a tag to explore
            selected_tag = st.selectbox("Select a tag to explore", [""] + all_tags)
            
            if selected_tag:
                # Fetch content with this tag
                try:
                    response = requests.get(
                        f"{API_ENDPOINT}/knowledge/list", 
                        params={"tags": selected_tag, "limit": 100}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") == "success":
                            tagged_items = result.get("results", [])
                            
                            if tagged_items:
                                st.write(f"Found {len(tagged_items)} items tagged with '{selected_tag}'")
                                
                                # Count by content type
                                content_types = {}
                                for item in tagged_items:
                                    item_type = item.get('content_type', 'unknown')
                                    content_types[item_type] = content_types.get(item_type, 0) + 1
                                
                                # Create a bar chart
                                chart_data = pd.DataFrame({
                                    'Content Type': list(content_types.keys()),
                                    'Count': list(content_types.values())
                                })
                                
                                st.bar_chart(
                                    chart_data.set_index('Content Type')
                                )
                                
                                # Show the items
                                st.subheader("Tagged Content")
                                for item in tagged_items:
                                    item_type = item.get('content_type', 'unknown')
                                    icon = CONTENT_TYPE_ICONS.get(item_type, "📄")
                                    
                                    with st.container():
                                        col1, col2 = st.columns([3, 1])
                                        
                                        with col1:
                                            st.markdown(f"**{icon} {item.get('title', 'Untitled')}**")
                                            if item.get("summary"):
                                                st.write(item.get("summary")[:100] + "..." if len(item.get("summary", "")) > 100 else item.get("summary"))
                                        
                                        with col2:
                                            st.write(f"Type: {item_type}")
                                            st.write(f"Added: {format_date(item.get('created_at', ''))}")
                                            
                                        if st.button(f"View", key=f"tag_view_{item.get('id')}"):
                                            st.session_state.selected_content_id = item.get("id")
                                            st.session_state.view_content_details = True
                                            st.experimental_rerun()
                                        
                                        st.markdown("---")
                            else:
                                st.info(f"No content found with tag '{selected_tag}'")
                except Exception as e:
                    st.error(f"Error fetching tagged content: {str(e)}")
        else:
            st.info("No tags found in the knowledge repository.")

def display_content_details(content_id):
    """Display detailed content information"""
    try:
        response = requests.get(f"{API_ENDPOINT}/knowledge/{content_id}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                content = result.get("content", {})
                content_type = content.get("content_type", "unknown")
                
                # Create a button to go back to the list
                if st.button("Back to list"):
                    st.session_state.view_content_details = False
                    st.experimental_rerun()
                
                # Display content details with appropriate content type icon
                icon = CONTENT_TYPE_ICONS.get(content_type, "📄") 
                st.title(f"{icon} {content.get('title', 'Untitled')}")
                
                # Metadata section with tabs for different aspects
                metadata_tab, summary_tab, entities_tab, full_content_tab = st.tabs([
                    "Metadata", "Summary", "Entities & Tags", "Full Content"
                ])
                
                with metadata_tab:
                    # Content type with colored badge
                    bg_color = CONTENT_TYPE_COLORS.get(content_type, "#f0f0f0")
                    content_type_badge = f'<span style="background-color: {bg_color}; padding: 5px 10px; margin-right: 5px; border-radius: 10px;">{content_type}</span>'
                    st.markdown(content_type_badge, unsafe_allow_html=True)
                    
                    # Metadata columns
                    col1, col2 = st.columns(2)
                    with col1:
                        # Source
                        source = content.get('source', 'Unknown')
                        if source.startswith("http"):
                            st.markdown(f"**Source:** [{source}]({source})")
                        else:
                            st.markdown(f"**Source:** {source}")
                        
                        # Author
                        if content.get("author"):
                            st.markdown(f"**Author:** {content.get('author')}")
                            
                        # Content type specific metadata
                        if content_type == "pdf" and content.get("metadata"):
                            metadata = content.get("metadata")
                            if metadata.get("page_count"):
                                st.markdown(f"**Pages:** {metadata.get('page_count')}")
                                
                        elif content_type == "audio" and content.get("metadata"):
                            metadata = content.get("metadata")
                            if metadata.get("duration"):
                                st.markdown(f"**Duration:** {metadata.get('duration')}")
                            if metadata.get("language"):
                                st.markdown(f"**Language:** {metadata.get('language').title()}")
                    
                    with col2:
                        # Timestamps
                        if content.get("published_date"):
                            st.markdown(f"**Published:** {format_date(content.get('published_date'))}")
                        
                        if content.get("created_at"):
                            st.markdown(f"**Added to Repository:** {format_date(content.get('created_at'))}")
                        
                        if content.get("updated_at"):
                            st.markdown(f"**Last Updated:** {format_date(content.get('updated_at'))}")
                
                with summary_tab:
                    st.subheader("Summary")
                    st.markdown(content.get("summary", "No summary available"))
                
                with entities_tab:
                    # Tags section
                    if content.get("tags"):
                        st.subheader("Tags")
                        tags_html = " ".join([
                            f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>'
                            for tag in content.get("tags", [])
                        ])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    
                    # Entities section
                    if content.get("entities"):
                        st.subheader("Entities")
                        entities = content.get("entities", {})
                        
                        if entities and len(entities) > 0:
                            entity_tabs = st.tabs([category.title() for category in entities.keys()])
                            for i, (category, items) in enumerate(entities.items()):
                                if items:
                                    with entity_tabs[i]:
                                        # Create clickable entity tags
                                        entity_html = " ".join([
                                            f'<span style="background-color: #e6f2ff; padding: 3px 8px; margin-right: 5px; border-radius: 10px; margin-bottom: 5px; display: inline-block;">{item}</span>'
                                            for item in items
                                        ])
                                        st.markdown(entity_html, unsafe_allow_html=True)
                
                with full_content_tab:
                    st.subheader("Full Content")
                    
                    # Handle different content types appropriately
                    if content_type == "url":
                        st.markdown(content.get("full_text", "No full text available"))
                        st.markdown(f"**Original URL:** [{content.get('source')}]({content.get('source')})")
                        
                    elif content_type == "pdf":
                        st.markdown(content.get("full_text", "No full text available"))
                        st.write("PDF content is extracted as text. For original formatting, please refer to the source document.")
                        
                    elif content_type == "audio":
                        st.markdown(content.get("full_text", "No transcription available"))
                        st.write("This is a transcription of the audio content.")
                        
                    else:  # text or other types
                        st.markdown(content.get("full_text", "No full text available"))
                
                # Actions section (export, delete, etc.)
                st.subheader("Actions")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Export options (placeholder)
                    export_format = st.selectbox(
                        "Export Format",
                        ["Text", "Markdown", "JSON"]
                    )
                    
                with col2:
                    # Export button
                    if st.button("Export"):
                        if export_format == "Text":
                            export_data = f"{content.get('title', 'Untitled')}\n\n"
                            export_data += f"Source: {content.get('source', 'Unknown')}\n"
                            if content.get("author"):
                                export_data += f"Author: {content.get('author')}\n"
                            export_data += f"Added: {content.get('created_at', '')}\n\n"
                            export_data += f"Summary:\n{content.get('summary', 'No summary available')}\n\n"
                            export_data += f"Content:\n{content.get('full_text', 'No full text available')}"
                            
                            st.download_button(
                                "Download Text",
                                export_data,
                                file_name=f"{content.get('title', 'content')}.txt",
                                mime="text/plain"
                            )
                        elif export_format == "Markdown":
                            export_data = f"# {content.get('title', 'Untitled')}\n\n"
                            export_data += f"**Source:** {content.get('source', 'Unknown')}\n"
                            if content.get("author"):
                                export_data += f"**Author:** {content.get('author')}\n"
                            export_data += f"**Added:** {content.get('created_at', '')}\n\n"
                            export_data += f"## Summary\n{content.get('summary', 'No summary available')}\n\n"
                            export_data += f"## Content\n{content.get('full_text', 'No full text available')}"
                            
                            st.download_button(
                                "Download Markdown",
                                export_data,
                                file_name=f"{content.get('title', 'content')}.md",
                                mime="text/markdown"
                            )
                        elif export_format == "JSON":
                            export_data = json.dumps(content, indent=2)
                            
                            st.download_button(
                                "Download JSON",
                                export_data,
                                file_name=f"{content.get('title', 'content')}.json",
                                mime="application/json"
                            )
                
                # Delete button
                if st.button("Delete Content", key=f"delete_{content_id}"):
                    if st.session_state.get("confirm_delete") == content_id:
                        # Confirmed delete
                        delete_response = requests.delete(f"{API_ENDPOINT}/knowledge/{content_id}")
                        if delete_response.status_code == 200:
                            st.success("Content deleted successfully!")
                            st.session_state.view_content_details = False
                            # Refresh tag cache after deleting content
                            get_all_tags(force_refresh=True)
                            st.experimental_rerun()
                        else:
                            st.error(f"Error deleting content: {delete_response.text}")
                        # Reset confirmation state
                        st.session_state.confirm_delete = None
                    else:
                        # Ask for confirmation
                        st.session_state.confirm_delete = content_id
                        st.warning("Click delete button again to confirm.")
            else:
                st.error(f"Error: {result.get('message')}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

def search_page():
    st.header("Search Knowledge")
    
    # Two-column layout for search interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Enhanced search form
        with st.form("search_form"):
            search_query = st.text_input("Search Query", help="Enter keywords or phrases to search for")
            
            # Additional filters in expandable section
            with st.expander("Advanced Search Options", expanded=False):
                # Content type filter
                content_type = st.selectbox(
                    "Content Type",
                    ["All", "url", "pdf", "audio", "text"]
                )
                
                # Tags filter
                tags = tag_selector("Filter by Tags")
                
                # Date filter
                date_filter = st.selectbox(
                    "Date Filter",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
                )
                
                if date_filter == "Custom Range":
                    date_col1, date_col2 = st.columns(2)
                    with date_col1:
                        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                    with date_col2:
                        end_date = st.date_input("End Date", datetime.now())
            
            # Search options
            search_options = st.multiselect(
                "Search Options",
                ["Search titles", "Search summaries", "Search full text", "Search entities"],
                default=["Search titles", "Search summaries"]
            )
            
            # Results limit
            limit = st.slider("Max Results", min_value=5, max_value=30, value=10, step=5)
            
            # Submit button
            submitted = st.form_submit_button("Search", use_container_width=True)
    
    with col2:
        # Search tips
        st.subheader("Search Tips")
        st.markdown("""
        * Use **quotes** for exact phrases: `"machine learning"`
        * Use **AND** between terms: `python AND data`
        * Use **OR** to match either term: `python OR java`
        * Use **-** to exclude terms: `python -django`
        """)
        
        # Recent searches (placeholder)
        if 'recent_searches' not in st.session_state:
            st.session_state.recent_searches = []
            
        if len(st.session_state.recent_searches) > 0:
            st.subheader("Recent Searches")
            for i, search in enumerate(st.session_state.recent_searches[-5:]):
                if st.button(search, key=f"recent_{i}"):
                    search_query = search
                    submitted = True
    
    # Create tabs for different result views
    results_tab, visualize_tab = st.tabs(["Search Results", "Visualize"])
    
    # Process search when submitted
    if submitted and search_query:
        # Add to recent searches
        if search_query not in st.session_state.recent_searches:
            st.session_state.recent_searches.append(search_query)
            # Keep only the last 10 searches
            if len(st.session_state.recent_searches) > 10:
                st.session_state.recent_searches.pop(0)
        
        with results_tab:
            with st.spinner("Searching..."):
                try:
                    # Prepare query parameters
                    params = {
                        "query": search_query,
                        "limit": limit
                    }
                    if content_type != "All":
                        params["content_type"] = content_type
                    if tags.strip():
                        params["tags"] = tags
                    
                    # Add date filter if specified
                    date_query = None
                    if date_filter == "Last 7 Days":
                        date_query = (datetime.now() - timedelta(days=7)).isoformat()
                    elif date_filter == "Last 30 Days":
                        date_query = (datetime.now() - timedelta(days=30)).isoformat()
                    elif date_filter == "Last 90 Days":
                        date_query = (datetime.now() - timedelta(days=90)).isoformat()
                    elif date_filter == "Custom Range" and start_date and end_date:
                        date_query = f"{start_date.isoformat()},{end_date.isoformat()}"
                    
                    if date_query:
                        params["date_range"] = date_query
                    
                    # Add search options if specified
                    search_fields = []
                    if "Search titles" in search_options:
                        search_fields.append("title")
                    if "Search summaries" in search_options:
                        search_fields.append("summary")
                    if "Search full text" in search_options:
                        search_fields.append("full_text")
                    if "Search entities" in search_options:
                        search_fields.append("entities")
                    
                    if search_fields:
                        params["fields"] = ",".join(search_fields)
                    
                    # Make API request
                    response = requests.get(f"{API_ENDPOINT}/knowledge/search", params=params)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") == "success":
                            search_results = result.get("results", [])
                            
                            # Store results for visualization tab
                            st.session_state.search_results = search_results
                            
                            # Display search results
                            if search_results:
                                st.success(f"Found {len(search_results)} results for '{search_query}'")
                                
                                for item in search_results:
                                    item_type = item.get('content_type', 'unknown')
                                    bg_color = CONTENT_TYPE_COLORS.get(item_type, "#f0f0f0")
                                    icon = CONTENT_TYPE_ICONS.get(item_type, "📄")
                                    
                                    with st.container():
                                        # Header with colored background
                                        st.markdown(f"""
                                        <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                            <div style="display: flex; justify-content: space-between;">
                                                <h3 style="margin: 0;">{icon} {item.get('title', 'Untitled')}</h3>
                                                <div>{item_type}</div>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        col1, col2, col3 = st.columns([3, 1, 1])
                                        
                                        with col1:
                                            # Show snippet with highlighted search terms
                                            if item.get("snippet"):
                                                # Highlight search terms in the snippet
                                                snippet = item.get("snippet")
                                                # Simple regex-based highlighting
                                                for term in re.findall(r'\w+', search_query):
                                                    if len(term) > 2:  # Only highlight terms with 3+ chars
                                                        pattern = re.compile(f"({term})", re.IGNORECASE)
                                                        snippet = pattern.sub(r"**\1**", snippet)
                                                
                                                st.markdown(snippet)
                                            else:
                                                st.write(item.get("summary", "")[:150] + "...")
                                        
                                        with col2:
                                            # Author if available
                                            if item.get("author"):
                                                st.write(f"Author: {item.get('author')}")
                                            
                                            # Show tags if any (up to 3)
                                            if item.get("tags"):
                                                tags_to_show = item.get("tags")[:3]
                                                tags_html = " ".join([
                                                    f'<span style="background-color: #f0f0f0; padding: 2px 5px; margin-right: 3px; border-radius: 5px; font-size: 0.8em;">{tag}</span>'
                                                    for tag in tags_to_show
                                                ])
                                                if len(item.get("tags")) > 3:
                                                    tags_html += f' <span style="font-size: 0.8em;">+{len(item.get("tags")) - 3} more</span>'
                                                st.markdown(tags_html, unsafe_allow_html=True)
                                        
                                        with col3:
                                            # Show similarity score if available
                                            if item.get("similarity") is not None:
                                                sim_pct = int(item.get("similarity") * 100)
                                                st.progress(item.get("similarity"))
                                                st.write(f"Relevance: {sim_pct}%")
                                            
                                            # Timestamp
                                            if item.get("created_at"):
                                                st.write(f"Added: {format_date(item.get('created_at'))}")
                                        
                                        # View button
                                        if st.button(f"View Details", key=f"search_view_{item.get('id')}"):
                                            # Switch to view page and show this content
                                            st.session_state.page = "View Knowledge"
                                            st.session_state.selected_content_id = item.get("id")
                                            st.session_state.view_content_details = True
                                            st.experimental_rerun()
                                        
                                        st.markdown("---")
                            else:
                                st.info(f"No results found for '{search_query}'")
                                
                                # Suggest alternative searches
                                st.subheader("Suggestions")
                                st.markdown("""
                                * Try using more general terms
                                * Check for spelling errors
                                * Try searching in different content types
                                * Remove filters to broaden your search
                                """)
                        else:
                            st.error(f"Error: {result.get('message')}")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
        
        with visualize_tab:
            # Show visualization of search results if available
            if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
                search_results = st.session_state.search_results
                
                # Create a DataFrame for visualization
                if len(search_results) > 0:
                    # Content type distribution
                    st.subheader("Content Type Distribution")
                    
                    # Count by content type
                    content_types = {}
                    for item in search_results:
                        item_type = item.get('content_type', 'unknown')
                        content_types[item_type] = content_types.get(item_type, 0) + 1
                    
                    # Create chart data
                    chart_data = pd.DataFrame({
                        'Content Type': list(content_types.keys()),
                        'Count': list(content_types.values())
                    })
                    
                    # Display chart
                    st.bar_chart(
                        chart_data.set_index('Content Type')
                    )
                    
                    # Show timeline
                    st.subheader("Content Timeline")
                    
                    # Prepare data
                    timeline_data = []
                    for item in search_results:
                        if item.get("created_at"):
                            try:
                                date = datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')).date()
                                timeline_data.append({
                                    "date": date,
                                    "content_type": item.get("content_type", "unknown")
                                })
                            except:
                                pass
                    
                    if timeline_data:
                        # Convert to DataFrame
                        timeline_df = pd.DataFrame(timeline_data)
                        
                        # Count by date and content type
                        timeline_df = timeline_df.groupby(["date", "content_type"]).size().reset_index(name="count")
                        
                        # Create chart
                        chart = alt.Chart(timeline_df).mark_bar().encode(
                            x="date:T",
                            y="count:Q",
                            color="content_type:N",
                            tooltip=["date", "content_type", "count"]
                        ).properties(height=300)
                        
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("Timeline data not available for these results.")
            else:
                st.info("Search for content to see visualizations.")
    elif submitted:
        st.warning("Please enter a search query.")

def dashboard_page():
    """Dashboard with insights and analytics about the knowledge repository"""
    st.header("Knowledge Dashboard")
    
    # Fetch all content for analytics
    try:
        response = requests.get(f"{API_ENDPOINT}/knowledge/list", params={"limit": 500})
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                content_items = result.get("results", [])
                
                if content_items:
                    # Overview statistics
                    st.subheader("Repository Overview")
                    
                    # Calculate basic stats
                    total_items = len(content_items)
                    content_types = {}
                    tags_count = {}
                    dates = []
                    
                    for item in content_items:
                        # Count by content type
                        item_type = item.get('content_type', 'unknown')
                        content_types[item_type] = content_types.get(item_type, 0) + 1
                        
                        # Count tag occurrences
                        for tag in item.get('tags', []):
                            tags_count[tag] = tags_count.get(tag, 0) + 1
                        
                        # Extract dates for timeline
                        if item.get("created_at"):
                            try:
                                date = datetime.fromisoformat(item.get("created_at").replace('Z', '+00:00')).date()
                                dates.append(date)
                            except:
                                pass
                    
                    # Display metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Items", total_items)
                    with col2:
                        st.metric("Content Types", len(content_types))
                    with col3:
                        st.metric("Unique Tags", len(tags_count))
                    with col4:
                        # Calculate date range
                        if dates:
                            date_range = max(dates) - min(dates)
                            st.metric("Days of Content", date_range.days + 1)
                        else:
                            st.metric("Days of Content", 0)
                    
                    # Content type breakdown
                    st.subheader("Content by Type")
                    
                    # Create chart data
                    types_data = pd.DataFrame({
                        'Content Type': list(content_types.keys()),
                        'Count': list(content_types.values())
                    })
                    
                    # Add color mapping
                    types_data['Color'] = types_data['Content Type'].apply(
                        lambda x: CONTENT_TYPE_COLORS.get(x, "#f0f0f0")
                    )
                    
                    # Display horizontal bar chart
                    chart = alt.Chart(types_data).mark_bar().encode(
                        y=alt.Y('Content Type:N', sort='-x'),
                        x='Count:Q',
                        color=alt.Color('Content Type:N', scale=alt.Scale(
                            domain=list(CONTENT_TYPE_COLORS.keys()),
                            range=list(CONTENT_TYPE_COLORS.values())
                        )),
                        tooltip=['Content Type', 'Count']
                    ).properties(height=200)
                    
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Content timeline
                    st.subheader("Content Growth Over Time")
                    
                    if dates:
                        # Convert to DataFrame
                        dates_df = pd.DataFrame({
                            'date': dates
                        })
                        
                        # Count by date
                        dates_count = dates_df.groupby('date').size().reset_index(name='count')
                        
                        # Calculate cumulative sum
                        dates_count['cumulative'] = dates_count['count'].cumsum()
                        
                        # Create line chart
                        base = alt.Chart(dates_count).encode(
                            x='date:T'
                        )
                        
                        line = base.mark_line(color='#5276A7').encode(
                            y='cumulative:Q'
                        )
                        
                        bars = base.mark_bar(color='#5276A7', opacity=0.3).encode(
                            y='count:Q'
                        )
                        
                        chart = (line + bars).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("Timeline data not available.")
                    
                    # Popular tags
                    st.subheader("Most Common Tags")
                    
                    if tags_count:
                        # Sort tags by frequency
                        sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)
                        top_tags = sorted_tags[:20]  # Show top 20 tags
                        
                        # Create chart data
                        tags_data = pd.DataFrame({
                            'Tag': [tag for tag, _ in top_tags],
                            'Count': [count for _, count in top_tags]
                        })
                        
                        # Display horizontal bar chart
                        chart = alt.Chart(tags_data).mark_bar().encode(
                            y=alt.Y('Tag:N', sort='-x'),
                            x='Count:Q',
                            tooltip=['Tag', 'Count']
                        ).properties(height=min(400, len(top_tags) * 25))
                        
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("No tags found in the repository.")
                    
                    # Recent additions
                    st.subheader("Recently Added Content")
                    
                    # Sort by creation date
                    recent_items = sorted(
                        content_items, 
                        key=lambda x: x.get("created_at", ""), 
                        reverse=True
                    )[:5]  # Show 5 most recent
                    
                    for item in recent_items:
                        item_type = item.get('content_type', 'unknown')
                        icon = CONTENT_TYPE_ICONS.get(item_type, "📄")
                        
                        st.markdown(f"**{icon} {item.get('title', 'Untitled')}** - {format_date(item.get('created_at', ''))}")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if item.get("summary"):
                                st.write(item.get("summary")[:100] + "..." if len(item.get("summary", "")) > 100 else item.get("summary"))
                        with col2:
                            if st.button(f"View", key=f"view_recent_{item.get('id')}"):
                                st.session_state.page = "View Knowledge"
                                st.session_state.selected_content_id = item.get("id")
                                st.session_state.view_content_details = True
                                st.experimental_rerun()
                        
                        st.markdown("---")
                else:
                    st.info("No content found in the knowledge repository.")
                    
                    # Show getting started tips
                    st.subheader("Getting Started")
                    st.markdown("""
                    To start building your knowledge repository:
                    
                    1. Go to the **Process Content** page
                    2. Select a content type (URL, PDF, Text, Audio)
                    3. Upload or paste your content
                    4. Click "Process Content" to analyze and store it
                    
                    Once you have content, this dashboard will show insights and analytics!
                    """)
            else:
                st.error(f"Error: {result.get('message')}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

def settings_page():
    st.header("Settings")
    
    # LLM Settings
    st.subheader("LLM Settings")
    
    # Get current settings
    try:
        # Get local LLM status
        local_status = requests.get(f"{API_ENDPOINT}/test-local")
        local_available = local_status.status_code == 200 and local_status.json().get("status") == "success"
        
        # Get available local models
        models_response = requests.get(f"{API_ENDPOINT}/list-local-models")
        available_models = []
        if models_response.status_code == 200:
            models_data = models_response.json()
            if models_data.get("status") == "success":
                available_models = models_data.get("models", [])
        
        # Get current settings from environment
        current_local_llm = os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"
        current_local_model = os.getenv("LOCAL_LLM_MODEL", "llama3")
        current_cloud_provider = "OpenAI" if os.getenv("OPENAI_API_KEY") else "Anthropic"
    except Exception as e:
        st.warning(f"Could not fetch current settings: {str(e)}")
        current_local_llm = False
        current_cloud_provider = "OpenAI"
        current_local_model = "llama3"
        available_models = []
        local_available = False
    
    # Local LLM settings
    local_settings_tab, cloud_settings_tab, app_settings_tab = st.tabs([
        "Local LLM Settings", "Cloud LLM Settings", "Application Settings"
    ])
    
    with local_settings_tab:
        st.write("Local LLM Status:", "🟢 Available" if local_available else "🔴 Not Available")
        use_local_llm = st.checkbox("Use Local LLM when available", value=current_local_llm)
        
        if use_local_llm:
            if not local_available:
                st.warning("Local LLM is not available. Please make sure Ollama is running.")
                
                st.info("""
                **How to setup Ollama:**
                1. Download Ollama from https://ollama.ai/
                2. Install and run Ollama
                3. Pull models using `ollama pull [model_name]`
                """)
            else:
                if not available_models:
                    st.info("No local models found. The system will attempt to pull the selected model when needed.")
                else:
                    st.success(f"Found {len(available_models)} local models!")
                
                # Extract model names from Ollama's response
                model_names = [m["name"] for m in available_models if isinstance(m, dict) and "name" in m]
                local_model = st.selectbox(
                    "Local Model",
                    ["llama3", "mistral", "llama3:8b", "mistral:7b", "orca-mini"] + model_names,
                    index=0
                )
                
                # Display model info if available
                if model_names and local_model in model_names:
                    model_info = next((m for m in available_models if m["name"] == local_model), None)
                    if model_info:
                        st.write(f"Model size: {model_info.get('size', 'Unknown')}")
                        st.write(f"Modified: {model_info.get('modified', 'Unknown')}")
                
                # Add a button to pull the selected model
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("Pull Selected Model"):
                        with st.spinner(f"Pulling model {local_model}..."):
                            try:
                                response = requests.post(
                                    f"{API_ENDPOINT}/test-local",
                                    json={"model": local_model}
                                )
                                if response.status_code == 200:
                                    st.success(f"Successfully pulled model {local_model}")
                                else:
                                    st.error(f"Failed to pull model: {response.text}")
                            except Exception as e:
                                st.error(f"Error pulling model: {str(e)}")
    
    with cloud_settings_tab:
        # Cloud provider settings
        st.subheader("Preferred Cloud Provider")
        
        cloud_provider = st.selectbox(
            "Provider",
            ["OpenAI", "Anthropic"],
            index=0 if current_cloud_provider == "OpenAI" else 1
        )
        
        if cloud_provider == "OpenAI":
            # OpenAI settings
            st.subheader("OpenAI Settings")
            
            openai_api_key = st.text_input("OpenAI API Key", value="••••••••••••••••••••••", type="password")
            
            model = st.selectbox(
                "Default Model",
                ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                index=0
            )
            
            st.info("""
            OpenAI is used for:
            - Complex entity extraction
            - Summarization of longer documents
            - Advanced content analysis
            """)
        else:  # Anthropic
            # Anthropic settings
            st.subheader("Anthropic Settings")
            
            anthropic_api_key = st.text_input("Anthropic API Key", value="••••••••••••••••••••••", type="password")
            
            model = st.selectbox(
                "Default Model",
                ["claude-3-sonnet", "claude-3-haiku", "claude-3-opus"],
                index=0
            )
            
            st.info("""
            Anthropic Claude is used for:
            - Long-form analysis
            - Nuanced comprehension tasks
            - Detailed content extraction
            """)
    
    with app_settings_tab:
        # Application settings
        st.subheader("Content Processing Settings")
        
        # Content type settings
        st.write("Configure default behavior for content processing:")
        
        default_tab, url_tab, pdf_tab, audio_tab = st.tabs([
            "General Settings", "URL Settings", "PDF Settings", "Audio Settings"
        ])
        
        with default_tab:
            max_content_length = st.number_input(
                "Maximum Content Length",
                min_value=1000,
                max_value=500000,
                value=100000,
                step=10000,
                help="Maximum number of characters to process for any content type"
            )
            
            auto_tag = st.checkbox("Auto-generate tags for all content", value=True)
            auto_entities = st.checkbox("Auto-extract entities for all content", value=True)
        
        with url_tab:
            url_timeout = st.number_input(
                "URL Fetch Timeout (seconds)",
                min_value=5,
                max_value=60,
                value=30,
                step=5,
                help="Maximum time to wait when fetching URL content"
            )
            
            extract_images = st.checkbox("Extract and describe images from URLs", value=False)
        
        with pdf_tab:
            max_pages = st.number_input(
                "Maximum PDF Pages",
                min_value=1,
                max_value=500,
                value=100,
                step=10,
                help="Maximum number of pages to process from PDF documents"
            )
            
            extract_tables = st.checkbox("Extract tables from PDFs", value=True)
        
        with audio_tab:
            max_audio_length = st.number_input(
                "Maximum Audio Length (minutes)",
                min_value=1,
                max_value=180,
                value=60,
                step=5,
                help="Maximum audio duration to process"
            )
            
            transcription_quality = st.select_slider(
                "Transcription Quality",
                options=["Low", "Medium", "High"],
                value="Medium",
                help="Higher quality requires more processing time"
            )
    
    # Save settings button
    if st.button("Save Settings"):
        # In a real app, we would save these settings to a configuration file or database
        # For now, we'll just show a success message
        st.success("Settings saved! Note: In a production environment, these settings would be persisted.")
        
        # Show what would be saved
        settings_data = {
            "LLM_SETTINGS": {
                "LOCAL_LLM_ENABLED": use_local_llm,
                "LOCAL_LLM_MODEL": local_model if use_local_llm else None,
                "CLOUD_PROVIDER": cloud_provider,
                "CLOUD_MODEL": model
            },
            "CONTENT_SETTINGS": {
                "MAX_CONTENT_LENGTH": max_content_length,
                "AUTO_TAG": auto_tag,
                "AUTO_ENTITIES": auto_entities,
                "URL_TIMEOUT": url_timeout,
                "EXTRACT_IMAGES": extract_images,
                "MAX_PDF_PAGES": max_pages,
                "EXTRACT_TABLES": extract_tables,
                "MAX_AUDIO_LENGTH": max_audio_length,
                "TRANSCRIPTION_QUALITY": transcription_quality
            }
        }
        
        st.json(settings_data)

if __name__ == "__main__":
    main()