"""
Content card component for displaying content items consistently.

This component provides standardized content card rendering 
throughout the BlueAbel AIOS application.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import os

# Import tag component
from app.ui.components.tag import render_tag_collection

# Import configuration (to be implemented)
# from app.ui.config import CONTENT_TYPE_ICONS, CONTENT_TYPE_COLORS

# Temporary configuration (should be moved to config.py)
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

def format_date(date_str: str) -> str:
    """Format date string for display"""
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except:
        return date_str

def render_content_card(content: Dict[str, Any], 
                        on_view_click: Optional[Callable[[str], None]] = None,
                        show_summary: bool = True,
                        show_tags: bool = True,
                        show_metadata: bool = True,
                        max_summary_length: int = 200,
                        card_key: str = "") -> None:
    """
    Render a content item as a card with standardized styling.
    
    Args:
        content: Content item dictionary with standard keys
        on_view_click: Function to call when view button is clicked (receives content_id)
        show_summary: Whether to display the content summary
        show_tags: Whether to display content tags
        show_metadata: Whether to display additional metadata
        max_summary_length: Maximum length for summary text
        card_key: Unique key prefix for the card elements
    """
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
            if show_metadata:
                # Author if available
                if content.get("author"):
                    st.write(f"Author: {content.get('author')}")
                
                # Source if it's a URL
                source = content.get('source', '')
                if source and source.startswith('http'):
                    st.write(f"[Source]({source})")
                
                # Content type specific metadata
                if content_type == "pdf" and content.get("metadata", {}).get("page_count"):
                    st.write(f"Pages: {content.get('metadata', {}).get('page_count')}")
                elif content_type == "audio" and content.get("metadata", {}).get("duration"):
                    st.write(f"Duration: {content.get('metadata', {}).get('duration')}")
                elif content_type == "social" and content.get("metadata", {}).get("platform"):
                    st.write(f"Platform: {content.get('metadata', {}).get('platform').title()}")
        
        # Show tags if enabled
        if show_tags and content.get("tags"):
            render_tag_collection(
                content.get("tags", []),
                bg_color="#f0f0f0",
                max_display=5
            )
        
        # Action buttons
        if on_view_click and content_id:
            if st.button(f"View Details", key=f"{card_key}_view_{content_id}"):
                on_view_click(content_id)
        
        # Separator
        st.markdown("---")

def render_content_grid(content_items: List[Dict[str, Any]],
                        on_view_click: Optional[Callable[[str], None]] = None,
                        columns: int = 1,
                        show_summary: bool = True,
                        show_tags: bool = True,
                        show_metadata: bool = True,
                        max_summary_length: int = 150,
                        grid_key: str = "") -> None:
    """
    Render multiple content items in a grid layout.
    
    Args:
        content_items: List of content item dictionaries
        on_view_click: Function to call when view button is clicked
        columns: Number of columns in the grid (1-4)
        show_summary: Whether to display content summaries
        show_tags: Whether to display content tags
        show_metadata: Whether to display additional metadata
        max_summary_length: Maximum length for summary text
        grid_key: Unique key prefix for the grid elements
    """
    if not content_items:
        st.info("No content items to display.")
        return
    
    # Ensure columns is between 1 and 4
    columns = max(1, min(4, columns))
    
    # Create column objects
    cols = st.columns(columns)
    
    # Display content items in grid
    for i, item in enumerate(content_items):
        with cols[i % columns]:
            render_content_card(
                content=item,
                on_view_click=on_view_click,
                show_summary=show_summary, 
                show_tags=show_tags,
                show_metadata=show_metadata,
                max_summary_length=max_summary_length,
                card_key=f"{grid_key}_{i}"
            )

def render_content_list(content_items: List[Dict[str, Any]],
                        on_view_click: Optional[Callable[[str], None]] = None,
                        show_summary: bool = True,
                        show_tags: bool = True,
                        show_metadata: bool = True,
                        max_summary_length: int = 200,
                        list_key: str = "") -> None:
    """
    Render multiple content items in a vertical list layout.
    
    Args:
        content_items: List of content item dictionaries
        on_view_click: Function to call when view button is clicked
        show_summary: Whether to display content summaries
        show_tags: Whether to display content tags
        show_metadata: Whether to display additional metadata
        max_summary_length: Maximum length for summary text
        list_key: Unique key prefix for the list elements
    """
    if not content_items:
        st.info("No content items to display.")
        return
    
    # Display each content item
    for i, item in enumerate(content_items):
        render_content_card(
            content=item,
            on_view_click=on_view_click,
            show_summary=show_summary,
            show_tags=show_tags,
            show_metadata=show_metadata,
            max_summary_length=max_summary_length,
            card_key=f"{list_key}_{i}"
        )