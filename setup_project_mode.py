#!/usr/bin/env python3
"""
Setup script for Project Mode configuration
"""

import os
import shutil

def setup_project_mode():
    """Setup the .env file for project mode."""
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Please copy env.example to .env first:")
        print("cp env.example .env")
        return False
    
    # Read current .env
    with open('.env', 'r') as f:
        content = f.read()
    
    # Update for project mode
    new_content = """# Project Mode Configuration for libft monorepo

# Monorepo to split (your current repository)
SOURCE_REPO_URL=git@github.com:elenasurovtseva/testmonorepo.git

# Mode: project-based splitting
MODE=project

# Projects to extract (your current projects)
PROJECTS=fractol,printf,pushswap

# Common library path
COMMON_PATH=libft

# GitHub organization or username
ORG=elenasurovtseva

# GitHub Personal Access Token with repo scope
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""
    
    # Backup current .env
    shutil.copy('.env', '.env.backup')
    print("✅ Backed up current .env to .env.backup")
    
    # Write new .env
    with open('.env', 'w') as f:
        f.write(new_content)
    
    print("✅ Updated .env for project mode")
    print("\n⚠️  IMPORTANT: Edit .env and update these values:")
    print("   - SOURCE_REPO_URL: Your actual repository URL")
    print("   - ORG: Your GitHub username or organization")
    print("   - GITHUB_TOKEN: Your actual GitHub token")
    print("\nThen run: python test_config.py")
    
    return True

if __name__ == "__main__":
    setup_project_mode()
