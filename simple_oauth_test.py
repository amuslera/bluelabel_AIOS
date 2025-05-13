#!/usr/bin/env python3
import os
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OAuth credentials
client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8081/gateway/google/callback")

# Use a very basic scope that doesn't require the Gmail API
BASIC_SCOPE = "https://www.googleapis.com/auth/userinfo.email"

# Format OAuth URL
params = {
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "response_type": "code",
    "scope": BASIC_SCOPE,
    "access_type": "offline",
    "prompt": "consent",
    "include_granted_scopes": "true"
}

auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

print(f"Generated Simple OAuth Test URL (basic scope only):\n{auth_url}")
print("\nThis URL uses only the basic email scope to test your OAuth configuration.")
print("If this works while the full Gmail scope doesn't, you need to enable the Gmail API in Google Cloud Console.")