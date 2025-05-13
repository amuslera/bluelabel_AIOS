# BlueAbel AIOS - ContentMind main Streamlit app
import streamlit as st
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_app")

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import configuration
from app.ui.config import get_page_config, get_theme, get_custom_css, PAGES

# Set Streamlit page configuration
st.set_page_config(**get_page_config())

# Apply custom CSS
st.markdown(f"<style>{get_custom_css()}</style>", unsafe_allow_html=True)

# CSS to hide duplicate sidebar elements
st.markdown("""
<style>
/* Hide duplicate sidebar elements */
[data-testid="stSidebar"] > div > div > div:nth-child(n+2) {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

def set_page(page_name: str) -> None:
    """
    Set the current page in session state and trigger rerun.
    
    Args:
        page_name: The name of the page to navigate to
    """
    if 'page' in st.session_state and st.session_state.page == page_name:
        return  # Already on this page
    
    st.session_state.page = page_name
    st.experimental_rerun()

def render_sidebar():
    """Render the sidebar navigation menu"""
    st.sidebar.title("ContentMind")
    st.sidebar.markdown("---")
    
    # Display page categories and links
    for category, pages in PAGES.items():
        st.sidebar.subheader(category)
        
        for page in pages:
            page_name = page["name"]
            page_icon = page.get("icon", "")
            
            # Determine if this is the active page
            is_active = st.session_state.page == page_name
            
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
                    key=f"nav_{page_name.lower().replace(' ', '_')}",
                    help=page.get("description", "")
                ):
                    set_page(page_name)

def main():
    """Main application entry point"""
    # Initialize theme
    theme = get_theme(st.session_state.get('is_dark_mode', False))
    
    # Set page title
    st.title("BlueAbel AIOS - ContentMind", anchor=False)
    
    # Initialize session state variables if not already set
    if 'page' not in st.session_state:
        st.session_state.page = "Process Content"
    
    # First render the sidebar - ONLY ONCE
    render_sidebar()
    
    # Route to the appropriate page based on session state
    try:
        current_page = st.session_state.page
        
        if current_page == "Process Content":
            from app.ui.pages.process_content import render_process_content_page
            render_process_content_page()
            
        elif current_page == "View Knowledge":
            st.header("View Knowledge")
            st.info("Knowledge repository view is under development")
            
        elif current_page == "Search":
            st.header("Search")
            st.info("Search functionality is under development")
            
        elif current_page == "Component Editor":
            from app.ui.pages.component_editor import component_editor_page
            component_editor_page()
            
        elif current_page == "Component Library":
            from app.ui.pages.component_library import render_component_library_page
            render_component_library_page()
            
        elif current_page == "Dashboard":
            st.header("Dashboard")
            st.info("Dashboard is under development")
            
        elif current_page == "Settings":
            st.header("Settings")
            st.info("Settings page is under development")
            
        elif current_page == "Google OAuth Setup":
            from app.ui.pages.oauth_setup import render_oauth_setup_page
            render_oauth_setup_page()
            
        elif current_page == "Digest Management":
            from app.ui.pages.digest_management import render_digest_management_page
            render_digest_management_page()
            
        elif current_page == "Prompt Manager":
            from app.ui.pages.prompt_manager import render_prompt_manager_page
            render_prompt_manager_page()
            
        else:
            st.info(f"Page '{current_page}' is not yet implemented")
    
    except Exception as e:
        logger.error(f"Error rendering page {st.session_state.get('page', 'unknown')}: {str(e)}")
        st.error(f"An error occurred while rendering the page: {str(e)}")
        st.info("If this error persists, please check the logs or contact support.")

if __name__ == "__main__":
    main()