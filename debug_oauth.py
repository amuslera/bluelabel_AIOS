#!/usr/bin/env python3
"""Debug script for Google OAuth Configuration"""

import os
import sys
import json

def print_env_variables():
    """Print relevant environment variables"""
    print("=== Environment Variables ===")
    oauth_vars = [var for var in os.environ if var.startswith("GOOGLE_")]
    if oauth_vars:
        for var in oauth_vars:
            # Mask the secret
            if var == "GOOGLE_CLIENT_SECRET":
                value = "*" * len(os.environ.get(var, ""))
            else:
                value = os.environ.get(var)
            print(f"{var}: {value}")
    else:
        print("No GOOGLE_* environment variables found")
    
    print("\n")

def check_tokens_file():
    """Check if the tokens file exists and read its contents"""
    print("=== Token File Check ===")
    token_file = os.environ.get("GOOGLE_TOKEN_FILE", "config/google_tokens.json")
    print(f"Token file path: {token_file}")
    
    if os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                tokens = json.load(f)
                # Mask sensitive data
                if "access_token" in tokens:
                    tokens["access_token"] = tokens["access_token"][:5] + "..." if tokens["access_token"] else "(empty)"
                if "refresh_token" in tokens:
                    tokens["refresh_token"] = tokens["refresh_token"][:5] + "..." if tokens["refresh_token"] else "(empty)"
                print(f"Token file contents: {json.dumps(tokens, indent=2)}")
        except Exception as e:
            print(f"Error reading token file: {str(e)}")
    else:
        print(f"Token file does not exist: {token_file}")
    
    print("\n")

def update_redirect_uri():
    """Update the redirect URI to use the correct port"""
    port = input("Enter the port your server is running on (e.g. 8081): ")
    if not port:
        print("No port entered, keeping current configuration")
        return
    
    try:
        port = int(port)
        os.environ["GOOGLE_REDIRECT_URI"] = f"http://localhost:{port}/gateway/google/callback"
        print(f"GOOGLE_REDIRECT_URI updated to: {os.environ['GOOGLE_REDIRECT_URI']}")
        
        # Update the config in the file too
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                env_content = f.read()
            
            if "GOOGLE_REDIRECT_URI=" in env_content:
                # Update existing value
                lines = env_content.split("\n")
                updated_lines = []
                for line in lines:
                    if line.startswith("GOOGLE_REDIRECT_URI="):
                        updated_lines.append(f"GOOGLE_REDIRECT_URI=http://localhost:{port}/gateway/google/callback")
                    else:
                        updated_lines.append(line)
                env_content = "\n".join(updated_lines)
            else:
                # Add new value
                env_content += f"\nGOOGLE_REDIRECT_URI=http://localhost:{port}/gateway/google/callback\n"
            
            with open(env_file, "w") as f:
                f.write(env_content)
            
            print(f"Updated {env_file} with new GOOGLE_REDIRECT_URI")
        else:
            # Create new .env file
            with open(env_file, "w") as f:
                f.write(f"GOOGLE_REDIRECT_URI=http://localhost:{port}/gateway/google/callback\n")
            
            print(f"Created {env_file} with GOOGLE_REDIRECT_URI")
    except ValueError:
        print("Invalid port number")

def set_oauth_credentials():
    """Set OAuth credentials manually"""
    client_id = input("Enter your Google OAuth client ID: ")
    client_secret = input("Enter your Google OAuth client secret: ")
    
    if not client_id or not client_secret:
        print("Client ID and secret are required")
        return
    
    # Update environment variables
    os.environ["GOOGLE_CLIENT_ID"] = client_id
    os.environ["GOOGLE_CLIENT_SECRET"] = client_secret
    
    # Update .env file
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            env_content = f.read()
        
        lines = env_content.split("\n")
        updated_lines = []
        client_id_updated = False
        client_secret_updated = False
        
        for line in lines:
            if line.startswith("GOOGLE_CLIENT_ID="):
                updated_lines.append(f"GOOGLE_CLIENT_ID={client_id}")
                client_id_updated = True
            elif line.startswith("GOOGLE_CLIENT_SECRET="):
                updated_lines.append(f"GOOGLE_CLIENT_SECRET={client_secret}")
                client_secret_updated = True
            else:
                updated_lines.append(line)
        
        if not client_id_updated:
            updated_lines.append(f"GOOGLE_CLIENT_ID={client_id}")
        
        if not client_secret_updated:
            updated_lines.append(f"GOOGLE_CLIENT_SECRET={client_secret}")
        
        env_content = "\n".join(updated_lines)
        
        with open(env_file, "w") as f:
            f.write(env_content)
        
        print(f"Updated {env_file} with new OAuth credentials")
    else:
        # Create new .env file
        with open(env_file, "w") as f:
            f.write(f"GOOGLE_CLIENT_ID={client_id}\n")
            f.write(f"GOOGLE_CLIENT_SECRET={client_secret}\n")
        
        print(f"Created {env_file} with OAuth credentials")
    
    print("OAuth credentials updated successfully")

def main():
    """Main function"""
    print("=== Google OAuth Debug Tool ===\n")
    
    while True:
        print("Select an option:")
        print("1. Print environment variables")
        print("2. Check tokens file")
        print("3. Update redirect URI")
        print("4. Set OAuth credentials")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            print_env_variables()
        elif choice == "2":
            check_tokens_file()
        elif choice == "3":
            update_redirect_uri()
        elif choice == "4":
            set_oauth_credentials()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again")
        
        print("-" * 50)

if __name__ == "__main__":
    main()