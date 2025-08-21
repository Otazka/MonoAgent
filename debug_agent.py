#!/usr/bin/env python3
"""
Debug script for the AI agent
"""

import os
import sys
from dotenv import load_dotenv

def debug_config():
    """Debug the configuration loading."""
    print("Loading environment variables...")
    load_dotenv()
    
    print(f"SOURCE_REPO_URL: {os.getenv('SOURCE_REPO_URL', 'NOT SET')}")
    print(f"BRANCHES: {os.getenv('BRANCHES', 'NOT SET')}")
    print(f"ORG: {os.getenv('ORG', 'NOT SET')}")
    print(f"GITHUB_TOKEN: {os.getenv('GITHUB_TOKEN', 'NOT SET')[:10] if os.getenv('GITHUB_TOKEN') else 'NOT SET'}...")
    print(f"COMMON_PATH: {os.getenv('COMMON_PATH', 'NOT SET')}")
    
    # Test branches parsing
    branches_str = os.getenv('BRANCHES', '')
    if branches_str:
        branches = [b.strip() for b in branches_str.split(',') if b.strip()]
        print(f"Parsed branches: {branches}")
    else:
        print("No branches found")

def test_imports():
    """Test if all imports work."""
    print("\nTesting imports...")
    try:
        import requests
        print("✅ requests imported")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
    
    try:
        from github import Github
        print("✅ PyGithub imported")
    except ImportError as e:
        print(f"❌ PyGithub import failed: {e}")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")

def test_github_connection():
    """Test GitHub connection."""
    print("\nTesting GitHub connection...")
    try:
        from github import Github
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("❌ No GitHub token found")
            return
        
        github = Github(token)
        user = github.get_user()
        print(f"✅ GitHub connection successful: {user.login}")
    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")

if __name__ == "__main__":
    print("🔍 Debugging AI Agent Configuration")
    print("=" * 50)
    
    debug_config()
    test_imports()
    test_github_connection()
    
    print("\n" + "=" * 50)
    print("Debug complete!")
