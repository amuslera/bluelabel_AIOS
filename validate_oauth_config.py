#!/usr/bin/env python3
import os
import json
import requests
import urllib.parse
from dotenv import load_dotenv

def main():
    """Validate OAuth configuration and credentials"""
    # Load environment variables
    load_dotenv()
    
    # Get OAuth credentials
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8081/gateway/google/callback")
    
    if not client_id or not client_secret:
        print("ERROR: Client ID or Client Secret not set in environment variables")
        return
    
    print("=== OAuth Configuration Validation ===")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {'*' * len(client_secret)}")
    print(f"Redirect URI: {redirect_uri}")
    
    # Gmail OAuth scopes
    GMAIL_SCOPES = [
        "https://mail.google.com/",  # Full access to Gmail
        "https://www.googleapis.com/auth/gmail.modify",  # Read/write Gmail but not delete
        "https://www.googleapis.com/auth/gmail.readonly",  # Read-only access
        "https://www.googleapis.com/auth/gmail.send"  # Send emails
    ]
    
    print("\nConfigured OAuth Scopes:")
    for scope in GMAIL_SCOPES:
        print(f"- {scope}")
    
    # Format OAuth URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true"
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    print(f"\nFull OAuth URL:")
    print(auth_url)
    
    # Check token file
    token_file = os.environ.get("GOOGLE_TOKEN_FILE", "config/google_tokens.json")
    print(f"\nToken file path: {token_file}")
    
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                tokens = json.load(f)
                # Mask sensitive data
                if "access_token" in tokens:
                    tokens["access_token"] = tokens["access_token"][:5] + "..." if tokens["access_token"] else "(empty)"
                if "refresh_token" in tokens:
                    tokens["refresh_token"] = tokens["refresh_token"][:5] + "..." if tokens["refresh_token"] else "(empty)"
                print(f"Token file exists with content: {json.dumps(tokens, indent=2)}")
        except Exception as e:
            print(f"Error reading token file: {str(e)}")
    else:
        print(f"Token file does not exist")
    
    # Check the redirect URL validation with Google
    print("\n=== OAuth Redirect URI Validation ===")
    try:
        # Make a direct request to the OAuth server (this is just for testing - will fail with 400)
        test_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "email",  # Minimal scope for test
        }
        
        test_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(test_params)}"
        response = requests.get(test_url, allow_redirects=False)
        
        # We expect a redirect to Google's login page, not a 400 error
        if response.status_code == 302 or response.status_code == 200:
            print("Redirect URI validation successful! The URI is properly registered.")
        elif "redirect_uri_mismatch" in response.text:
            print("ERROR: Redirect URI mismatch. Check that the URI is exactly registered in Google Cloud Console.")
            print("\nCommon issues:")
            print("1. URI in Google Cloud Console doesn't match exactly: http://localhost:8081/gateway/google/callback")
            print("2. If using a non-standard port, make sure it's explicitly allowed in the Google Cloud Console settings")
            print("3. Check for trailing slashes - they matter in OAuth URIs")
        elif "invalid_request" in response.text:
            print("ERROR: Invalid request. Check client ID and other parameters.")
        else:
            print(f"Unexpected response (status {response.status_code}):")
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
    
    except Exception as e:
        print(f"Error validating redirect URI: {str(e)}")
    
    print("\n=== Recommendations ===")
    print("1. Verify in Google Cloud Console that the exact redirect URI is registered:")
    print(f"   {redirect_uri}")
    print("2. Ensure the Gmail API is enabled for this project in Google Cloud Console")
    print("3. If using a test OAuth app, add your Google account as a test user")
    print("4. For non-verified apps, accept the unverified app warning during testing")

if __name__ == "__main__":
    main()