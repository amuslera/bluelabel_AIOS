"""
Tag component for displaying and interacting with content tags.

This component provides standardized tag rendering and interaction
throughout the BlueAbel AIOS application.
"""

import streamlit as st
from typing import List, Callable, Optional
import re

def render_tag(tag: str, 
               bg_color: str = "#f0f0f0", 
               text_color: str = "#333333",
               is_clickable: bool = False,
               on_click: Optional[Callable[[str], None]] = None,
               key_prefix: str = "") -> None:
    """
    Render a single tag with standardized styling.
    
    Args:
        tag: The tag text to display
        bg_color: Background color for the tag (hex code)
        text_color: Text color for the tag (hex code)
        is_clickable: Whether this tag should be clickable
        on_click: Function to call when tag is clicked (receives tag as argument)
        key_prefix: Prefix for the unique key used in clickable tags
    """
    # Sanitize tag for use in HTML and keys
    safe_tag = re.sub(r'[^a-zA-Z0-9_-]', '_', tag)
    
    if is_clickable and on_click is not None:
        # Create a clickable tag with a hidden button
        tag_html = f"""
        <span id="tag_{safe_tag}" style="background-color: {bg_color}; color: {text_color}; 
        padding: 4px 10px; margin-right: 8px; margin-bottom: 8px; border-radius: 12px; 
        display: inline-block; cursor: pointer; font-size: 0.9em;">
        {tag}
        </span>
        """
        st.markdown(tag_html, unsafe_allow_html=True)
        
        # Hidden button that monitors clicks
        if st.button(f"_{tag}", key=f"{key_prefix}_tag_{safe_tag}", help=f"Click to use tag: {tag}"):
            on_click(tag)
    else:
        # Create a static tag
        tag_html = f"""
        <span style="background-color: {bg_color}; color: {text_color}; 
        padding: 4px 10px; margin-right: 8px; margin-bottom: 8px; border-radius: 12px; 
        display: inline-block; font-size: 0.9em;">
        {tag}
        </span>
        """
        st.markdown(tag_html, unsafe_allow_html=True)

def render_tag_collection(tags: List[str], 
                         bg_color: str = "#f0f0f0", 
                         text_color: str = "#333333",
                         is_clickable: bool = False,
                         on_click: Optional[Callable[[str], None]] = None,
                         key_prefix: str = "",
                         max_display: int = 0) -> None:
    """
    Render a collection of tags with consistent styling.
    
    Args:
        tags: List of tag strings to display
        bg_color: Background color for the tags (hex code)
        text_color: Text color for the tags (hex code)
        is_clickable: Whether tags should be clickable
        on_click: Function to call when a tag is clicked (receives tag as argument)
        key_prefix: Prefix for the unique keys used in clickable tags
        max_display: Maximum tags to display (0 for all)
    """
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
        # Start HTML for tags
        tags_html = '<div style="margin-top: 5px; margin-bottom: 10px;">'
        
        for tag in display_tags:
            render_tag(tag, bg_color, text_color, is_clickable, on_click, key_prefix)
        
        # Display indicator for additional tags
        if has_more:
            more_count = len(tags) - max_display
            more_html = f"""
            <span style="background-color: #e0e0e0; color: #666; 
            padding: 4px 10px; border-radius: 12px; display: inline-block; font-size: 0.8em;">
            +{more_count} more
            </span>
            """
            st.markdown(more_html, unsafe_allow_html=True)
        
        # End HTML
        st.markdown('</div>', unsafe_allow_html=True)

def tag_selector(label: str, 
                all_tags: List[str],
                initial_tags: List[str] = None,
                key: str = "tag_selector") -> List[str]:
    """
    Interactive tag selector component with autocomplete and add/remove functionality.
    
    Args:
        label: Label for the tag selector
        all_tags: List of all available tags for suggestions
        initial_tags: Pre-selected tags
        key: Unique key for the component
        
    Returns:
        List of selected tags
    """
    if initial_tags is None:
        initial_tags = []
    
    # Initialize session state for tag storage
    if f"{key}_selected_tags" not in st.session_state:
        st.session_state[f"{key}_selected_tags"] = initial_tags.copy()
    
    # Create container for tag selection
    tag_container = st.container()
    
    with tag_container:
        # Display currently selected tags
        if st.session_state[f"{key}_selected_tags"]:
            st.write("Selected tags:")
            
            # Display selected tags with remove option
            selected_tags_html = " ".join([
                f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; '
                f'border-radius: 10px;">{tag} '
                f'<span style="cursor: pointer; color: #ff6b6b;" onclick="removeTag(\'{tag}\')">'
                f'×</span></span>'
                for tag in st.session_state[f"{key}_selected_tags"]
            ])
            st.markdown(selected_tags_html, unsafe_allow_html=True)
            
            # JavaScript for removing tags (doesn't work in Streamlit yet)
            # In a real implementation, we'd need to use a workaround
        
        # Dropdown for tag selection
        available_tags = [tag for tag in all_tags if tag not in st.session_state[f"{key}_selected_tags"]]
        new_tag = st.selectbox(
            f"{label} (select or type)",
            options=[""] + available_tags,
            key=f"{key}_tag_select"
        )
        
        # Custom tag input
        custom_tag = st.text_input(
            "Or enter a custom tag",
            key=f"{key}_custom_tag",
            placeholder="Press Enter to add"
        )
        
        # Add selected tag
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if new_tag and st.button("Add Selected Tag", key=f"{key}_add_selected"):
                if new_tag not in st.session_state[f"{key}_selected_tags"]:
                    st.session_state[f"{key}_selected_tags"].append(new_tag)
                    st.experimental_rerun()
        
        with col2:
            if custom_tag and st.button("Add Custom Tag", key=f"{key}_add_custom"):
                if custom_tag not in st.session_state[f"{key}_selected_tags"]:
                    st.session_state[f"{key}_selected_tags"].append(custom_tag)
                    # Reset custom tag input
                    st.session_state[f"{key}_custom_tag"] = ""
                    st.experimental_rerun()
    
    # Button to clear all tags
    if st.session_state[f"{key}_selected_tags"] and st.button("Clear All Tags", key=f"{key}_clear_all"):
        st.session_state[f"{key}_selected_tags"] = []
        st.experimental_rerun()
    
    # Return the current selection
    return st.session_state[f"{key}_selected_tags"]