#!/bin/bash
# Demo workflow script for Bluelabel AIOS
# This script demonstrates the complete workflow from content submission to digest creation

# Set the API endpoint
API_ENDPOINT="http://localhost:8080"

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

# Check if the API server is running
section "Checking API server"
if ! curl -s "$API_ENDPOINT/health" > /dev/null; then
    error "API server is not running. Please start the server with 'uvicorn app.main:app --reload'"
fi
success "API server is running"

# Step 1: Configure the Gateway agent
section "Configuring Gateway Agent"
info "Setting up email gateway (simulated)"
# In a real environment, this would configure actual email credentials
echo '{
  "email_address": "gateway@bluelabel-aios.com",
  "server": "imap.example.com",
  "password": "simulated_password",
  "port": 993,
  "use_ssl": true,
  "check_interval": 60,
  "enabled": true
}' > /tmp/email_config.json

curl -s -X POST "$API_ENDPOINT/gateway/email/config" \
  -H "Content-Type: application/json" \
  -d @/tmp/email_config.json > /dev/null

success "Email gateway configured"

# Step 2: Submit content via simulated email
section "Submitting Content via Gateway"

# URL content
info "Submitting URL content via simulated email"
curl -s -X POST "$API_ENDPOINT/gateway/email/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "user@example.com",
    "to": "gateway@bluelabel-aios.com",
    "subject": "[TAG: ai, news] Interesting AI article",
    "body": "https://example.com/ai-article",
    "date": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"
  }' > /dev/null
success "URL content submitted"

# Text content
info "Submitting text content via simulated email"
curl -s -X POST "$API_ENDPOINT/gateway/email/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "user@example.com",
    "to": "gateway@bluelabel-aios.com",
    "subject": "[TAG: note, personal] My thoughts on AI",
    "body": "Artificial intelligence is transforming various industries. Here are some key points to consider...\n\n1. AI is enhancing productivity\n2. Ethical considerations are important\n3. Human oversight remains essential",
    "date": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'"
  }' > /dev/null
success "Text content submitted"

# Step 3: Check that content was processed
section "Verifying Content Processing"
info "Checking that content was added to the knowledge repository"
sleep 3 # Give the system time to process

response=$(curl -s -X GET "$API_ENDPOINT/knowledge/list?limit=10")
count=$(echo $response | grep -o '"total":[0-9]*' | cut -d ':' -f2)

if [ "$count" -gt 0 ]; then
    success "Found $count items in the knowledge repository"
else
    error "No content found in the knowledge repository"
fi

# Step 4: Generate an on-demand digest
section "Generating On-Demand Digest"
info "Creating a digest for all content"

# Use current date and date from 7 days ago
end_date=$(date -u +"%Y-%m-%d")
start_date=$(date -u -v-7d +"%Y-%m-%d" 2>/dev/null || date -u -d "7 days ago" +"%Y-%m-%d")

digest_response=$(curl -s -X POST "$API_ENDPOINT/digests/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "digest_type": "daily",
    "date_range": "'"$start_date,$end_date"'",
    "delivery_method": "view_only",
    "content_types": ["url", "text", "pdf", "audio", "social"],
    "max_items": 20
  }')

digest_id=$(echo $digest_response | grep -o '"digest_id":"[^"]*"' | cut -d '"' -f4)

if [ -n "$digest_id" ]; then
    success "Digest generated with ID: $digest_id"
else
    error "Failed to generate digest"
fi

# Step 5: Schedule a recurring digest
section "Scheduling Recurring Digest"
info "Setting up a daily digest schedule"

curl -s -X POST "$API_ENDPOINT/scheduler/digests" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_type": "daily",
    "time": "08:00",
    "recipient": "user@example.com",
    "digest_type": "daily",
    "delivery_method": "email",
    "content_types": ["url", "pdf", "text", "audio", "social"],
    "tags": []
  }' > /dev/null

success "Daily digest scheduled for 8:00 AM"

# Step 6: Simulate digest execution
section "Simulating Scheduled Digest Execution"
info "Manually triggering the scheduled digest"

# Get the scheduled digest ID
schedule_response=$(curl -s -X GET "$API_ENDPOINT/scheduler/digests")
schedule_id=$(echo $schedule_response | grep -o '"id":"[^"]*"' | head -1 | cut -d '"' -f4)

if [ -n "$schedule_id" ]; then
    curl -s -X POST "$API_ENDPOINT/scheduler/digests/$schedule_id/execute" > /dev/null
    success "Scheduled digest executed"
else
    error "Could not find a scheduled digest"
fi

# Conclusion
section "Workflow Demo Complete"
info "Full workflow demonstration completed successfully"
info "You have:"
echo "✓ Configured the Gateway agent"
echo "✓ Submitted content via email"
echo "✓ Verified content processing"
echo "✓ Generated an on-demand digest"
echo "✓ Scheduled a recurring digest"
echo "✓ Simulated digest execution"

info "Next steps:"
echo "1. Check the Streamlit UI for more details at http://localhost:8501"
echo "2. Explore the 'Digest Management' page to view and manage digests"
echo "3. Check your email (if configured) for delivered digests"

success "Demo completed successfully!"