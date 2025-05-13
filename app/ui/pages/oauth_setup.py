"""
Google OAuth Setup Page

This module provides a Streamlit UI for setting up and managing Google OAuth
for the email gateway.
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, Any, Optional

# API endpoint
API_ENDPOINT = "http://localhost:8081"  # Update as needed

def render_oauth_setup_page():
    """Render the Google OAuth setup page."""
    st.write("Loaded OAuth page: start")
    st.title("Google OAuth Setup")
    st.write("Loaded OAuth page: after title")
    st.caption("Configure Google OAuth for secure email access")
    
    # Create tabs for different sections
    tabs = st.tabs(["Setup Guide", "Status & Management"])
    st.write("Loaded OAuth page: after tabs")
    
    with tabs[0]:
        st.write("Loaded OAuth page: in Setup Guide tab")
        render_setup_guide()
    
    with tabs[1]:
        st.write("Loaded OAuth page: in Status & Management tab")
        render_status_management()

def render_setup_guide():
    """Render the setup guide section."""
    st.markdown("""
    ### Step 1: Create Google Cloud Project
    
    1. Go to [Google Cloud Console](https://console.cloud.google.com/)
    2. Create a new project or select an existing one
    3. Give your project a meaningful name, like "Bluelabel AIOS Email Gateway"
    
    ### Step 2: Configure OAuth Consent Screen
    
    1. In Google Cloud Console, go to **APIs & Services > OAuth consent screen**
    2. Select **External** user type
    3. Fill in the required information:
       - App name: "Bluelabel AIOS"
       - User support email: Your email
       - Developer contact information: Your email
    4. Add the following scopes:
       - `https://mail.google.com/`
       - `https://www.googleapis.com/auth/gmail.modify`
       - `https://www.googleapis.com/auth/gmail.readonly`
       - `https://www.googleapis.com/auth/gmail.send`
    5. Add your email as a test user
    
    ### Step 3: Create OAuth Credentials
    
    1. Go to **APIs & Services > Credentials**
    2. Click **Create Credentials > OAuth client ID**
    3. Select **Web application** as the application type
    4. Add authorized redirect URI: `http://localhost:8081/gateway/google/callback`
    5. Click **Create** and note your Client ID and Client Secret
    """)
    
    # OAuth credentials form
    with st.form("oauth_credentials"):
        st.subheader("Enter OAuth Credentials")
        
        client_id = st.text_input("Client ID", placeholder="Enter your Google OAuth Client ID")
        client_secret = st.text_input("Client Secret", type="password", placeholder="Enter your Google OAuth Client Secret")
        
        submitted = st.form_submit_button("Save Credentials")
        
        if submitted:
            if not client_id or not client_secret:
                st.error("Please enter both Client ID and Client Secret")
            else:
                try:
                    response = requests.post(
                        f"{API_ENDPOINT}/gateway/google/config",
                        json={
                            "client_id": client_id,
                            "client_secret": client_secret
                        }
                    )
                    
                    if response.status_code == 200:
                        st.success("Credentials saved successfully!")
                        st.info("Click the 'Start Authentication' button in the Status & Management tab to begin the OAuth flow.")
                    else:
                        st.error(f"Error saving credentials: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def render_status_management():
    """Render the status and management section."""
    st.subheader("OAuth Status")
    
    # Check current status
    try:
        status_response = requests.get(f"{API_ENDPOINT}/gateway/google/status")
        status_data = status_response.json()
        
        # Display status
        status = status_data.get("status", "unknown")
        message = status_data.get("message", "")
        
        if status == "authenticated":
            st.success("✅ " + message)
            
            # Show token expiration
            expires_in = status_data.get("expires_in", 0)
            if expires_in:
                st.info(f"Token expires in {expires_in} seconds")
            
            # Show management options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Refresh Token"):
                    try:
                        response = requests.post(f"{API_ENDPOINT}/gateway/google/refresh")
                        if response.status_code == 200:
                            st.success("Token refreshed successfully!")
                            st.experimental_rerun()
                        else:
                            st.error(f"Error refreshing token: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            with col2:
                if st.button("Revoke Access"):
                    try:
                        response = requests.post(f"{API_ENDPOINT}/gateway/google/revoke")
                        if response.status_code == 200:
                            st.success("Access revoked successfully!")
                            st.experimental_rerun()
                        else:
                            st.error(f"Error revoking access: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        elif status == "expired":
            st.warning("⚠️ " + message)
            if st.button("Refresh Token"):
                try:
                    response = requests.post(f"{API_ENDPOINT}/gateway/google/refresh")
                    if response.status_code == 200:
                        st.success("Token refreshed successfully!")
                        st.experimental_rerun()
                    else:
                        st.error(f"Error refreshing token: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        else:
            st.info("Not authenticated")
            
            # Get auth URL
            try:
                auth_response = requests.get(f"{API_ENDPOINT}/gateway/google/auth")
                auth_data = auth_response.json()
                auth_url = auth_data.get("auth_url")
                
                if auth_url:
                    st.markdown("### Start Authentication")
                    st.markdown(f"[Click here to start Google authentication]({auth_url})")
                    st.info("After authenticating, you'll be redirected back to this page.")
            except Exception as e:
                st.error(f"Error getting auth URL: {str(e)}")
    
    except Exception as e:
        st.error(f"Error checking status: {str(e)}")
    
    # Show configuration status
    st.subheader("Configuration Status")
    
    try:
        # Check if credentials are configured
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        
        if client_id and client_secret:
            st.success("✅ OAuth credentials are configured")
        else:
            st.warning("⚠️ OAuth credentials are not configured")
            st.info("Please enter your credentials in the Setup Guide tab")
    
    except Exception as e:
        st.error(f"Error checking configuration: {str(e)}") 