"""
Status indicator component for consistent status and state visualization.

This component provides standardized status indicators and loaders
throughout the BlueAbel AIOS application.
"""

import streamlit as st
from typing import Optional, Dict, Any
import time

def status_badge(status: str, 
                 label: Optional[str] = None, 
                 tooltip: Optional[str] = None) -> None:
    """
    Display a status badge with consistent styling.
    
    Args:
        status: Status name (success, error, warning, info, pending)
        label: Custom label (defaults to status name)
        tooltip: Tooltip text on hover
    """
    # Define status colors and icons
    status_styles = {
        "success": {"color": "#28a745", "icon": "✓", "bg": "#d4edda"},
        "error": {"color": "#dc3545", "icon": "✕", "bg": "#f8d7da"},
        "warning": {"color": "#ffc107", "icon": "⚠", "bg": "#fff3cd"},
        "info": {"color": "#17a2b8", "icon": "ℹ", "bg": "#d1ecf1"},
        "pending": {"color": "#6c757d", "icon": "⋯", "bg": "#e2e3e5"}
    }
    
    # Get the right style, default to info if not found
    style = status_styles.get(status.lower(), status_styles["info"])
    
    # Use provided label or capitalize the status
    display_label = label if label is not None else status.capitalize()
    
    # Create badge HTML
    tooltip_attr = f'title="{tooltip}"' if tooltip else ''
    badge_html = f"""
    <span style="background-color: {style['bg']}; color: {style['color']}; 
                 padding: 3px 8px; border-radius: 10px; font-size: 0.9em;
                 display: inline-flex; align-items: center;" {tooltip_attr}>
        <span style="font-weight: bold; margin-right: 4px;">{style['icon']}</span>
        {display_label}
    </span>
    """
    
    st.markdown(badge_html, unsafe_allow_html=True)

def loading_indicator(message: str = "Loading...", key: Optional[str] = None) -> None:
    """
    Display a custom loading indicator.
    
    Args:
        message: Loading message to display
        key: Unique key for the component
    """
    # Generate a random key if none provided
    if key is None:
        key = f"loading_{int(time.time() * 1000)}"
    
    # Create a pulsing loading indicator
    loading_html = f"""
    <div style="display: flex; align-items: center; margin: 10px 0;">
        <div style="width: 12px; height: 12px; border-radius: 50%; 
                   background-color: #5c6bc0; margin-right: 10px;
                   animation: pulse 1.5s infinite ease-in-out;">
        </div>
        <span style="color: #5c6bc0;">{message}</span>
    </div>
    
    <style>
    @keyframes pulse {{
        0% {{ opacity: 0.3; transform: scale(0.8); }}
        50% {{ opacity: 1.0; transform: scale(1.2); }}
        100% {{ opacity: 0.3; transform: scale(0.8); }}
    }}
    </style>
    """
    
    st.markdown(loading_html, unsafe_allow_html=True)

def processing_status(state: Dict[str, Any], key: str = "process") -> None:
    """
    Display the status of a multi-step process with progress.
    
    Args:
        state: Dictionary with process state information:
            - status: Overall status (pending, processing, completed, failed)
            - progress: Progress value between 0-100
            - step: Current step name
            - steps: Total steps
            - message: Status message
            - details: Optional details or error message
        key: Unique key for the component
    """
    # Extract state information with defaults
    status = state.get("status", "pending")
    progress = state.get("progress", 0)
    current_step = state.get("step", "")
    total_steps = state.get("steps", 1)
    message = state.get("message", "")
    details = state.get("details", "")
    
    # Status badge based on state
    if status == "processing":
        status_badge("pending", label="Processing")
    elif status == "completed":
        status_badge("success", label="Completed")
    elif status == "failed":
        status_badge("error", label="Failed")
    else:
        status_badge("info", label="Pending")
    
    # Progress bar if processing
    if status in ["processing", "completed"]:
        st.progress(int(progress))
    
    # Status message
    if message:
        st.write(message)
    
    # Step indication if provided
    if current_step and total_steps > 1:
        st.write(f"Step {current_step} of {total_steps}")
    
    # Details or error message if available
    if details:
        if status == "failed":
            st.error(details)
        else:
            with st.expander("Details", expanded=False):
                st.write(details)

def api_status_indicator(endpoint: str = "http://localhost:8080/health", key: str = "api_status") -> None:
    """
    Display API connection status indicator.
    
    Args:
        endpoint: Health check endpoint URL
        key: Unique key for the component
    """
    import requests
    
    # Try to fetch API status
    try:
        with st.spinner("Checking API status..."):
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                api_status = "success"
                message = "API Connected"
                details = "The API is operational and responding normally."
            else:
                api_status = "warning"
                message = "API Issues"
                details = f"API responded with status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        api_status = "error"
        message = "API Unreachable"
        details = "Cannot connect to the API. It may be offline."
    except requests.exceptions.Timeout:
        api_status = "warning"
        message = "API Timeout"
        details = "The API is responding too slowly."
    except Exception as e:
        api_status = "error"
        message = "API Error"
        details = f"Error checking API status: {str(e)}"
    
    # Display status
    status_badge(api_status, message, details)
    
    # If warning or error, show more options
    if api_status in ["warning", "error"]:
        if st.button("Retry Connection", key=f"{key}_retry"):
            st.experimental_rerun()