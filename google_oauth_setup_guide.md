# Google OAuth Setup Guide

This guide will help you properly configure Google OAuth for Gmail integration.

## Issue: Bad Request (400) Error

If you're seeing a "Bad Request - Error 400" when trying to authenticate with Google, follow these steps to diagnose and fix the issue.

## Step 1: Verify OAuth Configuration in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (the one with client ID: `387555905237-u0uro845dh0jj34o34fggk4om6avnh3g.apps.googleusercontent.com`)
3. Navigate to "APIs & Services" > "Credentials"
4. Find and edit the OAuth 2.0 Client ID being used

Verify the following:

- **Authorized redirect URIs** must include exactly: `http://localhost:8081/gateway/google/callback`
- Check that there are no extra spaces, missing or extra slashes, etc.
- Ensure the port number (8081) is correct

## Step 2: Verify the API is Enabled

1. Go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Make sure it shows as "Enabled"
4. If not, click on it and enable it

## Step 3: Verify OAuth Consent Screen Configuration

1. Go to "APIs & Services" > "OAuth consent screen"
2. Ensure all required fields are completed:
   - App name
   - User support email
   - Developer contact information
   - Authorized domains
3. Verify scopes are configured correctly, including:
   - `https://mail.google.com/`
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`

## Step 4: Add Test Users (for apps in testing)

If your application is in "Testing" mode (not published):

1. Go to "APIs & Services" > "OAuth consent screen"
2. Scroll down to "Test users"
3. Click "Add Users"
4. Add your Google email account that you're trying to authenticate with

## Step 5: Try the Authentication Again

After making the necessary changes:

1. Run the OAuth URL test script:
   ```bash
   python3 test_oauth_url.py
   ```

2. Copy the generated URL and open it in a browser

3. If you still receive errors:
   - Check browser console for more specific error messages
   - Look for query parameters in the error URL that might indicate the specific issue

## Step 6: Test with a Simpler Scope

If you're still having issues, try with just a basic scope to verify the overall OAuth flow works:

1. Edit `test_oauth_url.py` and change the scopes to just:
   ```python
   GMAIL_SCOPES = ["https://www.googleapis.com/auth/userinfo.email"]
   ```

2. Run again and try authenticating with this simpler scope

## Common Error Causes

- **redirect_uri_mismatch**: The redirect URI doesn't exactly match what's registered
- **invalid_client**: Client ID or secret is incorrect
- **access_denied**: User denied permission or app is blocked
- **invalid_scope**: One or more requested scopes are invalid or formatted incorrectly
- **Error 403: Access Not Configured**: The API has not been enabled for the project

## Testing the Complete Flow

Once you've fixed the OAuth configuration, test the complete flow with:

```bash
# Get the auth URL
curl "http://localhost:8081/gateway/google/auth"

# After successful authentication (you'll be redirected), check status
curl "http://localhost:8081/gateway/google/status"

# Configure and start the email gateway with OAuth
curl -X POST "http://localhost:8081/gateway/email/google"

# Check the email gateway status
curl "http://localhost:8081/gateway/email/status"
```

## Need More Help?

If you're still experiencing issues, check the application logs and Google Cloud Console logs for more detailed error information.