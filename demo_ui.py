import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import json

# ----- CONFIGURATION -----
# These would normally be in config.py
CONTENT_TYPE_ICONS = {
    "url": "🔗",
    "pdf": "📄",
    "text": "📝",
    "audio": "🔊",
    "social": "📱"
}

CONTENT_TYPE_COLORS = {
    "url": "#c2e0f4",    # Light blue
    "pdf": "#f5d5cb",    # Light coral
    "text": "#d5f5d5",   # Light green
    "audio": "#e6d9f2",  # Light purple
    "social": "#fce8c5"  # Light orange
}

THEME = {
    "primary_color": "#4a6bf2",
    "secondary_color": "#f26e50",
    "background_color": "#ffffff",
    "text_color": "#333333",
    "accent_color": "#50c878",
}

PAGES = {
    "Content Management": [
        {"name": "Process Content", "icon": "🆕", "description": "Process and analyze new content"},
        {"name": "View Knowledge", "icon": "📚", "description": "Browse and search knowledge repository"},
        {"name": "Search", "icon": "🔍", "description": "Advanced search capabilities"}
    ],
    "Prompt Management": [
        {"name": "Component Editor", "icon": "✏️", "description": "Create and edit prompt components"},
        {"name": "Component Library", "icon": "📋", "description": "Browse and manage prompt components"}
    ],
    "System": [
        {"name": "Dashboard", "icon": "📊", "description": "System status and analytics"},
        {"name": "Settings", "icon": "⚙️", "description": "Configure system settings"}
    ]
}

# ----- COMPONENT FUNCTIONS -----
def format_date(date_str):
    """Format date string for display"""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str

def render_tag_collection(tags, bg_color="#f0f0f0", max_display=0):
    """Render a collection of tags with consistent styling."""
    if not tags:
        return
    
    # Handle max_display
    display_tags = tags
    has_more = False
    
    if max_display > 0 and len(tags) > max_display:
        display_tags = tags[:max_display]
        has_more = True
    
    # Create container for tag display
    tag_container = st.container()
    
    with tag_container:
        # Create tag HTML
        tags_html = '<div style="margin-top: 5px; margin-bottom: 10px;">'
        
        for tag in display_tags:
            tags_html += f"""
            <span style="background-color: {bg_color}; color: #333333; 
            padding: 4px 10px; margin-right: 8px; margin-bottom: 8px; border-radius: 12px; 
            display: inline-block; font-size: 0.9em;">
            {tag}
            </span>
            """
        
        # Display indicator for additional tags
        if has_more:
            more_count = len(tags) - max_display
            tags_html += f"""
            <span style="background-color: #e0e0e0; color: #666; 
            padding: 4px 10px; border-radius: 12px; display: inline-block; font-size: 0.8em;">
            +{more_count} more
            </span>
            """
        
        # End HTML
        tags_html += '</div>'
        st.markdown(tags_html, unsafe_allow_html=True)

def status_badge(status, label=None, tooltip=None):
    """Display a status badge with consistent styling."""
    # Define status colors and icons
    status_styles = {
        "success": {"color": "#28a745", "icon": "✓", "bg": "#d4edda"},
        "error": {"color": "#dc3545", "icon": "✕", "bg": "#f8d7da"},
        "warning": {"color": "#ffc107", "icon": "⚠", "bg": "#fff3cd"},
        "info": {"color": "#17a2b8", "icon": "ℹ", "bg": "#d1ecf1"},
        "pending": {"color": "#6c757d", "icon": "⋯", "bg": "#e2e3e5"}
    }
    
    # Get the right style, default to info if not found
    style = status_styles.get(status.lower(), status_styles["info"])
    
    # Use provided label or capitalize the status
    display_label = label if label is not None else status.capitalize()
    
    # Create badge HTML
    tooltip_attr = f'title="{tooltip}"' if tooltip else ''
    badge_html = f"""
    <span style="background-color: {style['bg']}; color: {style['color']}; 
                 padding: 5px 10px; border-radius: 10px; font-size: 0.9em;
                 display: inline-flex; align-items: center; margin-bottom: 10px;" {tooltip_attr}>
        <span style="font-weight: bold; margin-right: 4px;">{style['icon']}</span>
        {display_label}
    </span>
    """
    
    st.markdown(badge_html, unsafe_allow_html=True)

