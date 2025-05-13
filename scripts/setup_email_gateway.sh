#!/bin/bash
# Setup Email Gateway for Bluelabel AIOS

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
    echo -e "\n${BLUE}========== $1 ==========${NC}\n"
}

# Function to print success messages
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print info messages
info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to print error messages
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

API_ENDPOINT=${API_ENDPOINT:-"http://localhost:8081"}

section "Bluelabel AIOS Email Gateway Setup"
echo "This script will help you set up the Email Gateway for Bluelabel AIOS."
echo "You'll need an email account with IMAP and SMTP access."
echo 

# Check if the API server is running
echo "Checking if the API server is running..."
if ! curl -s "$API_ENDPOINT/health" > /dev/null; then
    info "API server not running. Make sure it's started with 'uvicorn app.main:app --reload'"
    info "You can still configure the gateway, but it won't start automatically."
else
    success "API server is running"
fi

# Ask for email server details
section "Email Account Configuration"
echo "Please enter your email account details:"
read -p "Email address: " EMAIL_ADDRESS
read -p "IMAP server (e.g., imap.gmail.com): " IMAP_SERVER
read -p "IMAP port (default: 993): " IMAP_PORT
IMAP_PORT=${IMAP_PORT:-993}
read -sp "Password or App Password: " EMAIL_PASSWORD
echo
read -p "Use SSL for IMAP? (Y/n): " USE_SSL
USE_SSL=${USE_SSL:-Y}
if [[ "${USE_SSL^^}" == "Y" ]]; then
    USE_SSL=true
else
    USE_SSL=false
fi

# SMTP configuration
read -p "SMTP server (default: same as IMAP): " SMTP_SERVER
SMTP_SERVER=${SMTP_SERVER:-$IMAP_SERVER}
read -p "SMTP port (default: 587): " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-587}
read -p "Use TLS for SMTP? (Y/n): " USE_TLS
USE_TLS=${USE_TLS:-Y}
if [[ "${USE_TLS^^}" == "Y" ]]; then
    USE_TLS=true
else
    USE_TLS=false
fi

# Advanced settings
section "Advanced Settings"
read -p "Check interval in seconds (default: 300): " CHECK_INTERVAL
CHECK_INTERVAL=${CHECK_INTERVAL:-300}
read -p "Reply to sender with processing status? (Y/n): " REPLY_TO_SENDER
REPLY_TO_SENDER=${REPLY_TO_SENDER:-Y}
if [[ "${REPLY_TO_SENDER^^}" == "Y" ]]; then
    REPLY_TO_SENDER=true
else
    REPLY_TO_SENDER=false
fi

# Create configuration JSON
CONFIG_JSON=$(cat <<EOF
{
  "email_address": "$EMAIL_ADDRESS",
  "server": "$IMAP_SERVER",
  "password": "$EMAIL_PASSWORD",
  "port": $IMAP_PORT,
  "use_ssl": $USE_SSL,
  "use_tls": false,
  "check_interval": $CHECK_INTERVAL,
  "outgoing_server": "$SMTP_SERVER",
  "outgoing_port": $SMTP_PORT,
  "outgoing_use_ssl": false,
  "outgoing_use_tls": $USE_TLS,
  "enabled": true,
  "reply_to_sender": $REPLY_TO_SENDER
}
EOF
)

# Save configuration to a temporary file
echo "$CONFIG_JSON" > /tmp/email_config.json

# Configure the gateway
section "Configuring Email Gateway"
if curl -s -X POST "$API_ENDPOINT/gateway/email/config" \
  -H "Content-Type: application/json" \
  -d @/tmp/email_config.json > /dev/null; then
    success "Email gateway configured successfully"
else
    if curl -s "$API_ENDPOINT/health" > /dev/null; then
        error "Failed to configure email gateway. Check the API server logs."
    else
        # Save to .env file instead
        info "API server not available. Saving configuration to .env file instead."
        if [ -f ".env" ]; then
            cp .env .env.backup
            success "Created backup of existing .env file"
        fi
        
        # Update or create .env file
        cat <<EOF >> .env
# Email Gateway Configuration
MAIL_SERVER=$IMAP_SERVER
MAIL_PORT=$IMAP_PORT
MAIL_USERNAME=$EMAIL_ADDRESS
MAIL_PASSWORD=$EMAIL_PASSWORD
MAIL_USE_SSL=$USE_SSL
MAIL_USE_TLS=False
MAIL_CHECK_INTERVAL=$CHECK_INTERVAL

# SMTP Settings
MAIL_FROM=$EMAIL_ADDRESS
MAIL_FROM_NAME=Bluelabel AIOS
SMTP_SERVER=$SMTP_SERVER
SMTP_PORT=$SMTP_PORT
SMTP_USERNAME=$EMAIL_ADDRESS
SMTP_PASSWORD=$EMAIL_PASSWORD
SMTP_USE_SSL=False
SMTP_USE_TLS=$USE_TLS

# Processing settings
MAIL_FOLDER=INBOX
MAIL_PROCESSED_FOLDER=Processed
MAIL_ERROR_FOLDER=Errors
MAIL_REPLY_TO_SENDER=$REPLY_TO_SENDER
EOF
        success "Configuration saved to .env file"
    fi
fi

# Clean up
rm /tmp/email_config.json

# Try to start the gateway
section "Starting Email Gateway"
if curl -s "$API_ENDPOINT/health" > /dev/null; then
    if curl -s -X POST "$API_ENDPOINT/gateway/email/start" > /dev/null; then
        success "Email gateway started successfully"
    else
        error "Failed to start email gateway. Check the API server logs."
    fi
else
    info "API server not available. The gateway will be started when you run the server."
    info "You can start it manually with: curl -X POST \"$API_ENDPOINT/gateway/email/start\""
fi

section "Setup Complete"
info "Your Email Gateway has been configured!"
echo
echo "You can now send emails to: $EMAIL_ADDRESS"
echo "Format examples:"
echo "  - Subject: [TAG: ai, research] Article to process"
echo "  - Body: Include a URL, text content, or attach files"
echo
info "For more information, see docs/email_gateway_setup.md"
echo

# Final check
if curl -s "$API_ENDPOINT/gateway/email/status" > /dev/null; then
    echo "Current gateway status:"
    curl -s "$API_ENDPOINT/gateway/email/status" | jq
else
    echo "To check the gateway status later: curl $API_ENDPOINT/gateway/email/status"
fi