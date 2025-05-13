# app/services/gateway/google_oauth.py
import base64
import json
import os
import requests
import time
from typing import Dict, Optional, Any, Tuple
from urllib.parse import urlencode

from fastapi import HTTPException

class GoogleOAuth:
    """OAuth2 handler for Google APIs (Gmail, etc.)"""
    
    # Google OAuth endpoints
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    # Get port from environment or use the default port the server is running on
    SERVER_PORT = os.environ.get("SERVER_PORT", "8081")  # Default to 8081 if not set
    REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", f"http://localhost:{SERVER_PORT}/gateway/google/callback")
    
    # OAuth scopes for Gmail access
    GMAIL_SCOPES = [
        "https://mail.google.com/",  # Full access to Gmail
        "https://www.googleapis.com/auth/gmail.modify",  # Read/write Gmail but not delete
        "https://www.googleapis.com/auth/gmail.readonly",  # Read-only access
        "https://www.googleapis.com/auth/gmail.send"  # Send emails
    ]
    
    def __init__(self):
        """Initialize Google OAuth handler"""
        self.client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        self.client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        self.tokens = {}
        
        # Load tokens from file if available
        self._load_tokens()
        
    def _load_tokens(self) -> None:
        """Load OAuth tokens from file"""
        token_file = os.environ.get("GOOGLE_TOKEN_FILE", "config/google_tokens.json")
        try:
            if os.path.exists(token_file):
                with open(token_file, "r") as f:
                    self.tokens = json.load(f)
        except Exception as e:
            print(f"Error loading Google OAuth tokens: {str(e)}")
            self.tokens = {}
            
    def _save_tokens(self) -> None:
        """Save OAuth tokens to file"""
        token_file = os.environ.get("GOOGLE_TOKEN_FILE", "config/google_tokens.json")
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            
            with open(token_file, "w") as f:
                json.dump(self.tokens, f, indent=2)
        except Exception as e:
            print(f"Error saving Google OAuth tokens: {str(e)}")
            
    def get_authorization_url(self) -> str:
        """Generate URL for user to authorize the application"""
        if not self.client_id:
            raise HTTPException(status_code=400, detail="Google OAuth client ID not configured")

        # Ensure all required parameters are included
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",  # This is required
            "scope": " ".join(self.GMAIL_SCOPES),
            "access_type": "offline",  # Get refresh token
            "prompt": "consent",  # Force consent screen for refresh token
            "include_granted_scopes": "true"  # Include previously granted scopes
        }

        # Double check that response_type is included
        if "response_type" not in params or not params["response_type"]:
            params["response_type"] = "code"

        # Build the URL with properly encoded parameters
        auth_url = f"{self.AUTH_URL}?{urlencode(params)}"
        print(f"Generated auth URL: {auth_url}")  # Debug print
        return auth_url
    
    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """Handle OAuth callback with authorization code"""
        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=400, 
                detail="Google OAuth client ID and secret not configured"
            )
            
        # Exchange code for tokens
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get tokens: {response.text}"
            )
            
        # Store the tokens
        self.tokens = response.json()
        self.tokens["created_at"] = int(time.time())
        self._save_tokens()
        
        return {
            "status": "success",
            "message": "Google OAuth authentication successful",
            "expires_in": self.tokens.get("expires_in", 3600)
        }
    
    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        # Check if we have tokens
        if not self.tokens or "access_token" not in self.tokens:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated with Google. Please authorize first."
            )
            
        # Check if token is expired
        created_at = self.tokens.get("created_at", 0)
        expires_in = self.tokens.get("expires_in", 3600)
        current_time = int(time.time())
        
        # If token is expired or about to expire in the next 5 minutes
        if current_time >= (created_at + expires_in - 300):
            # Refresh the token
            if "refresh_token" not in self.tokens:
                raise HTTPException(
                    status_code=401,
                    detail="Refresh token not available. Please reauthorize."
                )
                
            await self._refresh_token()
            
        return self.tokens["access_token"]
    
    async def _refresh_token(self) -> None:
        """Refresh the access token"""
        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=400,
                detail="Google OAuth client ID and secret not configured"
            )
            
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.tokens["refresh_token"],
            "grant_type": "refresh_token"
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail=f"Failed to refresh token: {response.text}"
            )
            
        # Update tokens
        refresh_token = self.tokens.get("refresh_token")  # Keep existing refresh token
        self.tokens.update(response.json())
        self.tokens["created_at"] = int(time.time())
        
        # Make sure we don't lose the refresh token
        if refresh_token and "refresh_token" not in self.tokens:
            self.tokens["refresh_token"] = refresh_token
            
        self._save_tokens()
        
    async def create_imap_access(self) -> Tuple[str, str]:
        """Create IMAP XOAUTH2 string for Gmail access"""
        # First get a valid token
        access_token = await self.get_valid_token()
        
        # Get the email address from the tokens
        email = self.tokens.get("email", os.environ.get("GOOGLE_EMAIL", ""))
        
        # Create the XOAUTH2 string
        auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
        auth_string_b64 = base64.b64encode(auth_string.encode()).decode()
        
        return email, auth_string_b64
    
    async def create_smtp_access(self) -> Tuple[str, str]:
        """Create SMTP XOAUTH2 string for Gmail access"""
        # Uses same format as IMAP XOAUTH2
        return await self.create_imap_access()
    
    async def revoke_tokens(self) -> Dict[str, Any]:
        """Revoke the OAuth tokens"""
        if not self.tokens or "access_token" not in self.tokens:
            return {
                "status": "success", 
                "message": "No active tokens to revoke"
            }
            
        # Revoke access token
        token = self.tokens.get("access_token")
        response = requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token}
        )
        
        # Clear tokens
        self.tokens = {}
        self._save_tokens()
        
        return {
            "status": "success",
            "message": "Tokens revoked successfully"
        }

# Global instance
google_oauth = GoogleOAuth()