def render_content_card(content, show_summary=True, show_tags=True, max_summary_length=200):
    """Render a content item as a card with standardized styling."""
    # Extract basic content info
    content_id = content.get('id', '')
    title = content.get('title', 'Untitled')
    content_type = content.get('content_type', 'unknown')
    
    # Get styling elements for content type
    bg_color = CONTENT_TYPE_COLORS.get(content_type, "#f0f0f0")
    icon = CONTENT_TYPE_ICONS.get(content_type, "📄")
    
    # Create card container with styling
    with st.container():
        # Header with colored background
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px 5px 0 0; 
                    margin-bottom: 0; border-bottom: 1px solid rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 1.2em;">{icon} {title}</h3>
                <div style="font-size: 0.9em; opacity: 0.8;">{content_type} • {format_date(content.get('created_at', ''))}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Card body with lighter background
        st.markdown(f"""
        <div style="background-color: {bg_color}25; padding: 10px; border-radius: 0 0 5px 5px; 
                    margin-top: 0; margin-bottom: 15px;">
        </div>
        """, unsafe_allow_html=True)
        
        # Content in two columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Show summary if enabled
            if show_summary and content.get("summary"):
                summary = content.get("summary", "")
                if max_summary_length > 0 and len(summary) > max_summary_length:
                    summary = summary[:max_summary_length] + "..."
                st.write(summary)
        
        with col2:
            # Metadata section
            # Author if available
            if content.get("author"):
                st.write(f"Author: {content.get('author')}")
            
            # Source if it's a URL
            source = content.get('source', '')
            if source and source.startswith('http'):
                st.write(f"[Source]({source})")
        
        # Show tags if enabled
        if show_tags and content.get("tags"):
            render_tag_collection(content.get("tags", []), bg_color="#f0f0f0", max_display=5)
        
        # Action buttons
        if st.button(f"View Details", key=f"view_{content_id}"):
            st.session_state.view_content_details = True
            st.session_state.selected_content_id = content_id
        
        # Separator
        st.markdown("---")

