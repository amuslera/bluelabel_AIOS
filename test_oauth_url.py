#!/usr/bin/env python3
import os
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OAuth credentials
client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8081/gateway/google/callback")

# Gmail OAuth scopes
GMAIL_SCOPES = [
    "https://mail.google.com/",  # Full access to Gmail
    "https://www.googleapis.com/auth/gmail.modify",  # Read/write Gmail but not delete
    "https://www.googleapis.com/auth/gmail.readonly",  # Read-only access
    "https://www.googleapis.com/auth/gmail.send"  # Send emails
]

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

print(f"Generated OAuth URL:\n{auth_url}")
print("\nParameters:")
for key, value in params.items():
    print(f"{key}: {value}")

# Check environment
print("\nEnvironment variables:")
print(f"GOOGLE_CLIENT_ID: {client_id}")
print(f"GOOGLE_REDIRECT_URI: {redirect_uri}")