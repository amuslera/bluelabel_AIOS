"""
Streamlit page for managing and viewing content digests.

This module provides a UI for:
- Viewing past digests
- Configuring scheduled digests
- Requesting on-demand digests
"""

import streamlit as st
import requests
import json
from datetime import datetime, time, timedelta
import pandas as pd
from typing import Dict, Any, List, Optional

# Define API endpoint (using the same as in main streamlit_app.py)
import os
API_ENDPOINT = os.environ.get("API_ENDPOINT", "http://localhost:8080")

def format_date(date_str):
    """Format date string for display"""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def digest_management_page():
    """Main digest management page."""
    st.title("Digest Management")
    
    # Create tabs for different digest management functions
    view_tab, schedule_tab, on_demand_tab = st.tabs([
        "View Digests", "Scheduled Digests", "On-Demand Digest"
    ])
    
    with view_tab:
        render_view_digests_tab()
    
    with schedule_tab:
        render_scheduled_digests_tab()
    
    with on_demand_tab:
        render_on_demand_digest_tab()

def render_view_digests_tab():
    """Render the tab for viewing past digests."""
    st.subheader("Past Digests")
    
    # Fetch past digests from the API
    try:
        response = requests.get(f"{API_ENDPOINT}/digests/history")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                digests = result.get("digests", [])
                
                if digests:
                    # Convert to DataFrame for better display
                    df_data = []
                    for digest in digests:
                        df_data.append({
                            "Title": digest.get("title", "Untitled Digest"),
                            "Type": digest.get("digest_type", "Unknown").title(),
                            "Created": format_date(digest.get("created_at", "")),
                            "Items": len(digest.get("content_items", [])),
                            "ID": digest.get("id")
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    # Display as a table
                    st.dataframe(
                        df,
                        column_config={
                            "Title": st.column_config.TextColumn("Title"),
                            "Type": st.column_config.TextColumn("Type"),
                            "Created": st.column_config.TextColumn("Created"),
                            "Items": st.column_config.NumberColumn("Items"),
                            "ID": st.column_config.TextColumn("ID", width="small")
                        },
                        hide_index=True
                    )
                    
                    # Allow selection of a digest to view details
                    selected_digest = st.selectbox(
                        "Select Digest to View",
                        [""] + [digest.get("title", f"Digest {digest.get('id')}") for digest in digests]
                    )
                    
                    if selected_digest:
                        # Find the selected digest
                        selected_id = None
                        for digest in digests:
                            if digest.get("title") == selected_digest or f"Digest {digest.get('id')}" == selected_digest:
                                selected_id = digest.get("id")
                                display_digest_details(digest)
                                break
                else:
                    st.info("No past digests found. Digests will appear here once generated.")
            else:
                st.error(f"Error: {result.get('message')}")
        else:
            st.info("Digest history feature is not available yet. Check back soon!")
    except requests.RequestException:
        st.info("Digest history feature is not available yet. Check back soon!")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def display_digest_details(digest: Dict[str, Any]):
    """Display the details of a selected digest."""
    st.header(digest.get("title", "Untitled Digest"))
    
    # Display digest metadata
    col1, col2 = st.columns(2)
    with col1:
        st.text(f"Type: {digest.get('digest_type', 'Unknown').title()}")
        st.text(f"Generated: {format_date(digest.get('created_at', ''))}")
    
    with col2:
        if digest.get("recipient"):
            st.text(f"Recipient: {digest.get('recipient')}")
        if digest.get("delivery_method"):
            st.text(f"Delivery Method: {digest.get('delivery_method').title()}")
    
    # Display digest content
    st.subheader("Digest Content")
    st.markdown(digest.get("content", "No content available"))
    
    # Display content items included in the digest
    if digest.get("content_items"):
        st.subheader("Included Content")
        
        for item in digest.get("content_items", []):
            with st.expander(item.get("title", "Untitled")):
                st.markdown(f"**Summary:** {item.get('summary', 'No summary available')}")
                
                if item.get("source"):
                    source = item.get("source")
                    if source.startswith("http"):
                        st.markdown(f"**Source:** [{source}]({source})")
                    else:
                        st.markdown(f"**Source:** {source}")
                
                if item.get("content_type"):
                    st.text(f"Type: {item.get('content_type').title()}")
                
                if item.get("tags"):
                    tags_html = " ".join([
                        f'<span style="background-color: #f0f0f0; padding: 3px 8px; margin-right: 5px; border-radius: 10px;">{tag}</span>'
                        for tag in item.get("tags", [])
                    ])
                    st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
    
    # Actions (export, etc.)
    st.subheader("Actions")
    
    export_format = st.selectbox(
        "Export Format",
        ["Text", "Markdown", "JSON"]
    )
    
    if st.button("Export Digest"):
        if export_format == "Text":
            export_data = f"{digest.get('title', 'Untitled Digest')}\n\n"
            export_data += f"Type: {digest.get('digest_type', 'Unknown').title()}\n"
            export_data += f"Generated: {format_date(digest.get('created_at', ''))}\n\n"
            export_data += f"{digest.get('content', 'No content available')}"
            
            st.download_button(
                "Download Text",
                export_data,
                file_name=f"digest_{digest.get('id')}.txt",
                mime="text/plain"
            )
        elif export_format == "Markdown":
            export_data = f"# {digest.get('title', 'Untitled Digest')}\n\n"
            export_data += f"**Type:** {digest.get('digest_type', 'Unknown').title()}\n"
            export_data += f"**Generated:** {format_date(digest.get('created_at', ''))}\n\n"
            export_data += f"{digest.get('content', 'No content available')}"
            
            st.download_button(
                "Download Markdown",
                export_data,
                file_name=f"digest_{digest.get('id')}.md",
                mime="text/markdown"
            )
        elif export_format == "JSON":
            export_data = json.dumps(digest, indent=2)
            
            st.download_button(
                "Download JSON",
                export_data,
                file_name=f"digest_{digest.get('id')}.json",
                mime="application/json"
            )

def render_scheduled_digests_tab():
    """Render the tab for scheduling and managing digest schedules."""
    st.subheader("Scheduled Digests")
    
    # Show existing scheduled digests
    try:
        response = requests.get(f"{API_ENDPOINT}/scheduler/digests")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                scheduled_digests = result.get("scheduled_digests", [])
                
                # Toggle for showing inactive schedules
                show_inactive = st.checkbox("Show inactive schedules", value=False)
                
                # Filter by active status if needed
                if not show_inactive:
                    scheduled_digests = [d for d in scheduled_digests if d.get("active", False)]
                
                if scheduled_digests:
                    st.write(f"Found {len(scheduled_digests)} scheduled digests")
                    
                    # Display as a table
                    df_data = []
                    for digest in scheduled_digests:
                        df_data.append({
                            "Type": digest.get("digest_type", "Unknown").title(),
                            "Schedule": f"{digest.get('schedule_type', 'Unknown').title()} at {digest.get('time', 'Unknown')}",
                            "Next Run": format_date(digest.get("next_run", "")),
                            "Recipient": digest.get("recipient", ""),
                            "Active": "✅" if digest.get("active", False) else "❌",
                            "ID": digest.get("id")
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    st.dataframe(
                        df,
                        column_config={
                            "Type": st.column_config.TextColumn("Type"),
                            "Schedule": st.column_config.TextColumn("Schedule"),
                            "Next Run": st.column_config.TextColumn("Next Run"),
                            "Recipient": st.column_config.TextColumn("Recipient"),
                            "Active": st.column_config.TextColumn("Active"),
                            "ID": st.column_config.TextColumn("ID", width="small")
                        },
                        hide_index=True
                    )
                    
                    # Allow selection of a schedule to edit
                    selected_schedule = st.selectbox(
                        "Select Schedule to Edit",
                        [""] + [f"{d.get('digest_type', 'Unknown').title()} {d.get('schedule_type', '')} ({d.get('id')})" for d in scheduled_digests]
                    )
                    
                    if selected_schedule:
                        # Extract ID from selection
                        schedule_id = selected_schedule.split("(")[-1].rstrip(")")
                        selected_digest = next((d for d in scheduled_digests if d.get("id") == schedule_id), None)
                        
                        if selected_digest:
                            edit_scheduled_digest(selected_digest)
                else:
                    st.info("No scheduled digests found")
            else:
                st.error(f"Error: {result.get('message')}")
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    # Option to create a new scheduled digest
    with st.expander("Create New Scheduled Digest", expanded=len(scheduled_digests) == 0):
        create_scheduled_digest()

def create_scheduled_digest():
    """Form to create a new scheduled digest."""
    with st.form("create_digest_form"):
        st.subheader("New Scheduled Digest")
        
        # Basic settings
        digest_type = st.selectbox(
            "Digest Type",
            ["daily", "weekly", "monthly", "custom"],
            index=0
        )
        
        schedule_type = st.selectbox(
            "Schedule Frequency",
            ["daily", "weekly", "monthly"],
            index=0
        )
        
        # Time selection
        hour = st.slider("Hour (24-hour format)", 0, 23, 8)
        minute = st.slider("Minute", 0, 59, 0, step=5)
        time_str = f"{hour:02d}:{minute:02d}"
        
        # Recipient and delivery settings
        delivery_method = st.selectbox(
            "Delivery Method",
            ["email", "whatsapp", "slack"],
            index=0
        )
        
        recipient = st.text_input(
            "Recipient" + (" (Email)" if delivery_method == "email" else ""),
            placeholder="Enter recipient" + (" email" if delivery_method == "email" else "")
        )
        
        # Content filtering options
        st.subheader("Content Filtering")
        
        # Get all available content types
        content_types = st.multiselect(
            "Content Types to Include",
            ["url", "pdf", "text", "audio", "social"],
            default=["url", "pdf", "text"]
        )
        
        # Get all tags for suggestions
        all_tags = []
        try:
            # Fetch all content
            response = requests.get(f"{API_ENDPOINT}/knowledge/list", params={"limit": 100})
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    content_items = result.get("results", [])
                    # Extract all unique tags
                    all_tags_set = set()
                    for item in content_items:
                        if item.get("tags"):
                            all_tags_set.update(item.get("tags"))
                    all_tags = sorted(list(all_tags_set))
        except:
            pass
        
        # Tag selection
        selected_tags = st.multiselect(
            "Filter by Tags (optional)",
            all_tags
        )
        
        # Submit button
        submitted = st.form_submit_button("Schedule Digest")
    
    if submitted:
        # Validate inputs
        if not recipient:
            st.error("Recipient is required")
        else:
            # Prepare API request
            request_data = {
                "schedule_type": schedule_type,
                "time": time_str,
                "recipient": recipient,
                "digest_type": digest_type,
                "delivery_method": delivery_method,
                "content_types": content_types if content_types else None,
                "tags": selected_tags if selected_tags else None
            }
            
            # Submit to API
            try:
                response = requests.post(
                    f"{API_ENDPOINT}/scheduler/digests",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        st.success(f"Digest scheduled successfully! Next run: {format_date(result.get('next_run', ''))}")
                        # Refresh the page to show the new schedule
                        st.experimental_rerun()
                    else:
                        st.error(f"Error: {result.get('message')}")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Error scheduling digest: {str(e)}")

def edit_scheduled_digest(digest: Dict[str, Any]):
    """Edit an existing scheduled digest."""
    st.subheader(f"Edit Scheduled Digest")
    
    # Get current values
    current_digest_type = digest.get("digest_type", "daily")
    current_schedule_type = digest.get("schedule_type", "daily")
    current_time = digest.get("time", "08:00")
    current_delivery_method = digest.get("delivery_method", "email")
    current_recipient = digest.get("recipient", "")
    current_content_types = digest.get("content_types", [])
    current_tags = digest.get("tags", [])
    current_active = digest.get("active", True)
    
    # Parse time
    try:
        hour, minute = map(int, current_time.split(":"))
    except:
        hour, minute = 8, 0
    
    with st.form("edit_digest_form"):
        # Basic settings
        digest_type = st.selectbox(
            "Digest Type",
            ["daily", "weekly", "monthly", "custom"],
            index=["daily", "weekly", "monthly", "custom"].index(current_digest_type) if current_digest_type in ["daily", "weekly", "monthly", "custom"] else 0
        )
        
        schedule_type = st.selectbox(
            "Schedule Frequency",
            ["daily", "weekly", "monthly"],
            index=["daily", "weekly", "monthly"].index(current_schedule_type) if current_schedule_type in ["daily", "weekly", "monthly"] else 0
        )
        
        # Time selection
        new_hour = st.slider("Hour (24-hour format)", 0, 23, hour)
        new_minute = st.slider("Minute", 0, 59, minute, step=5)
        time_str = f"{new_hour:02d}:{new_minute:02d}"
        
        # Recipient and delivery settings
        delivery_method = st.selectbox(
            "Delivery Method",
            ["email", "whatsapp", "slack"],
            index=["email", "whatsapp", "slack"].index(current_delivery_method) if current_delivery_method in ["email", "whatsapp", "slack"] else 0
        )
        
        recipient = st.text_input(
            "Recipient" + (" (Email)" if delivery_method == "email" else ""),
            value=current_recipient
        )
        
        # Content filtering options
        st.subheader("Content Filtering")
        
        # Get all available content types
        content_types = st.multiselect(
            "Content Types to Include",
            ["url", "pdf", "text", "audio", "social"],
            default=current_content_types
        )
        
        # Get all tags for suggestions
        all_tags = []
        try:
            # Fetch all content
            response = requests.get(f"{API_ENDPOINT}/knowledge/list", params={"limit": 100})
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    content_items = result.get("results", [])
                    # Extract all unique tags
                    all_tags_set = set()
                    for item in content_items:
                        if item.get("tags"):
                            all_tags_set.update(item.get("tags"))
                    all_tags = sorted(list(all_tags_set))
        except:
            pass
        
        # Tag selection
        selected_tags = st.multiselect(
            "Filter by Tags (optional)",
            all_tags,
            default=current_tags
        )
        
        # Active status
        active = st.checkbox("Active", value=current_active)
        
        # Submit button
        submitted = st.form_submit_button("Update Digest Schedule")
    
    if submitted:
        # Validate inputs
        if not recipient:
            st.error("Recipient is required")
        else:
            # Prepare API request
            request_data = {
                "schedule_type": schedule_type,
                "time": time_str,
                "recipient": recipient,
                "digest_type": digest_type,
                "delivery_method": delivery_method,
                "content_types": content_types if content_types else None,
                "tags": selected_tags if selected_tags else None,
                "active": active
            }
            
            # Submit to API
            try:
                response = requests.put(
                    f"{API_ENDPOINT}/scheduler/digests/{digest.get('id')}",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("status") == "success":
                        st.success(f"Digest schedule updated successfully! Next run: {format_date(result.get('next_run', ''))}")
                        # Refresh the page to show the updated schedule
                        st.experimental_rerun()
                    else:
                        st.error(f"Error: {result.get('message')}")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Error updating digest schedule: {str(e)}")
    
    # Add option to delete/cancel
    if st.button("Cancel This Scheduled Digest"):
        try:
            response = requests.delete(f"{API_ENDPOINT}/scheduler/digests/{digest.get('id')}")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    st.success("Digest schedule cancelled successfully!")
                    # Refresh the page
                    st.experimental_rerun()
                else:
                    st.error(f"Error: {result.get('message')}")
            else:
                st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error cancelling digest schedule: {str(e)}")

def render_on_demand_digest_tab():
    """Render the tab for requesting an on-demand digest."""
    st.subheader("Generate On-Demand Digest")
    
    with st.form("on_demand_digest_form"):
        # Digest options
        digest_type = st.selectbox(
            "Digest Type",
            ["daily", "weekly", "monthly", "custom"],
            index=0
        )
        
        # Custom date range for content
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Content From", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("Content To", datetime.now())
        
        # Content filtering options
        st.subheader("Content Filtering")
        
        # Get all available content types
        content_types = st.multiselect(
            "Content Types to Include",
            ["url", "pdf", "text", "audio", "social"],
            default=["url", "pdf", "text"]
        )
        
        # Get all tags for suggestions
        all_tags = []
        try:
            # Fetch all content
            response = requests.get(f"{API_ENDPOINT}/knowledge/list", params={"limit": 100})
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    content_items = result.get("results", [])
                    # Extract all unique tags
                    all_tags_set = set()
                    for item in content_items:
                        if item.get("tags"):
                            all_tags_set.update(item.get("tags"))
                    all_tags = sorted(list(all_tags_set))
        except:
            pass
        
        # Tag selection
        selected_tags = st.multiselect(
            "Filter by Tags (optional)",
            all_tags
        )
        
        # Max items
        max_items = st.slider("Maximum Content Items", 5, 50, 20)
        
        # Delivery options
        st.subheader("Delivery Options")
        delivery_method = st.selectbox(
            "Delivery Method",
            ["view_only", "email", "whatsapp", "slack"],
            index=0
        )
        
        # Show recipient field if not view only
        recipient = None
        if delivery_method != "view_only":
            recipient = st.text_input(
                "Recipient" + (" (Email)" if delivery_method == "email" else ""),
                placeholder="Enter recipient" + (" email" if delivery_method == "email" else "")
            )
        
        # Submit button
        submitted = st.form_submit_button("Generate Digest Now")
    
    if submitted:
        # Validate inputs
        if delivery_method != "view_only" and not recipient:
            st.error("Recipient is required for delivery methods other than 'View Only'")
        else:
            # Show progress
            with st.spinner("Generating digest..."):
                # Prepare API request
                request_data = {
                    "digest_type": digest_type,
                    "date_range": f"{start_date.isoformat()},{end_date.isoformat()}",
                    "content_types": content_types if content_types else None,
                    "tags": selected_tags if selected_tags else None,
                    "max_items": max_items,
                    "delivery_method": delivery_method,
                    "recipient": recipient
                }
                
                # Submit to API
                try:
                    response = requests.post(
                        f"{API_ENDPOINT}/digests/generate",
                        json=request_data
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") == "success":
                            st.success("Digest generated successfully!")
                            
                            # If view_only, show the digest immediately
                            if delivery_method == "view_only" and result.get("digest"):
                                display_digest_details(result.get("digest"))
                            else:
                                delivery_target = recipient or "the specified destination"
                                st.info(f"Digest has been delivered to {delivery_target}")
                        else:
                            st.error(f"Error: {result.get('message')}")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Error generating digest: {str(e)}")

def render_digest_management_page():
    """Main entry point for the digest management page."""
    digest_management_page()

if __name__ == "__main__":
    render_digest_management_page()