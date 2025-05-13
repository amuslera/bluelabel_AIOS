"""
Navigation component for consistent navigation throughout the application.

This module provides standardized navigation components and helpers
for the BlueAbel AIOS application.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
import re

# Import configuration
from app.ui.config import PAGES

def set_page(page_name: str) -> None:
    """
    Set the current page in session state and trigger rerun.
    
    Args:
        page_name: The name of the page to navigate to
    """
    if 'page' in st.session_state and st.session_state.page == page_name:
        return  # Already on this page
        
    st.session_state.page = page_name
    
    # Add to recent pages history
    if 'recent_pages' not in st.session_state:
        st.session_state.recent_pages = []
    
    # Only add to history if it's not already the most recent page
    if not st.session_state.recent_pages or st.session_state.recent_pages[-1] != page_name:
        st.session_state.recent_pages.append(page_name)
        # Keep only the most recent 10 pages
        if len(st.session_state.recent_pages) > 10:
            st.session_state.recent_pages.pop(0)
    
    # Trigger rerun to show the new page
    st.experimental_rerun()

def render_sidebar_navigation() -> None:
    """
    Render the sidebar navigation menu with categories and pages.
    """
    # Make sure page state is initialized
    if 'page' not in st.session_state:
        st.session_state.page = "Process Content"
    
    current_page = st.session_state.page
    
    # Show logo and app title
    st.sidebar.image("https://via.placeholder.com/150x50.png?text=BlueAbel+AIOS", width=200)
    st.sidebar.title("ContentMind")
    
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
                        background-color: rgba(74, 107, 242, 0.1);
                        color: #4a6bf2;
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
                    key=f"nav_{re.sub(r'[^0-9a-zA-Z]+', '_', page_name.lower())}",
                    help=page.get("description", "")
                ):
                    set_page(page_name)
        
        # Add space between categories
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # Divider and footer
    st.sidebar.markdown("---")
    
    # Quick actions section
    with st.sidebar.expander("Quick Actions", expanded=False):
        if st.button("New Content", key="quick_new_content"):
            set_page("Process Content")
        
        if st.button("Search Knowledge", key="quick_search"):
            set_page("Search")
        
        if st.button("New Component", key="quick_new_component"):
            set_page("Component Editor")
            # Set state to create new component
            st.session_state.component_id = None
    
    # Status indicator in sidebar footer
    st.sidebar.markdown("---")
    
    # Only import here to avoid circular imports
    from app.ui.components.status_indicator import api_status_indicator
    
    # Show API status in sidebar footer
    col1, col2 = st.sidebar.columns(2)
    with col1:
        api_status_indicator()
    with col2:
        if 'is_dark_mode' not in st.session_state:
            st.session_state.is_dark_mode = False
            
        theme_label = "🌙 Dark Mode" if not st.session_state.is_dark_mode else "☀️ Light Mode"
        if st.button(theme_label, key="toggle_theme"):
            st.session_state.is_dark_mode = not st.session_state.is_dark_mode

def render_breadcrumbs(additional_crumbs: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Render breadcrumb navigation at the top of a page.
    
    Args:
        additional_crumbs: List of additional breadcrumbs to display after the main one
                           Format: [{"name": "Name", "is_active": False, "on_click": callback}]
    """
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
                breadcrumb_html += f'<span style="color: #666; cursor: pointer;" onclick="handleCrumbClick({i})">{name}</span>'
            
            # Add separator if not the last item
            if i < len(crumbs) - 1:
                breadcrumb_html += '<span style="margin: 0 8px; color: #999;">›</span>'
        
        breadcrumb_html += '</div>'
        
        # Display breadcrumbs
        st.markdown(breadcrumb_html, unsafe_allow_html=True)
        
        # Create hidden buttons for breadcrumb clicks
        for i, crumb in enumerate(crumbs):
            if not crumb.get("is_active", False):
                if st.button(f"_{crumb['name']}", key=f"breadcrumb_{i}", help=f"Navigate to {crumb['name']}", label_visibility="collapsed"):
                    # Handle breadcrumb click
                    if i == 0:  # Home
                        set_page("Process Content")  # Default home page
                    elif i == 1 and current_category:  # Category
                        # Go to first page in category
                        set_page(PAGES[current_category][0]["name"])
                    elif "on_click" in crumb and callable(crumb["on_click"]):
                        crumb["on_click"]()

