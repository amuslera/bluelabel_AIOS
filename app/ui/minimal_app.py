"""
Minimal Streamlit app for BlueAbel AIOS
This is a completely standalone implementation with no dependencies on other UI files
"""

import streamlit as st

# Set page configuration with minimal settings
st.set_page_config(
    page_title="BlueAbel AIOS",
    page_icon="🧠",
    layout="wide"
)

# Main app
def main():
    # Header
    st.title("BlueAbel AIOS - Minimal View")
    
    # Sidebar
    st.sidebar.title("Navigation")
    
    # Simple navigation
    page = st.sidebar.radio(
        "Select Page",
        ["Home", "Process Content", "View Content", "Settings"],
        label_visibility="collapsed"
    )
    
    # Display different pages based on selection
    if page == "Home":
        st.header("Home")
        st.write("Welcome to the BlueAbel AIOS system.")
        st.info("This is a minimal UI implementation to bypass the duplicate rendering issues.")
        
    elif page == "Process Content":
        st.header("Process Content")
        
        # Simple content processing form
        content_type = st.selectbox("Content Type", ["URL", "Text", "File"])
        
        if content_type == "URL":
            st.text_input("Enter URL")
        elif content_type == "Text":
            st.text_area("Enter Text")
        else:
            st.file_uploader("Upload File")
            
        st.button("Process")
        
    elif page == "View Content":
        st.header("Content Repository")
        
        # Placeholder content
        st.write("No content available yet.")
        
    elif page == "Settings":
        st.header("Settings")
        
        # Simple settings
        st.checkbox("Dark Mode")
        st.selectbox("Default Model", ["GPT-4", "Claude", "Local"])
        
        st.button("Save Settings")

# Run the app
if __name__ == "__main__":
    main()