def render_sidebar_navigation():
    """Render the sidebar navigation menu with categories and pages."""
    # Make sure page state is initialized
    if 'page' not in st.session_state:
        st.session_state.page = "Process Content"
    
    current_page = st.session_state.page
    
    # Show logo and app title
    st.sidebar.title("BlueAbel AIOS")
    st.sidebar.caption("ContentMind")
    
    # Divider
    st.sidebar.markdown("---")
    
    # Navigation with categories
    for category, pages in PAGES.items():
        st.sidebar.subheader(category)
        
        for page in pages:
            page_name = page["name"]
            page_icon = page.get("icon", "")
            
            # Determine if this is the active page
            is_active = current_page == page_name
            
            # Create a button-like effect for navigation
            if is_active:
                # Active page style
                st.sidebar.markdown(
                    f"""
                    <div style="
                        padding: 8px 15px;
                        border-radius: 5px;
                        background-color: #4a6bf2;
                        color: white;
                        font-weight: bold;
                        display: flex;
                        align-items: center;
                        margin-bottom: 5px;
                    ">
                        <span style="margin-right: 10px;">{page_icon}</span>
                        {page_name}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Create a clickable option
                if st.sidebar.button(
                    f"{page_icon} {page_name}",
                    key=f"nav_{page_name.lower().replace(' ', '_')}"
                ):
                    st.session_state.page = page_name
                    st.rerun()
        
        # Add space between categories
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # Divider and footer
    st.sidebar.markdown("---")
    
    # Quick actions section
    with st.sidebar.expander("Quick Actions", expanded=False):
        if st.button("New Content", key="quick_new_content"):
            st.session_state.page = "Process Content"
            st.rerun()
        
        if st.button("Search Knowledge", key="quick_search"):
            st.session_state.page = "Search"
            st.rerun()
    
    # Status indicator
    st.sidebar.markdown("---")
    
    # Dark mode toggle
    if 'is_dark_mode' not in st.session_state:
        st.session_state.is_dark_mode = False
        
    theme_label = "🌙 Dark Mode" if not st.session_state.is_dark_mode else "☀️ Light Mode"
    if st.sidebar.button(theme_label, key="toggle_theme"):
        st.session_state.is_dark_mode = not st.session_state.is_dark_mode
        st.rerun()

def render_breadcrumbs(additional_crumbs=None):
    """Render breadcrumb navigation at the top of a page."""
    # Create container for breadcrumbs
    breadcrumb_container = st.container()
    
    with breadcrumb_container:
        # Get current page
        current_page = st.session_state.page
        
        # Find category for current page
        current_category = None
        for category, pages in PAGES.items():
            if any(page["name"] == current_page for page in pages):
                current_category = category
                break
        
        # Start building breadcrumbs
        crumbs = [
            {"name": "Home", "is_active": False},
            {"name": current_category, "is_active": False},
            {"name": current_page, "is_active": True}
        ]
        
        # Add any additional breadcrumbs
        if additional_crumbs:
            # Insert additional crumbs before the active page
            crumbs = crumbs[:-1] + additional_crumbs + [crumbs[-1]]
        
        # Build breadcrumb HTML
        breadcrumb_html = '<div style="display: flex; align-items: center; margin-bottom: 15px; font-size: 0.9em;">'
        
        for i, crumb in enumerate(crumbs):
            name = crumb["name"]
            is_active = crumb.get("is_active", False)
            
            # Style based on active state
            if is_active:
                breadcrumb_html += f'<span style="color: #4a6bf2; font-weight: bold;">{name}</span>'
            else:
                breadcrumb_html += f'<span style="color: #666;">{name}</span>'
            
            # Add separator if not the last item
            if i < len(crumbs) - 1:
                breadcrumb_html += '<span style="margin: 0 8px; color: #999;">›</span>'
        
        breadcrumb_html += '</div>'
        
        # Display breadcrumbs
        st.markdown(breadcrumb_html, unsafe_allow_html=True)

def tag_selector(label, all_tags):
    """Interactive tag selector component."""
    # Initialize the session state for selected tags
    key = f"{label}_selected_tags"
    if key not in st.session_state:
        st.session_state[key] = []
    
    # Display currently selected tags
    if st.session_state[key]:
        st.write("Selected tags:")
        render_tag_collection(st.session_state[key])
    
    # Dropdown for tag selection
    available_tags = [tag for tag in all_tags if tag not in st.session_state[key]]
    new_tag = st.selectbox(
        f"{label} (select or type)",
        options=[""] + available_tags,
        key=f"{key}_select"
    )
    
    # Add tag button
    if new_tag and st.button("Add Tag", key=f"{key}_add"):
        if new_tag not in st.session_state[key]:
            st.session_state[key].append(new_tag)
            st.rerun()
    
    # Return the current selection
    return st.session_state[key]

# ----- DEMO DATA -----
def generate_sample_content(count=10):
    """Generate sample content data for demonstration."""
    content_types = list(CONTENT_TYPE_ICONS.keys())
    sample_data = []
    
    for i in range(count):
        content_type = content_types[i % len(content_types)]
        created_date = (datetime.now() - timedelta(days=i)).isoformat()
        
        sample_data.append({
            "id": f"content_{i}",
            "title": f"Sample {content_type.title()} Content {i+1}",
            "content_type": content_type,
            "summary": f"This is a sample summary for {content_type} content. It demonstrates how the content card component displays summaries with uniform styling across different content types.",
            "author": f"Author {i+1}" if i % 3 == 0 else None,
            "source": f"https://example.com/sample/{i}" if content_type == "url" else None,
            "tags": [f"tag{j}" for j in range(1, (i % 5) + 2)],
            "created_at": created_date,
            "updated_at": created_date
        })
    
    return sample_data

# ----- PAGE FUNCTIONS -----
def process_content_page():
    """Render the improved process content page."""
    # Render breadcrumbs
    render_breadcrumbs()

    # Page header with improved styling
    st.header("Process New Content")
    st.caption("Add and analyze content from various sources")
    
    # Content type tabs
    st.markdown("### Content Type")
    
    # Create tabs for content types
    content_types = ["url", "text", "pdf", "audio", "social"]
    content_type_icons = [CONTENT_TYPE_ICONS.get(ct, "📄") for ct in content_types]
    content_type_cols = st.columns(len(content_types))
    
    if 'content_type' not in st.session_state:
        st.session_state.content_type = "url"
    
    selected_type_index = content_types.index(st.session_state.content_type) if st.session_state.content_type in content_types else 0
    
    for i, (col, ct, icon) in enumerate(zip(content_type_cols, content_types, content_type_icons)):
        with col:
            is_selected = i == selected_type_index
            button_style = "primary" if is_selected else "secondary"
            if st.button(f"{icon} {ct.title()}", type=button_style, key=f"content_type_{ct}", use_container_width=True):
                st.session_state.content_type = ct
                st.rerun()
    
    # Content input based on selected type
    content_type = st.session_state.content_type
    
    # Form with the appropriate inputs for the selected content type
    with st.form("content_form"):
        st.markdown(f"### {CONTENT_TYPE_ICONS.get(content_type, '📄')} {content_type.title()} Content")
        
        if content_type == "url":
            content = st.text_input("URL", "https://example.com", placeholder="Enter a URL to process")
            
        elif content_type == "text":
            content = st.text_area("Text Content", "", height=300, placeholder="Paste or type text content here...")
            
            # Optional metadata for text content
            with st.expander("Text Metadata (Optional)", expanded=False):
                title = st.text_input("Title (leave empty to auto-generate)", "")
                source = st.text_input("Source", "Manual Input")
                author = st.text_input("Author", "")
                    
        elif content_type == "pdf":
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_uploader")
            if uploaded_file:
                st.success(f"Uploaded: {uploaded_file.name}")
                
        elif content_type == "audio":
            uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a"], key="audio_uploader")
            if uploaded_file:
                st.success(f"Uploaded: {uploaded_file.name}")

        elif content_type == "social":
            # Social media input
            platform = st.selectbox(
                "Social Media Platform",
                ["Twitter/X", "LinkedIn", "Reddit", "Instagram", "Facebook", "Other"],
                index=0
            )

            # Thread mode toggle
            is_thread = st.checkbox("This is a thread (multiple posts)", value=False)

            if is_thread:
                # Thread collection mode
                st.markdown("##### Thread Collection")
                st.info("Add URLs in order (first post at the top)")
                
                thread_url1 = st.text_input("Post 1", placeholder="Enter URL of first post")
                thread_url2 = st.text_input("Post 2", placeholder="Enter URL of second post")
                st.metric("Thread size", "2 posts")
            else:
                # Single post mode
                content = st.text_input("Social Media URL", "", placeholder="Enter URL of social media post")

            # Optional metadata for social media
            with st.expander("Social Media Metadata (Optional)", expanded=False):
                include_comments = st.checkbox("Include comments/replies (when available)", value=True)
                extract_user = st.checkbox("Extract user information", value=True)

        # Optional tags
        st.markdown("### Suggested Tags")
        st.caption("Optional tags to suggest for the content.")
        
        # Sample tags for demo
        all_tags = ["ai", "machine_learning", "news", "research", "technology", "science", "health", "business"]
        suggested_tags = tag_selector("Suggested Tags", all_tags)
        
        # Advanced options
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
        
        # Submit button
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("Process Content", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("Reset", use_container_width=True)
    
    # Handle form submission for demo
    if submitted:
        # In the demo, we'll just show the processing UI and then some sample results
        st.session_state.processing_demo = True
        
        with st.spinner("Processing content..."):
            # Demo processing status
            progress_bar = st.progress(25)
            st.caption("Preparing content for processing...")
            
            # Update progress 
            progress_bar.progress(50)
            st.caption("Processing content...")
            
            # Update progress again
            progress_bar.progress(75)
            st.caption("Finalizing results...")
            
            # Complete the progress
            progress_bar.progress(100)
            
            # Success message
            status_badge("success", "Processing Complete", "Content processed successfully with AI models")
            
            # Storage success
            status_badge("success", "Content Saved", "Content saved to knowledge repository with ID: content_12345")
        
        # Display demo result
        st.header("Processing Result")
        
        sample_result = {
            "id": "content_12345",
            "title": f"Sample {content_type.title()} Content",
            "content_type": content_type,
            "summary": "This is a sample summary generated from the processed content. It demonstrates how the summary component would display the AI-generated summary with consistent styling.",
            "author": "Demo Author" if content_type == "text" else None,
            "source": "https://example.com/sample/1" if content_type == "url" else None,
            "tags": suggested_tags if suggested_tags else ["ai", "demo", "sample"],
            "created_at": datetime.now().isoformat(),
            "entities": {
                "people": ["John Doe", "Jane Smith"],
                "organizations": ["Example Corp", "Demo Org"],
                "locations": ["New York", "San Francisco"],
                "concepts": ["Machine Learning", "Artificial Intelligence"]
            }
        }
        
        # Create tabs for different views
        meta_tab, summary_tab, entities_tab = st.tabs([
            "Metadata", "Summary", "Entities & Tags"
        ])
        
        with meta_tab:
            # Metadata display
            col1, col2 = st.columns(2)
            with col1:
                icon = CONTENT_TYPE_ICONS.get(content_type, "📄")
                st.subheader(f"{icon} {sample_result.get('title')}")
                
                if sample_result.get("source"):
                    st.markdown(f"**Source:** [{sample_result['source']}]({sample_result['source']})")
                if sample_result.get("author"):
                    st.markdown(f"**Author:** {sample_result['author']}")
            
            with col2:
                st.markdown(f"**Processed:** {format_date(sample_result['created_at'])}")
                st.markdown(f"**Content Type:** {content_type}")
        
        with summary_tab:
            # Summary display
            st.markdown(sample_result['summary'])
        
        with entities_tab:
            # Tags section
            if sample_result.get("tags"):
                st.subheader("Tags")
                render_tag_collection(sample_result["tags"])
            
            # Entities section
            if sample_result.get("entities"):
                st.subheader("Entities")
                
                # Use tabs for entity categories
                entity_tabs = st.tabs([category.title() for category in sample_result["entities"].keys()])
                for i, (category, items) in enumerate(sample_result["entities"].items()):
                    with entity_tabs[i]:
                        render_tag_collection(items, bg_color="#e6f2ff")

def view_knowledge_page():
    """Render the improved knowledge repository page."""
    # Render breadcrumbs
    render_breadcrumbs()
    
    # Page header
    st.header("Knowledge Repository")
    st.caption("Browse and search your processed content")
    
    # Main tabs for different views
    list_tab, calendar_tab, tag_tab = st.tabs(["List View", "Calendar View", "Tag Explorer"])
    
    with list_tab:
        # Filters in expandable section
        with st.expander("Filters", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Content type filter
                content_type = st.selectbox(
                    "Content Type",
                    ["All"] + list(CONTENT_TYPE_ICONS.keys())
                )
            
            with col2:
                # Sample tags for demo
                all_tags = ["ai", "machine_learning", "news", "research", "technology", "science", "health", "business"]
                filter_tags = tag_selector("Filter by Tags", all_tags)
        
        # Generate sample content
        sample_content = generate_sample_content(10)
        
        # Filter based on selected filters
        if content_type != "All":
            sample_content = [item for item in sample_content if item["content_type"] == content_type]
        
        if filter_tags:
            sample_content = [
                item for item in sample_content 
                if any(tag in item.get("tags", []) for tag in filter_tags)
            ]
        
        # Show count
        st.write(f"Showing {len(sample_content)} items")
        
        # Display content list
        for item in sample_content:
            render_content_card(item)
        
        # Display item details if requested
        if hasattr(st.session_state, 'view_content_details') and st.session_state.view_content_details:
            if hasattr(st.session_state, 'selected_content_id'):
                # Find the selected content
                selected_item = next((item for item in sample_content if item["id"] == st.session_state.selected_content_id), None)
                
                if selected_item:
                    st.subheader(f"Content Details: {selected_item['title']}")
                    
                    # Create tabs for different views
                    detail_tabs = st.tabs(["Metadata", "Summary", "Tags & Entities"])
                    
                    with detail_tabs[0]:
                        # Metadata display
                        st.json(selected_item)
                    
                    with detail_tabs[1]:
                        # Summary display
                        st.markdown(selected_item['summary'])
                    
                    with detail_tabs[2]:
                        # Tags and entities
                        st.subheader("Tags")
                        render_tag_collection(selected_item.get("tags", []))
                    
                    # Back button
                    if st.button("Back to list"):
                        st.session_state.view_content_details = False
                        st.rerun()
    
    with calendar_tab:
        st.info("Calendar view coming soon")
    
    with tag_tab:
        st.subheader("Tag Explorer")
        
        # Generate list of all tags
        all_tags = set()
        for item in generate_sample_content(20):
            all_tags.update(item.get("tags", []))
        
        # Create tag cloud HTML
        cloud_html = '<div style="margin: 20px 0;">'
        
        for tag in sorted(list(all_tags)):
            # Random font size between 14 and 24px
            font_size = 14 + (hash(tag) % 10)
            cloud_html += f"""
            <span style="background-color: #f0f0f0; padding: 5px 10px; margin: 5px; 
            border-radius: 10px; font-size: {font_size}px; display: inline-block;">
            {tag}
            </span>
            """
        
        cloud_html += '</div>'
        st.markdown(cloud_html, unsafe_allow_html=True)
        
        # Select a tag to explore
        selected_tag = st.selectbox("Select a tag to explore", [""] + sorted(list(all_tags)))
        
        if selected_tag:
            # Filter content by selected tag
            tagged_items = [
                item for item in generate_sample_content(20)
                if selected_tag in item.get("tags", [])
            ]
            
            st.write(f"Found {len(tagged_items)} items with tag '{selected_tag}'")
            
            # Count by content type
            type_counts = {}
            for item in tagged_items:
                item_type = item.get('content_type', 'unknown')
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            # Create chart data
            chart_data = pd.DataFrame({
                'Content Type': list(type_counts.keys()),
                'Count': list(type_counts.values())
            })
            
            # Display chart
            st.bar_chart(chart_data.set_index('Content Type'))
            
            # Display items
            for item in tagged_items[:5]:  # Show first 5 items
                render_content_card(item)

def search_page():
    """Render the improved search page."""
    # Render breadcrumbs
    render_breadcrumbs()
    
    # Page header
    st.header("Search Knowledge")
    st.caption("Search across all content in your knowledge repository")
    
    # Search form
    with st.form("search_form"):
        search_query = st.text_input("Search Query", help="Enter keywords or phrases to search for")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Content type filter
            content_type = st.selectbox(
                "Content Type",
                ["All"] + list(CONTENT_TYPE_ICONS.keys())
            )
        
        with col2:
            # Sample tags for demo
            all_tags = ["ai", "machine_learning", "news", "research", "technology", "science", "health", "business"]
            search_tags = tag_selector("Filter by Tags", all_tags)
        
        # Search options
        search_options = st.multiselect(
            "Search Options",
            ["Search titles", "Search summaries", "Search full text", "Search entities"],
            default=["Search titles", "Search summaries"]
        )
        
        # Submit button
        submitted = st.form_submit_button("Search", use_container_width=True, type="primary")
    
    # Process search - demo only
    if submitted and search_query:
        st.success(f"Searching for '{search_query}'")
        
        # Filter sample results
        sample_content = generate_sample_content(20)
        
        # Simulate search results - just filter contents containing the search query in title or summary
        search_results = [
            item for item in sample_content
            if (search_query.lower() in item["title"].lower() or 
                search_query.lower() in item["summary"].lower())
        ]
        
        # Filter by content type
        if content_type != "All":
            search_results = [item for item in search_results if item["content_type"] == content_type]
        
        # Filter by tags
        if search_tags:
            search_results = [
                item for item in search_results 
                if any(tag in item.get("tags", []) for tag in search_tags)
            ]
        
        # Display results count
        st.write(f"Found {len(search_results)} results")
        
        # Create tabs for list view and visualization
        results_tab, visualize_tab = st.tabs(["Search Results", "Visualize"])
        
        with results_tab:
            # Display search results
            for item in search_results:
                # Highlight search terms in summary
                summary = item["summary"]
                highlighted_summary = summary.replace(
                    search_query, 
                    f"<span style='background-color: yellow;'>{search_query}</span>"
                )
                
                # Use a custom card with highlighted content
                with st.container():
                    # Header with colored background
                    bg_color = CONTENT_TYPE_COLORS.get(item["content_type"], "#f0f0f0")
                    icon = CONTENT_TYPE_ICONS.get(item["content_type"], "📄")
                    
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <h3 style="margin: 0; font-size: 1.2em;">{icon} {item['title']}</h3>
                            <div style="font-size: 0.9em; opacity: 0.8;">{item['content_type']} • {format_date(item['created_at'])}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display highlighted summary
                    st.markdown(f"<div>{highlighted_summary}</div>", unsafe_allow_html=True)
                    
                    # Display tags
                    if item.get("tags"):
                        render_tag_collection(item["tags"], max_display=3)
                    
                    # View button
                    if st.button(f"View Details", key=f"search_view_{item['id']}"):
                        st.session_state.view_content_details = True
                        st.session_state.selected_content_id = item["id"]
                        st.rerun()
                    
                    st.markdown("---")
        
        with visualize_tab:
            # Simple visualization of search results
            st.subheader("Results Distribution")
            
            # Count by content type
            type_counts = {}
            for item in search_results:
                item_type = item.get('content_type', 'unknown')
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            # Create chart data
            chart_data = pd.DataFrame({
                'Content Type': list(type_counts.keys()),
                'Count': list(type_counts.values())
            })
            
            # Display chart
            st.bar_chart(chart_data.set_index('Content Type'))

def dashboard_page():
    """Render the improved dashboard page."""
    # Render breadcrumbs
    render_breadcrumbs()
    
    # Page header
    st.header("Dashboard")
    st.caption("System overview and analytics")
    
    # Key metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Content", "253", "+14")
    
    with col2:
        st.metric("Active Agents", "3", "")
    
    with col3:
        st.metric("Processing Queue", "0", "-2")
    
    with col4:
        st.metric("Knowledge Tags", "126", "+8")
    
    # Content growth chart
    st.subheader("Content Growth")
    
    # Generate sample date data
    dates = pd.date_range(end=datetime.now(), periods=30)
    cumulative_counts = list(range(220, 220 + 30))
    
    # Create dataframe
    df = pd.DataFrame({
        "date": dates,
        "count": cumulative_counts
    })
    
    # Create Altair chart
    chart = alt.Chart(df).mark_line().encode(
        x='date:T',
        y='count:Q'
    ).properties(height=250)
    
    # Display chart
    st.altair_chart(chart, use_container_width=True)
    
    # Content distribution
    st.subheader("Content by Type")
    
    # Mock data for content types
    type_data = pd.DataFrame({
        'Content Type': list(CONTENT_TYPE_ICONS.keys()),
        'Count': [80, 65, 45, 30, 33]
    })
    
    # Display chart
    st.bar_chart(type_data.set_index('Content Type'))
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Sample activities
    activities = [
        {"action": "Content Added", "details": "PDF document processed", "time": "5 minutes ago"},
        {"action": "Agent Updated", "details": "ContentMind agent configuration changed", "time": "1 hour ago"},
        {"action": "Search Performed", "details": "Query: 'artificial intelligence trends'", "time": "2 hours ago"},
        {"action": "Content Updated", "details": "Tags added to existing content", "time": "3 hours ago"},
        {"action": "System Backup", "details": "Automatic system backup completed", "time": "6 hours ago"}
    ]
    
    # Display activities
    for activity in activities:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{activity['action']}**: {activity['details']}")
        with col2:
            st.caption(activity['time'])
        st.markdown("---")

def settings_page():
    """Render the improved settings page."""
    # Render breadcrumbs
    render_breadcrumbs()
    
    # Page header
    st.header("Settings")
    st.caption("Configure your system preferences")
    
    # Create tabs for different settings sections
    llm_tab, ui_tab, processing_tab = st.tabs(["LLM Settings", "UI Settings", "Processing Settings"])
    
    with llm_tab:
        st.subheader("LLM Provider Settings")
        
        # Provider selection
        provider = st.selectbox(
            "Default Provider",
            ["Auto", "OpenAI", "Anthropic", "Local"],
            index=0
        )
        
        # Model selection based on provider
        if provider == "OpenAI":
            model = st.selectbox(
                "Default Model",
                ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                index=2
            )
        elif provider == "Anthropic":
            model = st.selectbox(
                "Default Model",
                ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                index=1
            )
        elif provider == "Local":
            model = st.selectbox(
                "Default Model",
                ["llama3", "mistral", "llama3:8b", "mistral:7b"],
                index=0
            )
        
        # API keys in password fields
        if provider == "OpenAI":
            st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        elif provider == "Anthropic":
            st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
        
        # Local LLM toggle
        if provider == "Local" or st.checkbox("Enable Local LLM Fallback", value=False):
            st.info("Local LLM will be used when preferred provider is unavailable")
            
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Maximum Tokens", min_value=256, max_value=8192, value=2048, step=256)
            with col2:
                st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
    
    with ui_tab:
        st.subheader("UI Preferences")
        
        # Theme selection
        theme_mode = st.radio(
            "Theme",
            ["Light", "Dark", "System Default"],
            horizontal=True,
            index=0
        )
        
        # UI density
        ui_density = st.select_slider(
            "UI Density",
            options=["Compact", "Normal", "Spacious"],
            value="Normal"
        )
        
        # Date format
        date_format = st.selectbox(
            "Date Format",
            ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "Month DD, YYYY"],
            index=0
        )
        
        # Items per page
        items_per_page = st.slider("Items per page", min_value=5, max_value=50, value=10, step=5)
    
    with processing_tab:
        st.subheader("Content Processing Settings")
        
        # Max content size
        st.number_input("Maximum Content Length (characters)", 
                      min_value=1000, 
                      max_value=1000000, 
                      value=100000,
                      step=10000)
        
        # Processing preferences
        st.checkbox("Auto-generate tags", value=True)
        st.checkbox("Auto-extract entities", value=True)
        st.checkbox("Store full content text", value=True)
        st.checkbox("Enable content versioning", value=False)
    
    # Save button
    if st.button("Save Settings", type="primary"):
        st.success("Settings saved!")
        
        # Show what would be saved
        with st.expander("Saved configuration", expanded=False):
            settings = {
                "llm": {
                    "provider": provider,
                    "model": locals().get("model", "auto"),
                    "temperature": 0.0,
                    "max_tokens": 2048
                },
                "ui": {
                    "theme": theme_mode,
                    "density": ui_density,
                    "date_format": date_format,
                    "items_per_page": items_per_page
                },
                "processing": {
                    "max_content_length": 100000,
                    "auto_tags": True,
                    "auto_entities": True,
                    "store_full_text": True,
                    "enable_versioning": False
                }
            }
            st.json(settings)

# ----- MAIN APPLICATION -----
def main():
    # Set up page config
    st.set_page_config(page_title="BlueAbel AIOS", layout="wide")

    # Apply direct CSS overrides at the very beginning
    st.markdown("""
    <style>
    /* Primary button styling - blue instead of red */
    .stButton button,
    button[kind=primary],
    button[data-baseweb=button][kind=primary] {
        background-color: #4a6bf2 !important;
        border-color: #4a6bf2 !important;
        color: white !important;
        border-radius: 6px;
        font-weight: 500;
    }

    /* Button hover state */
    .stButton button:hover,
    button[kind=primary]:hover,
    button[data-baseweb=button][kind=primary]:hover {
        background-color: #3a5be2 !important;
        border-color: #3a5be2 !important;
    }

    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #4a6bf2 !important;
    }

    /* Make Streamlit tabs use blue */
    .st-emotion-cache-6qob1r.eczjsme3,
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #4a6bf2 !important;
        color: white !important;
    }

    /* Make the tab indicator blue */
    .st-emotion-cache-1n76uvr.eczjsme4,
    div[role="tablist"] [data-testid="stVerticalBlock"] > div:last-child {
        background-color: #4a6bf2 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Apply custom CSS
    custom_css = """
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
    }

    /* Override ALL red buttons to use blue instead with !important */
    button[kind="primary"],
    button[data-baseweb="button"][kind="primary"],
    .stButton button[kind="primary"],
    .stButton button[data-baseweb="button"][kind="primary"] {
        background-color: #4a6bf2 !important;
        border-color: #4a6bf2 !important;
    }

    button[kind="primary"]:hover,
    button[data-baseweb="button"][kind="primary"]:hover,
    .stButton button[kind="primary"]:hover,
    .stButton button[data-baseweb="button"][kind="primary"]:hover {
        background-color: #3a5be2 !important;
        border-color: #3a5be2 !important;
    }

    .stTextInput input, .stSelectbox, .stTextArea textarea {
        border-radius: 6px;
    }

    /* Apply blue to all progress bars */
    .stProgress .st-emotion-cache-17z6hbz,
    .stProgress > div > div > div > div {
        background-color: #4a6bf2 !important;
    }

    /* Tab styling to use blue instead of red for active tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        font-weight: 500;
    }

    /* Make Streamlit tabs use blue */
    .st-emotion-cache-6qob1r.eczjsme3,
    .st-ae.st-af.st-ag.st-ah.st-ai.st-aj.st-bq.st-bp.st-ce,
    .stTabs [aria-selected="true"] {
        background-color: #4a6bf2 !important;
        color: white !important;
    }

    /* Make the tab indicator blue */
    .st-emotion-cache-1n76uvr.eczjsme4,
    .st-bv.st-bp.st-ce,
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #4a6bf2 !important;
    }

    /* Override radio buttons to use blue */
    .st-emotion-cache-1inwz65,
    .st-bs.st-ee.st-eb.st-bp.st-ce.st-e8 {
        color: #4a6bf2 !important;
    }
    """
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "Process Content"
    
    # Render the navigation sidebar
    render_sidebar_navigation()
    
    # Render the selected page
    if st.session_state.page == "Process Content":
        process_content_page()
    elif st.session_state.page == "View Knowledge":
        view_knowledge_page()
    elif st.session_state.page == "Search":
        search_page()
    elif st.session_state.page == "Dashboard":
        dashboard_page()
    elif st.session_state.page == "Settings":
        settings_page()
    else:
        st.info(f"Page '{st.session_state.page}' demo is not yet implemented")

if __name__ == "__main__":
    main()