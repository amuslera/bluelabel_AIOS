"""
BlueAbel AIOS - Fresh UI Implementation

This is a completely new implementation with no dependencies on the old UI.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# -----------------------------------------------------------------------------
# STREAMLIT CONFIGURATION - NO IMPORTS FROM ELSEWHERE
# -----------------------------------------------------------------------------

# Page configuration
st.set_page_config(
    page_title="BlueAbel AIOS - Fresh UI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a Bug": None,
        "About": "# BlueAbel AIOS\nA fresh implementation."
    }
)

# Apply custom CSS to clean up the interface
# We're not importing CSS from anywhere else to avoid conflicts
st.markdown("""
<style>
/* Global styles */
body {
    font-family: sans-serif;
}

/* Sidebar styling */
.css-1d391kg {
    padding-top: 2rem;
}

/* Header styling */
h1 {
    font-size: 2rem;
    margin-bottom: 1.5rem;
}

/* Button styling */
.stButton button {
    background-color: #4a6bf2;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 0.3rem;
}

/* Card styling */
.card {
    padding: 1.5rem;
    border-radius: 0.5rem;
    background-color: #f8f9fa;
    margin-bottom: 1rem;
    border: 1px solid #e9ecef;
}

/* Active page indicator */
.active-page {
    font-weight: bold;
    color: #4a6bf2;
}

/* Remove duplicate elements */
[data-testid="stSidebar"] > div > div:nth-child(2) {
    display: none !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# NAVIGATION FUNCTIONS
# -----------------------------------------------------------------------------

def initialize_session_state():
    """Initialize the session state with default values"""
    if 'page' not in st.session_state:
        st.session_state.page = "Home"

def render_navigation():
    """Render the sidebar navigation completely from scratch"""
    # Big title at the top
    st.sidebar.title("BlueAbel AIOS")
    st.sidebar.markdown("---")
    
    # Main navigation section
    st.sidebar.subheader("Main Navigation")
    
    # Use simple radio buttons for navigation
    # This is different from the original UI to avoid conflicts
    page = st.sidebar.radio(
        "Select Page",
        ["Home", "Process Content", "View Content", "Search", "Settings"],
        index=["Home", "Process Content", "View Content", "Search", "Settings"].index(st.session_state.page),
        key="main_nav",
        label_visibility="collapsed"
    )
    
    # Update the session state if the selection changed
    if page != st.session_state.page:
        st.session_state.page = page
        st.experimental_rerun()
    
    # Divider
    st.sidebar.markdown("---")
    
    # Tools section
    st.sidebar.subheader("Tools")
    
    # Simple buttons for tools
    if st.sidebar.button("Component Editor", key="btn_component_editor"):
        st.session_state.page = "Component Editor"
        st.experimental_rerun()
    
    if st.sidebar.button("Component Library", key="btn_component_library"):
        st.session_state.page = "Component Library"
        st.experimental_rerun()
    
    if st.sidebar.button("Digest Management", key="btn_digest_management"):
        st.session_state.page = "Digest Management"
        st.experimental_rerun()
    
    if st.sidebar.button("OAuth Setup", key="btn_oauth_setup"):
        st.session_state.page = "OAuth Setup"
        st.experimental_rerun()

# -----------------------------------------------------------------------------
# PAGE CONTENT FUNCTIONS
# -----------------------------------------------------------------------------

def render_home_page():
    """Render the home page"""
    st.header("Home")
    st.subheader("Welcome to BlueAbel AIOS")
    
    # Info message
    st.info("This is a fresh UI implementation with no dependencies on the old UI.")
    
    # Some example content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Activity")
        st.write("No recent activity to display.")
        
    with col2:
        st.subheader("System Status")
        st.write("All systems operational.")

def render_process_content_page():
    """Render the process content page"""
    st.header("Process Content")
    
    # Tabs for different content types
    tab1, tab2, tab3 = st.tabs(["URL", "Text", "File"])
    
    with tab1:
        st.text_input("URL", placeholder="Enter URL to process...")
        process_option = st.checkbox("Generate digest")
        st.button("Process URL")
    
    with tab2:
        st.text_area("Text Content", placeholder="Enter text to process...", height=200)
        process_option = st.checkbox("Extract entities")
        st.button("Process Text")
    
    with tab3:
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "docx"])
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
        st.button("Process File")

def render_view_content_page():
    """Render the view content page"""
    st.header("View Content")
    
    # Search bar
    search_term = st.text_input("Search", placeholder="Search content...")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.selectbox("Content Type", ["All", "URL", "Text", "File"])
    
    with col2:
        st.selectbox("Sort By", ["Date", "Relevance", "Title"])
    
    with col3:
        st.selectbox("Time Range", ["All Time", "Today", "This Week", "This Month"])
    
    # Placeholder content
    st.info("No content available to display.")

def render_search_page():
    """Render the search page"""
    st.header("Search")
    
    # Search query
    query = st.text_input("Search Query", placeholder="Enter search query...")
    
    # Advanced options
    with st.expander("Advanced Search Options"):
        st.checkbox("Search titles only")
        st.checkbox("Case sensitive")
        st.multiselect("Content Types", ["URL", "Text", "PDF", "Audio"])
    
    if st.button("Search"):
        if query:
            st.success(f"Search query: {query}")
            st.info("No results found.")
        else:
            st.error("Please enter a search query.")

def render_settings_page():
    """Render the settings page"""
    st.header("Settings")
    
    # Tabs for different settings categories
    tab1, tab2, tab3 = st.tabs(["General", "API", "Models"])
    
    with tab1:
        st.checkbox("Dark Mode")
        st.slider("Items Per Page", 5, 50, 10)
    
    with tab2:
        st.text_input("API Endpoint", value="http://localhost:8081")
        st.number_input("Timeout (seconds)", 10, 300, 60)
    
    with tab3:
        st.selectbox("Default Provider", ["OpenAI", "Anthropic", "Local"])
        st.selectbox("Default Model", ["GPT-4", "Claude 3", "Llama 3"])
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

def render_component_editor_page():
    """Render the component editor page"""
    st.header("Component Editor")
    st.info("Component Editor functionality is under development.")

def render_component_library_page():
    """Render the component library page"""
    st.header("Component Library")
    st.info("Component Library functionality is under development.")

def render_digest_management_page():
    """Render the digest management page"""
    st.header("Digest Management")
    st.info("Digest Management functionality is under development.")

def render_oauth_setup_page():
    """Render the OAuth setup page"""
    st.header("OAuth Setup")
    st.info("OAuth Setup functionality is under development.")

# -----------------------------------------------------------------------------
# MAIN APPLICATION
# -----------------------------------------------------------------------------

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Render the navigation sidebar
    render_navigation()
    
    # Render the appropriate page based on the current page in session state
    current_page = st.session_state.page
    
    if current_page == "Home":
        render_home_page()
    elif current_page == "Process Content":
        render_process_content_page()
    elif current_page == "View Content":
        render_view_content_page()
    elif current_page == "Search":
        render_search_page()
    elif current_page == "Settings":
        render_settings_page()
    elif current_page == "Component Editor":
        render_component_editor_page()
    elif current_page == "Component Library":
        render_component_library_page()
    elif current_page == "Digest Management":
        render_digest_management_page()
    elif current_page == "OAuth Setup":
        render_oauth_setup_page()
    else:
        st.error(f"Unknown page: {current_page}")

# -----------------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()