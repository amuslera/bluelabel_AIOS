#!/usr/bin/env python3
"""
Google Cloud API Check Tool

This script helps verify if the necessary APIs are configured
for your Google Cloud project.

Usage:
1. Make sure you have the Google Cloud SDK installed
2. Run this script and follow the prompts
"""

import os
import subprocess
import json
from dotenv import load_dotenv

def run_gcloud_command(command):
    """Run a gcloud command and return the output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception running command: {str(e)}")
        return None

def get_project_id_from_client_id(client_id):
    """Extract project ID from client ID if possible"""
    try:
        # Client IDs usually have format: [number]-[hash].apps.googleusercontent.com
        if ".apps.googleusercontent.com" in client_id:
            project_number = client_id.split("-")[0]
            print(f"Extracted project number: {project_number}")
            return project_number
    except:
        pass
    return None

def main():
    # Load environment variables
    load_dotenv()
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    
    if not client_id:
        print("ERROR: GOOGLE_CLIENT_ID is not set in your .env file")
        return
    
    print(f"Using client ID: {client_id}")
    
    # Try to extract project number
    project_number = get_project_id_from_client_id(client_id)
    
    # Check if gcloud is installed
    gcloud_installed = run_gcloud_command("which gcloud")
    if not gcloud_installed:
        print("\nGoogle Cloud SDK (gcloud) is not installed or not in your PATH.")
        print("Please install it to use this script: https://cloud.google.com/sdk/docs/install")
        
        print("\nManual check instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Navigate to 'APIs & Services' > 'Library'")
        print("4. Search for 'Gmail API' and ensure it's enabled")
        print("5. Also check 'APIs & Services' > 'OAuth consent screen' to ensure it's properly configured")
        print("6. If your app is in testing mode, ensure your Google account is added as a test user")
        return
    
    print("\nChecking Google Cloud authentication status...")
    auth_status = run_gcloud_command("gcloud auth list")
    
    if "No credentialed accounts" in auth_status or not auth_status:
        print("You are not authenticated with Google Cloud SDK.")
        print("Please run: gcloud auth login")
        return
    
    print("\nYou are authenticated with Google Cloud SDK.")
    
    # Try to get the current project
    current_project = run_gcloud_command("gcloud config get-value project")
    
    if not current_project or current_project == "(unset)":
        print("No Google Cloud project is currently set.")
        if project_number:
            print(f"Setting project to the one matching your client ID (project number: {project_number})...")
            set_project = run_gcloud_command(f"gcloud config set project {project_number}")
            if not set_project:
                print("Failed to set project. Please set it manually with:")
                print(f"gcloud config set project [YOUR_PROJECT_ID]")
                return
        else:
            print("Please set your project ID manually with:")
            print("gcloud config set project [YOUR_PROJECT_ID]")
            return
    
    print(f"\nChecking APIs for project: {current_project}")
    
    # Check if Gmail API is enabled
    gmail_api_status = run_gcloud_command("gcloud services list --filter='name:gmail.googleapis.com'")
    
    if not gmail_api_status or "gmail.googleapis.com" not in gmail_api_status:
        print("\n⚠️ Gmail API is NOT enabled for this project.")
        print("This is likely the cause of the OAuth error.")
        print("\nTo enable it, run:")
        print("gcloud services enable gmail.googleapis.com")
    else:
        print("\n✅ Gmail API is enabled for this project.")
    
    # Get OAuth configuration details
    print("\nChecking OAuth configuration...")
    oauth_clients = run_gcloud_command("gcloud alpha iap oauth-clients list 2>/dev/null")
    
    if oauth_clients and client_id in oauth_clients:
        print(f"✅ Found OAuth client ID in this project: {client_id}")
    else:
        print(f"❌ Could not find OAuth client ID in this project: {client_id}")
        print("This might mean:")
        print("1. You're not using the correct Google Cloud project")
        print("2. The client ID is from a different project")
        print("3. You need sufficient permissions to view OAuth clients")
    
    print("\nRequired Google Cloud APIs:")
    print("- Gmail API (gmail.googleapis.com) - For Gmail access")
    print("- People API (people.googleapis.com) - For contact information")
    print("- Google Drive API (drive.googleapis.com) - If you need attachment support")
    
    print("\nTo enable any missing API, run:")
    print("gcloud services enable [API_NAME]")
    
    print("\nChecking OAuth consent screen configuration...")
    print("Since this can't be checked via command line, please verify in Google Cloud Console:")
    print("1. Go to https://console.cloud.google.com/apis/credentials/consent")
    print("2. Ensure all required fields are filled out")
    print("3. Make sure your scopes are properly configured")
    print("4. If in testing mode, ensure your Google account is added as a test user")

if __name__ == "__main__":
    main()