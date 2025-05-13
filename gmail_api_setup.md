# Gmail API Setup Guide

This guide will help you properly set up the Gmail API and OAuth consent screen in Google Cloud Console.

## Step 1: Enable the Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (the one with client ID: `387555905237-u0uro845dh0jj34o34fggk4om6avnh3g.apps.googleusercontent.com`)
3. In the left navigation panel, select "APIs & Services" > "Library"
4. Search for "Gmail API"
5. Click on the Gmail API from the search results
6. Click the "ENABLE" button (or "MANAGE" if it's already enabled)

## Step 2: Configure the OAuth Consent Screen

1. In the left navigation panel, select "APIs & Services" > "OAuth consent screen"
2. Select the appropriate user type:
   - **External**: For personal projects or if you're not using a Google Workspace domain
   - **Internal**: Only available for Google Workspace organizations
3. Fill out the required information:
   - App name: The name users will see when they authenticate
   - User support email: Your email address for user support
   - Developer contact information: Your email address
   - Authorized domains: Add domains if needed

4. Click "SAVE AND CONTINUE"

5. Add the Gmail scopes:
   - Click "ADD OR REMOVE SCOPES"
   - Search for and select the following scopes:
     - `https://mail.google.com/`
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
   - Click "UPDATE"
   - Click "SAVE AND CONTINUE"

6. Add test users (for apps in testing):
   - Click "ADD USERS"
   - Add your Google email address that you'll use for testing
   - Click "SAVE AND CONTINUE"

7. Review your app registration summary and click "BACK TO DASHBOARD"

## Step 3: Configure OAuth Credentials

1. In the left navigation panel, select "APIs & Services" > "Credentials"
2. Click on the OAuth 2.0 Client ID that you're using
3. Verify the "Authorized redirect URIs" section contains exactly:
   - `http://localhost:8081/gateway/google/callback`
4. Add the redirect URI if it's not already there
5. Click "SAVE"

## Step 4: Testing the API Access

After completing the setup, try authenticating using the simplified test script:

```bash
python3 simple_oauth_test.py
```

If the basic authentication with email scope works but the Gmail scopes don't, double-check the Gmail API is enabled and all required scopes are added to your OAuth consent screen.

## Common Issues and Solutions

### "Bad Request - Error 400"

1. **API not enabled**: Make sure the Gmail API is enabled
2. **Invalid scope**: Verify all the scopes are properly configured
3. **Redirect URI mismatch**: Ensure the redirect URI is exactly as specified
4. **Testing restrictions**: If your app is in testing mode, ensure your Google account is added as a test user

### "Error 403: Access Not Configured" 

This means the API has not been enabled for your project. Follow Step 1 to enable the Gmail API.

### "redirect_uri_mismatch"

The redirect URI in your request doesn't match the one configured in Google Cloud Console. Make sure it matches exactly, including the protocol (http/https), port number, and path.

### App verification warnings

If your app is unverified, you'll see security warnings during authentication. For testing purposes, you can proceed by clicking "Advanced" and then "Go to [Your App Name] (unsafe)".

## Using OAuth in Production

For a production application, consider completing the verification process:

1. Go to the OAuth consent screen settings
2. Add all required information and branding
3. Submit your app for verification

This will allow you to use the OAuth integration without the unverified app warnings.