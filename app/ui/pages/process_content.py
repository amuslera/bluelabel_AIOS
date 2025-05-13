"""
Process New Content Page

This module provides a Streamlit UI for processing new content through the AI pipeline.
"""

import streamlit as st
import requests
from typing import Dict, Any, Optional
import json
from datetime import datetime
import os
import mimetypes

# API endpoint
API_ENDPOINT = "http://localhost:8081/agents/contentmind/process"

def render_process_content_page():
    """Render the Process New Content page."""
    st.title("Process New Content")
    st.caption("Process new content through the AI pipeline")
    
    # Create tabs for different content types
    email_tab, web_tab, file_tab = st.tabs(["Email Content", "Web Content", "File Content"])
    
    with email_tab:
        render_email_content()
    
    with web_tab:
        render_web_content()
    
    with file_tab:
        render_file_content()

def render_email_content():
    """Render the email content processing form."""
    st.subheader("Process Email Content")
    
    email_content = st.text_area(
        "Email Content",
        placeholder="Paste your email content here...",
        help="Enter the email content to process",
        height=200
    )
    
    if email_content:
        # Processing options
        options = {
            "extract_entities": st.checkbox("Extract Entities", value=True),
            "summarize": st.checkbox("Generate Summary", value=True),
            "analyze_sentiment": st.checkbox("Analyze Sentiment", value=True),
            "generate_response": st.checkbox("Generate Response", value=False),
            "extract_metadata": st.checkbox("Extract Email Metadata", value=True)
        }
        
        if st.button("Process Email"):
            try:
                # Prepare metadata
                metadata = {
                    "source": "email",
                    "content_type": "email",
                    "processing_options": options
                }
                
                # Send request to API
                response = requests.post(
                    API_ENDPOINT,
                    json={
                        "content_type": "email",
                        "content": email_content,
                        "metadata": metadata
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    display_processing_results(result)
                else:
                    st.error(f"Error processing email: {response.text}")
                    
            except Exception as e:
                st.error(f"Error processing email: {str(e)}")
    else:
        st.info("Please enter email content to process")

def render_web_content():
    """Render the web content processing form."""
    st.subheader("Process Web Content")
    
    url = st.text_input(
        "Enter URL",
        placeholder="https://example.com/article",
        help="Enter the URL of the web page to process"
    )
    
    if url:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            st.warning("Please enter a valid URL starting with http:// or https://")
            return
            
        # Processing options
        options = {
            "extract_entities": st.checkbox("Extract Entities", value=True),
            "summarize": st.checkbox("Generate Summary", value=True),
            "analyze_sentiment": st.checkbox("Analyze Sentiment", value=True),
            "generate_response": st.checkbox("Generate Response", value=False),
            "extract_metadata": st.checkbox("Extract Metadata", value=True)
        }
        
        if st.button("Process URL"):
            try:
                # Prepare metadata
                metadata = {
                    "source": url,
                    "content_type": "web",
                    "processing_options": options
                }
                
                # Send request to API
                response = requests.post(
                    API_ENDPOINT,
                    json={
                        "content_type": "web",
                        "content": url,
                        "metadata": metadata
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    display_processing_results(result)
                else:
                    st.error(f"Error processing URL: {response.text}")
                    
            except Exception as e:
                st.error(f"Error processing URL: {str(e)}")
    else:
        st.info("Please enter a URL to process")

def render_file_content():
    """Render the file content processing form."""
    st.subheader("Process File Content")
    
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["txt", "pdf", "docx", "md"],
        help="Supported formats: TXT, PDF, DOCX, MD"
    )
    
    if uploaded_file:
        # Get file metadata
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        file_type = os.path.splitext(file_name)[1].lower().lstrip('.')
        
        # Display file info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"File: {file_name}")
        with col2:
            st.info(f"Size: {file_size / 1024:.1f} KB")
        
        # Processing options
        options = {
            "extract_entities": st.checkbox("Extract Entities", value=True),
            "summarize": st.checkbox("Generate Summary", value=True),
            "analyze_sentiment": st.checkbox("Analyze Sentiment", value=True),
            "generate_response": st.checkbox("Generate Response", value=False)
        }
        
        if st.button("Process File"):
            try:
                # Prepare the file for upload
                files = {
                    'file': (file_name, uploaded_file, mimetypes.guess_type(file_name)[0] or 'application/octet-stream')
                }
                
                # Prepare metadata
                metadata = {
                    "source": file_name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "processing_options": options
                }
                
                # Send request to API
                response = requests.post(
                    API_ENDPOINT,
                    files=files,
                    data={"metadata": json.dumps(metadata)}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    display_processing_results(result)
                else:
                    st.error(f"Error processing file: {response.text}")
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    else:
        st.info("Please upload a file to process")

def display_processing_results(result: Dict[str, Any]):
    """Display the processing results in a structured format."""
    if result.get("status") == "success":
        # Check if fallback was used
        fallback_used = False
        fallback_reason = ""
        providers_used = result.get("providers_used", {})

        # Check if any provider is 'fallback'
        for task, provider in providers_used.items():
            if provider == "fallback":
                fallback_used = True
                fallback_reason = result.get("fallback_reason", "")
                break

        # Display success message with caveat if fallback was used
        if fallback_used:
            st.warning("Content processed with fallback mechanisms due to LLM unavailability.")
            if fallback_reason:
                st.info(f"Reason: {fallback_reason}")
        else:
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
        elif storage_info.get("error"):
            st.warning(f"Content could not be stored: {storage_info.get('error')}")

        # Get processed content
        processed = result.get("processed_content", {})
        content_type = result.get("content_type", "unknown")

        # Title with content type icon
        st.header(f"📄 {processed.get('title', 'Untitled')}")

        # Metadata in expandable section
        with st.expander("Metadata", expanded=True):
            # Basic metadata (source, processing time)
            col1, col2 = st.columns(2)
            with col1:
                source = processed.get('source', 'Unknown')
                # Only make URLs clickable
                if source and isinstance(source, str) and source.startswith("http"):
                    st.markdown(f"**Source:** [{source}]({source})")
                else:
                    st.markdown(f"**Source:** {source}")
            with col2:
                processed_time = processed.get('extracted_at', datetime.now().isoformat())
                st.markdown(f"**Processed:** {processed_time}")

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
                        st.markdown(f"**Published:** {processed.get('published_date')}")

        # Summary section
        st.subheader("Summary")
        summary = processed.get("summary", "No summary available")
        st.markdown(summary)

        if fallback_used and "summary" in providers_used and providers_used["summary"] == "fallback":
            st.info("⚠️ This is a basic summary generated without LLM processing")

        # Show which providers were used
        with st.expander("AI Models Used", expanded=fallback_used):
            providers_used = result.get("providers_used", {})
            if providers_used:
                st.markdown("The following AI models were used to process this content:")

                for task, provider in providers_used.items():
                    if provider:
                        provider_display = provider.title()
                        if provider == "fallback":
                            provider_display = "⚠️ Fallback (No LLM)"
                        st.markdown(f"- **{task.replace('_', ' ').title()}**: {provider_display}")
                    else:
                        st.markdown(f"- **{task.replace('_', ' ').title()}**: Not used")

                if fallback_used:
                    st.warning("""
                    ⚠️ Fallback processing was used because the LLM service was not available.
                    This results in simpler processing with less advanced features.
                    The system will automatically attempt to use LLM services when they become available.
                    """)

        # Tags
        if processed.get("tags"):
            st.subheader("Tags")
            tags_html = " ".join([
                f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>'
                for tag in processed.get("tags", [])
            ])
            st.markdown(tags_html, unsafe_allow_html=True)

            if fallback_used and "tagging" in providers_used and providers_used["tagging"] == "fallback":
                st.info("⚠️ These are basic tags extracted without LLM processing")

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

            # Show fallback notice if applicable
            if fallback_used and "entity_extraction" in providers_used and providers_used["entity_extraction"] == "fallback":
                st.info("⚠️ Entity extraction was limited due to LLM unavailability")

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
        # Handle different types of errors
        error_message = result.get('message', 'Unknown error')
        st.error(f"Error processing content: {error_message}") 