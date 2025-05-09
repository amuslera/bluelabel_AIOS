# app/ui/streamlit_app.py
import streamlit as st
import requests
import json
from datetime import datetime

# Set Streamlit page configuration
st.set_page_config(
    page_title="Bluelabel AIOS - ContentMind",
    page_icon="🧠",
    layout="wide"
)

# Define API endpoint (assumes FastAPI is running on port 8000)
API_ENDPOINT = "http://localhost:8000"

def main():
    st.title("Bluelabel AIOS - ContentMind")
    
    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Process Content", "View Knowledge", "Search", "Settings"]
    )
    
    if page == "Process Content":
        process_content_page()
    elif page == "View Knowledge":
        view_knowledge_page()
    elif page == "Search":
        search_page()
    elif page == "Settings":
        settings_page()

def process_content_page():
    st.header("Process New Content")
    
    # Input form
    with st.form("content_form"):
        content_type = st.selectbox(
            "Content Type",
            ["url", "text", "pdf", "audio"]
        )
        
        if content_type == "url":
            content = st.text_input("URL", "https://example.com")
        elif content_type == "text":
            content = st.text_area("Text Content", "Paste your text here...")
        elif content_type == "pdf":
            content = st.file_uploader("Upload PDF", type=["pdf"])
            if content:
                content = "pdf_file_placeholder"  # We'll handle file uploads properly later
        elif content_type == "audio":
            content = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a"])
            if content:
                content = "audio_file_placeholder"  # We'll handle file uploads properly later
        
        submitted = st.form_submit_button("Process Content")
    
    if submitted:
        with st.spinner("Processing content..."):
            # Only URL processing is fully implemented at this point
            if content_type == "url":
                try:
                    response = requests.post(
                        f"{API_ENDPOINT}/agents/contentmind/process",
                        json={"content_type": content_type, "content": content}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        display_processing_result(result)
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to API: {str(e)}")
            else:
                st.warning(f"{content_type.capitalize()} processing is not yet implemented.")

def display_processing_result(result):
    """Display content processing result"""
    st.success("Content processed successfully!")
    
    if result.get("status") == "success":
        with st.expander("Processing Result", expanded=True):
            processed = result.get("processed_content", {})
            
            st.subheader(processed.get("title", "Untitled"))
            
            # Show metadata
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Source:** {processed.get('source', 'Unknown')}")
            with col2:
                st.markdown(f"**Processed:** {processed.get('extracted_at', datetime.now().isoformat())}")
            
            # Show summary
            st.markdown("### Summary")
            st.markdown(processed.get("summary", "No summary available"))
    else:
        st.error(f"Processing error: {result.get('message', 'Unknown error')}")

def view_knowledge_page():
    st.header("Knowledge Repository")
    st.info("Knowledge repository viewing will be implemented in a future update.")

def search_page():
    st.header("Search Knowledge")
    
    search_query = st.text_input("Search Query")
    
    if search_query:
        st.info(f"Search functionality for '{search_query}' will be implemented in a future update.")

def settings_page():
    st.header("Settings")
    
    # LLM Settings
    st.subheader("LLM Settings")
    
    use_local_llm = st.checkbox("Use Local LLM when available", value=False)
    preferred_cloud_provider = st.selectbox(
        "Preferred Cloud Provider",
        ["OpenAI", "Anthropic"]
    )
    
    # Content Processing Settings
    st.subheader("Content Processing Settings")
    
    max_content_length = st.slider(
        "Maximum Content Length (characters)",
        min_value=1000,
        max_value=100000,
        value=50000,
        step=1000
    )
    
    # Save settings button
    if st.button("Save Settings"):
        st.success("Settings saved! (Note: This is a placeholder - settings aren't actually saved yet)")

if __name__ == "__main__":
    main()