def render_page_tabs(tabs: List[Dict[str, Any]], 
                     current_tab: str, 
                     on_tab_change: Callable[[str], None],
                     key_prefix: str = "page_tab") -> None:
    """
    Render custom tabs for page-level navigation with active highlighting.
    
    Args:
        tabs: List of tab info dictionaries: [{"name": "Tab1", "icon": "🔍", "key": "tab1"}]
        current_tab: Key of the currently active tab
        on_tab_change: Function to call when tab changes (receives tab key)
        key_prefix: Prefix for tab button keys
    """
    # Create container for tabs
    tabs_container = st.container()
    
    with tabs_container:
        # Create columns for tabs
        cols = st.columns(len(tabs))
        
        for i, tab in enumerate(tabs):
            tab_name = tab["name"]
            tab_icon = tab.get("icon", "")
            tab_key = tab["key"]
            
            with cols[i]:
                # Determine if this is the active tab
                is_active = current_tab == tab_key
                
                # Create tab button with appropriate styling
                if is_active:
                    # Active tab - show as selected but not clickable
                    st.markdown(
                        f"""
                        <div style="
                            text-align: center;
                            padding: 8px 10px;
                            border-radius: 5px 5px 0 0;
                            background-color: #4a6bf2;
                            color: white;
                            font-weight: bold;
                            cursor: default;
                        ">
                            {tab_icon} {tab_name}
                        </div>
                        <div style="
                            height: 3px;
                            background-color: #4a6bf2;
                            margin-bottom: 15px;
                        "></div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Inactive tab - clickable
                    if st.button(
                        f"{tab_icon} {tab_name}",
                        key=f"{key_prefix}_{tab_key}",
                        help=tab.get("description", f"Switch to {tab_name} tab")
                    ):
                        on_tab_change(tab_key)
                    
                    # Add separator line
                    st.markdown(
                        """
                        <div style="
                            height: 1px;
                            background-color: #ddd;
                            margin-bottom: 15px;
                        "></div>
                        """,
                        unsafe_allow_html=True
                    )

def render_recently_viewed(title: str = "Recently Viewed", 
                          limit: int = 5,
                          show_clear_button: bool = True,
                          key_prefix: str = "recent") -> None:
    """
    Render a list of recently viewed items for quick navigation.
    
    Args:
        title: Section title
        limit: Maximum number of items to show
        show_clear_button: Whether to show a clear history button
        key_prefix: Prefix for button keys
    """
    # Check if we have recent views
    if 'recent_views' not in st.session_state:
        st.session_state.recent_views = []
    
    # Only display if we have items
    if not st.session_state.recent_views:
        return
    
    # Create container and title
    with st.container():
        st.subheader(title)
        
        # Get limited list of recent items
        recent_items = st.session_state.recent_views[-limit:]
        
        # Display items in reverse order (most recent first)
        for i, item in enumerate(reversed(recent_items)):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Show item title and type
                icon = item.get("icon", "📄")
                st.markdown(f"**{icon} {item.get('title', 'Untitled')}**")
                st.caption(f"{item.get('type', 'Item')} • {item.get('timestamp', '')}")
            
            with col2:
                # View button
                if st.button("View", key=f"{key_prefix}_view_{i}"):
                    # Handle view action based on item type
                    if item.get("type") == "content":
                        st.session_state.page = "View Knowledge"
                        st.session_state.selected_content_id = item.get("id")
                        st.session_state.view_content_details = True
                        st.experimental_rerun()
                    elif item.get("type") == "component":
                        st.session_state.page = "Component Editor"
                        st.session_state.component_id = item.get("id")
                        st.experimental_rerun()
        
        # Clear history button
        if show_clear_button and st.button("Clear History", key=f"{key_prefix}_clear"):
            st.session_state.recent_views = []
            st.experimental_rerun()