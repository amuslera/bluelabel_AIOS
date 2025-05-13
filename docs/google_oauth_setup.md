# Setting Up Google OAuth for Email Gateway

This guide explains how to set up Google OAuth for the Email Gateway in Bluelabel AIOS, allowing secure access to Gmail accounts without using passwords.

## Why Use OAuth?

Google Workspace and Gmail are increasingly restricting direct IMAP/SMTP access with passwords. OAuth2 is Google's recommended approach for applications that need to access Gmail because:

1. It's more secure - no passwords are stored or transmitted
2. It provides granular access control
3. It works even when 2-factor authentication is enabled
4. It allows administrators to control which applications can access email
5. It avoids issues with "Less secure app access" restrictions

## Prerequisites

Before you begin, you'll need:

1. A Google account with administrative access to your Workspace domain (or a personal Gmail account)
2. Access to the Google Cloud Console

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Give your project a meaningful name, like "Bluelabel AIOS Email Gateway"

## Step 2: Configure the OAuth Consent Screen

1. In the Google Cloud Console, navigate to **APIs & Services > OAuth consent screen**
2. Select the appropriate user type:
   - **Internal** (recommended): If you're using Google Workspace and only want to allow users in your organization
   - **External**: If you need to allow any Google account, including personal Gmail accounts
3. Fill in the required information:
   - App name: "Bluelabel AIOS"
   - User support email: Your email address
   - Developer contact information: Your email address
4. Click **Save and Continue**
5. On the Scopes screen, add the following scopes:
   - `https://mail.google.com/` (Full access to Gmail)
   - `https://www.googleapis.com/auth/gmail.send` (Send email only)
6. Click **Save and Continue**
7. Review your settings and click **Back to Dashboard**

## Step 3: Create OAuth Credentials

1. In the Google Cloud Console, navigate to **APIs & Services > Credentials**
2. Click **Create Credentials** and select **OAuth client ID**
3. For Application type, select **Web application**
4. Give your client a name, like "Bluelabel AIOS Email Gateway"
5. Add authorized redirect URIs:
   - `http://localhost:8080/gateway/google/callback` (for local development)
   - Add your production URL if deploying to a server
6. Click **Create**
7. Note the **Client ID** and **Client Secret** - you'll need these for configuration

## Step 4: Enable the Gmail API

1. In the Google Cloud Console, navigate to **APIs & Services > Library**
2. Search for "Gmail API" and select it
3. Click **Enable**

## Step 5: Configure Bluelabel AIOS

Now that you have your Google OAuth credentials, you need to configure Bluelabel AIOS to use them.

### Option 1: Using the API

```bash
curl -X POST "http://localhost:8080/gateway/google/config" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }'
```

### Option 2: Using Environment Variables

Add these variables to your `.env` file:

```
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET
```

## Step 6: Authenticate with Google

Now you need to authenticate Bluelabel AIOS with your Google account:

1. Get the authentication URL:

```bash
curl "http://localhost:8080/gateway/google/auth"
```

2. Open the returned `auth_url` in your browser
3. Sign in to your Google account
4. Review the permissions and click **Allow**
5. You will be redirected back to Bluelabel AIOS

## Step 7: Configure and Start the Email Gateway

After authentication, you can configure and start the Email Gateway using OAuth:

```bash
curl -X POST "http://localhost:8080/gateway/email/google"
```

This will:
1. Use your Google OAuth tokens to authenticate with Gmail
2. Configure the Email Gateway with the appropriate settings
3. Start the Email Gateway service

## Checking Authentication Status

You can check the status of your Google authentication:

```bash
curl "http://localhost:8080/gateway/google/status"
```

## Revoking Access

If you need to revoke Bluelabel AIOS's access to your Google account:

```bash
curl -X POST "http://localhost:8080/gateway/google/revoke"
```

## Troubleshooting

### Authentication Errors

If you see authentication errors:

1. Verify your client ID and client secret are correct
2. Make sure the redirect URI in your configuration matches exactly what's in Google Cloud Console
3. Check if your OAuth consent screen is configured correctly
4. Make sure the Gmail API is enabled

### Token Expiration

OAuth access tokens expire periodically. Bluelabel AIOS automatically refreshes them, but if you encounter issues:

1. Check the status endpoint to see if the token is expired
2. Revoke the current tokens and re-authenticate

### Google Workspace Restrictions

If you're using Google Workspace, you might need to:

1. Ensure the app is allowlisted in your Google Workspace Admin console
2. Check that API access is enabled for your organization
3. Verify that the user has appropriate permissions

## Security Considerations

Keep these security considerations in mind:

1. Keep your Google client secret secure - don't commit it to public repositories
2. Use HTTPS in production environments
3. Only grant the minimum necessary permissions
4. Regularly audit which applications have access to your Google account