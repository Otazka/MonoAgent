#!/usr/bin/env python3
"""
Force update existing repositories with correct content
"""

import os
import subprocess
import tempfile
import shutil
from split_repo_agent import RepoSplitter, RepoSplitterConfig

def force_update_repositories():
    """Force update existing repositories with correct content."""
    
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    config = RepoSplitterConfig(
        source_repo_url=os.getenv('SOURCE_REPO_URL'),
        mode='project',
        projects=os.getenv('PROJECTS', '').split(','),
        common_path=os.getenv('COMMON_PATH'),
        org=os.getenv('ORG'),
        github_token=os.getenv('GITHUB_TOKEN'),
        dry_run=False
    )
    
    with RepoSplitter(config) as splitter:
        # Clone source repo
        splitter.clone_source_repo()
        
        # Force update each project
        for project in config.projects:
            project = project.strip()
            if not project:
                continue
                
            repo_name = f"{project}-app"
            repo_url = f"https://github.com/{config.org}/{repo_name}.git"
            
            print(f"Force updating {repo_name}...")
            
            # Extract project to temp directory
            project_repo_path = os.path.join(splitter.temp_dir, f"project_{project}")
            
            # Clone the mirror repo
            splitter.run_git_command(['git', 'clone', splitter.source_repo_path, project_repo_path])
            
            # Change to the project repo directory
            os.chdir(project_repo_path)
            
            # Check if the project directory exists
            if not os.path.exists(project):
                print(f"Warning: Project directory '{project}' not found")
                continue
            
            # Use git filter-repo to extract only the project path
            splitter.run_git_command([
                'git', 'filter-repo',
                '--path', f'{project}/',
                '--path-rename', f'{project}/:',
                '--force'
            ])
            
            # Check if main branch exists after filtering
            result = splitter.run_git_command(['git', 'branch', '--list', 'main'], check=False)
            if not result.stdout.strip():
                splitter.run_git_command(['git', 'checkout', '-b', 'main'])
            
            # Remove remote origin if it exists
            result = splitter.run_git_command(['git', 'remote', 'remove', 'origin'], check=False)
            
            # Add new remote
            splitter.run_git_command(['git', 'remote', 'add', 'origin', repo_url])
            
            # Force push to update the repository
            splitter.run_git_command(['git', 'push', '-f', 'origin', 'main'])
            
            print(f"✅ Updated {repo_name}")
        
        # Force update common libraries
        if config.common_path:
            repo_name = "common-libs"
            repo_url = f"https://github.com/{config.org}/{repo_name}.git"
            
            print(f"Force updating {repo_name}...")
            
            common_repo_path = os.path.join(splitter.temp_dir, "common_libs")
            
            # Clone the mirror repo
            splitter.run_git_command(['git', 'clone', splitter.source_repo_path, common_repo_path])
            
            # Change to the common repo directory
            os.chdir(common_repo_path)
            
            # Use git filter-repo to extract only the common path
            splitter.run_git_command([
                'git', 'filter-repo',
                '--path', f'{config.common_path}/',
                '--path-rename', f'{config.common_path}/:',
                '--force'
            ])
            
            # Check if main branch exists after filtering
            result = splitter.run_git_command(['git', 'branch', '--list', 'main'], check=False)
            if not result.stdout.strip():
                splitter.run_git_command(['git', 'checkout', '-b', 'main'])
            
            # Remove remote origin if it exists
            result = splitter.run_git_command(['git', 'remote', 'remove', 'origin'], check=False)
            
            # Add new remote
            splitter.run_git_command(['git', 'remote', 'add', 'origin', repo_url])
            
            # Force push to update the repository
            splitter.run_git_command(['git', 'push', '-f', 'origin', 'main'])
            
            print(f"✅ Updated {repo_name}")

if __name__ == "__main__":
    force_update_repositories()
