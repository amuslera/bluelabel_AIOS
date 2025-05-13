#!/usr/bin/env python3
"""
Direct OAuth Testing Tool for Gmail API

This script implements a minimal standalone OAuth flow to test Google OAuth
without depending on the full application.
"""

import os
import json
import base64
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import requests
import threading
import time

# Load environment variables
load_dotenv()

# OAuth configuration
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8089/callback"  # Using a different port to avoid conflicts
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Gmail API scopes
GMAIL_SCOPES = [
    "https://mail.google.com/",  # Full access to Gmail
    "https://www.googleapis.com/auth/gmail.modify",  # Read/write Gmail but not delete
    "https://www.googleapis.com/auth/gmail.readonly",  # Read-only access
    "https://www.googleapis.com/auth/gmail.send"  # Send emails
]

# For testing with a simpler scope
EMAIL_SCOPE = ["https://www.googleapis.com/auth/userinfo.email"]

# Global variables
received_code = None
auth_complete = threading.Event()

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback requests"""
    
    def do_GET(self):
        """Handle GET requests to the callback URL"""
        global received_code, auth_complete
        
        # Parse the query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if "code" in params:
            # Got the authorization code
            received_code = params["code"][0]
            
            # Send a response to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            response_html = """
            <html>
            <head><title>OAuth Authentication Successful</title></head>
            <body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the application.</p>
                <script>window.close();</script>
            </body>
            </html>
            """
            
            self.wfile.write(response_html.encode())
            
            # Signal that we've received the code
            auth_complete.set()
        elif "error" in params:
            # Authentication error
            error = params["error"][0]
            error_description = params.get("error_description", ["Unknown error"])[0]
            
            # Send an error response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            response_html = f"""
            <html>
            <head><title>OAuth Authentication Error</title></head>
            <body>
                <h1>Authentication Error</h1>
                <p>Error: {error}</p>
                <p>Description: {error_description}</p>
            </body>
            </html>
            """
            
            self.wfile.write(response_html.encode())
            
            # Signal that auth is complete (with an error)
            auth_complete.set()
        else:
            # Unknown response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            response_html = """
            <html>
            <head><title>OAuth Authentication Error</title></head>
            <body>
                <h1>Authentication Error</h1>
                <p>Unknown response from OAuth provider.</p>
            </body>
            </html>
            """
            
            self.wfile.write(response_html.encode())
            
            # Signal that auth is complete (with an error)
            auth_complete.set()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        return


def start_callback_server():
    """Start the callback server"""
    server = HTTPServer(("localhost", 8089), OAuthCallbackHandler)
    print("Started callback server on http://localhost:8089")
    
    # Run the server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server


def get_authorization_url(use_gmail_scopes=True):
    """Generate the authorization URL"""
    if not CLIENT_ID:
        print("Error: GOOGLE_CLIENT_ID not configured")
        return None
    
    # Use Gmail scopes or just email scope for testing
    scopes = GMAIL_SCOPES if use_gmail_scopes else EMAIL_SCOPE
    
    # Build the authorization URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true"
    }
    
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return auth_url


def exchange_code_for_tokens(code):
    """Exchange the authorization code for tokens"""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not configured")
        return None
    
    # Exchange the code for tokens
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code != 200:
        print(f"Error getting tokens: {response.text}")
        return None
    
    return response.json()


def test_gmail_api(access_token):
    """Test the Gmail API with the access token"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get user profile
    user_response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        headers=headers
    )
    
    if user_response.status_code != 200:
        print(f"Error accessing Gmail API: {user_response.text}")
        return False
    
    user_profile = user_response.json()
    print(f"\n✅ Successfully accessed Gmail API for: {user_profile.get('emailAddress')}")
    
    # Try to get labels as a further test
    labels_response = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers=headers
    )
    
    if labels_response.status_code != 200:
        print(f"Error accessing Gmail labels: {labels_response.text}")
        return False
    
    labels = labels_response.json().get("labels", [])
    print(f"Found {len(labels)} Gmail labels")
    
    return True


def create_oauth_token_for_imap(email, access_token):
    """Create an XOAUTH2 token for IMAP authentication"""
    auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_string.encode()).decode()


def main():
    print("==== Google OAuth Direct Testing Tool ====")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not configured")
        print("Please set these in your .env file and try again")
        return
    
    # Ask whether to use Gmail scopes or just email scope
    use_gmail_scopes = input("Test with full Gmail scopes? (y/n, default: y): ").lower() != "n"
    
    # Start the callback server
    server = start_callback_server()
    
    # Get the authorization URL
    auth_url = get_authorization_url(use_gmail_scopes)
    if not auth_url:
        return
    
    print(f"\nAuthorization URL (opening in browser):\n{auth_url}")
    
    # Open the URL in the default browser
    webbrowser.open(auth_url)
    
    # Wait for the callback
    print("\nWaiting for authorization...")
    auth_complete.wait(timeout=300)  # Wait up to 5 minutes
    
    if not received_code:
        print("Error: Did not receive authorization code")
        server.shutdown()
        return
    
    print("\nReceived authorization code")
    
    # Exchange the code for tokens
    tokens = exchange_code_for_tokens(received_code)
    if not tokens:
        server.shutdown()
        return
    
    # Print token information (but mask sensitive data)
    print("\nReceived tokens:")
    token_info = tokens.copy()
    if "access_token" in token_info:
        token_info["access_token"] = token_info["access_token"][:10] + "..." if token_info["access_token"] else "(empty)"
    if "refresh_token" in token_info:
        token_info["refresh_token"] = token_info["refresh_token"][:10] + "..." if token_info["refresh_token"] else "(empty)"
    print(json.dumps(token_info, indent=2))
    
    # Save tokens to a file
    token_file = "config/google_direct_test_tokens.json"
    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    print(f"\nSaved tokens to {token_file}")
    
    # Test Gmail API if using Gmail scopes
    if use_gmail_scopes and "access_token" in tokens:
        print("\nTesting Gmail API access...")
        test_gmail_api(tokens["access_token"])
    
    # Shut down the server
    server.shutdown()
    
    print("\nTest complete!")
    print("If this test was successful but the main application still has issues:")
    print("1. Check that the redirect URI in Google Cloud Console matches exactly: http://localhost:8081/gateway/google/callback")
    print("2. Ensure the Gmail API is enabled in your Google Cloud project")
    print("3. Check that your OAuth consent screen has all required scopes")
    
    # Give instructions for using the tokens with the main application
    if use_gmail_scopes and tokens.get("access_token") and tokens.get("refresh_token"):
        print("\nTo use these tokens with the main application, you can:")
        print("1. Copy the token file to config/google_tokens.json:")
        print(f"   cp {token_file} config/google_tokens.json")
        print("2. Then try configuring and starting the email gateway:")
        print("   curl -X POST \"http://localhost:8081/gateway/email/google\"")


if __name__ == "__main__":
    main()