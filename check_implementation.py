#!/usr/bin/env python3
"""
Simple script to check our implementation without running full tests.
This simply validates that the key components we've created can be imported.
"""

import os
import sys

def check_imports():
    print("Checking key imports...")
    
    try:
        from app.agents.gateway.agent import GatewayAgent
        print("✅ GatewayAgent imported successfully")
    except ImportError as e:
        print(f"❌ Error importing GatewayAgent: {e}")
    
    try:
        from app.agents.digest.agent import DigestAgent
        print("✅ DigestAgent imported successfully")
    except ImportError as e:
        print(f"❌ Error importing DigestAgent: {e}")
    
    try:
        from app.services.scheduler.scheduler_service import SchedulerService
        print("✅ SchedulerService imported successfully")
    except ImportError as e:
        print(f"❌ Error importing SchedulerService: {e}")
    
    try:
        from app.ui.pages.digest_management import render_digest_management_page
        print("✅ Digest management UI imported successfully")
    except ImportError as e:
        print(f"❌ Error importing digest management UI: {e}")

def check_file_structure():
    print("\nChecking file structure...")
    
    files_to_check = [
        "app/agents/gateway/agent.py",
        "app/agents/digest/agent.py",
        "app/agents/digest/scheduling_tool.py",
        "app/services/scheduler/scheduler_service.py",
        "app/ui/pages/digest_management.py",
        "scripts/demo_workflow.sh",
        "docs/workflow_diagram.md",
        "WORKFLOW.md"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} not found")

def check_agent_registry():
    print("\nChecking agent registry...")
    
    try:
        from app.core.registry.agent_registry import AgentRegistry
        
        # Get the registered agent classes
        agent_classes = AgentRegistry._agent_classes
        
        if 'gateway' in agent_classes:
            print("✅ Gateway agent is registered in the AgentRegistry")
        else:
            print("❌ Gateway agent not found in the AgentRegistry")
            
        if 'digest' in agent_classes:
            print("✅ Digest agent is registered in the AgentRegistry")
        else:
            print("❌ Digest agent not found in the AgentRegistry")
            
    except ImportError as e:
        print(f"❌ Error importing AgentRegistry: {e}")

def check_readme_updates():
    print("\nChecking README updates...")
    
    with open("README.md", "r") as f:
        readme_content = f.read()
    
    if "Gateway Agent" in readme_content:
        print("✅ Gateway Agent is documented in README")
    else:
        print("❌ Gateway Agent not found in README")
        
    if "Digest Agent" in readme_content:
        print("✅ Digest Agent is documented in README")
    else:
        print("❌ Digest Agent not found in README")

def main():
    print("Running implementation check...")
    check_imports()
    check_file_structure()
    check_agent_registry()
    check_readme_updates()
    print("\nDone!")

if __name__ == "__main__":
    main()