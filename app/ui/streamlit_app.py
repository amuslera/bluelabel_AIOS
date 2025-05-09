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
                    # Prepare the provider preferences
                    provider_preferences = {
                        "summary": provider_map[summary_provider],
                        "entity_extraction": provider_map[entity_provider],
                        "tagging": provider_map[tag_provider]
                    }
                    
                    # Remove None values
                    provider_preferences = {k: v for k, v in provider_preferences.items() if v is not None}
                    
                    response = requests.post(
                        f"{API_ENDPOINT}/agents/contentmind/process",
                        json={
                            "content_type": content_type, 
                            "content": content,
                            "provider_preferences": provider_preferences
                        }
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
    if result.get("status") == "success":
        st.success("Content processed successfully!")
        
        # Processing Result container
        st.header("Processing Result")
            
        processed = result.get("processed_content", {})
        
        # Title
        st.header(processed.get("title", "Untitled"))
        
        # Metadata
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Source:** [{processed.get('source', 'Unknown')}]({processed.get('source', '#')})")
        with col2:
            processed_time = processed.get('extracted_at', datetime.now().isoformat())
            st.markdown(f"**Processed:** {processed_time}")
        
        # Author and date if available
        if processed.get("author") or processed.get("published_date"):
            col1, col2 = st.columns(2)
            if processed.get("author"):
                with col1:
                    st.markdown(f"**Author:** {processed.get('author')}")
            if processed.get("published_date"):
                with col2:
                    st.markdown(f"**Published:** {processed.get('published_date')}")
        
        # Summary
        st.subheader("Summary")
        st.markdown(processed.get("summary", "No summary available"))
        
        # Show which providers were used
        providers_used = result.get("providers_used", {})
        if providers_used:
            st.subheader("Models Used")
            st.markdown("The following AI models were used to process this content:")
            
            for task, provider in providers_used.items():
                if provider:
                    st.markdown(f"- **{task.replace('_', ' ').title()}**: {provider.title()}")
                else:
                    st.markdown(f"- **{task.replace('_', ' ').title()}**: Not used")
        
        # Tags
        if processed.get("tags"):
            st.subheader("Tags")
            tags_html = " ".join([f"<span style='background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;'>{tag}</span>" for tag in processed.get("tags", [])])
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
                            st.write(", ".join(items))
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
    
    # Get current settings
    try:
        response = requests.get(f"{API_ENDPOINT}/")
        if response.status_code == 200:
            # In a real app, we would have an endpoint to get current settings
            # For now, we'll use default values
            current_local_llm = False
            current_cloud_provider = "OpenAI"
            current_local_model = "llama3"
    except:
        current_local_llm = False
        current_cloud_provider = "OpenAI"
        current_local_model = "llama3"
    
    # Local LLM settings
    use_local_llm = st.checkbox("Use Local LLM when available", value=current_local_llm)
    
    if use_local_llm:
        local_model = st.selectbox(
            "Local Model",
            ["llama3", "mistral", "llama3:8b", "mistral:7b", "orca-mini"],
            index=0
        )
    
    # Cloud provider settings
    st.subheader("Cloud Provider Settings")
    
    cloud_provider = st.selectbox(
        "Preferred Cloud Provider",
        ["OpenAI", "Anthropic"],
        index=0 if current_cloud_provider == "OpenAI" else 1
    )
    
    if cloud_provider == "OpenAI":
        model = st.selectbox(
            "OpenAI Model",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            index=0
        )
    else:  # Anthropic
        model = st.selectbox(
            "Anthropic Model",
            ["claude-3-sonnet", "claude-3-haiku", "claude-3-opus"],
            index=0
        )
    
    st.subheader("Task-Specific Provider Preferences")
    
    summarization_provider = st.selectbox(
        "Summarization Provider",
        ["Auto (Based on Complexity)", "OpenAI", "Anthropic", "Local (if available)"],
        index=0
    )
    
    entity_extraction_provider = st.selectbox(
        "Entity Extraction Provider",
        ["Auto (Based on Complexity)", "OpenAI", "Anthropic", "Local (if available)"],
        index=0
    )
    
    tagging_provider = st.selectbox(
        "Content Tagging Provider",
        ["Auto (Based on Complexity)", "OpenAI", "Anthropic", "Local (if available)"],
        index=0
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
        # In a real app, we would send these settings to the backend
        # For now, we'll just display a success message
        settings_to_update = {
            "LOCAL_LLM_ENABLED": use_local_llm,
            "LOCAL_LLM_MODEL": local_model if use_local_llm else "llama3",
            "CLOUD_PROVIDER": cloud_provider,
            "CLOUD_MODEL": model,
            "SUMMARIZATION_PROVIDER": summarization_provider,
            "ENTITY_EXTRACTION_PROVIDER": entity_extraction_provider,
            "TAGGING_PROVIDER": tagging_provider,
            "MAX_CONTENT_LENGTH": max_content_length
        }
        
        st.success(f"Settings saved! {settings_to_update}\n\nNote: You need to restart the API server for these changes to take effect, or update your .env file directly.")
        
        # Also show the environment variables to set
        st.code(f"""
# Add these to your .env file:
LOCAL_LLM_ENABLED={"true" if use_local_llm else "false"}
LOCAL_LLM_MODEL={local_model if use_local_llm else "llama3"}
PREFERRED_CLOUD_PROVIDER={cloud_provider.upper()}
PREFERRED_MODEL={model}
        """)

if __name__ == "__main__":
    main()