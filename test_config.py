#!/usr/bin/env python3
"""
Configuration and Prerequisites Test Script

This script validates the configuration and checks that all prerequisites
are met before running the repository splitter.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv


def check_python_version():
    """Check if Python version is 3.9+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_git():
    """Check if git is installed and available."""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git: {result.stdout.strip()}")
            return True
        else:
            print("❌ Git not found")
            return False
    except FileNotFoundError:
        print("❌ Git not found in PATH")
        return False


def check_git_filter_repo():
    """Check if git-filter-repo is installed."""
    try:
        result = subprocess.run(['git-filter-repo', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ git-filter-repo: {result.stdout.strip()}")
            return True
        else:
            print("❌ git-filter-repo not found")
            return False
    except FileNotFoundError:
        print("❌ git-filter-repo not found in PATH")
        print("   Install with: pip install git-filter-repo")
        return False


def check_python_dependencies():
    """Check if required Python packages are installed."""
    required_packages = [
        ('PyGithub', 'github'),
        ('python-dotenv', 'dotenv'),
        ('requests', 'requests')
    ]
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} not installed")
            print(f"   Install with: pip install {package_name}")
            return False
    return True


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Copy env.template to .env and configure it")
        return False
    
    print("✅ .env file found")
    
    # Load and validate environment variables
    load_dotenv()
    
    # Check mode
    mode = os.getenv('MODE', 'branch').lower()
    print(f"✅ MODE: {mode}")
    
    required_vars = ['SOURCE_REPO_URL', 'ORG', 'GITHUB_TOKEN']
    
    # Add mode-specific required variables
    if mode == 'branch':
        required_vars.append('BRANCHES')
    elif mode == 'project':
        required_vars.append('PROJECTS')
    else:
        print(f"❌ Invalid MODE: {mode}. Must be 'branch' or 'project'")
        return False
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * len(value)}")  # Hide sensitive values
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Validate mode-specific variables
    if mode == 'branch':
        branches = os.getenv('BRANCHES', '').split(',')
        branches = [branch.strip() for branch in branches if branch.strip()]
        if not branches:
            print("❌ BRANCHES is empty or contains no valid branch names")
            return False
        print(f"✅ Found {len(branches)} branches: {', '.join(branches)}")
    
    elif mode == 'project':
        projects = os.getenv('PROJECTS', '').split(',')
        projects = [project.strip() for project in projects if project.strip()]
        if not projects:
            print("❌ PROJECTS is empty or contains no valid project names")
            return False
        print(f"✅ Found {len(projects)} projects: {', '.join(projects)}")
    
    # Check optional variables
    common_path = os.getenv('COMMON_PATH')
    if common_path:
        print(f"✅ COMMON_PATH: {common_path}")
    else:
        print("ℹ️  COMMON_PATH: not set (optional)")
    
    return True


def test_github_connection():
    """Test GitHub API connection."""
    from github import Github
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not set")
        return False
    
    try:
        github = Github(token)
        user = github.get_user()
        print(f"✅ GitHub connection successful: {user.login}")
        return True
    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")
        return False


def main():
    """Run all checks."""
    print("🔍 Checking prerequisites and configuration...")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Git", check_git),
        ("git-filter-repo", check_git_filter_repo),
        ("Python Dependencies", check_python_dependencies),
        ("Environment File", check_env_file),
        ("GitHub Connection", test_github_connection),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! You're ready to run the repository splitter.")
        print("\nNext steps:")
        print("1. Review your configuration in .env")
        print("2. Run: python split_repo_agent.py --dry-run")
        print("3. If dry run looks good, run: python split_repo_agent.py")
        
        # Show mode-specific information
        load_dotenv()
        mode = os.getenv('MODE', 'branch').lower()
        if mode == 'branch':
            branches = os.getenv('BRANCHES', '').split(',')
            branches = [branch.strip() for branch in branches if branch.strip()]
            print(f"\nMode: Branch-based splitting")
            print(f"Will create {len(branches)} repositories (one per branch)")
        else:
            projects = os.getenv('PROJECTS', '').split(',')
            projects = [project.strip() for project in projects if project.strip()]
            print(f"\nMode: Project-based splitting")
            print(f"Will create {len(projects)} repositories (one per project)")
        
        common_path = os.getenv('COMMON_PATH')
        if common_path:
            print(f"Plus 1 common-libs repository (from {common_path})")
    else:
        print("❌ Some checks failed. Please fix the issues above before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
