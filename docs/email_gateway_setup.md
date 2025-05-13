# Email Gateway Setup Guide

This guide explains how to set up the Email Gateway for Bluelabel AIOS to automatically process content sent via email.

## Overview

The Email Gateway allows you to:

1. Send content to a designated email address
2. Have it automatically processed by Bluelabel AIOS
3. Store the processed content in your knowledge repository
4. Optionally receive a confirmation email with processing results

## Setup Options

There are two ways to configure the Email Gateway:

1. **API Configuration**: Use the REST API to configure the gateway programmatically
2. **Environment Variables**: Set the configuration directly in your `.env` file or system environment

## Required Email Settings

You'll need an email account that supports IMAP for receiving emails and SMTP for sending responses.

### Gmail Setup (Recommended for Testing)

1. Create a Gmail account or use an existing one
2. Enable 2-Step Verification in your Google Account
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
3. Generate an App Password
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Use the generated 16-character password as your password in the configuration

### Other Email Providers

You can use any email provider that supports IMAP and SMTP, such as:

- Outlook/Office 365
- Yahoo Mail
- ProtonMail (with Bridge)
- Custom domain email

Gather the following information from your email provider:
- IMAP server address and port (usually 993)
- SMTP server address and port (usually 587 or 465)
- Username/email address
- Password or app password

## Configuration via API

The easiest way to configure the Email Gateway is through the REST API:

```bash
curl -X POST "http://localhost:8080/gateway/email/config" \
  -H "Content-Type: application/json" \
  -d '{
    "email_address": "your-aios@gmail.com",
    "server": "imap.gmail.com",
    "password": "your-app-password",
    "port": 993,
    "use_ssl": true,
    "use_tls": false,
    "check_interval": 300,
    "outgoing_server": "smtp.gmail.com",
    "outgoing_port": 587,
    "outgoing_use_ssl": false,
    "outgoing_use_tls": true,
    "enabled": true,
    "reply_to_sender": true
  }'
```

## Configuration via Environment Variables

Alternatively, you can set the configuration in your `.env` file:

```
# Inbound (IMAP) settings
MAIL_SERVER=imap.gmail.com
MAIL_PORT=993
MAIL_USERNAME=your-aios@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_SSL=True
MAIL_USE_TLS=False
MAIL_CHECK_INTERVAL=300

# Outbound (SMTP) settings
MAIL_FROM=your-aios@gmail.com
MAIL_FROM_NAME=Bluelabel AIOS
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-aios@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_SSL=False
SMTP_USE_TLS=True

# Processing settings
MAIL_FOLDER=INBOX
MAIL_PROCESSED_FOLDER=Processed
MAIL_ERROR_FOLDER=Errors

# Special features
MAIL_ALLOWED_SENDERS=your-personal-email@example.com,work-email@example.com
MAIL_SUBJECT_KEYWORDS=process,analyze,read,save
MAIL_REPLY_TO_SENDER=True
```

## Starting the Email Gateway

After configuring the gateway, you need to start it:

```bash
curl -X POST "http://localhost:8080/gateway/email/start"
```

This starts the email monitoring service, which will check for new emails at the configured interval.

## Using the Email Gateway

Once configured and started, you can use the Email Gateway as follows:

1. **Send an email** to your configured email address (e.g., your-aios@gmail.com)
2. **Include content** in one of these ways:
   - Add a link in the body
   - Paste text directly in the body
   - Attach a PDF or other supported file
   - Attach an audio file for transcription
3. **Use tags in the subject** (optional):
   - `[TAG: ai, research, important]` to add suggested tags
   - Include keywords like "process" or "analyze" to ensure processing (if configured)
4. **Receive a confirmation** (if reply_to_sender is enabled) with processing results

### Example Email

```
To: your-aios@gmail.com
Subject: [TAG: AI, research] Interesting article to process

https://example.com/interesting-article

This seems like a very interesting article about AI research that we should save and analyze.
```

## Testing the Gateway

You can test the Email Gateway without sending real emails using the simulation endpoint:

```bash
curl -X POST "http://localhost:8080/gateway/email/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "your-personal-email@example.com",
    "to": "your-aios@gmail.com",
    "subject": "[TAG: test] Test email for processing",
    "body": "https://example.com/test-article"
  }'
```

## Checking Gateway Status

To check the current status of the Email Gateway:

```bash
curl "http://localhost:8080/gateway/email/status"
```

## Stopping the Gateway

If needed, you can stop the Email Gateway:

```bash
curl -X POST "http://localhost:8080/gateway/email/stop"
```

## Troubleshooting

If you encounter issues with the Email Gateway:

1. **Check your credentials**: Make sure your username and password are correct
2. **Check IMAP/SMTP settings**: Verify the server addresses and ports
3. **Check permissions**: Make sure your email account allows IMAP access
4. **Check app passwords**: For Gmail, make sure you're using an App Password
5. **Check logs**: Look for errors in the application logs
6. **Try simulation**: Test with the simulation endpoint to bypass email issues

## Security Considerations

Keep these security considerations in mind:

1. **Use app passwords**: Avoid storing your main account password
2. **Set allowed senders**: Restrict who can send emails to the gateway
3. **Create a dedicated account**: Don't use your personal email account
4. **Monitor access**: Regularly check for unauthorized access to your email account
5. **Secure your API**: Add authentication to the API endpoints in production

## Advanced Configuration

### Filtering Emails

You can configure which emails are processed by:

- Setting `MAIL_ALLOWED_SENDERS` to a comma-separated list of allowed email addresses
- Setting `MAIL_SUBJECT_KEYWORDS` to keywords that must appear in the subject
- Creating custom email filters in your email account to route emails to specific folders

### Processing Multiple Email Accounts

To process multiple email accounts:

1. Configure one primary email account as described above
2. Set up email forwarding from other accounts to your primary account
3. Use email filters or tags in the subject to differentiate sources

### Custom Folder Structure

You can customize the folder structure:

- `MAIL_FOLDER`: The folder to check for new emails (default: "INBOX")
- `MAIL_PROCESSED_FOLDER`: Where to move processed emails (default: "Processed")
- `MAIL_ERROR_FOLDER`: Where to move emails that failed processing (default: "Errors")